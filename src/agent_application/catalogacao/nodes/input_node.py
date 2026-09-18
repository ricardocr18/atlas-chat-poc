"""
nodes/input_node.py
--------------------
Segundo nó do grafo (Fase 7) — valida os dados buscados do repositório.

Fase 1-6: validava campos de um JSON estruturado (team, application...).
Fase 7: valida se a busca do repositório trouxe o mínimo necessário
        para gerar documentação com qualidade.

Por que validar aqui e não deixar passar direto?
  Um repositório pode não ter README, não ter manifesto reconhecido,
  ou a árvore de arquivos pode ter vindo vazia. Nesses casos é melhor
  avisar cedo do que deixar a LLM gerar documentação sem contexto.
"""

import logging
from typing import Any

from src.agent_application.state import DocumentacaoState

logger = logging.getLogger(__name__)


def input_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Valida os dados do repositório buscados pelo repository_fetch_node.

    Verifica:
      - repo_data foi preenchido (busca não falhou)
      - existe pelo menos README ou algum manifesto (senão não há
        conteúdo suficiente para documentar)

    Args:
        state: Estado atual com repo_data preenchido

    Returns:
        dict com atualizações para o estado do grafo
    """
    logger.info("=" * 55)
    logger.info("[input_node] Validando dados do repositório")
    logger.info("=" * 55)

    if state.get("status_final") == "erro":
        logger.warning(
            "[input_node] ⚠ Erro detectado na busca do repositório — pulando validação"
        )
        return {"etapa_atual": "input_node"}

    repo_data = state.get("repo_data")
    erros = list(state.get("erros", []))

    if not repo_data:
        erro = "repo_data ausente — repository_fetch_node pode ter falhado"
        logger.error("[input_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "input_node",
        }

    tem_readme = bool(repo_data.get("readme_content"))
    tem_manifesto = bool(repo_data.get("manifestos"))

    if not tem_readme and not tem_manifesto:
        erro = (
            "Repositório sem README e sem manifesto reconhecido — "
            "conteúdo insuficiente para gerar documentação de qualidade"
        )
        logger.warning("[input_node] ⚠ %s", erro)
        erros.append(erro)
        # Não bloqueia o fluxo — segue com aviso, a LLM ainda pode
        # gerar algo a partir da árvore de arquivos e linguagem detectada

    logger.info(
        "[input_node] ✓ Repositório: '%s/%s'",
        repo_data.get("owner"),
        repo_data.get("repo_name"),
    )
    logger.info(
        "[input_node] ✓ Linguagem detectada: '%s'",
        repo_data.get("linguagem_principal") or "não identificada",
    )
    logger.info("[input_node] ✓ README presente: %s", tem_readme)
    logger.info("[input_node] ✓ Manifestos presentes: %s", tem_manifesto)
    logger.info("[input_node] ✓ Validação concluída — seguindo para documentation_node")

    return {
        "erros": erros,
        "etapa_atual": "input_node",
    }