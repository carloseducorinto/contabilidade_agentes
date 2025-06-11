"""
Validadores de entrada para segurança adicional
"""
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import validator, ValidationError
from ..exceptions import ValidationError as CustomValidationError


class InputValidator:
    """Classe para validação de entradas do usuário"""
    
    # Padrões de validação
    CNPJ_PATTERN = re.compile(r'^\d{2}\.?\d{3}\.?\d{3}\/?\d{4}\-?\d{2}$')
    CPF_PATTERN = re.compile(r'^\d{3}\.?\d{3}\.?\d{3}\-?\d{2}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\(?[0-9]{2}\)?\s?[0-9]{4,5}\-?[0-9]{4}$')
    
    # Caracteres perigosos para injeção
    DANGEROUS_CHARS = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(--|\#|\/\*|\*\/)',
        r'(\bOR\b.*\b=\b|\bAND\b.*\b=\b)',
        r'(\bUNION\b.*\bSELECT\b)'
    ]
    
    @classmethod
    def validate_cnpj(cls, cnpj: str) -> bool:
        """
        Valida formato e dígitos verificadores do CNPJ
        
        Args:
            cnpj: CNPJ a ser validado
            
        Returns:
            True se válido
        """
        if not cnpj or not isinstance(cnpj, str):
            return False
        
        # Remove formatação
        clean_cnpj = re.sub(r'[^\d]', '', cnpj)
        
        # Verifica se tem 14 dígitos
        if len(clean_cnpj) != 14:
            return False
        
        # Verifica se não são todos iguais
        if clean_cnpj == clean_cnpj[0] * 14:
            return False
        
        # Calcula primeiro dígito verificador
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(clean_cnpj[i]) * weights1[i] for i in range(12))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calcula segundo dígito verificador
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(int(clean_cnpj[i]) * weights2[i] for i in range(13))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        # Verifica dígitos
        return int(clean_cnpj[12]) == digit1 and int(clean_cnpj[13]) == digit2
    
    @classmethod
    def validate_cpf(cls, cpf: str) -> bool:
        """
        Valida formato e dígitos verificadores do CPF
        
        Args:
            cpf: CPF a ser validado
            
        Returns:
            True se válido
        """
        if not cpf or not isinstance(cpf, str):
            return False
        
        # Remove formatação
        clean_cpf = re.sub(r'[^\d]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(clean_cpf) != 11:
            return False
        
        # Verifica se não são todos iguais
        if clean_cpf == clean_cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        sum1 = sum(int(clean_cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calcula segundo dígito verificador
        sum2 = sum(int(clean_cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        # Verifica dígitos
        return int(clean_cpf[9]) == digit1 and int(clean_cpf[10]) == digit2
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Valida formato de email
        
        Args:
            email: Email a ser validado
            
        Returns:
            True se válido
        """
        if not email or not isinstance(email, str):
            return False
        
        return bool(cls.EMAIL_PATTERN.match(email))
    
    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """
        Valida formato de telefone brasileiro
        
        Args:
            phone: Telefone a ser validado
            
        Returns:
            True se válido
        """
        if not phone or not isinstance(phone, str):
            return False
        
        return bool(cls.PHONE_PATTERN.match(phone))
    
    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        """
        Verifica se o texto contém padrões de SQL injection
        
        Args:
            text: Texto a ser verificado
            
        Returns:
            True se contém padrões suspeitos
        """
        if not text or not isinstance(text, str):
            return False
        
        text_upper = text.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def check_xss_patterns(cls, text: str) -> bool:
        """
        Verifica se o texto contém padrões de XSS
        
        Args:
            text: Texto a ser verificado
            
        Returns:
            True se contém padrões suspeitos
        """
        if not text or not isinstance(text, str):
            return False
        
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def sanitize_string(cls, text: str, max_length: int = 1000) -> str:
        """
        Sanitiza uma string removendo caracteres perigosos
        
        Args:
            text: Texto a ser sanitizado
            max_length: Tamanho máximo permitido
            
        Returns:
            Texto sanitizado
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Limita tamanho
        sanitized = text[:max_length]
        
        # Remove caracteres perigosos
        for char in cls.DANGEROUS_CHARS:
            sanitized = sanitized.replace(char, '')
        
        # Remove quebras de linha múltiplas
        sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
        
        # Remove espaços múltiplos
        sanitized = re.sub(r' {3,}', '  ', sanitized)
        
        return sanitized.strip()
    
    @classmethod
    def validate_file_type(cls, filename: str, allowed_types: List[str]) -> bool:
        """
        Valida se o tipo de arquivo é permitido
        
        Args:
            filename: Nome do arquivo
            allowed_types: Lista de extensões permitidas
            
        Returns:
            True se o tipo é permitido
        """
        if not filename or not isinstance(filename, str):
            return False
        
        # Extrai extensão
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        return extension in [t.lower() for t in allowed_types]
    
    @classmethod
    def validate_file_size(cls, file_size: int, max_size: int) -> bool:
        """
        Valida se o tamanho do arquivo é permitido
        
        Args:
            file_size: Tamanho do arquivo em bytes
            max_size: Tamanho máximo permitido em bytes
            
        Returns:
            True se o tamanho é permitido
        """
        return 0 < file_size <= max_size
    
    @classmethod
    def validate_numeric_range(cls, value: Union[int, float], min_val: Optional[Union[int, float]] = None, 
                             max_val: Optional[Union[int, float]] = None) -> bool:
        """
        Valida se um valor numérico está dentro do range permitido
        
        Args:
            value: Valor a ser validado
            min_val: Valor mínimo (opcional)
            max_val: Valor máximo (opcional)
            
        Returns:
            True se está no range
        """
        if not isinstance(value, (int, float)):
            return False
        
        if min_val is not None and value < min_val:
            return False
        
        if max_val is not None and value > max_val:
            return False
        
        return True
    
    @classmethod
    def validate_date_format(cls, date_str: str) -> bool:
        """
        Valida formato de data (YYYY-MM-DD)
        
        Args:
            date_str: String de data
            
        Returns:
            True se o formato é válido
        """
        if not date_str or not isinstance(date_str, str):
            return False
        
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @classmethod
    def validate_request_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e sanitiza dados de requisição
        
        Args:
            data: Dados da requisição
            
        Returns:
            Dados validados e sanitizados
            
        Raises:
            CustomValidationError: Se dados inválidos
        """
        if not isinstance(data, dict):
            raise CustomValidationError("Dados devem ser um objeto JSON válido")
        
        validated_data = {}
        errors = []
        
        for key, value in data.items():
            # Sanitiza chave
            clean_key = cls.sanitize_string(key, 100)
            if not clean_key:
                errors.append(f"Chave inválida: {key}")
                continue
            
            # Valida valor baseado no tipo
            if isinstance(value, str):
                # Verifica padrões maliciosos
                if cls.check_sql_injection(value):
                    errors.append(f"Padrão SQL injection detectado em {key}")
                    continue
                
                if cls.check_xss_patterns(value):
                    errors.append(f"Padrão XSS detectado em {key}")
                    continue
                
                # Sanitiza string
                validated_data[clean_key] = cls.sanitize_string(value)
            
            elif isinstance(value, (int, float)):
                # Valida ranges numéricos básicos
                if not cls.validate_numeric_range(value, -999999999, 999999999):
                    errors.append(f"Valor numérico fora do range em {key}")
                    continue
                
                validated_data[clean_key] = value
            
            elif isinstance(value, dict):
                # Recursivamente valida objetos aninhados
                try:
                    validated_data[clean_key] = cls.validate_request_data(value)
                except CustomValidationError as e:
                    errors.append(f"Erro em {key}: {str(e)}")
            
            elif isinstance(value, list):
                # Valida listas (limitando tamanho)
                if len(value) > 100:
                    errors.append(f"Lista muito grande em {key} (máximo 100 itens)")
                    continue
                
                validated_list = []
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        validated_list.append(cls.sanitize_string(item))
                    elif isinstance(item, (int, float, bool)):
                        validated_list.append(item)
                    elif isinstance(item, dict):
                        try:
                            validated_list.append(cls.validate_request_data(item))
                        except CustomValidationError as e:
                            errors.append(f"Erro em {key}[{i}]: {str(e)}")
                
                validated_data[clean_key] = validated_list
            
            else:
                # Outros tipos (bool, None)
                validated_data[clean_key] = value
        
        if errors:
            raise CustomValidationError(f"Erros de validação: {'; '.join(errors)}")
        
        return validated_data

