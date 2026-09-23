"""
infrastructure/repository/gitlab_client.py
----------------------------------------------
Cliente de busca de repositórios via API REST do GitLab.

Incremento na Fase 7: mesma detecção de sinais determinísticos do
github_client.py, incluindo agora também a data de criação do
repositório (repositorio_criado_em) — mantém a mesma interface de
retorno para os dois provedores.

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
    "settings.gradle",       # revela módulos em projetos Gradle multi-módulo
    "pom.xml",
    "go.mod",
    "Dockerfile",
    "docker-compose.yml",
    ".gitlab-ci.yml",        # revela tecnologia de build/deploy do pipeline
]

# Mesmo padrão do github_client.py — genérico por domínio, não por nome
# de biblioteca, para escalar entre linguagens/ecossistemas diferentes.
PADRAO_DOMINIO_INTERNO = re.compile(r"https?://([a-zA-Z0-9.-]+\.sicredi\.net)")

MARCADORES_README_ESTRUTURADO = [
    "## objetivo",
    "## responsáveis",
    "## responsaveis",
    "## build",
    "linktitle:",
    "geekdoccollapsesection",
]

TIMEOUT_SEGUNDOS = 15


def extrair_project_path(url: str) -> str:
    """
    Extrai o caminho do projeto (namespace/repo) a partir de uma URL do GitLab.
    """
    settings = get_settings()
    base_url_limpa = settings.gitlab_base_url.rstrip("/")

    padrao = rf"{re.escape(base_url_limpa)}/(.+?)(?:/blob/.*|/-/.*|\.git)?$"
    match = re.search(padrao, url)

    if not match:
        raise ValueError(f"URL do GitLab inválida ou não reconhecida: {url}")

    return match.group(1)


def _detectar_registros_internos(readme: str | None, manifestos: dict[str, str]) -> list[str]:
    """Mesma lógica do github_client.py — ver docstring lá."""
    texto_completo = (readme or "") + "\n" + "\n".join(manifestos.values())
    encontrados = PADRAO_DOMINIO_INTERNO.findall(texto_completo)
    return sorted(set(encontrados))


def _detectar_modulos(manifestos: dict[str, str]) -> list[str]:
    """Mesma lógica do github_client.py — ver docstring lá."""
    settings_gradle = manifestos.get("settings.gradle", "")
    if not settings_gradle:
        return []

    modulos = re.findall(r"include\s+['\"]([^'\"]+)['\"]", settings_gradle)
    return modulos


def _detectar_readme_estruturado(readme: str | None) -> bool:
    """Mesma lógica do github_client.py — ver docstring lá."""
    if not readme:
        return False

    readme_lower = readme.lower()
    encontrados = sum(1 for marcador in MARCADORES_README_ESTRUTURADO if marcador in readme_lower)
    return encontrados >= 2


def buscar_repositorio(url: str) -> dict:
    """
    Busca as informações necessárias de um repositório GitLab, incluindo
    os sinais determinísticos de padrão corporativo (Fase 7 — incremento).

    Mesma estrutura de retorno do github_client.buscar_repositorio().

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
        # 'created_at' vem no formato ISO 8601, mesmo padrão do GitHub
        repositorio_criado_em = dados_repo.get("created_at")

        logger.info(
            "[gitlab_client] ✓ Metadados obtidos — branch: '%s' | criado em: '%s'",
            default_branch,
            repositorio_criado_em,
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

    # --- 5. Sinais determinísticos (Fase 7 — incremento) ---
    registros_internos = _detectar_registros_internos(readme_content, manifestos)
    modulos = _detectar_modulos(manifestos)
    readme_estruturado = _detectar_readme_estruturado(readme_content)

    if registros_internos:
        logger.info(
            "[gitlab_client] ✓ Domínios internos detectados: %s", registros_internos
        )
    if modulos:
        logger.info(
            "[gitlab_client] ✓ Projeto multi-módulo detectado: %s", modulos
        )
    if readme_estruturado:
        logger.info(
            "[gitlab_client] ✓ README segue template estruturado conhecido"
        )

    return {
        "repository_url": url,
        "owner": owner or project_path,
        "repo_name": repo_name or project_path,
        "event_id": project_path,
        "linguagem_principal": None,
        "descricao": descricao,
        "default_branch": default_branch,
        "repositorio_criado_em": repositorio_criado_em,
        "readme_content": readme_content,
        "arquivos": arquivos,
        "manifestos": manifestos,
        # --- Sinais determinísticos, usados como pistas pelos prompts ---
        "registros_internos_detectados": registros_internos,
        "modulos_detectados": modulos,
        "multi_modulo_detectado": len(modulos) > 1,
        "readme_estruturado_detectado": readme_estruturado,
    }