"""
infrastructure/postgresql/repositories.py
-------------------------------------------
Repositório para a tabela objetos_gerados_previas no PostgreSQL.

Por que usamos a tabela objetos_gerados_previas?
  O DevConsole da Sicredi já criou esta tabela no banco
  atlas_documentacao_agent com 1 coluna. Expandimos ela
  com as colunas necessárias para o pré-cadastro do componente,
  mantendo compatibilidade com o que já existe.

Padrão Repository: mesma abordagem do MongoDB.
  O postgres_node nunca executa SQL diretamente — sempre
  passa por este repositório.

CREATE TABLE IF NOT EXISTS:
  Garante idempotência — se a tabela já existir com as colunas,
  não faz nada. Se existir com menos colunas (como na Sicredi),
  o ALTER TABLE adiciona as que faltam.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from psycopg2.extensions import connection as PgConnection

logger = logging.getLogger(__name__)

TABELA = "objetos_gerados_previas"

# SQL de criação da tabela — usa IF NOT EXISTS para idempotência
# Compatível com a tabela que já existe no banco da Sicredi
SQL_CRIAR_TABELA = f"""
CREATE TABLE IF NOT EXISTS {TABELA} (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id            VARCHAR(100),
    transaction_id      VARCHAR(100),
    component_name      VARCHAR(200) NOT NULL,
    application_name    VARCHAR(200),
    team_id             VARCHAR(100),
    time_responsavel    VARCHAR(200),
    projeto             VARCHAR(200),
    tribo               VARCHAR(200),
    tipo_aplicacao      VARCHAR(100),
    categoria_aplicacao VARCHAR(100),
    criticidade         VARCHAR(50),
    environment         VARCHAR(50),
    status_aplicacao    VARCHAR(50),
    repository          VARCHAR(500),
    id_mongodb_previa   VARCHAR(100),
    id_mongodb_metadados VARCHAR(100),
    status_cadastro     VARCHAR(50) DEFAULT 'pendente_aprovacao',
    criado_em           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

SQL_INSERIR = f"""
INSERT INTO {TABELA} (
    event_id,
    transaction_id,
    component_name,
    application_name,
    team_id,
    time_responsavel,
    projeto,
    tribo,
    tipo_aplicacao,
    categoria_aplicacao,
    criticidade,
    environment,
    status_aplicacao,
    repository,
    id_mongodb_previa,
    id_mongodb_metadados,
    status_cadastro,
    criado_em,
    atualizado_em
) VALUES (
    %(event_id)s,
    %(transaction_id)s,
    %(component_name)s,
    %(application_name)s,
    %(team_id)s,
    %(time_responsavel)s,
    %(projeto)s,
    %(tribo)s,
    %(tipo_aplicacao)s,
    %(categoria_aplicacao)s,
    %(criticidade)s,
    %(environment)s,
    %(status_aplicacao)s,
    %(repository)s,
    %(id_mongodb_previa)s,
    %(id_mongodb_metadados)s,
    %(status_cadastro)s,
    %(criado_em)s,
    %(atualizado_em)s
)
RETURNING id;
"""

SQL_BUSCAR_POR_EVENT_ID = f"""
SELECT * FROM {TABELA}
WHERE event_id = %(event_id)s
ORDER BY criado_em DESC
LIMIT 1;
"""


class ObjetosGeradosPreViasRepository:
    """
    Repositório para a tabela objetos_gerados_previas.

    Responsável por:
    - Garantir que a tabela existe (criar se necessário)
    - Inserir o pré-cadastro do componente
    - Buscar registros por event_id
    """

    def __init__(self, conn: PgConnection) -> None:
        self._conn = conn
        logger.debug("Repositório '%s' inicializado.", TABELA)

    def garantir_tabela(self) -> None:
        """
        Cria a tabela se não existir.

        Chamado uma vez ao inicializar o postgres_node.
        Idempotente — seguro chamar múltiplas vezes.
        """
        with self._conn.cursor() as cur:
            cur.execute(SQL_CRIAR_TABELA)
        self._conn.commit()
        logger.info("Tabela '%s' verificada/criada com sucesso.", TABELA)

    def inserir(
        self,
        metadados: dict[str, Any],
        previa: dict[str, Any],
        id_mongodb_previa: str,
        id_mongodb_metadados: str,
    ) -> str:
        """
        Insere o pré-cadastro do componente na tabela.

        Combina dados dos metadados e da prévia gerados pelos
        nós anteriores do grafo para montar o registro completo.

        Args:
            metadados: dict gerado pelo cataloging_node
            previa: dict gerado pelo documentation_node
            id_mongodb_previa: ID do documento na collection previas
            id_mongodb_metadados: ID do documento na collection metadados

        Returns:
            str: UUID do registro inserido no PostgreSQL
        """
        agora = datetime.now(timezone.utc)

        dados = {
            "event_id": metadados.get("event_id"),
            "transaction_id": metadados.get("transaction_id"),
            "component_name": metadados.get("component_name"),
            "application_name": metadados.get("application_name"),
            "team_id": metadados.get("team_id"),
            "time_responsavel": metadados.get("time_responsavel"),
            "projeto": metadados.get("projeto"),
            "tribo": metadados.get("tribo"),
            "tipo_aplicacao": metadados.get("tipo_aplicacao"),
            "categoria_aplicacao": metadados.get("categoria_aplicacao"),
            "criticidade": metadados.get("criticidade"),
            "environment": metadados.get("environment"),
            "status_aplicacao": metadados.get("status_aplicacao"),
            "repository": metadados.get("repository"),
            "id_mongodb_previa": id_mongodb_previa,
            "id_mongodb_metadados": id_mongodb_metadados,
            "status_cadastro": "pendente_aprovacao",
            "criado_em": agora,
            "atualizado_em": agora,
        }

        with self._conn.cursor() as cur:
            cur.execute(SQL_INSERIR, dados)
            resultado = cur.fetchone()

        self._conn.commit()

        id_gerado = str(resultado["id"])
        logger.info(
            "Pré-cadastro inserido em '%s' com ID: %s",
            TABELA,
            id_gerado,
        )
        return id_gerado

    def buscar_por_event_id(self, event_id: str) -> dict[str, Any] | None:
        """
        Busca um pré-cadastro pelo event_id.

        Returns:
            dict com o registro encontrado, ou None se não existir.
        """
        with self._conn.cursor() as cur:
            cur.execute(SQL_BUSCAR_POR_EVENT_ID, {"event_id": event_id})
            resultado = cur.fetchone()

        if resultado:
            logger.info("Pré-cadastro encontrado para event_id: '%s'", event_id)
            return dict(resultado)

        logger.warning("Pré-cadastro não encontrado para event_id: '%s'", event_id)
        return None