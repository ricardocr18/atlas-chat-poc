"""
infrastructure/postgresql/repositories.py
-------------------------------------------
Repositório para a tabela objetos_gerados_previas no PostgreSQL.

Fase 6: adicionados os campos versao, versao_ativa, motivo_reprovacao
        e avaliado_por, preparando a estrutura para suportar o
        versionamento de tentativas quando o agente de classificação
        existir. A LÓGICA de versionamento (incrementar versao,
        marcar versao_ativa=false em registros antigos) NÃO é
        implementada nesta fase — apenas a estrutura da tabela.

Por que usamos a tabela objetos_gerados_previas?
  O DevConsole da Sicredi já criou esta tabela no banco
  atlas_documentacao_agent. Expandimos ela com as colunas
  necessárias, mantendo compatibilidade com o que já existe.

Padrão Repository: mesma abordagem do MongoDB.
  O postgres_node nunca executa SQL diretamente — sempre
  passa por este repositório.

CREATE TABLE IF NOT EXISTS + ALTER TABLE:
  Garante idempotência — se a tabela já existir sem os novos
  campos (como no ambiente que já estava em uso desde a Fase 5),
  o ALTER TABLE adiciona os campos que faltam sem apagar dados.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from psycopg2.extensions import connection as PgConnection

logger = logging.getLogger(__name__)

TABELA = "objetos_gerados_previas"

# SQL de criação da tabela — usa IF NOT EXISTS para idempotência
# Já inclui os campos de versionamento desde a criação (ambientes novos)
SQL_CRIAR_TABELA = f"""
CREATE TABLE IF NOT EXISTS {TABELA} (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id             VARCHAR(100),
    transaction_id       VARCHAR(100),
    component_name       VARCHAR(200) NOT NULL,
    application_name     VARCHAR(200),
    team_id              VARCHAR(100),
    time_responsavel     VARCHAR(200),
    projeto              VARCHAR(200),
    tribo                VARCHAR(200),
    tipo_aplicacao       VARCHAR(100),
    categoria_aplicacao  VARCHAR(100),
    criticidade          VARCHAR(50),
    environment          VARCHAR(50),
    status_aplicacao     VARCHAR(50),
    repository           VARCHAR(500),
    id_mongodb_previa    VARCHAR(100),
    id_mongodb_metadados VARCHAR(100),
    status_cadastro      VARCHAR(50) DEFAULT 'pendente_aprovacao',
    versao               INTEGER DEFAULT 1,
    versao_ativa         BOOLEAN DEFAULT TRUE,
    motivo_reprovacao    TEXT,
    avaliado_por         VARCHAR(100),
    criado_em            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

# ALTER TABLE idempotente — garante que tabelas criadas ANTES da Fase 6
# (como a do ambiente Sicredi, criada na Fase 5) recebam os novos campos
# sem perder os dados já existentes.
SQL_ADICIONAR_CAMPOS_FASE6 = f"""
ALTER TABLE {TABELA}
    ADD COLUMN IF NOT EXISTS versao INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS versao_ativa BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS motivo_reprovacao TEXT,
    ADD COLUMN IF NOT EXISTS avaliado_por VARCHAR(100);
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
    versao,
    versao_ativa,
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
    %(versao)s,
    %(versao_ativa)s,
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

    Fase 6: os campos versao, versao_ativa, motivo_reprovacao e
            avaliado_por existem na tabela mas a lógica de
            versionamento (múltiplas tentativas) ainda não está
            implementada. Todo registro inserido hoje nasce com
            versao=1 e versao_ativa=true.
    """

    def __init__(self, conn: PgConnection) -> None:
        self._conn = conn
        logger.debug("Repositório '%s' inicializado.", TABELA)

    def garantir_tabela(self) -> None:
        """
        Cria a tabela se não existir, e adiciona os campos da Fase 6
        caso a tabela já exista de uma fase anterior.

        Seguro chamar múltiplas vezes — nunca apaga dados.
        """
        with self._conn.cursor() as cur:
            cur.execute(SQL_CRIAR_TABELA)
            cur.execute(SQL_ADICIONAR_CAMPOS_FASE6)
        self._conn.commit()
        logger.info(
            "Tabela '%s' verificada/atualizada com sucesso (campos Fase 6 garantidos).",
            TABELA,
        )

    def inserir(
        self,
        metadados: dict[str, Any],
        previa: dict[str, Any],
        id_mongodb_previa: str,
        id_mongodb_metadados: str,
    ) -> str:
        """
        Insere o pré-cadastro do componente na tabela.

        Fase 6: todo registro novo nasce com versao=1 e
                versao_ativa=true.

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
            "versao": 1,
            "versao_ativa": True,
            "criado_em": agora,
            "atualizado_em": agora,
        }

        with self._conn.cursor() as cur:
            cur.execute(SQL_INSERIR, dados)
            resultado = cur.fetchone()

        self._conn.commit()

        id_gerado = str(resultado["id"])
        logger.info(
            "Pré-cadastro inserido em '%s' com ID: %s (versao=1)",
            TABELA,
            id_gerado,
        )
        return id_gerado

    def buscar_por_event_id(self, event_id: str) -> dict[str, Any] | None:
        """
        Busca o registro mais recente de um event_id.

        Returns:
            dict com o registro encontrado, ou None se não existir.
        """
        with self._conn.cursor() as cur:
            cur.execute(SQL_BUSCAR_POR_EVENT_ID, {"event_id": event_id})
            resultado = cur.fetchone()

        if resultado:
            logger.info("Registro encontrado para event_id: '%s'", event_id)
            return dict(resultado)

        logger.warning("Registro não encontrado para event_id: '%s'", event_id)
        return None