"""
agents/documentacao/state.py
------------------------------
Define o Estado compartilhado do grafo LangGraph.

O Estado é o objeto central do LangGraph — ele é passado de nó em nó,
sendo enriquecido progressivamente. Cada nó lê o que precisa do estado
e escreve o resultado de volta nele.

Analogia: pense no Estado como uma ficha de pedido num restaurante.
Ela começa com o pedido do cliente (JSON de entrada) e cada estação
da cozinha vai preenchendo sua parte até a ficha estar completa.

Ciclo de vida do Estado neste grafo:
  1. input_node        → preenche json_entrada, valida dados
  2. documentation_node → preenche previa_documentacao
  3. cataloging_node   → preenche metadados_catalogo
  4. persistence_node  → preenche ids_mongodb após salvar
  5. supervisor_node   → preenche status_final e encerra
"""

from typing import Any
from typing_extensions import TypedDict


class DocumentacaoState(TypedDict):
    """
    Estado completo do grafo de documentação e catalogação.

    Todos os campos são opcionais exceto json_entrada — os nós
    preenchem progressivamente conforme o grafo avança.

    Campos:
        json_entrada: JSON normalizado recebido do inventário
                      (virá do Kafka na Fase 4, mock por ora)

        previa_documentacao: prévia de documentação gerada pelo
                             documentation_node. Será salva na
                             collection documentos_gerados_previas.
                             Na Fase 3 será gerada pela LLM OpenAI.

        metadados_catalogo: metadados estruturados gerados pelo
                            cataloging_node. Será salvo na collection
                            componentes_catalogados_metadados.
                            Na Fase 3 será gerado pela LLM OpenAI.

        id_mongodb_previa: ID do documento inserido na collection
                           documentos_gerados_previas. Preenchido
                           pelo persistence_node após salvar.

        id_mongodb_metadados: ID do documento inserido na collection
                              componentes_catalogados_metadados.
                              Preenchido pelo persistence_node.

        status_final: resultado da execução do grafo.
                      Valores: "sucesso" | "erro" | "processando"

        erros: lista de erros acumulados durante a execução.
               O grafo não para no primeiro erro — acumula e
               o supervisor_node decide o que fazer.

        etapa_atual: nome do nó sendo executado no momento.
                     Útil para logs e debugging.
    """

    # --- Entrada ---
    json_entrada: dict[str, Any]

    # --- Gerado pelo documentation_node (Fase 3: LLM) ---
    previa_documentacao: dict[str, Any] | None

    # --- Gerado pelo cataloging_node (Fase 3: LLM) ---
    metadados_catalogo: dict[str, Any] | None

    # --- Preenchido pelo persistence_node ---
    id_mongodb_previa: str | None
    id_mongodb_metadados: str | None

    # --- Controle de fluxo ---
    status_final: str | None
    erros: list[str]
    etapa_atual: str | None


def criar_estado_inicial(json_entrada: dict[str, Any]) -> DocumentacaoState:
    """
    Cria o estado inicial do grafo com valores padrão.

    Sempre chamado antes de iniciar o grafo — garante que todos
    os campos existem mesmo que ainda não preenchidos.

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
        status_final="processando",
        erros=[],
        etapa_atual="iniciando",
    )