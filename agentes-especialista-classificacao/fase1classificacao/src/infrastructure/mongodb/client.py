"""Cliente MongoDB do agente de classificacao.

Este agente se conecta ao MESMO servidor MongoDB usado pelo
atlas-documentacao-agent, mas acessa DUAS databases logicas distintas:

- MONGO_DB_DOCUMENTACAO (leitura): onde o atlas-documentacao-agent grava
  as prevas de documentacao e os metadados catalogados.
- MONGO_DB_CLASSIFICACAO (escrita): propria deste agente, para auditoria
  interna e o veredito final de avaliacao.

Nao ha nenhuma "conexao" especial entre os dois agentes — sao dois
processos independentes acessando o mesmo servidor MongoDB, cada um com
sua propria string de conexao (que, localmente, aponta para o mesmo
localhost:27017).
"""

from __future__ import annotations

import logging

from pymongo import MongoClient
from pymongo.database import Database

from fase1classificacao.src.application.settings import settings

logger = logging.getLogger(__name__)

# --- Nomes das collections (documentados no CONTRATO_SAIDA do agente de
# documentacao e no plano de construcao deste agente) ---

# Collections do atlas-documentacao-agent (LEITURA)
COL_DOCUMENTOS_GERADOS_PREVIAS = "documentos_gerados_previas"
COL_COMPONENTES_CATALOGADOS_METADADOS = "componentes_catalogados_metadados"

# Collections proprias do atlas-classificacao-agent (ESCRITA)
COL_CURADORIA_CONTROLE_METADADOS = "curadoria_controle_metadados"
COL_DOCUMENTACAO_AVALIADA = "documentacao_avaliada"

_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    """Retorna uma instancia unica (singleton) do MongoClient."""
    global _client
    if _client is None:
        _client = MongoClient(settings.mongo_uri)
    return _client


def get_documentacao_db() -> Database:
    """Database do atlas-documentacao-agent (uso: somente leitura)."""
    return get_mongo_client()[settings.mongo_db_documentacao]


def get_classificacao_db() -> Database:
    """Database propria do atlas-classificacao-agent (uso: leitura e escrita)."""
    return get_mongo_client()[settings.mongo_db_classificacao]


def check_mongo_connection() -> dict:
    """Verifica a conectividade com o servidor Mongo e com as 4 collections
    relevantes para este agente (2 de leitura, 2 de escrita).

    Nao escreve nada nas collections de LEITURA (sao do outro agente).
    Faz um teste de escrita seguro (insere e remove um documento de teste)
    apenas nas collections proprias (ESCRITA), ja que sao exclusivas deste
    agente e hoje estao vazias.
    """
    resultado: dict = {"ok": True, "detalhes": {}}

    try:
        client = get_mongo_client()
        # ping ao servidor - falha rapido se o Mongo nao estiver acessivel
        client.admin.command("ping")
        resultado["detalhes"]["servidor"] = "ok (ping bem-sucedido)"
    except Exception as e:  # noqa: BLE001
        resultado["ok"] = False
        resultado["detalhes"]["servidor"] = f"FALHOU: {e}"
        return resultado  # sem servidor, nao adianta testar o resto

    # --- Leitura: database do agente de documentacao ---
    try:
        doc_db = get_documentacao_db()
        qtd_previas = doc_db[COL_DOCUMENTOS_GERADOS_PREVIAS].count_documents({})
        qtd_metadados = doc_db[COL_COMPONENTES_CATALOGADOS_METADADOS].count_documents({})
        resultado["detalhes"][COL_DOCUMENTOS_GERADOS_PREVIAS] = (
            f"ok (leitura) - {qtd_previas} documento(s) encontrado(s)"
        )
        resultado["detalhes"][COL_COMPONENTES_CATALOGADOS_METADADOS] = (
            f"ok (leitura) - {qtd_metadados} documento(s) encontrado(s)"
        )
    except Exception as e:  # noqa: BLE001
        resultado["ok"] = False
        resultado["detalhes"]["leitura_documentacao"] = f"FALHOU: {e}"

    # --- Escrita: database propria do agente de classificacao ---
    try:
        cls_db = get_classificacao_db()
        for nome_collection in (COL_CURADORIA_CONTROLE_METADADOS, COL_DOCUMENTACAO_AVALIADA):
            colecao = cls_db[nome_collection]
            doc_teste = {"_teste_conectividade": True}
            inserted = colecao.insert_one(doc_teste)
            colecao.delete_one({"_id": inserted.inserted_id})
            resultado["detalhes"][nome_collection] = "ok (leitura + escrita confirmadas)"
    except Exception as e:  # noqa: BLE001
        resultado["ok"] = False
        resultado["detalhes"]["escrita_classificacao"] = f"FALHOU: {e}"

    return resultado
