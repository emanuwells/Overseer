"""
forms_reader.py
Leitor de ficheiros Excel provenientes do Microsoft Forms
Versão: 0.2.0
"""

import pandas as pd
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import traceback
from pathlib import Path

from overseer_sdk.logger import get_logger

logger = get_logger("forms_reader")


class FormsReader:
    """Leitor de ficheiros Excel do Microsoft Forms"""

    def __init__(self, mappings: Dict):
        """
        Inicializa o leitor de Forms

        Args:
            mappings: Dicionário com mapeamentos de séries
        """
        # Escolhe apenas séries configuradas para Forms, mantendo compatibilidade
        if 'forms_series' in mappings:
            candidate_series = mappings['forms_series']
        elif 'series_config' in mappings:
            candidate_series = mappings['series_config']
        else:
            candidate_series = mappings

        forms_only = {
            name: config for name, config in candidate_series.items()
            if config.get('forms_enabled')
        }

        # Se existirem séries marcadas explicitamente para Forms, usa só essas.
        # Caso contrário (config antiga), usa todas as séries disponíveis.
        if forms_only:
            self.series_config = forms_only
        else:
            self.series_config = candidate_series

        # Criar índice reverso: id_ind -> lista de séries
        self.id_ind_to_series = {}
        for serie_name, config in self.series_config.items():
            id_ind = config.get('id_ind', '').lower()
            if id_ind:
                if id_ind not in self.id_ind_to_series:
                    self.id_ind_to_series[id_ind] = []
                self.id_ind_to_series[id_ind].append({
                    'serie_name': serie_name,
                    'config': config
                })

        logger.info(f"FormsReader inicializado com {len(self.series_config)} séries mapeadas")
        logger.info(f"IDs mapeados: {list(self.id_ind_to_series.keys())}")

    @staticmethod
    def is_forms_file(filename: str) -> bool:
        """
        Verifica se o ficheiro é um ficheiro Forms.
        
        Args:
            filename: Nome do ficheiro
            
        Returns:
            True se for ficheiro Forms
        """
        return bool(re.match(r'^(Ind\d+)', filename, re.IGNORECASE))

    def _extract_id_ind(self, filename: str) -> Optional[str]:
        """
        Extrai o ID_Ind do nome do ficheiro

        Args:
            filename: Nome do ficheiro

        Returns:
            ID_Ind extraído ou None
        """
        match = re.match(r'(Ind\d+)', filename, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return None

    def _detect_periodicity(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """
        Deteta a periodicidade dos dados baseando-se nas colunas com valores.

        Dá prioridade às periodicidades mais específicas (Mensal/Semestral/Trimestral)
        e só recorre a Anual quando não existem colunas preenchidas para os outros casos.
        """
        columns = list(df.columns)
        columns_clean = [str(col).strip().lower() for col in columns]

        def column_has_values(column_name: str) -> bool:
            """Retorna True se a coluna existir e tiver pelo menos um valor não-nulo."""
            return column_name in df.columns and df[column_name].notna().any()

        def matches_keyword(col_idx: int, keyword: str) -> bool:
            """Evita falsos positivos (ex.: 'mes' a casar com 'Semestral')."""
            col_clean = columns_clean[col_idx]
            keyword_clean = keyword.strip().lower()

            if keyword_clean in {'mes', 'mês'}:
                tokens = [token.lower() for token in re.split(r'\W+', col_clean)]
                return keyword_clean in tokens

            return keyword_clean in col_clean

        # Ordem de detecção: Semestral → Trimestral → Mensal → Anual
        priority_patterns = [
            ('Semestral', ['semestral', 'semestre']),
            ('Trimestral', ['trimestral', 'trimestre']),
            ('Mensal', ['mensal', 'mês', 'mes'])
        ]

        for periodicity, keywords in priority_patterns:
            for keyword in keywords:
                for idx in range(len(columns_clean)):
                    if matches_keyword(idx, keyword):
                        original_col = columns[idx]
                        if column_has_values(original_col):
                            logger.debug(f"DEBUG: periodicidade '{periodicity}' detectada pela coluna '{original_col}'")
                            logger.info(f"Periodicidade detectada: {periodicity} (coluna: {original_col})")
                            return periodicity, original_col

        # Fallback para anual usando a coluna de Ano
        for idx, col_clean in enumerate(columns_clean):
            if 'ano' in col_clean:
                original_col = columns[idx]
                logger.debug("DEBUG: periodicidade 'Anual' assumida pela coluna 'Ano'")
                logger.info(f"Periodicidade detectada: Anual (coluna: {original_col})")
                return 'Anual', original_col

        logger.warning("Periodicidade não detectada, assumindo Anual")
        return 'Anual', None

    def _extract_year_from_row(self, row: pd.Series) -> Optional[str]:
        """
        Procura um valor de ano noutras colunas do registo (ex.: coluna 'Ano').
        """
        if row is None:
            return None

        for col in row.index:
            if 'ano' in str(col).lower():
                year_value = row[col]
                if pd.isna(year_value):
                    continue

                year_str = str(year_value).strip()
                match = re.search(r'(19|20)\d{2}', year_str)
                if match:
                    return match.group(0)

                # Se for um número inteiro (ex.: 2025)
                try:
                    return f"{int(float(year_value))}"
                except (ValueError, TypeError):
                    continue

        return None

    def _parse_period_value(self, value: str, periodicity: str, row: pd.Series) -> Optional[str]:
        """
        Converte o valor do período para formato padronizado

        Args:
            value: Valor do período (ex: "2024", "Janeiro 2024", "1º Trimestre 2024")
            periodicity: Periodicidade detectada
            row: Linha completa do DataFrame (para obter ano noutros campos)

        Returns:
            Período formatado ou None
        """
        if pd.isna(value) or value == '':
            return None

        value_str = str(value).strip()

        logger.debug(f"DEBUG: _parse_period_value input: value='{value_str}', periodicity='{periodicity}'")
        # Extrair ano
        year_match = re.search(r'(19|20)\d{2}', value_str)
        if year_match:
            year = year_match.group(0)
        else:
            year = self._extract_year_from_row(row)
            if not year:
                logger.warning(f"Não foi possível extrair ano de '{value_str}' nem da linha correspondente. Retornando None.")
                return None  # Não é possível processar sem ano

        if periodicity == 'Anual':
            return year

        elif periodicity == 'Mensal':
            # Mapeamento de meses
            months = {
                'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
                'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
                'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
            }
            value_lower = value_str.lower()
            for month_name, month_num in months.items():
                if month_name in value_lower:
                    return f"{year}-{month_num}"

            # Tentar formato numérico (ex: "1/2024")
            month_match = re.search(r'(\d{1,2})', value_str)
            if month_match:
                month = month_match.group(1).zfill(2)
                return f"{year}-{month}"

        elif periodicity == 'Trimestral':
            # Extrair número do trimestre
            quarter_match = re.search(r'(\d)[ºª°]?\s*[Tt]', value_str)
            if quarter_match:
                quarter = quarter_match.group(1)
                return f"{year}-T{quarter}"

        elif periodicity == 'Semestral':
            # Extrair número do semestre
            value_lower = value_str.lower()
            # Lógica simples e robusta: se tiver '1' ou 'primeiro', é o 1º semestre. Senão, é o 2º.
            if '1' in value_str or 'primeiro' in value_lower:
                semester = 1
            else:
                semester = 2
            return f"{year}-S{semester}"

        logger.debug(f"DEBUG: _parse_period_value output: None for value='{value_str}', periodicity='{periodicity}'")
        return None

    def _find_value_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Identifica colunas de valores no DataFrame

        Args:
            df: DataFrame com os dados

        Returns:
            Lista de nomes de colunas de valores
        """
        value_columns = []

        # Excluir colunas conhecidas que não são valores
        exclude_patterns = [
            'id', 'data', 'período', 'periodo', 'ano', 'mês', 'mes',
            'trimestre', 'semestre', 'timestamp', 'email', 'nome'
        ]

        for col in df.columns:
            col_lower = col.lower()
            # Verificar se não é uma coluna de exclusão
            if not any(pattern in col_lower for pattern in exclude_patterns):
                # Verificar se tem valores numéricos
                if pd.api.types.is_numeric_dtype(df[col]) or df[col].dtype == 'object':
                    value_columns.append(col)

        return value_columns

    def scan_directory(self, directory: str) -> List[str]:
        """
        Varre o diretório e retorna lista de ficheiros Forms

        Args:
            directory: Caminho do diretório

        Returns:
            Lista de caminhos de ficheiros Forms
        """
        forms_files = []

        logger.info(f"🔍 A varrer diretório para ficheiros Forms: {directory}")

        if not os.path.exists(directory):
            logger.error(f"Diretório não existe: {directory}")
            return forms_files

        for filename in os.listdir(directory):
            if not filename.endswith('.xlsx') or filename.startswith('~$'):
                continue

            # Extrair ID_Ind
            id_ind = self._extract_id_ind(filename)
            if not id_ind:
                logger.debug(f"Não foi possível extrair ID_Ind de: {filename}")
                continue

            # Verificar se está mapeado
            if id_ind not in self.id_ind_to_series:
                logger.debug(f"ID não mapeado: {id_ind} (ficheiro: {filename})")
                continue

            filepath = os.path.join(directory, filename)
            forms_files.append(filepath)
            logger.info(f"✅ Ficheiro Forms encontrado: {filename} (ID: {id_ind})")

        logger.info(f"📋 Encontrados {len(forms_files)} ficheiros Forms mapeados")
        return forms_files

    def read_forms_file(self, filepath: str) -> Optional[Dict]:
        """
        Lê um ficheiro Excel do Forms e retorna os dados estruturados

        Args:
            filepath: Caminho do ficheiro

        Returns:
            Dicionário com dados estruturados ou None em caso de erro
        """
        try:
            filename = os.path.basename(filepath)
            logger.info(f"📋 A ler ficheiro Forms: {filename}")

            # Extrair ID_Ind
            id_ind = self._extract_id_ind(filename)
            if not id_ind:
                logger.warning(f"Não foi possível extrair ID_Ind de: {filename}")
                return {
                    'error': 'ID_Ind não extraído do nome do ficheiro',
                    'error_type': 'id_ind_not_found',
                    'source_file': filename
                }

            # Verificar mapeamento
            if id_ind not in self.id_ind_to_series:
                logger.warning(f"⚠️  Série não mapeada: {id_ind} (ficheiro: {filename})")
                return {
                    'error': f'Série não mapeada: {id_ind}',
                    'error_type': 'unmapped_series',
                    'source_file': filename
                }

            # Obter configurações das séries para este ID
            series_configs = self.id_ind_to_series[id_ind]

            # Ler Excel
            df = pd.read_excel(filepath)

            if df.empty:
                logger.warning(f"Ficheiro vazio: {filename}")
                return {
                    'error': 'Ficheiro vazio',
                    'error_type': 'empty_file',
                    'source_file': filename
                }

            # Detectar periodicidade
            periodicity, period_column = self._detect_periodicity(df)

            if not period_column:
                logger.error(f"Coluna de período não encontrada em: {filename}")
                return {
                    'error': 'Coluna de período não encontrada',
                    'error_type': 'period_not_found',
                    'source_file': filename
                }

            # Processar cada série configurada
            all_records = []

            for serie_info in series_configs:
                serie_name = serie_info['serie_name']
                config = serie_info['config']
                description = config.get('descricao', '')

                # Extrair número do ID_Ind
                id_ind_num = None
                match = re.search(r'\d+', config.get('id_ind', ''))
                if match:
                    id_ind_num = int(match.group(0))

                # Determinar colunas de valor
                value_columns_config = config.get('value_column', [])

                if value_columns_config:
                    # Usar colunas especificadas no mapeamento
                    value_columns = []
                    for col in value_columns_config:
                        if col in df.columns:
                            value_columns.append(col)
                        else:
                            logger.warning(f"Coluna '{col}' não encontrada no ficheiro {filename}")

                    if not value_columns:
                        logger.warning(f"Nenhuma coluna de valor válida para série {serie_name}")
                        continue
                else:
                    # Detectar automaticamente
                    value_columns = self._find_value_columns(df)
                    if not value_columns:
                        logger.error(f"Nenhuma coluna de valor encontrada em: {filename}")
                        continue

                # Processar registos
                for _, row in df.iterrows():
                    period_value = row.get(period_column)
                    if pd.isna(period_value):
                        continue

                    # Converter período
                    period_formatted = self._parse_period_value(period_value, periodicity, row)
                    if not period_formatted:
                        logger.warning(f"Não foi possível converter período: {period_value}")
                        continue

                    # Processar cada coluna de valor
                    for value_col in value_columns:
                        value = row.get(value_col)

                        # Converter valor para numérico
                        try:
                            if pd.isna(value):
                                numeric_value = None
                            else:
                                # Remover % se existir
                                if isinstance(value, str):
                                    value = value.replace('%', '').replace(',', '.').strip()
                                numeric_value = float(value)
                        except (ValueError, TypeError):
                            logger.warning(f"Valor não numérico ignorado: {value}")
                            continue

                        # Determinar a tabela de destino com base na configuração da série
                        if config.get('is_baze21ra', False):
                            target_table = 'baze21RA'
                        else:
                            target_table = 'Indicadores'

                        # Criar registo
                        record = {
                            'id_ind': id_ind_num,
                            'serie_name': serie_name,
                            'description': description,
                            'period': period_formatted,
                            'target_table': target_table,
                            'value': numeric_value,
                            'frequency': periodicity,
                            'source_file': filename,
                            'metodo_imp': 'Microsoft Forms Pipeline'
                        }

                        all_records.append(record)

            if not all_records:
                logger.warning(f"Nenhum registo válido extraído de: {filename}")
                return None

            logger.info(f"✅ Extraídos {len(all_records)} registos de {filename}")

            return {
                'records': all_records,
                'source_file': filename,
                'id_ind': id_ind
            }

        except Exception as e:
            logger.error(f"Erro ao ler ficheiro Forms {filepath}: {e}")
            logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'error_type': 'exception',
                'source_file': Path(filepath).name if 'filepath' in locals() else 'desconhecido'
            }

    def process_forms_files(self, directory: str) -> List[Dict]:
        """
        Processa todos os ficheiros Forms num diretório

        Args:
            directory: Caminho do diretório

        Returns:
            Lista de dicionários com dados processados
        """
        all_data = []
        files = self.scan_directory(directory)

        for filepath in files:
            data = self.read_forms_file(filepath)
            if data:
                all_data.append(data)

        logger.info(f"✅ Processados {len(all_data)} ficheiros Forms com sucesso")
        return all_data
