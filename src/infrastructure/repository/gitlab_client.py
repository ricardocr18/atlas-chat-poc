"""
infrastructure/repository/gitlab_client.py
----------------------------------------------
Cliente de busca de repositórios via API REST do GitLab.

Preparado para o ambiente de produção da Sicredi (GitLab privado).
Segue a mesma interface de retorno do github_client.py — o resto do
grafo não precisa saber qual provedor foi usado.

⚠️ AINDA NÃO TESTADO — depende de acesso real ao GitLab da Sicredi
   (GITLAB_BASE_URL e GITLAB_TOKEN configurados no .env).

Documentação da API: https://docs.gitlab.com/ee/api/repositories.html
"""

import base64
import logging
import re
from urllib.parse import quote

import httpx

from src.infrastructure.repository.config import montar_headers_gitlab
from src.settings import get_settings

logger = logging.getLogger(__name__)

ARQUIVOS_MANIFESTO = [
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "build.gradle",
    "pom.xml",
    "go.mod",
    "Dockerfile",
    "docker-compose.yml",
]

TIMEOUT_SEGUNDOS = 15


def extrair_project_path(url: str) -> str:
    """
    Extrai o caminho do projeto (namespace/repo) a partir de uma URL do GitLab.

    Aceita formatos como:
      https://gitlab.sicredi.net/quality-console/quality-console-back-end
      https://gitlab.sicredi.net/quality-console/quality-console-back-end/blob/master

    Args:
        url: URL completa do repositório

    Returns:
        Caminho do projeto, ex: "quality-console/quality-console-back-end"
    """
    settings = get_settings()
    base_url_limpa = settings.gitlab_base_url.rstrip("/")

    padrao = rf"{re.escape(base_url_limpa)}/(.+?)(?:/blob/.*|/-/.*|\.git)?$"
    match = re.search(padrao, url)

    if not match:
        raise ValueError(f"URL do GitLab inválida ou não reconhecida: {url}")

    return match.group(1)


def buscar_repositorio(url: str) -> dict:
    """
    Busca as informações necessárias de um repositório GitLab.

    Mesma estrutura de retorno do github_client.buscar_repositorio(),
    para que o repository_fetch_node não precise diferenciar a origem.

    Args:
        url: URL do repositório no GitLab

    Returns:
        dict com todos os dados coletados

    Raises:
        httpx.HTTPStatusError: se alguma requisição obrigatória falhar
        ValueError: se a URL for inválida
    """
    settings = get_settings()
    project_path = extrair_project_path(url)
    project_id_encoded = quote(project_path, safe="")
    headers = montar_headers_gitlab()
    api_base = f"{settings.gitlab_base_url.rstrip('/')}/api/v4"

    logger.info("[gitlab_client] Buscando repositório: %s", project_path)

    with httpx.Client(timeout=TIMEOUT_SEGUNDOS, headers=headers) as client:
        # --- 1. Metadados do projeto ---
        resp_repo = client.get(f"{api_base}/projects/{project_id_encoded}")
        resp_repo.raise_for_status()
        dados_repo = resp_repo.json()

        default_branch = dados_repo.get("default_branch", "master")
        descricao = dados_repo.get("description")

        logger.info(
            "[gitlab_client] ✓ Metadados obtidos — branch: '%s'",
            default_branch,
        )

        # --- 2. README ---
        readme_content = None
        try:
            resp_readme = client.get(
                f"{api_base}/projects/{project_id_encoded}/repository/files/"
                f"README.md/raw",
                params={"ref": default_branch},
            )
            resp_readme.raise_for_status()
            readme_content = resp_readme.text
            logger.info(
                "[gitlab_client] ✓ README obtido — %d caracteres",
                len(readme_content),
            )
        except httpx.HTTPStatusError:
            logger.warning("[gitlab_client] ⚠ README não encontrado")

        # --- 3. Árvore de arquivos (recursiva) ---
        arquivos = []
        try:
            resp_tree = client.get(
                f"{api_base}/projects/{project_id_encoded}/repository/tree",
                params={"recursive": "true", "per_page": 100},
            )
            resp_tree.raise_for_status()
            tree_data = resp_tree.json()
            arquivos = [
                item["path"]
                for item in tree_data
                if item.get("type") == "blob"
            ]
            logger.info(
                "[gitlab_client] ✓ Árvore de arquivos obtida — %d arquivos",
                len(arquivos),
            )
        except httpx.HTTPStatusError:
            logger.warning("[gitlab_client] ⚠ Árvore de arquivos não pôde ser obtida")

        # --- 4. Arquivos de manifesto ---
        manifestos: dict[str, str] = {}
        for nome_arquivo in ARQUIVOS_MANIFESTO:
            if nome_arquivo not in arquivos:
                continue
            try:
                caminho_encoded = quote(nome_arquivo, safe="")
                resp_arquivo = client.get(
                    f"{api_base}/projects/{project_id_encoded}/repository/files/"
                    f"{caminho_encoded}/raw",
                    params={"ref": default_branch},
                )
                resp_arquivo.raise_for_status()
                manifestos[nome_arquivo] = resp_arquivo.text
                logger.info(
                    "[gitlab_client] ✓ Manifesto encontrado: '%s'", nome_arquivo
                )
            except httpx.HTTPStatusError:
                logger.debug(
                    "[gitlab_client] Manifesto '%s' listado mas não pôde ser lido",
                    nome_arquivo,
                )

    owner, _, repo_name = project_path.rpartition("/")

    return {
        "repository_url": url,
        "owner": owner or project_path,
        "repo_name": repo_name or project_path,
        "event_id": project_path,
        "linguagem_principal": None,  # GitLab não retorna isso no endpoint básico
        "descricao": descricao,
        "default_branch": default_branch,
        "readme_content": readme_content,
        "arquivos": arquivos,
        "manifestos": manifestos,
    }