"""
Mock do Jira — Simula o sistema de gestão de tarefas do Sicredi.

O Jira real é responsável por:
- Criar cards de trabalho (bugs, melhorias, tarefas, épicos)
- Acompanhar o progresso de cada card (To Do, Em andamento, Done)
- Associar cards a times, sprints e projetos
- Registrar comentários e histórico de alterações

Neste mock, simulamos a criação e consulta de cards
com a mesma estrutura que o Jira real retornaria.
"""

from datetime import datetime, timedelta
from typing import Optional
import random

# ─────────────────────────────────────────────
# CONFIGURAÇÕES DOS PROJETOS JIRA SIMULADOS
# ─────────────────────────────────────────────
PROJETOS_MOCK = {
    "ATLAS": {
        "key": "ATLAS",
        "nome": "Atlas - Plataforma de IA",
        "descricao": "Projeto principal da plataforma Atlas",
        "time": "Engenharia de IA",
        "lead": "Ricardo Ribeiro",
    },
    "DADOS": {
        "key": "DADOS",
        "nome": "Atlas - Engenharia de Dados",
        "descricao": "Projeto de ingestão e processamento de dados",
        "time": "Engenharia de Dados",
        "lead": "Programador B",
    },
}

# ─────────────────────────────────────────────
# TIPOS E STATUS DISPONÍVEIS
# ─────────────────────────────────────────────
TIPOS_CARD = ["Bug", "Melhoria", "Tarefa", "Épico", "História"]

STATUS_POSSIVEIS = {
    "todo": "A Fazer",
    "in_progress": "Em Andamento",
    "in_review": "Em Revisão",
    "done": "Concluído",
    "blocked": "Bloqueado",
}

PRIORIDADES = ["Crítica", "Alta", "Média", "Baixa"]

# ─────────────────────────────────────────────
# BASE DE CARDS SIMULADOS (já existentes)
# ─────────────────────────────────────────────
CARDS_MOCK = {
    "ATLAS-101": {
        "id": "ATLAS-101",
        "projeto": "ATLAS",
        "titulo": "Implementar agente classificador com LangGraph",
        "descricao": "Criar o agente especialista em classificação usando LangGraph com suporte a múltiplas intenções.",
        "tipo": "Tarefa",
        "status": "in_progress",
        "prioridade": "Alta",
        "responsavel": "Ricardo Ribeiro",
        "reporter": "Ricardo Ribeiro",
        "sprint": "Sprint 3",
        "story_points": 8,
        "tags": ["langraph", "agente", "classificador"],
        "criado_em": "2026-08-01T09:00:00",
        "atualizado_em": "2026-08-18T14:00:00",
        "comentarios": [
            {
                "autor": "Programador B",
                "texto": "Já integrei a conexão com o MongoDB para persistência.",
                "data": "2026-08-15T10:30:00",
            }
        ],
    },
    "ATLAS-102": {
        "id": "ATLAS-102",
        "projeto": "ATLAS",
        "titulo": "Configurar base vetorial PGVector no PostgreSQL",
        "descricao": "Habilitar extensão PGVector e criar tabelas de embeddings para o serviço de vetorização.",
        "tipo": "Tarefa",
        "status": "todo",
        "prioridade": "Alta",
        "responsavel": "Programador B",
        "reporter": "Ricardo Ribeiro",
        "sprint": "Sprint 3",
        "story_points": 5,
        "tags": ["pgvector", "postgresql", "embeddings"],
        "criado_em": "2026-08-05T11:00:00",
        "atualizado_em": "2026-08-05T11:00:00",
        "comentarios": [],
    },
    "ATLAS-103": {
        "id": "ATLAS-103",
        "projeto": "ATLAS",
        "titulo": "Bug: pipeline do atlas-inventario-ingestao falhando",
        "descricao": "O pipeline de CI/CD está falhando na etapa de testes. Erro relacionado à versão do asyncpg.",
        "tipo": "Bug",
        "status": "blocked",
        "prioridade": "Crítica",
        "responsavel": "Programador B",
        "reporter": "Ricardo Ribeiro",
        "sprint": "Sprint 3",
        "story_points": 3,
        "tags": ["bug", "ci-cd", "asyncpg"],
        "criado_em": "2026-08-19T08:00:00",
        "atualizado_em": "2026-08-20T09:00:00",
        "comentarios": [
            {
                "autor": "Ricardo Ribeiro",
                "texto": "Identificado: incompatibilidade do asyncpg com Python 3.14. Solução: usar psycopg2-binary.",
                "data": "2026-08-20T09:00:00",
            }
        ],
    },
    "DADOS-201": {
        "id": "DADOS-201",
        "projeto": "DADOS",
        "titulo": "Criar pipeline de ingestão de APIs do CMDB",
        "descricao": "Desenvolver o conector que busca dados do CMDB e normaliza para o formato padrão Atlas.",
        "tipo": "História",
        "status": "in_review",
        "prioridade": "Média",
        "responsavel": "Programador B",
        "reporter": "Programador B",
        "sprint": "Sprint 2",
        "story_points": 13,
        "tags": ["ingestao", "cmdb", "pipeline"],
        "criado_em": "2026-07-20T10:00:00",
        "atualizado_em": "2026-08-17T16:00:00",
        "comentarios": [],
    },
}


