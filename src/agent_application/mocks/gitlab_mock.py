"""
Mock do GitLab — Simula o repositório de código do Sicredi.

O GitLab real é responsável por:
- Armazenar o código fonte de todos os projetos
- Controlar branches, commits e merge requests
- Executar pipelines de CI/CD (build, test, deploy)
- Registrar quem alterou o quê e quando

Neste mock, simulamos repositórios fictícios dos mesmos
5 serviços Python da nossa arquitetura.
"""

from datetime import datetime, timedelta
from typing import Optional
import random

# ─────────────────────────────────────────────
# BASE DE REPOSITÓRIOS SIMULADOS
# ─────────────────────────────────────────────
REPOSITORIOS_MOCK = {
    "atlas-chat-rag": {
        "id": 1001,
        "nome": "atlas-chat-rag",
        "namespace": "atlas",
        "descricao": "Serviço principal de chat com RAG",
        "url": "https://gitlab.sicredi.net/atlas/atlas-chat-rag",
        "branch_padrao": "main",
        "branches": ["main", "develop", "feature/langgraph-v2", "hotfix/memory-leak"],
        "linguagem_principal": "Python",
        "visibilidade": "interno",
        "ultimo_commit": {
            "id": "76b5c327",
            "mensagem": "feat: adiciona suporte a múltiplos agentes",
            "autor": "Ricardo Ribeiro",
            "email": "ricardo@sicredi.com.br",
            "data": "2026-08-18T14:30:00",
        },
        "pipeline": {
            "status": "passed",
            "duracao_segundos": 142,
            "etapas": ["lint", "test", "build", "deploy-dev"],
        },
        "stats": {
            "total_commits": 87,
            "total_branches": 4,
            "contribuidores": 3,
            "issues_abertos": 2,
            "merge_requests_abertos": 1,
        },
    },
    "atlas-agente-classificador": {
        "id": 1002,
        "nome": "atlas-agente-classificador",
        "namespace": "atlas",
        "descricao": "Agente de classificação e pré-curadoria com LangGraph",
        "url": "https://gitlab.sicredi.net/atlas/atlas-agente-classificador",
        "branch_padrao": "main",
        "branches": ["main", "develop", "feature/novo-classificador"],
        "linguagem_principal": "Python",
        "visibilidade": "interno",
        "ultimo_commit": {
            "id": "a3f91b02",
            "mensagem": "fix: corrige classificação de componentes legados",
            "autor": "Programador B",
            "email": "prog_b@sicredi.com.br",
            "data": "2026-08-17T09:15:00",
        },
        "pipeline": {
            "status": "passed",
            "duracao_segundos": 98,
            "etapas": ["lint", "test", "build"],
        },
        "stats": {
            "total_commits": 43,
            "total_branches": 3,
            "contribuidores": 2,
            "issues_abertos": 5,
            "merge_requests_abertos": 2,
        },
    },
    "atlas-agente-catalogo": {
        "id": 1003,
        "nome": "atlas-agente-catalogo",
        "namespace": "atlas",
        "descricao": "Agente especialista em documentação e catálogo",
        "url": "https://gitlab.sicredi.net/atlas/atlas-agente-catalogo",
        "branch_padrao": "main",
        "branches": ["main", "develop"],
        "linguagem_principal": "Python",
        "visibilidade": "interno",
        "ultimo_commit": {
            "id": "c7d84e11",
            "mensagem": "feat: integra busca semântica no catálogo",
            "autor": "Ricardo Ribeiro",
            "email": "ricardo@sicredi.com.br",
            "data": "2026-08-19T16:45:00",
        },
        "pipeline": {
            "status": "running",
            "duracao_segundos": 67,
            "etapas": ["lint", "test", "build", "deploy-dev"],
        },
        "stats": {
            "total_commits": 29,
            "total_branches": 2,
            "contribuidores": 2,
            "issues_abertos": 1,
            "merge_requests_abertos": 0,
        },
    },
    "atlas-inventario-ingestao": {
        "id": 1004,
        "nome": "atlas-inventario-ingestao",
        "namespace": "atlas",
        "descricao": "Backend de ingestão e normalização de dados",
        "url": "https://gitlab.sicredi.net/atlas/atlas-inventario-ingestao",
        "branch_padrao": "main",
        "branches": ["main", "develop", "feature/novo-conector-kafka"],
        "linguagem_principal": "Python",
        "visibilidade": "interno",
        "ultimo_commit": {
            "id": "e2a15f88",
            "mensagem": "chore: atualiza dependências do poetry",
            "autor": "Programador B",
            "email": "prog_b@sicredi.com.br",
            "data": "2026-08-15T11:00:00",
        },
        "pipeline": {
            "status": "failed",
            "duracao_segundos": 55,
            "etapas": ["lint", "test"],
        },
        "stats": {
            "total_commits": 61,
            "total_branches": 3,
            "contribuidores": 4,
            "issues_abertos": 8,
            "merge_requests_abertos": 3,
        },
    },
    "atlas-vetorizacao": {
        "id": 1005,
        "nome": "atlas-vetorizacao",
        "namespace": "atlas",
        "descricao": "Backend de vetorização e replicação de documentos",
        "url": "https://gitlab.sicredi.net/atlas/atlas-vetorizacao",
        "branch_padrao": "main",
        "branches": ["main", "develop", "feature/pgvector-integration"],
        "linguagem_principal": "Python",
        "visibilidade": "interno",
        "ultimo_commit": {
            "id": "b9c32d44",
            "mensagem": "feat: implementa PGVector para embeddings",
            "autor": "Ricardo Ribeiro",
            "email": "ricardo@sicredi.com.br",
            "data": "2026-08-20T08:30:00",
        },
        "pipeline": {
            "status": "passed",
            "duracao_segundos": 113,
            "etapas": ["lint", "test", "build"],
        },
        "stats": {
            "total_commits": 18,
            "total_branches": 3,
            "contribuidores": 2,
            "issues_abertos": 3,
            "merge_requests_abertos": 1,
        },
    },
}

