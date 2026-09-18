"""
agent_application/agent_service.py
-------------------------------------
Orquestrador da aplicação — ponto de entrada do grafo LangGraph.

Fase 7: a entrada principal passa a ser uma URL de repositório
        (REPOSITORY_URL no .env), hardcoded para fins de teste/mock
        nesta fase. O consumer Kafka (Fase 4) permanece disponível
        na infraestrutura, mas não é o caminho usado por padrão aqui
        — quando o evento do inventário passar a carregar uma URL de
        repositório, basta plugar essa mesma função como callback.

Responsabilidades:
  1. Ler a URL do repositório configurada
  2. Criar o estado inicial do grafo com essa URL
  3. Executar o grafo LangGraph
  4. Exibir o resultado final
"""

import logging

from src.agent_application.graph import criar_grafo_documentacao
from src.agent_application.state import criar_estado_inicial
from src.settings import get_settings

logger = logging.getLogger(__name__)


def _processar_repositorio(repository_url: str) -> None:
    """
    Executa o grafo completo para uma URL de repositório.

    Args:
        repository_url: URL do repositório a ser analisado
    """
    logger.info("Repositório a processar: '%s'", repository_url)

    estado_inicial = criar_estado_inicial(repository_url)
    grafo = criar_grafo_documentacao()
    estado_final = grafo.invoke(estado_inicial)

    logger.info("")
    logger.info("=" * 60)
    logger.info("RESULTADO FINAL DO GRAFO")
    logger.info("=" * 60)
    logger.info("Status         : %s", estado_final.get("status_final"))
    logger.info("Última etapa   : %s", estado_final.get("etapa_atual"))
    logger.info("ID documentação: %s", estado_final.get("id_mongodb_previa"))
    logger.info("ID checklist   : %s", estado_final.get("id_mongodb_metadados"))
    logger.info("ID postgres    : %s", estado_final.get("id_postgres"))

    erros = estado_final.get("erros", [])
    if erros:
        logger.warning("Avisos/Erros   : %d ocorrência(s)", len(erros))
        for erro in erros:
            logger.warning("  • %s", erro)
    else:
        logger.info("Erros          : nenhum")

    logger.info("=" * 60)


def executar_grafo() -> None:
    """
    Ponto de entrada principal — Fase 7: entrada via URL de repositório.

    A URL é lida de REPOSITORY_URL no .env (hardcoded nesta fase para
    fins de teste). No futuro, essa função poderá ser chamada como
    callback de um consumer Kafka, exatamente como _processar_mensagem
    era chamada na Fase 4 — nenhuma mudança estrutural no restante do
    projeto seria necessária.
    """
    settings = get_settings()

    logger.info("=" * 60)
    logger.info("ATLAS DOCUMENTACAO AGENT — FASE 7")
    logger.info("Entrada via URL de repositório (%s)", settings.repository_provider)
    logger.info("=" * 60)

    _processar_repositorio(settings.repository_url)