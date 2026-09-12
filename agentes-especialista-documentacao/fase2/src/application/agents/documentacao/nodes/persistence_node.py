"""
nodes/persistence_node.py
---------------------------
Quarto nó do grafo — persiste os dados gerados nas collections corretas.

Responsabilidade única: receber o estado com previa_documentacao e
metadados_catalogo já gerados e salvar cada um na sua collection
correta no MongoDB.

Este é o nó que responde à sua pergunta original:
  "os nodes vão escolher para onde enviar corretamente as informações
   para os devidos Collections corretas"

Decisões de roteamento:
  previa_documentacao  → collection documentos_gerados_previas
  metadados_catalogo   → collection componentes_catalogados_metadados

Por que isso é um Node e não uma Tool?
  Porque a persistência é SEMPRE obrigatória — não depende de
  nenhuma decisão da LLM. Todo componente processado DEVE ser
  salvo nas duas collections. Tools são para ações opcionais
  que a LLM decide chamar ou não.

Importante: este nó usa os repositórios da Fase 1 sem alteração.
  Isso demonstra o valor da arquitetura em camadas — a infraestrutura
  construída na Fase 1 é reaproveitada integralmente.
"""

import logging
from typing import Any

from src.application.agents.documentacao.state import DocumentacaoState
from src.infrastructure.mongodb import (
    ComponentesMetadadosRepository,
    DocumentosPreViasRepository,
    get_database,
)

logger = logging.getLogger(__name__)


def persistence_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Persiste a prévia e os metadados nas collections corretas do MongoDB.

    Fluxo:
      1. Verifica se há erros críticos no estado
      2. Verifica se os dados necessários foram gerados
      3. Abre conexão com MongoDB via context manager
      4. Salva previa_documentacao em documentos_gerados_previas
      5. Salva metadados_catalogo em componentes_catalogados_metadados
      6. Atualiza o estado com os IDs gerados pelo MongoDB

    Args:
        state: Estado com previa_documentacao e metadados_catalogo

    Returns:
        dict com id_mongodb_previa e id_mongodb_metadados preenchidos
    """
    logger.info("-" * 55)
    logger.info("[persistence_node] Iniciando persistência no MongoDB")
    logger.info("-" * 55)

    # Se houve erro crítico, não persiste dados incompletos
    if state.get("status_final") == "erro":
        logger.warning(
            "[persistence_node] ⚠ Erro crítico detectado — abortando persistência"
        )
        return {"etapa_atual": "persistence_node"}

    previa = state.get("previa_documentacao")
    metadados = state.get("metadados_catalogo")
    erros = list(state.get("erros", []))

    # Valida se os dados foram gerados pelos nós anteriores
    if not previa:
        erro = "previa_documentacao não foi gerada pelo documentation_node"
        logger.error("[persistence_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "persistence_node",
        }

    if not metadados:
        erro = "metadados_catalogo não foram gerados pelo cataloging_node"
        logger.error("[persistence_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "persistence_node",
        }

    try:
        with get_database() as db:
            repo_previas = DocumentosPreViasRepository(db)
            repo_metadados = ComponentesMetadadosRepository(db)

            # --- Salva prévia → documentos_gerados_previas ---
            logger.info(
                "[persistence_node] Salvando prévia em 'documentos_gerados_previas'..."
            )
            id_previa = repo_previas.inserir(previa)
            logger.info(
                "[persistence_node] ✓ Prévia salva com ID: %s", id_previa
            )

            # --- Salva metadados → componentes_catalogados_metadados ---
            logger.info(
                "[persistence_node] Salvando metadados em 'componentes_catalogados_metadados'..."
            )
            id_metadados = repo_metadados.inserir(metadados)
            logger.info(
                "[persistence_node] ✓ Metadados salvos com ID: %s", id_metadados
            )

        logger.info(
            "[persistence_node] ✓ Persistência concluída — seguindo para supervisor_node"
        )

        return {
            "id_mongodb_previa": id_previa,
            "id_mongodb_metadados": id_metadados,
            "erros": erros,
            "etapa_atual": "persistence_node",
        }

    except Exception as exc:
        erro = f"Erro ao persistir no MongoDB: {str(exc)}"
        logger.error("[persistence_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "persistence_node",
        }