# ─────────────────────────────────────────────
# HISTÓRICO DE COMMITS SIMULADO
# ─────────────────────────────────────────────
def _gerar_commits_simulados(repo_nome: str, quantidade: int = 5) -> list:
    """Gera uma lista de commits simulados para um repositório."""
    autores = ["Ricardo Ribeiro", "Programador B", "Time Atlas"]
    prefixos = ["feat:", "fix:", "chore:", "docs:", "refactor:", "test:"]
    acoes = [
        "adiciona novo agente",
        "corrige bug no classificador",
        "atualiza dependências",
        "melhora documentação",
        "refatora conexão com banco",
        "adiciona testes unitários",
        "implementa nova tool",
        "ajusta prompt do agente",
    ]

    commits = []
    for i in range(quantidade):
        dias_atras = i * random.randint(1, 3)
        data = datetime.now() - timedelta(days=dias_atras)
        commits.append({
            "id": f"{random.randint(10000000, 99999999):08x}",
            "mensagem": f"{random.choice(prefixos)} {random.choice(acoes)}",
            "autor": random.choice(autores),
            "data": data.strftime("%Y-%m-%dT%H:%M:%S"),
            "branch": "main",
        })

    return commits


# ─────────────────────────────────────────────
# FUNÇÕES DE CONSULTA AO GITLAB
# ─────────────────────────────────────────────

def buscar_repositorio(nome_repo: str) -> dict:
    """
    Busca um repositório pelo nome exato.

    Exemplo de uso:
        repo = buscar_repositorio("atlas-chat-rag")
    """
    repo = REPOSITORIOS_MOCK.get(nome_repo)

    if not repo:
        return {
            "encontrado": False,
            "erro": f"Repositório '{nome_repo}' não encontrado no GitLab",
        }

    return {
        "encontrado": True,
        "repositorio": repo,
    }


def listar_repositorios(namespace: Optional[str] = "atlas") -> dict:
    """
    Lista todos os repositórios de um namespace (grupo).

    Exemplo de uso:
        repos = listar_repositorios(namespace="atlas")
    """
    repos = [
        r for r in REPOSITORIOS_MOCK.values()
        if r["namespace"] == namespace
    ]

    return {
        "namespace": namespace,
        "total": len(repos),
        "repositorios": [
            {
                "id": r["id"],
                "nome": r["nome"],
                "descricao": r["descricao"],
                "pipeline_status": r["pipeline"]["status"],
                "ultimo_commit_data": r["ultimo_commit"]["data"],
            }
            for r in repos
        ],
    }


def buscar_status_pipeline(nome_repo: str) -> dict:
    """
    Retorna o status do pipeline de CI/CD de um repositório.

    Status possíveis: passed, failed, running, pending

    Exemplo de uso:
        status = buscar_status_pipeline("atlas-chat-rag")
    """
    repo = REPOSITORIOS_MOCK.get(nome_repo)

    if not repo:
        return {
            "encontrado": False,
            "erro": f"Repositório '{nome_repo}' não encontrado",
        }

    pipeline = repo["pipeline"]
    status_emoji = {
        "passed": "✅",
        "failed": "❌",
        "running": "🔄",
        "pending": "⏳",
    }

    return {
        "repositorio": nome_repo,
        "pipeline": {
            **pipeline,
            "icone": status_emoji.get(pipeline["status"], "❓"),
        },
    }


def buscar_commits_recentes(nome_repo: str, quantidade: int = 5) -> dict:
    """
    Retorna os commits mais recentes de um repositório.

    Exemplo de uso:
        commits = buscar_commits_recentes("atlas-chat-rag", quantidade=3)
    """
    repo = REPOSITORIOS_MOCK.get(nome_repo)

    if not repo:
        return {
            "encontrado": False,
            "erro": f"Repositório '{nome_repo}' não encontrado",
        }

    commits = [repo["ultimo_commit"]] + _gerar_commits_simulados(
        nome_repo, quantidade - 1
    )

    return {
        "repositorio": nome_repo,
        "branch": repo["branch_padrao"],
        "total_retornado": len(commits),
        "commits": commits,
    }


def buscar_branches(nome_repo: str) -> dict:
    """
    Lista todas as branches de um repositório.

    Exemplo de uso:
        branches = buscar_branches("atlas-agente-classificador")
    """
    repo = REPOSITORIOS_MOCK.get(nome_repo)

    if not repo:
        return {
            "encontrado": False,
            "erro": f"Repositório '{nome_repo}' não encontrado",
        }

    return {
        "repositorio": nome_repo,
        "branch_padrao": repo["branch_padrao"],
        "total_branches": len(repo["branches"]),
        "branches": repo["branches"],
    }