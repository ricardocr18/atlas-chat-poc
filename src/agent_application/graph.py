"""
agent_application/graph.py
------------------------------
Monta e compila o grafo LangGraph do agente de documentação.

Fase 7: adicionado repository_fetch_node como primeiro nó, antes do
        input_node — busca o conteúdo do repositório antes de
        qualquer validação ou geração via LLM.

Estrutura do grafo:
  START
    ↓
  repository_fetch_node  (busca README, árvore de arquivos, manifestos)
    ↓
  input_node             (valida se há conteúdo suficiente)
    ↓
  documentation_node     (gera wiki multi-seção via LLM OpenAI)
    ↓
  cataloging_node        (gera checklist técnico via LLM OpenAI)
    ↓
  persistence_node       (salva nas collections MongoDB)
    ↓
  postgres_node          (salva pré-cadastro no PostgreSQL)
    ↓
  supervisor_node        (valida e consolida o resultado)
    ↓
  END
"""

import logging

from langgraph.graph import END, START, StateGraph

from src.agent_application.catalogacao.nodes.cataloging_node import cataloging_node
from src.agent_application.catalogacao.nodes.documentation_node import documentation_node
from src.agent_application.catalogacao.nodes.input_node import input_node
from src.agent_application.catalogacao.nodes.persistence_node import persistence_node
from src.agent_application.catalogacao.nodes.postgres_node import postgres_node
from src.agent_application.catalogacao.nodes.repository_fetch_node import repository_fetch_node
from src.agent_application.catalogacao.nodes.supervisor_node import supervisor_node
from src.agent_application.state import DocumentacaoState

logger = logging.getLogger(__name__)


def criar_grafo_documentacao():
    """
    Monta e compila o grafo de documentação e catalogação.

    Returns:
        Grafo compilado pronto para receber invoke()
    """
    logger.info("Montando grafo de documentação e catalogação...")

    grafo = StateGraph(DocumentacaoState)

    # --- Adiciona os nós ---
    grafo.add_node("repository_fetch_node", repository_fetch_node)
    grafo.add_node("input_node", input_node)
    grafo.add_node("documentation_node", documentation_node)
    grafo.add_node("cataloging_node", cataloging_node)
    grafo.add_node("persistence_node", persistence_node)
    grafo.add_node("postgres_node", postgres_node)
    grafo.add_node("supervisor_node", supervisor_node)

    # --- Define as arestas (fluxo entre os nós) ---
    grafo.add_edge(START, "repository_fetch_node")
    grafo.add_edge("repository_fetch_node", "input_node")
    grafo.add_edge("input_node", "documentation_node")
    grafo.add_edge("documentation_node", "cataloging_node")
    grafo.add_edge("cataloging_node", "persistence_node")
    grafo.add_edge("persistence_node", "postgres_node")
    grafo.add_edge("postgres_node", "supervisor_node")
    grafo.add_edge("supervisor_node", END)

    grafo_compilado = grafo.compile()

    logger.info("Grafo compilado com sucesso — 7 nós, fluxo linear")
    logger.info(
        "Fluxo: START → repository_fetch → input → documentation → "
        "cataloging → persistence → postgres → supervisor → END"
    )

    return grafo_compilado