"""
application/agent_service.py
------------------------------
Orquestrador da aplicação — camada entre o entry point (main.py)
e a infraestrutura (MongoDB).

Na Fase 1: executa o teste de conexão com as duas collections.
Na Fase 2: este será o ponto de entrada do grafo LangGraph.

Separar essa lógica do main.py é importante: o main.py apenas
inicializa e delega. Toda lógica de orquestração fica aqui.
"""

import logging

from src.infrastructure.mongodb import (
    ComponentesMetadadosRepository,
    DocumentosPreViasRepository,
    get_database,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dados mockados — representam o que o agente vai gerar nas próximas fases
# ---------------------------------------------------------------------------

MOCK_METADADOS = {
    "component_name": "customer-api",
    "application_name": "Customer Atlas",
    "team_id": "team-demo-customer",
    "time_responsavel": "Time Aurora",
    "projeto": "Projeto Customer",
    "tribo": "Tribo Horizon",
    "tipo_aplicacao": "api",
    "categoria_aplicacao": "backend",
    "environment": "DEV",
    "status_aplicacao": "ativa",
    "repository": "atlas-demo/customer-api",
    "linguagens_detectadas": ["Python"],
    "tags": ["backend", "api", "customer", "atlas"],
    "criticidade": "alta",
    "cloud_provider": "cloud-demo",
}

MOCK_PREVIA_DOCUMENTACAO = {
    "event_id": "evt-doc-001",
    "transaction_id": "txn-doc-001",
    "component_name": "customer-api",
    "titulo": "customer-api — Prévia de Documentação",
    "descricao_gerada": (
        "O componente customer-api é uma API backend de criticidade alta, "
        "pertencente ao Projeto Customer da Tribo Horizon. "
        "Desenvolvida pelo Time Aurora, a aplicação está ativa no ambiente DEV "
        "e hospedada no repositório atlas-demo/customer-api."
    ),
    "responsaveis": {
        "tech_leads": ["Lucas Andrade"],
        "aprovadores": ["Mariana Ribeiro"],
        "arquitetos": ["Fernanda Martins"],
    },
    "fonte_evento": "evt-doc-001",
    "tipo_evento": "component.created",
}


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------


def executar_teste_conexao() -> None:
    """
    Executa o teste completo de conexão com o MongoDB.

    Fluxo:
    1. Abre conexão com o banco via context manager
    2. Insere documento mockado em 'componentes_catalogados_metadados'
    3. Insere documento mockado em 'documentos_gerados_previas'
    4. Lê e exibe os documentos inseridos
    5. Confirma sucesso ou registra o erro

    Este método será substituído pelo grafo LangGraph na Fase 2.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO TESTE DE CONEXÃO — FASE 1")
    logger.info("=" * 60)

    with get_database() as db:
        # --- Repositórios ---
        repo_metadados = ComponentesMetadadosRepository(db)
        repo_previas = DocumentosPreViasRepository(db)

        # --- Inserção em componentes_catalogados_metadados ---
        logger.info("[1/4] Inserindo metadados do componente...")
        id_metadados = repo_metadados.inserir(MOCK_METADADOS)
        logger.info("      ✓ Inserido com ID: %s", id_metadados)

        # --- Inserção em documentos_gerados_previas ---
        logger.info("[2/4] Inserindo prévia de documentação...")
        id_previa = repo_previas.inserir(MOCK_PREVIA_DOCUMENTACAO)
        logger.info("      ✓ Inserido com ID: %s", id_previa)

        # --- Leitura de validação: metadados ---
        logger.info("[3/4] Lendo metadados inseridos para validação...")
        metadados_lido = repo_metadados.buscar_por_component_name("customer-api")
        if metadados_lido:
            logger.info("      ✓ Componente encontrado: '%s'", metadados_lido.get("component_name"))
            logger.info("      ✓ Time responsável: '%s'", metadados_lido.get("time_responsavel"))
            logger.info("      ✓ Criticidade: '%s'", metadados_lido.get("criticidade"))
        else:
            logger.error("      ✗ Metadados não encontrados após inserção!")

        # --- Leitura de validação: prévia ---
        logger.info("[4/4] Lendo prévia inserida para validação...")
        previa_lida = repo_previas.buscar_por_event_id("evt-doc-001")
        if previa_lida:
            logger.info("      ✓ Prévia encontrada para evento: '%s'", previa_lida.get("event_id"))
            logger.info("      ✓ Título: '%s'", previa_lida.get("titulo"))
            logger.info("      ✓ Status: '%s'", previa_lida.get("status"))
        else:
            logger.error("      ✗ Prévia não encontrada após inserção!")

    logger.info("=" * 60)
    logger.info("FASE 1 CONCLUÍDA COM SUCESSO ✓")
    logger.info("Verifique os dados no MongoDB Compass:")
    logger.info("  DB: atlas_documentacao_agente")
    logger.info("  Collections: componentes_catalogados_metadados | documentos_gerados_previas")
    logger.info("=" * 60)