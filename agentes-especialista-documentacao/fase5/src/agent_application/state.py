"""
agents/documentacao/state.py
------------------------------
Define o Estado compartilhado do grafo LangGraph.

Fase 5: adicionado campo id_postgres para rastrear o registro
        inserido na tabela objetos_gerados_previas do PostgreSQL.

Ciclo de vida do Estado neste grafo:
  1. input_node        → valida e carrega o JSON
  2. documentation_node → preenche previa_documentacao
  3. cataloging_node   → preenche metadados_catalogo
  4. persistence_node  → preenche id_mongodb_previa e id_mongodb_metadados
  5. postgres_node     → preenche id_postgres
  6. supervisor_node   → preenche status_final e encerra
"""

from typing import Any
from typing_extensions import TypedDict


class DocumentacaoState(TypedDict):
    """
    Estado completo do grafo de documentação e catalogação.

    Campos:
        json_entrada: JSON normalizado recebido do inventário

        previa_documentacao: prévia gerada pelo documentation_node
                             → salva em documentos_gerados_previas (MongoDB)

        metadados_catalogo: metadados gerados pelo cataloging_node
                            → salva em componentes_catalogados_metadados (MongoDB)

        id_mongodb_previa: ID do documento em documentos_gerados_previas
        id_mongodb_metadados: ID do documento em componentes_catalogados_metadados
        id_postgres: UUID do registro em objetos_gerados_previas (PostgreSQL)

        status_final: "sucesso" | "erro" | "erro_parcial" | "processando"
        erros: lista de erros acumulados durante a execução
        etapa_atual: nome do nó sendo executado
    """

    # --- Entrada ---
    json_entrada: dict[str, Any]

    # --- Gerado pelo documentation_node ---
    previa_documentacao: dict[str, Any] | None

    # --- Gerado pelo cataloging_node ---
    metadados_catalogo: dict[str, Any] | None

    # --- Preenchido pelo persistence_node (MongoDB) ---
    id_mongodb_previa: str | None
    id_mongodb_metadados: str | None

    # --- Preenchido pelo postgres_node (PostgreSQL) ---
    id_postgres: str | None

    # --- Controle de fluxo ---
    status_final: str | None
    erros: list[str]
    etapa_atual: str | None


def criar_estado_inicial(json_entrada: dict[str, Any]) -> DocumentacaoState:
    """
    Cria o estado inicial do grafo com valores padrão.

    Args:
        json_entrada: JSON normalizado do inventário

    Returns:
        DocumentacaoState com json_entrada preenchido e
        todos os outros campos com valores padrão seguros.
    """
    return DocumentacaoState(
        json_entrada=json_entrada,
        previa_documentacao=None,
        metadados_catalogo=None,
        id_mongodb_previa=None,
        id_mongodb_metadados=None,
        id_postgres=None,
        status_final="processando",
        erros=[],
        etapa_atual="iniciando",
    )