"""
Gestor de Base de Dados MariaDB — Microsoft Forms 2 Datalake
Versão: 0.3.0
Autor: Emanuel Ferreira (emanuel.ferreira@cm-maia.pt)

Estende ``DatabaseManagerBase`` (overseer_sdk) com operações UPSERT
específicas para as tabelas Indicadores, baze21RA e fonte.
"""

import pymysql
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from overseer_sdk.logger import get_logger
from overseer_sdk.db_manager_base import DatabaseManagerBase


class DatabaseManager(DatabaseManagerBase):
    """
    Gestor de operações na base de dados BAZE.
    Suporta UPSERT inteligente para as tabelas:
    - Indicadores (dados mensais/mais frequentes)
    - baze21RA (dados anuais)
    - fonte (metadados das séries)
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str = "BAZE"
    ):
        super().__init__(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            autocommit=False,
        )
        self.logger = get_logger("db_manager")

    # ------------------------------------------------------------------
    # Override _execute_update for explicit commit/rollback
    # ------------------------------------------------------------------

    def _execute_update(self, query: str, params: tuple = None) -> int:
        """
        Executa uma query de atualização (INSERT/UPDATE/DELETE).
        Faz commit explícito no sucesso e rollback em caso de erro.
        """
        try:
            with self.connection.cursor() as cursor:
                affected = cursor.execute(query, params)
                self.connection.commit()
                return affected
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erro ao executar atualização: {e}")
            self.logger.debug(f"Query: {query}")
            self.logger.debug(f"Params: {params}")
            raise

    # ------------------------------------------------------------------
    # DDL — tabelas existentes em BAZE, nada a criar
    # ------------------------------------------------------------------

    def ensure_tables(self) -> None:
        """As tabelas Indicadores, baze21RA e fonte já existem em BAZE."""
        pass

    def _format_period_label(self, start_date: datetime, end_date: datetime) -> str:
        """
        Gera uma etiqueta amigável para o período (ex.: 2025-S1, 2025-T3, 2025-02).

        Args:
            start_date: Data de início usada na pesquisa
            end_date: Data de fim usada no registo

        Returns:
            String que representa o período.
        """
        year = start_date.year

        if start_date.month == 1 and end_date.month == 12 and end_date.year == year:
            return f"{year}"

        if start_date.month == 1 and end_date.month == 6:
            return f"{year}-S1"
        if start_date.month == 7 and end_date.month == 12:
            return f"{year}-S2"

        quarter_map = {1: 1, 4: 2, 7: 3, 10: 4}
        if end_date.month == start_date.month and start_date.year == end_date.year:
            return f"{year}-{start_date.month:02d}"
        if start_date.month in quarter_map and end_date.month == start_date.month + 2:
            return f"{year}-T{quarter_map[start_date.month]}"

        return start_date.strftime("%Y-%m-%d")

    def upsert_indicadores(
        self,
        nome: str,
        valor: float,
        search_date: datetime,
        record_date: datetime
    ) -> Tuple[bool, str]:
        """
        UPSERT na tabela Indicadores.
        Usa search_date para encontrar o registo e record_date para o guardar.

        Args:
            nome: Nome curto da série (ex: 'nhabit')
            valor: Valor numérico
            search_date: Data de início do período (para pesquisa)
            record_date: Data de fim do período (para registo)

        Returns:
            Tupla (sucesso, ação_realizada)
            ação_realizada: 'insert', 'update', 'skip'
        """
        try:
            # Verifica se já existe registo mais recente
            check_query = """
                SELECT id, valor, data, regDate 
                FROM Indicadores 
                WHERE nome = %s AND data BETWEEN %s AND %s
                ORDER BY regDate DESC 
                LIMIT 1
            """
            self.logger.debug(f"DEBUG: check_query params: nome={nome}, search_date={search_date}, record_date={record_date}")
            existing = self._execute_query(check_query, (nome, search_date, record_date))

            if existing:
                # Registo existe, verifica se deve atualizar
                existing_record = existing[0]
                self.logger.debug(f"DEBUG: existing_record found: {existing_record}")

                # Só atualiza se o valor for diferente
                # A condição de SKIP deve verificar se o registo já está PERFEITO (valor e data final corretos)
                if float(existing_record['valor']) == valor and existing_record['data'].date() == record_date.date():
                    period_label = self._format_period_label(search_date, record_date)
                    self.logger.info(f"⏭️  SKIP: Registo para '{nome}' em {period_label} já existe com o mesmo valor ({valor}).")
                    self.stats["skipped"] += 1
                    return True, "skip"

                # Atualiza registo existente
                update_query = """
                    UPDATE Indicadores 
                    SET valor = %s, data = %s, regDate = NOW()
                    WHERE id = %s
                """
                self._execute_update(update_query, (valor, record_date, existing_record['id']))

                self.logger.info(f"✏️  UPDATE: {nome} | {record_date.date()} | valor: {existing_record['valor']} → {valor}")
                self.stats["updates"] += 1
                return True, "update"

            else:
                # Novo registo
                insert_query = """
                    INSERT INTO Indicadores (nome, valor, data, regDate)
                    VALUES (%s, %s, %s, NOW())
                """
                self._execute_update(insert_query, (nome, valor, record_date))

                self.logger.info(f"➕ INSERT: {nome} | {record_date.date()} | valor: {valor}")
                self.stats["inserts"] += 1
                return True, "insert"

        except Exception as e:
            self.logger.error(f"Erro em upsert_indicadores: {e}")
            self.stats["errors"] += 1
            return False, "error"

    def upsert_baze21ra(
        self,
        nome_curto: str,
        ano: int,
        valor: float
    ) -> Tuple[bool, str]:
        """
        UPSERT na tabela baze21RA (séries anuais).
        Estrutura: id | ano | Cnhabit | Cemprego | ...

        Args:
            nome_curto: Nome curto da série (ex: 'nhabit')
            ano: Ano do registo
            valor: Valor numérico

        Returns:
            Tupla (sucesso, ação_realizada)
        """
        try:
            coluna = f"C{nome_curto}"

            # Verifica se a coluna existe
            check_col_query = f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{self.database}' 
                AND TABLE_NAME = 'baze21RA' 
                AND COLUMN_NAME = '{coluna}'
            """
            col_exists = self._execute_query(check_col_query)

            if not col_exists:
                self.logger.warning(f"Coluna {coluna} não existe em baze21RA")
                self.stats["errors"] += 1
                return False, "column_not_found"

            # Verifica se ano já existe
            check_query = f"""
                SELECT id, {coluna} 
                FROM baze21RA 
                WHERE ano = %s
            """
            existing = self._execute_query(check_query, (ano,))

            if existing:
                # Ano existe, atualiza coluna
                existing_valor = existing[0].get(coluna)

                if existing_valor == valor:
                    self.logger.info(f"⏭️  SKIP: Registo para '{coluna}' no ano {ano} já existe com o mesmo valor ({valor}).")
                    self.stats["skipped"] += 1
                    return True, "skip"

                update_query = f"""
                    UPDATE baze21RA 
                    SET {coluna} = %s 
                    WHERE ano = %s
                """
                self._execute_update(update_query, (valor, ano))

                self.logger.info(f"✏️  UPDATE baze21RA: {coluna} | {ano} | valor: {existing_valor} → {valor}")
                self.stats["updates"] += 1
                return True, "update"

            else:
                # Novo ano, insere linha
                insert_query = f"""
                    INSERT INTO baze21RA (ano, {coluna})
                    VALUES (%s, %s)
                """
                self._execute_update(insert_query, (ano, valor))

                self.logger.info(f"➕ INSERT baze21RA: {coluna} | {ano} | valor: {valor}")
                self.stats["inserts"] += 1
                return True, "insert"

        except Exception as e:
            self.logger.error(f"Erro em upsert_baze21ra: {e}")
            self.stats["errors"] += 1
            return False, "error"

    def upsert_fonte(
        self,
        nome: str,
        id_ind: Optional[int],
        descricao: str,
        tabela_sql: Optional[str] = None,
        metodo_imp: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        UPSERT na tabela fonte (metadados).

        Args:
            nome: Nome curto da série
            id_ind: ID numérico do indicador (ex: 97 para Ind097)
            descricao: Descrição da série
            tabela_sql: Tabela onde os dados foram inseridos ('Indicadores' ou 'baze21RA')
            metodo_imp: Método de importação (ex: 'Microsoft Forms Pipeline')

        Returns:
            Tupla (sucesso, ação_realizada)
        """
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            editor = "EF (emanuel.ferreira@cm-maia.pt)"
            status = "Disponível"

            # Verifica se série já existe
            check_query = "SELECT id, nome FROM fonte WHERE nome = %s"
            existing = self._execute_query(check_query, (nome,))

            if existing:
                # Atualiza metadados
                update_query = """
                    UPDATE fonte 
                    SET DataUltimaActual = %s,
                        DataUltimaActuaLocal = %s,
                        DataUltimaVerifica = %s,
                        tabela_sql = %s,
                        editor = %s,
                        descri = %s,
                        DescriPlus = %s,
                        status = %s,
                        MetodoImp = %s,
                        ID_Ind = %s
                    WHERE nome = %s
                """
                self._execute_update(
                    update_query,
                    (now, now, now, tabela_sql, editor, descricao, descricao, 
                     status, metodo_imp, id_ind, nome)
                )

                self.logger.info(f"✏️  UPDATE fonte: {nome} (ID_Ind: {id_ind})")
                self.stats["updates"] += 1
                return True, "update"

            else:
                # Nova série
                insert_query = """
                    INSERT INTO fonte 
                    (nome, ID_Ind, descri, DescriPlus, tabela_sql, editor, status, MetodoImp,
                     DataUltimaActual, DataUltimaActuaLocal, DataUltimaVerifica, RegDate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """
                self._execute_update(
                    insert_query,
                    (nome, id_ind, descricao, descricao, tabela_sql, editor, 
                     status, metodo_imp, now, now, now)
                )

                self.logger.info(f"➕ INSERT fonte: {nome} (ID_Ind: {id_ind})")
                self.stats["inserts"] += 1
                return True, "insert"

        except Exception as e:
            self.logger.error(f"Erro em upsert_fonte: {e}")
            self.stats["errors"] += 1
            return False, "error"

    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas das operações realizadas."""
        return self.stats.copy()


if __name__ == "__main__":
    # Teste do gestor de BD
    print("🧪 Teste do DatabaseManager")
    print("⚠️  Configure secrets/database.json antes de testar")
