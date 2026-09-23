"""
agent_application/state.py
------------------------------
Define o Estado compartilhado do grafo LangGraph.

Fase 7: substitui json_entrada por repository_url como entrada principal.
        Adiciona repo_data (dados brutos buscados do repositório) e
        muda previa_documentacao para o formato multi-seção (wiki).

Ciclo de vida do Estado neste grafo:
  1. repository_fetch_node → preenche repo_data a partir da repository_url
  2. input_node             → valida repo_data
  3. documentation_node     → preenche secoes_documentacao (formato wiki)
  4. cataloging_node        → preenche metadados_catalogo (checklist técnico)
  5. persistence_node       → preenche id_mongodb_previa e id_mongodb_metadados
  6. postgres_node          → preenche id_postgres
  7. supervisor_node        → preenche status_final e encerra
"""

from typing import Any
from typing_extensions import TypedDict


class DocumentacaoState(TypedDict):
    """
    Estado completo do grafo de documentação e catalogação.

    Campos:
        repository_url: URL do repositório a ser analisado (entrada)

        repo_data: dados brutos buscados do repositório pelo
                   repository_fetch_node — README, árvore de arquivos,
                   manifestos, linguagem, event_id derivado (owner/repo)

        secoes_documentacao: lista de seções geradas pelo documentation_node,
                             cada uma com titulo, ordem e conteudo_markdown
                             → salva em documentos_gerados_previas (MongoDB)

        metadados_catalogo: resultado do checklist técnico gerado pelo
                            cataloging_node (libs, segurança, bancos,
                            mensageria, tecnologia, Sicredi Flow, S3, imagem)
                            → salva em componentes_catalogados_metadados (MongoDB)

        id_mongodb_previa: ID do documento em documentos_gerados_previas
        id_mongodb_metadados: ID do documento em componentes_catalogados_metadados
        id_postgres: UUID do registro em objetos_gerados_previas (PostgreSQL)

        status_final: "sucesso" | "erro" | "erro_parcial" | "processando"
        erros: lista de erros acumulados durante a execução
        etapa_atual: nome do nó sendo executado
    """

    # --- Entrada ---
    repository_url: str

    # --- Preenchido pelo repository_fetch_node ---
    repo_data: dict[str, Any] | None

    # --- Gerado pelo documentation_node ---
    secoes_documentacao: list[dict[str, Any]] | None

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


def criar_estado_inicial(repository_url: str) -> DocumentacaoState:
    """
    Cria o estado inicial do grafo com valores padrão.

    Args:
        repository_url: URL do repositório a ser analisado

    Returns:
        DocumentacaoState com repository_url preenchida e
        todos os outros campos com valores padrão seguros.
    """
    return DocumentacaoState(
        repository_url=repository_url,
        repo_data=None,
        secoes_documentacao=None,
        metadados_catalogo=None,
        id_mongodb_previa=None,
        id_mongodb_metadados=None,
        id_postgres=None,
        status_final="processando",
        erros=[],
        etapa_atual="iniciando",
    )