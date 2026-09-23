"""
infrastructure/repository/github_client.py
----------------------------------------------
Cliente de busca de repositórios via API REST do GitHub.

Incremento na Fase 7: além dos dados básicos (README, árvore, manifestos),
este cliente agora detecta sinais determinísticos que ajudam a LLM a
julgar melhor o checklist técnico e a documentação, sem precisar
adivinhar — a detecção aqui é barata (regex) e serve de "pista" para
os prompts, não substitui o julgamento semântico da LLM.

Sinais novos detectados:
  - registros_internos_detectados: domínios internos (*.sicredi.net)
    encontrados em manifestos ou README — evidência forte de uso de
    infraestrutura corporativa, agnóstica de linguagem/ecossistema
  - modulos_detectados / multi_modulo_detectado: baseado em
    'include' no settings.gradle — sinaliza projeto multi-módulo
  - readme_estruturado_detectado: se o README segue um template
    corporativo conhecido (seções nomeadas tipo ## Objetivo,
    ## Responsáveis, ## Build) — quando true, a LLM deve preferir
    extrair diretamente essas seções em vez de resumir livremente
  - repositorio_criado_em: data de criação do repositório — dá
    contexto temporal para julgar maturidade e nível de documentação
    (um projeto de 2 anos com documentação básica é diferente de um
    projeto de 2 semanas no mesmo estado)

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

# Domínios internos — o padrão é genérico (qualquer subdomínio de
# sicredi.net), não uma lista de nomes de biblioteca. Isso escala para
# qualquer linguagem/ecossistema sem precisar de regra nova por caso.
PADRAO_DOMINIO_INTERNO = re.compile(r"https?://([a-zA-Z0-9.-]+\.sicredi\.net)")

# Marcadores que indicam um README seguindo template corporativo
# conhecido (ex: GeekDocs/Hugo usado em alguns repositórios Sicredi)
MARCADORES_README_ESTRUTURADO = [
    "## objetivo",
    "## responsáveis",
    "## responsaveis",
    "## build",
    "linktitle:",
    "geekdoccollapsesection",
]

TIMEOUT_SEGUNDOS = 15


def extrair_owner_repo(url: str) -> tuple[str, str]:
    """
    Extrai owner e nome do repositório a partir de uma URL do GitHub.
    """
    padrao = r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)"
    match = re.search(padrao, url)

    if not match:
        raise ValueError(f"URL do GitHub inválida ou não reconhecida: {url}")

    owner, repo = match.group(1), match.group(2)
    return owner, repo


def _detectar_registros_internos(readme: str | None, manifestos: dict[str, str]) -> list[str]:
    """
    Procura por domínios internos (*.sicredi.net) em qualquer conteúdo
    coletado. Detecção por padrão, não por nome de biblioteca — funciona
    igual para Java, Python, Node, Go, etc.

    Returns:
        Lista de domínios únicos encontrados (vazia se nenhum)
    """
    texto_completo = (readme or "") + "\n" + "\n".join(manifestos.values())
    encontrados = PADRAO_DOMINIO_INTERNO.findall(texto_completo)
    return sorted(set(encontrados))


def _detectar_modulos(manifestos: dict[str, str]) -> list[str]:
    """
    Procura por declarações 'include' no settings.gradle — cada include
    é um módulo de um projeto Gradle multi-módulo.

    Returns:
        Lista de nomes de módulos encontrados (vazia se não for multi-módulo
        ou não usar Gradle)
    """
    settings_gradle = manifestos.get("settings.gradle", "")
    if not settings_gradle:
        return []

    modulos = re.findall(r"include\s+['\"]([^'\"]+)['\"]", settings_gradle)
    return modulos


def _detectar_readme_estruturado(readme: str | None) -> bool:
    """
    Verifica se o README segue um template corporativo conhecido,
    contando quantos marcadores esperados aparecem.

    Returns:
        True se pelo menos 2 marcadores forem encontrados
    """
    if not readme:
        return False

    readme_lower = readme.lower()
    encontrados = sum(1 for marcador in MARCADORES_README_ESTRUTURADO if marcador in readme_lower)
    return encontrados >= 2


def buscar_repositorio(url: str) -> dict:
    """
    Busca as informações necessárias de um repositório GitHub, incluindo
    os sinais determinísticos de padrão corporativo (Fase 7 — incremento).

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
        # 'created_at' vem no formato ISO 8601 (ex: "2023-05-14T10:32:00Z")
        repositorio_criado_em = dados_repo.get("created_at")

        logger.info(
            "[github_client] ✓ Metadados obtidos — linguagem: '%s' | branch: '%s' | criado em: '%s'",
            linguagem,
            default_branch,
            repositorio_criado_em,
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

    # --- 5. Sinais determinísticos (Fase 7 — incremento) ---
    registros_internos = _detectar_registros_internos(readme_content, manifestos)
    modulos = _detectar_modulos(manifestos)
    readme_estruturado = _detectar_readme_estruturado(readme_content)

    if registros_internos:
        logger.info(
            "[github_client] ✓ Domínios internos detectados: %s", registros_internos
        )
    if modulos:
        logger.info(
            "[github_client] ✓ Projeto multi-módulo detectado: %s", modulos
        )
    if readme_estruturado:
        logger.info(
            "[github_client] ✓ README segue template estruturado conhecido"
        )

    return {
        "repository_url": url,
        "owner": owner,
        "repo_name": repo_name,
        "event_id": f"{owner}/{repo_name}",
        "linguagem_principal": linguagem,
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