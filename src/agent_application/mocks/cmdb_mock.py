"""
Mock do CMDB — Simula o catálogo de componentes de TI do Sicredi.

O CMDB real é responsável por:
- Armazenar informações de todos os componentes de TI (APIs, serviços, bancos)
- Registrar dependências entre componentes
- Manter histórico de versões e responsáveis
- Informar o status de saúde de cada componente

Neste mock, simulamos um catálogo com componentes fictícios mas
com estrutura idêntica ao que o CMDB real retornaria.
"""

from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# BASE DE DADOS SIMULADA DO CMDB
# Cada componente representa um serviço/API
# que existe no ambiente Sicredi
# ─────────────────────────────────────────────
COMPONENTES_MOCK = {
    "COMP-001": {
        "id": "COMP-001",
        "nome": "atlas-chat-rag",
        "tipo": "microsservico",
        "descricao": "Serviço principal de chat com RAG para consulta de documentação",
        "versao": "1.2.0",
        "linguagem": "Python",
        "framework": "LangGraph + FastAPI",
        "status": "ativo",
        "ambiente": ["desenvolvimento", "homologacao", "producao"],
        "responsavel": {
            "time": "Engenharia de IA",
            "email": "time-ia@sicredi.com.br",
        },
        "repositorio": "https://gitlab.sicredi.net/atlas/atlas-chat-rag",
        "dependencias": ["COMP-002", "COMP-003", "COMP-005"],
        "banco_dados": ["PostgreSQL", "MongoDB"],
        "criado_em": "2026-01-15",
        "atualizado_em": "2026-08-01",
    },
    "COMP-002": {
        "id": "COMP-002",
        "nome": "atlas-agente-classificador",
        "tipo": "microsservico",
        "descricao": "Agente especialista em classificação e pré-curadoria de conteúdo",
        "versao": "0.9.1",
        "linguagem": "Python",
        "framework": "LangGraph",
        "status": "ativo",
        "ambiente": ["desenvolvimento", "homologacao"],
        "responsavel": {
            "time": "Engenharia de IA",
            "email": "time-ia@sicredi.com.br",
        },
        "repositorio": "https://gitlab.sicredi.net/atlas/atlas-agente-classificador",
        "dependencias": ["COMP-003"],
        "banco_dados": ["MongoDB"],
        "criado_em": "2026-02-10",
        "atualizado_em": "2026-07-20",
    },
    "COMP-003": {
        "id": "COMP-003",
        "nome": "atlas-agente-catalogo",
        "tipo": "microsservico",
        "descricao": "Agente especialista em documentação e catálogo de componentes",
        "versao": "1.0.0",
        "linguagem": "Python",
        "framework": "LangGraph",
        "status": "ativo",
        "ambiente": ["desenvolvimento", "homologacao", "producao"],
        "responsavel": {
            "time": "Engenharia de IA",
            "email": "time-ia@sicredi.com.br",
        },
        "repositorio": "https://gitlab.sicredi.net/atlas/atlas-agente-catalogo",
        "dependencias": ["COMP-004"],
        "banco_dados": ["MongoDB"],
        "criado_em": "2026-02-20",
        "atualizado_em": "2026-08-05",
    },
    "COMP-004": {
        "id": "COMP-004",
        "nome": "atlas-inventario-ingestao",
        "tipo": "backend",
        "descricao": "Backend de ingestão, enriquecimento e normalização de dados de APIs",
        "versao": "0.8.3",
        "linguagem": "Python",
        "framework": "FastAPI",
        "status": "em_manutencao",
        "ambiente": ["desenvolvimento"],
        "responsavel": {
            "time": "Engenharia de Dados",
            "email": "time-dados@sicredi.com.br",
        },
        "repositorio": "https://gitlab.sicredi.net/atlas/atlas-inventario-ingestao",
        "dependencias": ["COMP-005"],
        "banco_dados": ["PostgreSQL"],
        "criado_em": "2026-03-01",
        "atualizado_em": "2026-08-10",
    },
    "COMP-005": {
        "id": "COMP-005",
        "nome": "atlas-vetorizacao",
        "tipo": "backend",
        "descricao": "Backend de vetorização e replicação de documentos aprovados",
        "versao": "0.5.0",
        "linguagem": "Python",
        "framework": "FastAPI",
        "status": "ativo",
        "ambiente": ["desenvolvimento", "homologacao"],
        "responsavel": {
            "time": "Engenharia de IA",
            "email": "time-ia@sicredi.com.br",
        },
        "repositorio": "https://gitlab.sicredi.net/atlas/atlas-vetorizacao",
        "dependencias": [],
        "banco_dados": ["PostgreSQL"],
        "criado_em": "2026-04-05",
        "atualizado_em": "2026-08-12",
    },
}


