"""
Utilitários de segurança para mascaramento de dados sensíveis
"""
import re
from typing import Any, Dict, List, Union


class DataMasker:
    """Classe para mascaramento de dados sensíveis"""
    
    # Padrões para identificar dados sensíveis
    SENSITIVE_PATTERNS = {
        'api_key': [
            r'(api[_-]?key[s]?)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
            r'(openai[_-]?api[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
            r'(secret[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?',
            r'(access[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?'
        ],
        'cnpj': [
            r'(\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2})'
        ],
        'cpf': [
            r'(\d{3}\.?\d{3}\.?\d{3}\-?\d{2})'
        ],
        'email': [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ],
        'phone': [
            r'(\(?[0-9]{2}\)?\s?[0-9]{4,5}\-?[0-9]{4})'
        ],
        'credit_card': [
            r'(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})'
        ]
    }
    
    @classmethod
    def mask_string(cls, text: str, mask_char: str = "*") -> str:
        """
        Mascara dados sensíveis em uma string
        
        Args:
            text: Texto a ser mascarado
            mask_char: Caractere para mascaramento
            
        Returns:
            Texto com dados sensíveis mascarados
        """
        if not isinstance(text, str):
            return text
        
        masked_text = text
        
        for data_type, patterns in cls.SENSITIVE_PATTERNS.items():
            for pattern in patterns:
                if data_type == 'api_key':
                    # Para chaves de API, mantém apenas os primeiros e últimos caracteres
                    def mask_api_key(match):
                        key_name = match.group(1)
                        key_value = match.group(2)
                        if len(key_value) > 8:
                            masked_value = key_value[:4] + mask_char * (len(key_value) - 8) + key_value[-4:]
                        else:
                            masked_value = mask_char * len(key_value)
                        return f"{key_name}: {masked_value}"
                    
                    masked_text = re.sub(pattern, mask_api_key, masked_text, flags=re.IGNORECASE)
                
                elif data_type in ['cnpj', 'cpf']:
                    # Para documentos, mantém apenas os últimos dígitos
                    def mask_document(match):
                        doc = match.group(1)
                        # Remove formatação
                        clean_doc = re.sub(r'[^\d]', '', doc)
                        if len(clean_doc) >= 4:
                            masked = mask_char * (len(clean_doc) - 4) + clean_doc[-4:]
                        else:
                            masked = mask_char * len(clean_doc)
                        return masked
                    
                    masked_text = re.sub(pattern, mask_document, masked_text)
                
                elif data_type == 'email':
                    # Para emails, mantém apenas o domínio
                    def mask_email(match):
                        email = match.group(1)
                        local, domain = email.split('@')
                        masked_local = local[0] + mask_char * (len(local) - 1) if len(local) > 1 else mask_char
                        return f"{masked_local}@{domain}"
                    
                    masked_text = re.sub(pattern, mask_email, masked_text)
                
                else:
                    # Para outros tipos, mascara completamente
                    masked_text = re.sub(pattern, mask_char * 8, masked_text)
        
        return masked_text
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any], mask_char: str = "*") -> Dict[str, Any]:
        """
        Mascara dados sensíveis em um dicionário
        
        Args:
            data: Dicionário a ser mascarado
            mask_char: Caractere para mascaramento
            
        Returns:
            Dicionário com dados sensíveis mascarados
        """
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        
        # Chaves que devem ser mascaradas
        sensitive_keys = {
            'api_key', 'openai_api_key', 'secret_key', 'access_token',
            'password', 'passwd', 'pwd', 'token', 'authorization',
            'cnpj', 'cpf', 'email', 'phone', 'telefone', 'celular'
        }
        
        for key, value in data.items():
            key_lower = key.lower()
            
            if isinstance(value, dict):
                masked_data[key] = cls.mask_dict(value, mask_char)
            elif isinstance(value, list):
                masked_data[key] = [cls.mask_dict(item, mask_char) if isinstance(item, dict) 
                                  else cls.mask_string(str(item), mask_char) if isinstance(item, str)
                                  else item for item in value]
            elif isinstance(value, str):
                if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
                    # Mascara completamente chaves sensíveis
                    if len(value) > 8:
                        masked_data[key] = value[:2] + mask_char * (len(value) - 4) + value[-2:]
                    else:
                        masked_data[key] = mask_char * len(value)
                else:
                    # Aplica mascaramento por padrão
                    masked_data[key] = cls.mask_string(value, mask_char)
            else:
                masked_data[key] = value
        
        return masked_data
    
    @classmethod
    def mask_log_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mascara dados sensíveis em um registro de log
        
        Args:
            record: Registro de log
            
        Returns:
            Registro com dados sensíveis mascarados
        """
        masked_record = record.copy()
        
        # Campos que podem conter dados sensíveis
        fields_to_mask = ['message', 'msg', 'args', 'extra', 'details']
        
        for field in fields_to_mask:
            if field in masked_record:
                if isinstance(masked_record[field], str):
                    masked_record[field] = cls.mask_string(masked_record[field])
                elif isinstance(masked_record[field], dict):
                    masked_record[field] = cls.mask_dict(masked_record[field])
        
        return masked_record


def mask_sensitive_data(data: Union[str, Dict[str, Any], List[Any]]) -> Union[str, Dict[str, Any], List[Any]]:
    """
    Função utilitária para mascarar dados sensíveis
    
    Args:
        data: Dados a serem mascarados
        
    Returns:
        Dados com informações sensíveis mascaradas
    """
    if isinstance(data, str):
        return DataMasker.mask_string(data)
    elif isinstance(data, dict):
        return DataMasker.mask_dict(data)
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data


def is_sensitive_field(field_name: str) -> bool:
    """
    Verifica se um campo contém dados sensíveis baseado no nome
    
    Args:
        field_name: Nome do campo
        
    Returns:
        True se o campo for sensível
    """
    sensitive_keywords = {
        'api_key', 'openai_api_key', 'secret_key', 'access_token',
        'password', 'passwd', 'pwd', 'token', 'authorization',
        'cnpj', 'cpf', 'email', 'phone', 'telefone', 'celular',
        'credit_card', 'cartao', 'card_number'
    }
    
    field_lower = field_name.lower()
    return any(keyword in field_lower for keyword in sensitive_keywords)


def validate_api_key_format(api_key: str) -> bool:
    """
    Valida o formato de uma chave de API
    
    Args:
        api_key: Chave de API a ser validada
        
    Returns:
        True se o formato for válido
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Chave deve ter pelo menos 20 caracteres
    if len(api_key) < 20:
        return False
    
    # Chave deve conter apenas caracteres alfanuméricos, hífens e underscores
    if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza um nome de arquivo removendo caracteres perigosos
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Nome do arquivo sanitizado
    """
    if not filename:
        return "unnamed_file"
    
    # Remove caracteres perigosos
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove espaços múltiplos e substitui por underscore
    sanitized = re.sub(r'\s+', '_', sanitized)
    
    # Remove pontos no início e fim
    sanitized = sanitized.strip('.')
    
    # Limita o tamanho
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        sanitized = name[:max_name_length] + ('.' + ext if ext else '')
    
    return sanitized or "unnamed_file"

