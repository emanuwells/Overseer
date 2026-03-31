"""
Validador de Dados
Versão: 0.1.0
Autor: Emanuel Ferreira (emanuel.ferreira@cm-maia.pt)

Valida dados antes de inserir na base de dados.
"""

from datetime import datetime
from typing import Any, Optional, Tuple, List
from dateutil import parser
import pytz
from overseer_sdk.logger import get_logger


class DataValidator:
    """
    Validador de dados com regras configuráveis.
    Valida tipos, formatos, valores obrigatórios e ranges.
    """
    
    def __init__(self, timezone: str = "Europe/Lisbon"):
        """
        Inicializa o validador.
        
        Args:
            timezone: Timezone para parsing de datas
        """
        self.logger = get_logger("validator")
        self.tz = pytz.timezone(timezone)
        self.errors: List[str] = []
    
    def validate_timestamp(
        self,
        value: Any,
        field_name: str = "data"
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Valida e converte um valor para timestamp.
        
        Aceita:
        - String no formato 'YYYY-MM-DD HH:MM:SS'
        - String ISO 8601
        - Objeto datetime
        - Timestamps Unix
        
        Args:
            value: Valor a validar
            field_name: Nome do campo (para mensagens de erro)
            
        Returns:
            Tupla (válido, datetime_convertido)
        """
        if value is None:
            error = f"Campo {field_name} é obrigatório"
            self.errors.append(error)
            self.logger.warning(error)
            return False, None
        
        try:
            # Se já for datetime
            if isinstance(value, datetime):
                return True, value
            
            # Se for string, tenta fazer parsing
            if isinstance(value, str):
                # Remove espaços extras
                value = value.strip()
                
                # Tenta formato comum 'YYYY-MM-DD HH:MM:SS'
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    return True, dt
                except ValueError:
                    pass
                
                # Tenta parsing genérico
                try:
                    dt = parser.parse(value)
                    return True, dt
                except Exception:
                    pass
            
            # Se for número (timestamp Unix)
            if isinstance(value, (int, float)):
                dt = datetime.fromtimestamp(value)
                return True, dt
            
            error = f"Campo {field_name} com formato inválido: {value}"
            self.errors.append(error)
            self.logger.warning(error)
            return False, None
            
        except Exception as e:
            error = f"Erro ao validar {field_name}: {e}"
            self.errors.append(error)
            self.logger.error(error)
            return False, None
    
    def validate_numeric(
        self,
        value: Any,
        field_name: str = "valor",
        allow_negative: bool = True,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        data_type: str = "float"
    ) -> Tuple[bool, Optional[float]]:
        """
        Valida e converte um valor numérico.
        
        Args:
            value: Valor a validar
            field_name: Nome do campo
            allow_negative: Permitir valores negativos
            min_value: Valor mínimo permitido
            max_value: Valor máximo permitido
            data_type: Tipo esperado ('int', 'float', 'decimal')
            
        Returns:
            Tupla (válido, valor_convertido)
        """
        if value is None or value == '':
            error = f"Campo {field_name} é obrigatório"
            self.errors.append(error)
            self.logger.warning(error)
            return False, None
        
        try:
            # Converte para float
            if isinstance(value, str):
                # Remove espaços e substitui vírgula por ponto
                value = value.strip().replace(',', '.')
            
            numeric_value = float(value)
            
            # Valida se permite negativos
            if not allow_negative and numeric_value < 0:
                error = f"Campo {field_name} não pode ser negativo: {numeric_value}"
                self.errors.append(error)
                self.logger.warning(error)
                return False, None
            
            # Valida range mínimo
            if min_value is not None and numeric_value < min_value:
                error = f"Campo {field_name} abaixo do mínimo ({min_value}): {numeric_value}"
                self.errors.append(error)
                self.logger.warning(error)
                return False, None
            
            # Valida range máximo
            if max_value is not None and numeric_value > max_value:
                error = f"Campo {field_name} acima do máximo ({max_value}): {numeric_value}"
                self.errors.append(error)
                self.logger.warning(error)
                return False, None
            
            # Converte para tipo específico
            if data_type == "int":
                numeric_value = int(numeric_value)
            
            return True, numeric_value
            
        except ValueError as e:
            error = f"Campo {field_name} não é numérico: {value}"
            self.errors.append(error)
            self.logger.warning(error)
            return False, None
        except Exception as e:
            error = f"Erro ao validar {field_name}: {e}"
            self.errors.append(error)
            self.logger.error(error)
            return False, None
    
    def validate_string(
        self,
        value: Any,
        field_name: str,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        allowed_values: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida um campo de texto.
        
        Args:
            value: Valor a validar
            field_name: Nome do campo
            required: Se é obrigatório
            min_length: Comprimento mínimo
            max_length: Comprimento máximo
            allowed_values: Lista de valores permitidos
            
        Returns:
            Tupla (válido, valor_limpo)
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            if required:
                error = f"Campo {field_name} é obrigatório"
                self.errors.append(error)
                self.logger.warning(error)
                return False, None
            return True, None
        
        try:
            str_value = str(value).strip()
            
            # Valida comprimento mínimo
            if min_length and len(str_value) < min_length:
                error = f"Campo {field_name} muito curto (mín: {min_length}): '{str_value}'"
                self.errors.append(error)
                self.logger.warning(error)
                return False, None
            
            # Valida comprimento máximo
            if max_length and len(str_value) > max_length:
                error = f"Campo {field_name} muito longo (máx: {max_length}): '{str_value[:50]}...'"
                self.errors.append(error)
                self.logger.warning(error)
                return False, None
            
            # Valida valores permitidos
            if allowed_values and str_value not in allowed_values:
                error = f"Campo {field_name} com valor inválido: '{str_value}'. Permitidos: {allowed_values}"
                self.errors.append(error)
                self.logger.warning(error)
                return False, None
            
            return True, str_value
            
        except Exception as e:
            error = f"Erro ao validar {field_name}: {e}"
            self.errors.append(error)
            self.logger.error(error)
            return False, None
    
    def validate_year(
        self,
        value: Any,
        field_name: str = "ano"
    ) -> Tuple[bool, Optional[int]]:
        """
        Valida um ano (entre 1900 e ano atual + 10).
        
        Args:
            value: Valor a validar
            field_name: Nome do campo
            
        Returns:
            Tupla (válido, ano)
        """
        current_year = datetime.now().year
        return self.validate_numeric(
            value,
            field_name=field_name,
            allow_negative=False,
            min_value=1900,
            max_value=current_year + 10,
            data_type="int"
        )
    
    def get_errors(self) -> List[str]:
        """
        Retorna lista de erros acumulados.
        
        Returns:
            Lista de mensagens de erro
        """
        return self.errors.copy()
    
    def clear_errors(self):
        """Limpa a lista de erros."""
        self.errors = []
    
    def has_errors(self) -> bool:
        """
        Verifica se há erros acumulados.
        
        Returns:
            True se houver erros
        """
        return len(self.errors) > 0


class RowValidator:
    """
    Validador de linha completa de dados.
    Valida múltiplos campos de uma vez.
    """
    
    def __init__(self):
        """Inicializa o validador de linhas."""
        self.validator = DataValidator()
        self.logger = get_logger("row_validator")
    
    def validate_indicadores_row(
        self,
        row: dict,
        series_config: dict
    ) -> Tuple[bool, dict]:
        """
        Valida uma linha para inserção na tabela Indicadores.
        
        Args:
            row: Dicionário com os dados da linha
            series_config: Configuração da série (validações específicas)
            
        Returns:
            Tupla (válido, dados_validados)
        """
        self.validator.clear_errors()
        validated = {}
        
        # Valida nome (obrigatório)
        valid, nome = self.validator.validate_string(
            row.get('nome'),
            'nome',
            required=True,
            min_length=1,
            max_length=100
        )
        if not valid:
            return False, {}
        validated['nome'] = nome
        
        # Valida data (obrigatório)
        valid, data = self.validator.validate_timestamp(
            row.get('data'),
            'data'
        )
        if not valid:
            return False, {}
        validated['data'] = data
        
        # Valida valor (obrigatório, numérico)
        value_type = series_config.get('validation', {}).get('value_type', 'float')
        min_val = series_config.get('validation', {}).get('value_min')
        max_val = series_config.get('validation', {}).get('value_max')
        
        valid, valor = self.validator.validate_numeric(
            row.get('valor'),
            'valor',
            allow_negative=min_val is None or min_val < 0,
            min_value=min_val,
            max_value=max_val,
            data_type=value_type
        )
        if not valid:
            return False, {}
        validated['valor'] = valor
        
        # Valida mês (opcional)
        if 'mes' in row:
            valid, mes = self.validator.validate_string(
                row.get('mes'),
                'mes',
                required=False,
                max_length=50
            )
            validated['mes'] = mes
        
        if self.validator.has_errors():
            self.logger.error(f"Erros de validação: {self.validator.get_errors()}")
            return False, {}
        
        return True, validated
    
    def validate_baze21ra_row(
        self,
        row: dict,
        series_config: dict
    ) -> Tuple[bool, dict]:
        """
        Valida uma linha para inserção na tabela baze21RA.
        
        Args:
            row: Dicionário com os dados da linha
            series_config: Configuração da série
            
        Returns:
            Tupla (válido, dados_validados)
        """
        self.validator.clear_errors()
        validated = {}
        
        # Valida nome curto (obrigatório)
        valid, nome = self.validator.validate_string(
            row.get('nome_curto'),
            'nome_curto',
            required=True
        )
        if not valid:
            return False, {}
        validated['nome_curto'] = nome
        
        # Valida ano (obrigatório)
        valid, ano = self.validator.validate_year(row.get('ano'), 'ano')
        if not valid:
            return False, {}
        validated['ano'] = ano
        
        # Valida valor (obrigatório, numérico)
        value_type = series_config.get('validation', {}).get('value_type', 'float')
        min_val = series_config.get('validation', {}).get('value_min')
        max_val = series_config.get('validation', {}).get('value_max')
        
        valid, valor = self.validator.validate_numeric(
            row.get('valor'),
            'valor',
            allow_negative=min_val is None or min_val < 0,
            min_value=min_val,
            max_value=max_val,
            data_type=value_type
        )
        if not valid:
            return False, {}
        validated['valor'] = valor
        
        if self.validator.has_errors():
            self.logger.error(f"Erros de validação: {self.validator.get_errors()}")
            return False, {}
        
        return True, validated


if __name__ == "__main__":
    # Teste do validador
    print("🧪 Teste do validador\n")
    
    validator = DataValidator()
    
    # Teste timestamp
    print("1. Validar timestamp:")
    valid, dt = validator.validate_timestamp("2024-06-01 00:00:00")
    print(f"   Válido: {valid} | Datetime: {dt}\n")
    
    # Teste numérico
    print("2. Validar numérico:")
    valid, num = validator.validate_numeric("1234.56", min_value=0)
    print(f"   Válido: {valid} | Valor: {num}\n")
    
    # Teste ano
    print("3. Validar ano:")
    valid, ano = validator.validate_year(2024)
    print(f"   Válido: {valid} | Ano: {ano}\n")
    
    print("✅ Testes concluídos")
