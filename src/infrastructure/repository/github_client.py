"""
infrastructure/repository/github_client.py
----------------------------------------------
Cliente de busca de repositórios via API REST do GitHub.

Usado no ambiente mockado (local). Busca apenas o necessário para
gerar a documentação — não clona o repositório inteiro:
  - Metadados básicos (linguagem, descrição, branch padrão)
  - README (decodificado de base64)
  - Árvore de arquivos (caminhos, sem conteúdo)
  - Conteúdo dos arquivos de manifesto conhecidos (pyproject.toml,
    package.json, build.gradle, pom.xml, requirements.txt)

Documentação da API: https://docs.github.com/en/rest
"""

import base64
import logging
import re

import httpx

from src.infrastructure.repository.config import montar_headers_github

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"

# Nomes de arquivo que, se encontrados na raiz, são buscados por completo
# — são a fonte mais confiável de "quais bibliotecas existem"
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


def extrair_owner_repo(url: str) -> tuple[str, str]:
    """
    Extrai owner e nome do repositório a partir de uma URL do GitHub.

    Aceita formatos como:
      https://github.com/owner/repo
      https://github.com/owner/repo/
      https://github.com/owner/repo/tree/main

    Args:
        url: URL completa do repositório

    Returns:
        (owner, repo_name)

    Raises:
        ValueError: se a URL não corresponder ao padrão esperado
    """
    padrao = r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)"
    match = re.search(padrao, url)

    if not match:
        raise ValueError(f"URL do GitHub inválida ou não reconhecida: {url}")

    owner, repo = match.group(1), match.group(2)
    return owner, repo


def buscar_repositorio(url: str) -> dict:
    """
    Busca as informações necessárias de um repositório GitHub.

    Fluxo:
      1. Extrai owner/repo da URL
      2. Busca metadados do repositório (linguagem, branch padrão, descrição)
      3. Busca o README (decodifica de base64)
      4. Busca a árvore de arquivos (recursiva)
      5. Busca o conteúdo dos arquivos de manifesto encontrados na raiz

    Args:
        url: URL do repositório no GitHub

    Returns:
        dict com todos os dados coletados, pronto para os próximos nós

    Raises:
        httpx.HTTPStatusError: se alguma requisição obrigatória falhar
        ValueError: se a URL for inválida
    """
    owner, repo_name = extrair_owner_repo(url)
    headers = montar_headers_github()

    logger.info("[github_client] Buscando repositório: %s/%s", owner, repo_name)

    with httpx.Client(timeout=TIMEOUT_SEGUNDOS, headers=headers) as client:
        # --- 1. Metadados do repositório ---
        resp_repo = client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}")
        resp_repo.raise_for_status()
        dados_repo = resp_repo.json()

        default_branch = dados_repo.get("default_branch", "main")
        linguagem = dados_repo.get("language")
        descricao = dados_repo.get("description")

        logger.info(
            "[github_client] ✓ Metadados obtidos — linguagem: '%s' | branch: '%s'",
            linguagem,
            default_branch,
        )

        # --- 2. README ---
        readme_content = None
        try:
            resp_readme = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/readme"
            )
            resp_readme.raise_for_status()
            readme_data = resp_readme.json()
            readme_content = base64.b64decode(
                readme_data.get("content", "")
            ).decode("utf-8", errors="replace")
            logger.info(
                "[github_client] ✓ README obtido — %d caracteres",
                len(readme_content),
            )
        except httpx.HTTPStatusError:
            logger.warning("[github_client] ⚠ README não encontrado no repositório")

        # --- 3. Árvore de arquivos (recursiva) ---
        arquivos = []
        try:
            resp_tree = client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/git/trees/"
                f"{default_branch}",
                params={"recursive": "1"},
            )
            resp_tree.raise_for_status()
            tree_data = resp_tree.json()
            arquivos = [
                item["path"]
                for item in tree_data.get("tree", [])
                if item.get("type") == "blob"
            ]
            logger.info(
                "[github_client] ✓ Árvore de arquivos obtida — %d arquivos",
                len(arquivos),
            )
        except httpx.HTTPStatusError:
            logger.warning("[github_client] ⚠ Árvore de arquivos não pôde ser obtida")

        # --- 4. Arquivos de manifesto (só os que existem na raiz) ---
        manifestos: dict[str, str] = {}
        for nome_arquivo in ARQUIVOS_MANIFESTO:
            if nome_arquivo not in arquivos:
                continue
            try:
                resp_arquivo = client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/contents/"
                    f"{nome_arquivo}"
                )
                resp_arquivo.raise_for_status()
                conteudo_data = resp_arquivo.json()
                manifestos[nome_arquivo] = base64.b64decode(
                    conteudo_data.get("content", "")
                ).decode("utf-8", errors="replace")
                logger.info(
                    "[github_client] ✓ Manifesto encontrado: '%s'", nome_arquivo
                )
            except httpx.HTTPStatusError:
                logger.debug(
                    "[github_client] Manifesto '%s' listado mas não pôde ser lido",
                    nome_arquivo,
                )

    return {
        "repository_url": url,
        "owner": owner,
        "repo_name": repo_name,
        "event_id": f"{owner}/{repo_name}",
        "linguagem_principal": linguagem,
        "descricao": descricao,
        "default_branch": default_branch,
        "readme_content": readme_content,
        "arquivos": arquivos,
        "manifestos": manifestos,
    }