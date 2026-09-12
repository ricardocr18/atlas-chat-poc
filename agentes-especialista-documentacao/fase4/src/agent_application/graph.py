"""
agents/documentacao/graph.py
------------------------------
Monta e compila o grafo LangGraph do agente de documentação.

Este arquivo é o "mapa" do grafo — define quais nós existem
e em que ordem se conectam. É aqui que a sequência do fluxo
fica visível de forma clara e centralizada.

Estrutura do grafo:
  START
    ↓
  input_node          (valida o JSON de entrada)
    ↓
  documentation_node  (gera prévia de documentação)
    ↓
  cataloging_node     (gera metadados de catálogo)
    ↓
  persistence_node    (salva nas collections corretas)
    ↓
  supervisor_node     (valida e consolida o resultado)
    ↓
  END

Por que grafo sequencial e não condicional?
  Na Fase 2, o fluxo é sempre linear — cada nó sempre leva
  ao próximo. Nas próximas fases poderemos adicionar arestas
  condicionais (ex: se o documento estiver incompleto, voltar
  ao input_node para reprocessar) sem mudar os nós.
"""

import logging

from langgraph.graph import END, START, StateGraph

from src.agent_application.catalogacao.nodes.cataloging_node import cataloging_node
from src.agent_application.catalogacao.nodes.documentation_node import documentation_node
from src.agent_application.catalogacao.nodes.input_node import input_node
from src.agent_application.catalogacao.nodes.persistence_node import persistence_node
from src.agent_application.catalogacao.nodes.supervisor_node import supervisor_node
from src.agent_application.state import DocumentacaoState

logger = logging.getLogger(__name__)


def criar_grafo_documentacao():
    """
    Monta e compila o grafo de documentação e catalogação.

    Fluxo de montagem:
      1. Instancia o StateGraph com o tipo do Estado
      2. Adiciona cada nó com seu nome e função
      3. Define as arestas (conexões entre nós)
      4. Define o ponto de entrada (START)
      5. Compila o grafo — a partir daqui ele está pronto para executar

    Returns:
        Grafo compilado pronto para receber invoke()
    """
    logger.info("Montando grafo de documentação e catalogação...")

    # --- 1. Instancia o grafo com o tipo do Estado ---
    # O StateGraph sabe que cada nó vai receber e retornar
    # um DocumentacaoState (ou subconjunto dele)
    grafo = StateGraph(DocumentacaoState)

    # --- 2. Adiciona os nós ---
    # Cada nó tem: nome (string) + função Python que executa
    grafo.add_node("input_node", input_node)
    grafo.add_node("documentation_node", documentation_node)
    grafo.add_node("cataloging_node", cataloging_node)
    grafo.add_node("persistence_node", persistence_node)
    grafo.add_node("supervisor_node", supervisor_node)

    # --- 3. Define as arestas (fluxo entre os nós) ---
    # Fluxo linear: cada nó leva ao próximo
    grafo.add_edge(START, "input_node")
    grafo.add_edge("input_node", "documentation_node")
    grafo.add_edge("documentation_node", "cataloging_node")
    grafo.add_edge("cataloging_node", "persistence_node")
    grafo.add_edge("persistence_node", "supervisor_node")
    grafo.add_edge("supervisor_node", END)

    # --- 4. Compila o grafo ---
    # Após compilar, o grafo está "fechado" — não aceita mais
    # modificações de estrutura, só execuções via invoke()
    grafo_compilado = grafo.compile()

    logger.info("Grafo compilado com sucesso — 5 nós, fluxo linear")
    logger.info(
        "Fluxo: START → input → documentation → cataloging → persistence → supervisor → END"
    )

    return grafo_compilado