"""Cliente PostgreSQL do agente de classificacao.

Este agente se conecta ao MESMO banco Postgres usado pelo
atlas-documentacao-agent (atlas_documentacao_agente), na tabela
objetos_gerados_previas. E' o unico ponto de dado que os dois agentes
realmente compartilham em via de mao dupla:

- LEITURA: descoberta de pendencias (status_cadastro = 'pendente_aprovacao')
- ESCRITA: atualizacao do veredito (status_cadastro, avaliado_por,
  motivo_reprovacao) apos os juizes avaliarem

Nao ha nenhum banco novo aqui — e' a mesma tabela, o mesmo servidor,
acessado por um segundo processo com sua propria conexao.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from fase1classificacao.src.application.settings import settings

logger = logging.getLogger(__name__)

TABELA_OBJETOS_GERADOS_PREVIAS = "objetos_gerados_previas"


@contextmanager
def get_connection() -> Iterator[PgConnection]:
    """Abre uma conexao Postgres e garante o fechamento ao final do bloco."""
    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        sslmode=settings.postgres_sslmode,
        cursor_factory=RealDictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()


def check_postgres_connection() -> dict:
    """Verifica conectividade, permissao de LEITURA e permissao de ESCRITA
    na tabela compartilhada objetos_gerados_previas.

    O teste de escrita usa um UPDATE dentro de uma transacao que e' sempre
    revertida (ROLLBACK) ao final, e filtrado por um id que nao existe
    (00000000-0000-0000-0000-000000000000) — ou seja, confirma que o
    usuario TEM permissao de UPDATE na tabela, sem alterar nenhuma linha
    real.
    """
    resultado: dict = {"ok": True, "detalhes": {}}

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), version();")
                info = cur.fetchone()
                resultado["detalhes"]["servidor"] = (
                    f"ok - conectado a '{info['current_database']}'"
                )

                # --- Teste de LEITURA na tabela compartilhada ---
                cur.execute(
                    f"SELECT COUNT(*) AS total FROM {TABELA_OBJETOS_GERADOS_PREVIAS};"
                )
                total = cur.fetchone()["total"]
                resultado["detalhes"][TABELA_OBJETOS_GERADOS_PREVIAS] = (
                    f"ok (leitura) - {total} registro(s) encontrado(s)"
                )

                cur.execute(
                    f"""
                    SELECT COUNT(*) AS total FROM {TABELA_OBJETOS_GERADOS_PREVIAS}
                    WHERE status_cadastro = 'pendente_aprovacao'
                      AND versao_ativa = true;
                    """
                )
                pendentes = cur.fetchone()["total"]
                resultado["detalhes"]["pendentes_aprovacao"] = (
                    f"{pendentes} registro(s) pendente(s) de avaliacao"
                )

                # --- Teste de ESCRITA (seguro: sempre revertido) ---
                cur.execute(
                    f"""
                    UPDATE {TABELA_OBJETOS_GERADOS_PREVIAS}
                    SET atualizado_em = atualizado_em
                    WHERE id = '00000000-0000-0000-0000-000000000000';
                    """
                )
                conn.rollback()
                resultado["detalhes"]["permissao_escrita"] = (
                    "ok (UPDATE permitido - transacao revertida de proposito)"
                )
    except Exception as e:  # noqa: BLE001
        resultado["ok"] = False
        resultado["detalhes"]["erro"] = str(e)

    return resultado
