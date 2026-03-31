"""
Leitor de Ficheiros Excel
Versão: 0.1.0
Autor: Emanuel Ferreira (emanuel.ferreira@cm-maia.pt)

Lê múltiplos ficheiros Excel com estruturas variáveis e identifica séries de dados.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from overseer_sdk.logger import get_logger


class ExcelReader:
    """
    Leitor inteligente de ficheiros Excel.
    Deteta automaticamente estrutura e identifica séries.
    """
    
    def __init__(self, mappings_config: dict):
        """
        Inicializa o leitor de Excel.
        
        Args:
            mappings_config: Configuração de mapeamentos carregada de mappings.json
        """
        self.logger = get_logger("excel_reader")
        self.config = mappings_config
        self.global_rules = mappings_config.get('global_rules', {})
        self.series_config = mappings_config.get('series_config', {})
    
    def extract_id_from_filename(self, filename: str) -> Optional[str]:
        """
        Extrai o ID_Ind do nome do ficheiro.
        Formato esperado: Ind001_nome_do_indicador.xlsx
        
        Args:
            filename: Nome do ficheiro
            
        Returns:
            ID extraído ou None
        """
        # Padrão: IndXXX ou IndXXXX no início do nome
        pattern = r'^(Ind\d{3,4})'
        match = re.match(pattern, filename, re.IGNORECASE)
        
        if match:
            id_ind = match.group(1)
            self.logger.debug(f"ID extraído: {id_ind} de {filename}")
            return id_ind
        
        self.logger.warning(f"Não foi possível extrair ID_Ind de: {filename}")
        return None
    
    def find_description_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Identifica a coluna de descrição no DataFrame.
        
        Args:
            df: DataFrame do Excel
            
        Returns:
            Nome da coluna de descrição ou None
        """
        desc_patterns = self.global_rules.get('description_patterns', [
            'descricao', 'descrição', 'Descrição', 'description', 'Description', 'Indicador'
        ])
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for pattern in desc_patterns:
                if pattern.lower() in col_lower:
                    self.logger.debug(f"Coluna de descrição encontrada: {col}")
                    return col
        
        self.logger.warning("Coluna de descrição não encontrada")
        return None
    
    def find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Identifica a coluna de data no DataFrame.
        
        Args:
            df: DataFrame do Excel
            
        Returns:
            Nome da coluna de data ou None
        """
        date_patterns = self.global_rules.get('date_columns', [
            'data', 'Data', 'DATA', 'date', 'Date', 'Ano', 'ano', 'Mês', 'mes', 'Trimestre', 'Semestre'
        ])
        
        for col in df.columns:
            col_str = str(col).strip()
            for pattern in date_patterns:
                if pattern.lower() in col_str.lower():
                    self.logger.debug(f"Coluna de data encontrada: {col}")
                    return col
        
        self.logger.warning("Coluna de data não encontrada")
        return None
    
    def find_value_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Identifica a coluna de valor no DataFrame.
        
        Args:
            df: DataFrame do Excel
            
        Returns:
            Nome da coluna de valor ou None
        """
        value_patterns = self.global_rules.get('value_columns', [
            'valor', 'Valor', 'VALUE', 'value', 'Quantidade', 'Total'
        ])
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for pattern in value_patterns:
                if pattern.lower() in col_lower:
                    self.logger.debug(f"Coluna de valor encontrada: {col}")
                    return col
        
        # Se não encontrar por nome, procura coluna numérica
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # Ignora colunas de ID ou ano
                if 'id' not in str(col).lower() and 'ano' not in str(col).lower():
                    self.logger.debug(f"Coluna de valor (numérica) encontrada: {col}")
                    return col
        
        self.logger.warning("Coluna de valor não encontrada")
        return None
    
    def identify_series(self, df: pd.DataFrame, desc_column: str) -> Optional[Tuple[str, str]]:
        """
        Identifica a série de dados pela descrição.
        
        Args:
            df: DataFrame do Excel
            desc_column: Nome da coluna de descrição
            
        Returns:
            Tupla (nome_curto, descricao) ou None
        """
        # Pega a primeira descrição não-nula
        for desc in df[desc_column].dropna():
            desc_str = str(desc).strip()
            
            # Procura nos series_config se alguma descrição coincide
            for nome_curto, config in self.series_config.items():
                config_desc = config.get('descricao', '').lower()
                
                if config_desc in desc_str.lower() or desc_str.lower() in config_desc:
                    self.logger.info(f"Série identificada: {nome_curto} - {desc_str}")
                    return nome_curto, desc_str
        
        # Se não encontrar, usa a primeira descrição como fallback
        first_desc = df[desc_column].dropna().iloc[0] if not df[desc_column].dropna().empty else "Desconhecido"
        self.logger.warning(f"Série não identificada em config. Usando descrição: {first_desc}")
        
        # Tenta criar nome curto a partir da descrição
        nome_curto = re.sub(r'[^a-zA-Z0-9]', '', str(first_desc)[:20]).lower()
        return nome_curto, str(first_desc)
    
    def determine_frequency(self, date_column: str, df: pd.DataFrame) -> str:
        """
        Determina a frequência dos dados (anual, mensal, trimestral, semestral).
        
        Args:
            date_column: Nome da coluna de data
            df: DataFrame
            
        Returns:
            Frequência ('anual', 'mensal', 'trimestral', 'semestral', 'diario')
        """
        col_lower = date_column.lower()
        
        if 'ano' in col_lower and 'mes' not in col_lower:
            return 'anual'
        elif 'trimestre' in col_lower:
            return 'trimestral'
        elif 'semestre' in col_lower:
            return 'semestral'
        elif 'mes' in col_lower or 'mês' in col_lower:
            return 'mensal'
        elif 'dia' in col_lower or 'data' in col_lower:
            # Tenta inferir pela diferença de datas
            try:
                dates = pd.to_datetime(df[date_column].dropna(), errors='coerce')
                if len(dates) >= 2:
                    diff = (dates.iloc[1] - dates.iloc[0]).days
                    if diff >= 300:
                        return 'anual'
                    elif diff >= 60:
                        return 'trimestral'
                    elif diff >= 20:
                        return 'mensal'
                    else:
                        return 'diario'
            except:
                pass
        
        return 'mensal'  # Default
    
    @staticmethod
    def is_forms_file(filename: str) -> bool:
        """
        Verifica se o ficheiro é um ficheiro Forms (deve ser processado pelo FormsReader).
        
        Args:
            filename: Nome do ficheiro
            
        Returns:
            True se for ficheiro Forms
        """
        # Ficheiros Forms começam com IndXXX- ou IndXXXX-
        pattern = r'^Ind\d{3,4}-'
        return bool(re.match(pattern, filename, re.IGNORECASE))
    
    def read_excel_file(self, file_path: Path) -> Dict:
        """
        Lê um ficheiro Excel e extrai os dados estruturados.
        
        Args:
            file_path: Caminho para o ficheiro Excel
            
        Returns:
            Dicionário com metadados e dados:
            {
                'id_ind': str,
                'nome_curto': str,
                'descricao': str,
                'frequency': str,
                'target_table': str,
                'data': List[Dict]  # Lista de linhas
            }
        """
        self.logger.info(f"📂 A ler ficheiro: {file_path.name}")
        
        # Verifica se é ficheiro Forms (deve ser processado pelo FormsReader)
        if self.is_forms_file(file_path.name):
            self.logger.info(f"⏭️  Ignorado (Forms): {file_path.name}")
            return None
        
        try:
            # Lê o Excel (primeira sheet por padrão)
            df = pd.read_excel(file_path, engine='openpyxl')
            
            if df.empty:
                self.logger.warning(f"Ficheiro vazio: {file_path.name}")
                return None
            
            self.logger.debug(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
            self.logger.debug(f"Colunas: {list(df.columns)}")
            
            # Extrai ID do nome do ficheiro
            id_ind = self.extract_id_from_filename(file_path.name)
            
            # Identifica colunas importantes
            desc_column = self.find_description_column(df)
            date_column = self.find_date_column(df)
            value_column = self.find_value_column(df)
            
            if not desc_column or not date_column or not value_column:
                self.logger.error(f"Colunas essenciais não encontradas em {file_path.name}")
                self.logger.error(f"Descrição: {desc_column}, Data: {date_column}, Valor: {value_column}")
                return None
            
            # Identifica a série
            nome_curto, descricao = self.identify_series(df, desc_column)
            
            # Determina frequência
            frequency = self.determine_frequency(date_column, df)
            
            # Determina tabela de destino
            series_conf = self.series_config.get(nome_curto, {})
            if frequency == 'anual':
                target_table = 'baze21RA'
            else:
                target_table = series_conf.get('target_table', 'Indicadores')
            
            # Extrai os dados
            data_rows = []
            for idx, row in df.iterrows():
                # Ignora linhas vazias
                if pd.isna(row[value_column]) or pd.isna(row[date_column]):
                    continue
                
                data_row = {
                    'nome_curto': nome_curto,
                    'descricao': descricao,
                    'data': row[date_column],
                    'valor': row[value_column]
                }
                
                # Se houver coluna de mês (texto)
                if 'mes' in df.columns or 'Mês' in df.columns:
                    mes_col = 'mes' if 'mes' in df.columns else 'Mês'
                    if not pd.isna(row[mes_col]):
                        data_row['mes'] = str(row[mes_col])
                
                data_rows.append(data_row)
            
            result = {
                'id_ind': id_ind,
                'nome_curto': nome_curto,
                'descricao': descricao,
                'frequency': frequency,
                'target_table': target_table,
                'series_config': series_conf,
                'data': data_rows
            }
            
            self.logger.info(
                f"✅ Ficheiro processado: {len(data_rows)} registos | "
                f"Série: {nome_curto} | Frequência: {frequency} | Tabela: {target_table}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao ler ficheiro {file_path.name}: {e}", exc_info=True)
            return None
    
    def scan_directory(self, directory: Path) -> List[Dict]:
        """
        Varre um diretório e lê todos os ficheiros Excel.
        
        Args:
            directory: Diretório a varrer
            
        Returns:
            Lista de dicionários com dados de cada ficheiro
        """
        self.logger.info(f"🔍 A varrer diretório: {directory}")
        
        if not directory.exists():
            self.logger.error(f"Diretório não existe: {directory}")
            return []
        
        # Encontra todos os ficheiros Excel
        excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xls"))
        excel_files = [f for f in excel_files if not f.name.startswith('~$')]  # Ignora ficheiros temporários
        
        self.logger.info(f"📊 Encontrados {len(excel_files)} ficheiros Excel")
        
        results = []
        for file_path in excel_files:
            result = self.read_excel_file(file_path)
            if result:
                results.append(result)
        
        self.logger.info(f"✅ Processados {len(results)} ficheiros com sucesso")
        return results


if __name__ == "__main__":
    # Teste do leitor de Excel
    print("🧪 Teste do ExcelReader")
    print("⚠️  Configure mappings.json e coloque ficheiros Excel na pasta de teste")