# ─────────────────────────────────────────────
# FUNÇÕES DE CONSULTA E CRIAÇÃO DE CARDS
# ─────────────────────────────────────────────

def buscar_card(card_id: str) -> dict:
    """
    Busca um card pelo ID.

    Exemplo de uso:
        card = buscar_card("ATLAS-101")
    """
    card = CARDS_MOCK.get(card_id)

    if not card:
        return {
            "encontrado": False,
            "erro": f"Card '{card_id}' não encontrado no Jira",
        }

    # Enriquece com o label de status legível
    card_enriquecido = {
        **card,
        "status_label": STATUS_POSSIVEIS.get(card["status"], card["status"]),
    }

    return {
        "encontrado": True,
        "card": card_enriquecido,
    }


def listar_cards_projeto(
    projeto_key: str,
    status: Optional[str] = None,
    responsavel: Optional[str] = None,
) -> dict:
    """
    Lista cards de um projeto com filtros opcionais.

    Exemplo de uso:
        # Todos os cards do ATLAS
        cards = listar_cards_projeto("ATLAS")

        # Só os bloqueados
        cards = listar_cards_projeto("ATLAS", status="blocked")

        # Só os do Programador B
        cards = listar_cards_projeto("ATLAS", responsavel="Programador B")
    """
    projeto = PROJETOS_MOCK.get(projeto_key)
    if not projeto:
        return {
            "encontrado": False,
            "erro": f"Projeto '{projeto_key}' não encontrado",
        }

    cards = [
        c for c in CARDS_MOCK.values()
        if c["projeto"] == projeto_key
    ]

    if status:
        cards = [c for c in cards if c["status"] == status]

    if responsavel:
        cards = [
            c for c in cards
            if responsavel.lower() in c["responsavel"].lower()
        ]

    return {
        "projeto": projeto_key,
        "filtros": {"status": status, "responsavel": responsavel},
        "total": len(cards),
        "cards": [
            {
                "id": c["id"],
                "titulo": c["titulo"],
                "tipo": c["tipo"],
                "status": STATUS_POSSIVEIS.get(c["status"], c["status"]),
                "prioridade": c["prioridade"],
                "responsavel": c["responsavel"],
                "story_points": c["story_points"],
            }
            for c in cards
        ],
    }