# ─────────────────────────────────────────────
# FUNÇÕES DE CONSULTA AO CMDB
# ─────────────────────────────────────────────

def buscar_componente_por_id(componente_id: str) -> dict:
    """
    Busca um componente pelo seu ID único no CMDB.

    Exemplo de uso:
        resultado = buscar_componente_por_id("COMP-001")
    """
    componente = COMPONENTES_MOCK.get(componente_id)

    if not componente:
        return {
            "encontrado": False,
            "erro": f"Componente '{componente_id}' não encontrado no CMDB",
        }

    return {
        "encontrado": True,
        "componente": componente,
    }


def buscar_componente_por_nome(nome: str) -> dict:
    """
    Busca componentes pelo nome (busca parcial, sem diferenciar maiúsculas).

    Exemplo de uso:
        resultado = buscar_componente_por_nome("atlas")
        # Retorna todos os componentes que têm "atlas" no nome
    """
    nome_lower = nome.lower()
    encontrados = [
        comp for comp in COMPONENTES_MOCK.values()
        if nome_lower in comp["nome"].lower()
        or nome_lower in comp["descricao"].lower()
    ]

    return {
        "total": len(encontrados),
        "componentes": encontrados,
    }


def listar_todos_componentes(status: Optional[str] = None) -> dict:
    """
    Lista todos os componentes do CMDB.
    Se passar um status (ativo, em_manutencao), filtra por ele.

    Exemplo de uso:
        todos = listar_todos_componentes()
        apenas_ativos = listar_todos_componentes(status="ativo")
    """
    componentes = list(COMPONENTES_MOCK.values())

    if status:
        componentes = [c for c in componentes if c["status"] == status]

    return {
        "total": len(componentes),
        "filtro_status": status or "todos",
        "componentes": componentes,
    }


def buscar_dependencias(componente_id: str) -> dict:
    """
    Retorna todos os componentes dos quais um componente depende.

    Útil para entender o impacto de uma mudança:
    "Se o COMP-001 parar, quais outros serviços serão afetados?"

    Exemplo de uso:
        deps = buscar_dependencias("COMP-001")
    """
    componente = COMPONENTES_MOCK.get(componente_id)

    if not componente:
        return {
            "encontrado": False,
            "erro": f"Componente '{componente_id}' não encontrado",
        }

    dependencias_detalhadas = []
    for dep_id in componente["dependencias"]:
        dep = COMPONENTES_MOCK.get(dep_id)
        if dep:
            dependencias_detalhadas.append({
                "id": dep["id"],
                "nome": dep["nome"],
                "status": dep["status"],
                "versao": dep["versao"],
            })

    return {
        "componente_id": componente_id,
        "componente_nome": componente["nome"],
        "total_dependencias": len(dependencias_detalhadas),
        "dependencias": dependencias_detalhadas,
    }


def registrar_componente(dados: dict) -> dict:
    """
    Simula o registro de um novo componente no CMDB.

    No CMDB real: faria uma chamada HTTP POST para cadastrar.
    No mock: apenas valida os campos e confirma o registro simulado.

    Campos obrigatórios: nome, tipo, descricao, linguagem, responsavel
    """
    campos_obrigatorios = ["nome", "tipo", "descricao", "linguagem", "responsavel"]
    campos_faltando = [c for c in campos_obrigatorios if c not in dados]

    if campos_faltando:
        return {
            "sucesso": False,
            "erro": f"Campos obrigatórios faltando: {', '.join(campos_faltando)}",
        }

    # Gera um ID simulado para o novo componente
    novo_id = f"COMP-{str(len(COMPONENTES_MOCK) + 1).zfill(3)}"

    novo_componente = {
        "id": novo_id,
        "status": "ativo",
        "criado_em": datetime.now().strftime("%Y-%m-%d"),
        "atualizado_em": datetime.now().strftime("%Y-%m-%d"),
        **dados,
    }

    # Adiciona na base mock (só dura enquanto o servidor estiver rodando)
    COMPONENTES_MOCK[novo_id] = novo_componente

    return {
        "sucesso": True,
        "mensagem": f"Componente registrado com sucesso no CMDB",
        "id_gerado": novo_id,
        "componente": novo_componente,
    }