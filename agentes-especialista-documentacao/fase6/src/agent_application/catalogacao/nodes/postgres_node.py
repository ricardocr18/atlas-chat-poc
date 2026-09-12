"""
nodes/postgres_node.py
------------------------
Quinto nó do grafo — persiste o pré-cadastro no PostgreSQL.

Posição no grafo:
  persistence_node (MongoDB) → postgres_node (PostgreSQL) → supervisor_node

Responsabilidade: receber o estado com todos os dados já gerados
e salvos no MongoDB, e inserir o pré-cadastro do componente na
tabela objetos_gerados_previas do PostgreSQL.

Por que depois do persistence_node?
  O postgres_node usa os IDs do MongoDB (id_mongodb_previa e
  id_mongodb_metadados) como referências cruzadas no PostgreSQL.
  Esses IDs só existem depois que o persistence_node executou.
  Isso cria um vínculo rastreável entre os três bancos.

Rastreabilidade entre bancos:
  MongoDB collection previas     → id_mongodb_previa
  MongoDB collection metadados   → id_mongodb_metadados
  PostgreSQL objetos_gerados_previas → referencia ambos os IDs
"""

import logging
from typing import Any

from src.agent_application.state import DocumentacaoState
from src.infrastructure.postgresql import (
    ObjetosGeradosPreViasRepository,
    get_connection,
)

logger = logging.getLogger(__name__)


def postgres_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Persiste o pré-cadastro do componente no PostgreSQL.

    Fluxo:
      1. Verifica se há erros críticos no estado
      2. Coleta os dados necessários do estado
      3. Abre conexão com PostgreSQL via context manager
      4. Garante que a tabela existe (cria se necessário)
      5. Insere o pré-cadastro com referências aos IDs do MongoDB
      6. Atualiza o estado com o ID gerado pelo PostgreSQL

    Args:
        state: Estado com todos os campos preenchidos pelos
               nós anteriores, incluindo IDs do MongoDB

    Returns:
        dict com id_postgres preenchido
    """
    logger.info("-" * 55)
    logger.info("[postgres_node] Iniciando persistência no PostgreSQL")
    logger.info("-" * 55)

    # Se houve erro crítico, não persiste dados incompletos
    if state.get("status_final") == "erro":
        logger.warning(
            "[postgres_node] ⚠ Erro crítico detectado — abortando persistência"
        )
        return {"etapa_atual": "postgres_node"}

    metadados = state.get("metadados_catalogo")
    previa = state.get("previa_documentacao")
    id_mongodb_previa = state.get("id_mongodb_previa")
    id_mongodb_metadados = state.get("id_mongodb_metadados")
    erros = list(state.get("erros", []))

    # Valida se os dados e IDs do MongoDB estão presentes
    if not metadados or not previa:
        erro = "metadados ou prévia ausentes — nós anteriores podem ter falhado"
        logger.error("[postgres_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "postgres_node",
        }

    if not id_mongodb_previa or not id_mongodb_metadados:
        erro = "IDs do MongoDB ausentes — persistence_node pode ter falhado"
        logger.error("[postgres_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "postgres_node",
        }

    try:
        with get_connection() as conn:
            repo = ObjetosGeradosPreViasRepository(conn)

            # Garante que a tabela existe antes de inserir
            repo.garantir_tabela()

            # Insere o pré-cadastro com referências cruzadas ao MongoDB
            logger.info(
                "[postgres_node] Inserindo pré-cadastro de '%s'...",
                metadados.get("component_name"),
            )
            id_postgres = repo.inserir(
                metadados=metadados,
                previa=previa,
                id_mongodb_previa=id_mongodb_previa,
                id_mongodb_metadados=id_mongodb_metadados,
            )

            logger.info(
                "[postgres_node] ✓ Pré-cadastro salvo com ID: %s",
                id_postgres,
            )

            # Leitura de validação
            registro = repo.buscar_por_event_id(
                metadados.get("event_id", "")
            )
            if registro:
                logger.info(
                    "[postgres_node] ✓ Validação — componente: '%s' | status: '%s'",
                    registro.get("component_name"),
                    registro.get("status_cadastro"),
                )

        logger.info(
            "[postgres_node] ✓ Persistência PostgreSQL concluída — seguindo para supervisor_node"
        )

        return {
            "id_postgres": id_postgres,
            "erros": erros,
            "etapa_atual": "postgres_node",
        }

    except Exception as exc:
        erro = f"Erro ao persistir no PostgreSQL: {str(exc)}"
        logger.error("[postgres_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "postgres_node",
        }