def criar_card(dados: dict) -> dict:
    """
    Simula a criação de um novo card no Jira.

    Campos obrigatórios:
        - projeto     : chave do projeto ("ATLAS" ou "DADOS")
        - titulo      : título do card
        - tipo        : "Bug", "Melhoria", "Tarefa", "História", "Épico"
        - descricao   : descrição detalhada
        - responsavel : nome do responsável
        - prioridade  : "Crítica", "Alta", "Média", "Baixa"

    Exemplo de uso:
        novo = criar_card({
            "projeto": "ATLAS",
            "titulo": "Implementar mock do WSO2",
            "tipo": "Tarefa",
            "descricao": "Criar o mock de autenticação WSO2",
            "responsavel": "Ricardo Ribeiro",
            "prioridade": "Alta",
        })
    """
    # Validação dos campos obrigatórios
    campos_obrigatorios = [
        "projeto", "titulo", "tipo", "descricao", "responsavel", "prioridade"
    ]
    campos_faltando = [c for c in campos_obrigatorios if not dados.get(c)]

    if campos_faltando:
        return {
            "sucesso": False,
            "erro": f"Campos obrigatórios faltando: {', '.join(campos_faltando)}",
        }

    # Valida projeto
    if dados["projeto"] not in PROJETOS_MOCK:
        return {
            "sucesso": False,
            "erro": f"Projeto '{dados['projeto']}' não existe. Use: {list(PROJETOS_MOCK.keys())}",
        }

    # Valida tipo
    if dados["tipo"] not in TIPOS_CARD:
        return {
            "sucesso": False,
            "erro": f"Tipo inválido. Use um de: {TIPOS_CARD}",
        }

    # Valida prioridade
    if dados["prioridade"] not in PRIORIDADES:
        return {
            "sucesso": False,
            "erro": f"Prioridade inválida. Use uma de: {PRIORIDADES}",
        }

    # Gera o ID do novo card
    projeto_key = dados["projeto"]
    cards_do_projeto = [
        c for c in CARDS_MOCK.values()
        if c["projeto"] == projeto_key
    ]
    proximo_numero = 100 + len(cards_do_projeto) + 1
    novo_id = f"{projeto_key}-{proximo_numero}"

    # Monta o card completo
    agora = datetime.now().isoformat()
    novo_card = {
        "id": novo_id,
        "projeto": projeto_key,
        "titulo": dados["titulo"],
        "descricao": dados["descricao"],
        "tipo": dados["tipo"],
        "status": "todo",
        "status_label": STATUS_POSSIVEIS["todo"],
        "prioridade": dados["prioridade"],
        "responsavel": dados["responsavel"],
        "reporter": dados.get("reporter", dados["responsavel"]),
        "sprint": dados.get("sprint", "Backlog"),
        "story_points": dados.get("story_points", 0),
        "tags": dados.get("tags", []),
        "criado_em": agora,
        "atualizado_em": agora,
        "comentarios": [],
    }

    # Salva na base mock
    CARDS_MOCK[novo_id] = novo_card

    return {
        "sucesso": True,
        "mensagem": "Card criado com sucesso no Jira",
        "card_id": novo_id,
        "url_card": f"https://jira.sicredi.com.br/browse/{novo_id}",
        "card": novo_card,
    }


def adicionar_comentario(card_id: str, autor: str, texto: str) -> dict:
    """
    Adiciona um comentário em um card existente.

    Exemplo de uso:
        resultado = adicionar_comentario(
            card_id="ATLAS-101",
            autor="Ricardo Ribeiro",
            texto="Implementação concluída, aguardando revisão.",
        )
    """
    card = CARDS_MOCK.get(card_id)

    if not card:
        return {
            "sucesso": False,
            "erro": f"Card '{card_id}' não encontrado",
        }

    comentario = {
        "autor": autor,
        "texto": texto,
        "data": datetime.now().isoformat(),
    }

    card["comentarios"].append(comentario)
    card["atualizado_em"] = datetime.now().isoformat()

    return {
        "sucesso": True,
        "mensagem": "Comentário adicionado com sucesso",
        "card_id": card_id,
        "comentario": comentario,
    }


def atualizar_status(card_id: str, novo_status: str) -> dict:
    """
    Atualiza o status de um card.

    Status válidos: todo, in_progress, in_review, done, blocked

    Exemplo de uso:
        resultado = atualizar_status("ATLAS-101", "done")
    """
    card = CARDS_MOCK.get(card_id)

    if not card:
        return {
            "sucesso": False,
            "erro": f"Card '{card_id}' não encontrado",
        }

    if novo_status not in STATUS_POSSIVEIS:
        return {
            "sucesso": False,
            "erro": f"Status inválido. Use um de: {list(STATUS_POSSIVEIS.keys())}",
        }

    status_anterior = card["status"]
    card["status"] = novo_status
    card["atualizado_em"] = datetime.now().isoformat()

    return {
        "sucesso": True,
        "mensagem": f"Status atualizado com sucesso",
        "card_id": card_id,
        "status_anterior": STATUS_POSSIVEIS[status_anterior],
        "status_atual": STATUS_POSSIVEIS[novo_status],
    }