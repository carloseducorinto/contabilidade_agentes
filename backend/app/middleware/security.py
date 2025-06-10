"""
Middleware de segurança para FastAPI
"""
import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from ..config import get_settings, is_production, get_cors_config
from ..logging_config import get_logger
from ..utils.security import sanitize_filename, mask_sensitive_data

settings = get_settings()
logger = get_logger("SecurityMiddleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar cabeçalhos de segurança"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Adiciona ID único à requisição para rastreamento
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Adiciona cabeçalhos de segurança
            if is_production():
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["X-XSS-Protection"] = "1; mode=block"
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                response.headers["Content-Security-Policy"] = "default-src 'self'"
            
            # Adiciona cabeçalhos informativos
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
            response.headers["X-API-Version"] = settings.app_version
            
            # Remove cabeçalhos que expõem informações do servidor
            response.headers.pop("Server", None)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no middleware de segurança: {str(e)}", extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method
            })
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware simples de rate limiting"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}  # Em produção, usar Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not is_production():
            # Desabilita rate limiting em desenvolvimento
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Limpa requisições antigas
        self._cleanup_old_requests(current_time)
        
        # Verifica rate limit
        if client_ip in self.requests:
            request_times = self.requests[client_ip]
            recent_requests = [t for t in request_times if current_time - t < 60]
            
            if len(recent_requests) >= self.calls_per_minute:
                logger.warning(f"Rate limit excedido para IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Máximo de {self.calls_per_minute} requisições por minuto",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )
            
            self.requests[client_ip] = recent_requests + [current_time]
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém o IP do cliente considerando proxies"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, current_time: float):
        """Remove requisições antigas do cache"""
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if current_time - t < 60]
            if not self.requests[ip]:
                del self.requests[ip]


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware para validação de requisições"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Valida tamanho do corpo da requisição
        if hasattr(request, "headers"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_file_size:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "Request too large",
                        "message": f"Tamanho máximo permitido: {settings.max_file_size / (1024*1024):.1f}MB"
                    }
                )
        
        # Valida User-Agent (bloqueia bots maliciosos conhecidos)
        user_agent = request.headers.get("user-agent", "").lower()
        blocked_agents = ["sqlmap", "nikto", "nmap", "masscan", "zap"]
        
        if any(agent in user_agent for agent in blocked_agents):
            logger.warning(f"Bloqueado User-Agent suspeito: {user_agent}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Forbidden", "message": "Access denied"}
            )
        
        # Sanitiza parâmetros de query
        if request.query_params:
            sanitized_params = {}
            for key, value in request.query_params.items():
                sanitized_key = sanitize_filename(key)
                sanitized_value = sanitize_filename(value) if isinstance(value, str) else value
                sanitized_params[sanitized_key] = sanitized_value
            
            # Em produção, você poderia substituir os parâmetros sanitizados
            # Por simplicidade, apenas logamos se houve mudanças
            if sanitized_params != dict(request.query_params):
                logger.info("Parâmetros de query sanitizados", extra={
                    "original": dict(request.query_params),
                    "sanitized": sanitized_params
                })
        
        return await call_next(request)


def setup_cors_middleware(app):
    """Configura middleware de CORS baseado no ambiente"""
    cors_config = get_cors_config()
    
    if is_production():
        # Em produção, CORS mais restritivo
        allowed_origins = [
            origin for origin in cors_config["allow_origins"] 
            if origin != "*"
        ]
        
        if not allowed_origins:
            # Se não há origens específicas configuradas, usa padrões seguros
            allowed_origins = [
                "https://localhost:3000",
                "https://localhost:8501",
                "https://127.0.0.1:3000",
                "https://127.0.0.1:8501"
            ]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Response-Time"]
        )
        
        logger.info(f"CORS configurado para produção com origens: {allowed_origins}")
    
    else:
        # Em desenvolvimento, CORS mais permissivo
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_config["allow_origins"],
            allow_credentials=cors_config["allow_credentials"],
            allow_methods=cors_config["allow_methods"],
            allow_headers=cors_config["allow_headers"]
        )
        
        logger.info("CORS configurado para desenvolvimento (permissivo)")


def setup_security_middleware(app):
    """Configura todos os middlewares de segurança"""
    
    # Rate limiting (apenas em produção)
    if is_production():
        app.add_middleware(RateLimitMiddleware, calls_per_minute=60)
        logger.info("Rate limiting habilitado (60 req/min)")
    
    # Validação de requisições
    app.add_middleware(RequestValidationMiddleware)
    logger.info("Middleware de validação de requisições habilitado")
    
    # Cabeçalhos de segurança
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Middleware de cabeçalhos de segurança habilitado")
    
    # CORS
    setup_cors_middleware(app)


class SecurityConfig:
    """Configurações de segurança centralizadas"""
    
    @staticmethod
    def validate_environment():
        """Valida configurações de segurança do ambiente"""
        issues = []
        
        # Verifica chave secreta em produção
        if is_production() and settings.secret_key == "dev-secret-key":
            issues.append("SECRET_KEY padrão sendo usada em produção")
        
        # Verifica CORS em produção
        if is_production() and "*" in settings.cors_origins:
            issues.append("CORS configurado para aceitar qualquer origem em produção")
        
        # Verifica se HTTPS está sendo usado em produção
        if is_production() and not any("https://" in origin for origin in settings.cors_origins):
            issues.append("Nenhuma origem HTTPS configurada em produção")
        
        # Verifica configuração de logs
        if is_production() and settings.log_level.upper() == "DEBUG":
            issues.append("Log level DEBUG em produção pode expor informações sensíveis")
        
        if issues:
            logger.warning("Problemas de segurança detectados:", extra={"issues": issues})
            return False, issues
        
        logger.info("Configurações de segurança validadas com sucesso")
        return True, []
    
    @staticmethod
    def get_security_headers() -> dict:
        """Retorna cabeçalhos de segurança recomendados"""
        if is_production():
            return {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Content-Security-Policy": "default-src 'self'",
                "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
            }
        else:
            return {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN"
            }

