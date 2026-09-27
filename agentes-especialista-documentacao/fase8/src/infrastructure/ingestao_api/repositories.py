"""
infrastructure/ingestao_api/repositories.py
------------------------------------------------
Repositório de LEITURA para a collection document_context
(banco atlas_ingestao_api, mantido pelo atlas-apis-ingestao).

Fase 8: mecanismo de descoberta é manual, por component_name — decisão
        tomada explicitamente para este momento do projeto. Um mecanismo
        automático (polling periódico ou evento Kafka publicado pelo
        atlas-apis-ingestao) fica para uma fase futura.

Este repositório é estritamente de LEITURA — nenhum método de escrita
é exposto aqui de propósito, para deixar explícito que este projeto
nunca deve alterar dados de outro serviço.
"""

import logging
from typing import Any

from pymongo.database import Database

logger = logging.getLogger(__name__)

COLLECTION_DOCUMENT_CONTEXT = "document_context"


class DocumentContextRepository:
    """
    Repositório de leitura para a collection document_context.

    Responsável por buscar o contexto completo de um componente,
    já normalizado pelo atlas-apis-ingestao, a partir do component_name.
    """

    def __init__(self, database: Database) -> None:
        self._collection = database[COLLECTION_DOCUMENT_CONTEXT]
        logger.debug(
            "Repositório de leitura '%s' inicializado.", COLLECTION_DOCUMENT_CONTEXT
        )

    def buscar_por_component_name(self, component_name: str) -> dict[str, Any] | None:
        """
        Busca o documento de contexto de um componente pelo nome exato.

        Args:
            component_name: nome do componente, deve bater exatamente
                             com o valor gravado pelo atlas-apis-ingestao

        Returns:
            dict com o documento completo (sem o campo _id do Mongo),
            ou None se nenhum componente com esse nome for encontrado
        """
        resultado = self._collection.find_one(
            {"component_name": component_name},
            {"_id": 0},
        )

        if resultado:
            logger.info(
                "[document_context] ✓ Componente '%s' encontrado.", component_name
            )
        else:
            logger.warning(
                "[document_context] ✗ Componente '%s' não encontrado "
                "no atlas_ingestao_api.",
                component_name,
            )

        return resultado