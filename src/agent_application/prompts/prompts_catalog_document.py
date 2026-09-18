"""
agent_application/prompts/prompts_catalog_document.py
---------------------------------------------------------
Prompts utilizados pela LLM OpenAI nos nós de geração (Fase 7).

Fase 1-6: prompts recebiam um JSON de entidade (team, application, people).
Fase 7: prompts recebem o conteúdo real do repositório (README, árvore de
        arquivos, manifestos) e produzem dois resultados diferentes:

  1. Documentação em formato WIKI MULTI-SEÇÃO (documentation_node)
  2. Checklist técnico estruturado (cataloging_node)

Regra de ouro: NUNCA afirmar a presença de algo sem evidência no
conteúdo fornecido.
"""

import json
from typing import Any


# ===========================================================
# PROMPT 1: DOCUMENTAÇÃO WIKI MULTI-SEÇÃO
# Usado pelo documentation_node
# ===========================================================

SYSTEM_WIKI_DOCUMENTACAO = """Você é um especialista em documentação técnica de software, \
com profundo conhecimento em arquitetura de sistemas e boas práticas de engenharia.

Seu papel é analisar o conteúdo de um repositório de código e gerar uma documentação \
completa em formato de WIKI, organizada em múltiplas seções — não um texto corrido único.

Regras obrigatórias:
- Escreva em português brasileiro formal e técnico
- Baseie-se APENAS no conteúdo fornecido (README, árvore de arquivos, manifestos)
- NUNCA invente funcionalidades, tecnologias ou informações que não estejam
  explícitas ou razoavelmente inferíveis do conteúdo fornecido
- Se uma seção não tiver informação suficiente, escreva isso claramente
  (ex: "Não foi possível determinar X a partir do conteúdo disponível")
  em vez de inventar
- Retorne APENAS um JSON válido — sem texto antes ou depois, sem blocos
  de código markdown (sem ```json)
- Cada seção deve ter conteúdo em Markdown (pode usar títulos, listas, negrito)"""


def montar_prompt_wiki_documentacao(repo_data: dict[str, Any]) -> str:
    """
    Monta o prompt human com os dados do repositório para gerar a wiki.
    """
    readme = repo_data.get("readme_content") or "(README não encontrado)"
    arquivos = repo_data.get("arquivos", [])
    manifestos = repo_data.get("manifestos", {})
    linguagem = repo_data.get("linguagem_principal") or "não identificada"

    arvore_resumida = "\n".join(f"- {a}" for a in arquivos[:80])
    if len(arquivos) > 80:
        arvore_resumida += f"\n... e mais {len(arquivos) - 80} arquivo(s)"

    manifestos_texto = "\n\n".join(
        f"### {nome}\n```\n{conteudo[:2000]}\n```"
        for nome, conteudo in manifestos.items()
    ) or "(nenhum arquivo de manifesto encontrado)"

    return f"""Analise os dados abaixo de um repositório e gere uma documentação \
completa em formato de wiki, organizada em seções.

## Repositório
- Nome: {repo_data.get('repo_name')}
- Owner: {repo_data.get('owner')}
- Linguagem principal detectada: {linguagem}
- Descrição (metadados da plataforma): {repo_data.get('descricao') or 'não informada'}

## README do repositório
{readme}

## Árvore de arquivos (parcial)
{arvore_resumida}

## Arquivos de manifesto encontrados
{manifestos_texto}

## O que gerar

Retorne um JSON com este formato exato:

{{
  "titulo_geral": "nome do projeto — Documentação Técnica",
  "secoes": [
    {{
      "titulo": "Visão Geral",
      "ordem": 1,
      "conteudo_markdown": "..."
    }},
    {{
      "titulo": "Tecnologias e Bibliotecas",
      "ordem": 2,
      "conteudo_markdown": "..."
    }},
    {{
      "titulo": "Estrutura do Projeto",
      "ordem": 3,
      "conteudo_markdown": "..."
    }},
    {{
      "titulo": "Como Rodar",
      "ordem": 4,
      "conteudo_markdown": "..."
    }}
  ]
}}

Gere exatamente estas 4 seções, nesta ordem. Cada "conteudo_markdown" deve ter \
entre 1 e 3 parágrafos (ou listas, quando fizer mais sentido)."""


# ===========================================================
# PROMPT 2: CHECKLIST TÉCNICO (retorna JSON estruturado)
# Usado pelo cataloging_node
# ===========================================================

SYSTEM_CHECKLIST_TECNICO = """Você é um especialista em análise técnica e catalogação \
de componentes de software em grandes organizações de tecnologia.

Seu papel é analisar o conteúdo de um repositório e responder a um checklist técnico \
fixo, com base SOMENTE em evidências encontradas no conteúdo fornecido.

Regras obrigatórias — leia com atenção, são as mais importantes deste prompt:
- Para CADA item do checklist, responda com um dos três status:
  "confirmado"      → há evidência clara e direta (ex: dependência declarada)
  "parcial"         → há indício mas não certeza total (ex: SDK genérico presente,
                       mas sem confirmação de uso ativo daquela funcionalidade)
  "nao_identificado" → nenhuma evidência encontrada
- NUNCA marque algo como "confirmado" sem citar a evidência no campo "detalhe"
- É esperado e correto que vários itens sejam "nao_identificado" — não force
  a encontrar tecnologia que não está lá
- Retorne APENAS um JSON válido — sem texto antes ou depois, sem blocos
  de código markdown"""


def montar_prompt_checklist_tecnico(repo_data: dict[str, Any]) -> str:
    """
    Monta o prompt human com os dados do repositório para o checklist técnico.
    """
    manifestos = repo_data.get("manifestos", {})
    manifestos_texto = "\n\n".join(
        f"### {nome}\n```\n{conteudo[:3000]}\n```"
        for nome, conteudo in manifestos.items()
    ) or "(nenhum arquivo de manifesto encontrado)"

    arquivos = repo_data.get("arquivos", [])
    arvore_resumida = "\n".join(f"- {a}" for a in arquivos[:80])

    return f"""Analise os dados abaixo e responda ao checklist técnico deste componente.

## Repositório
- Nome: {repo_data.get('repo_name')}
- Linguagem principal: {repo_data.get('linguagem_principal') or 'não identificada'}

## Arquivos de manifesto
{manifestos_texto}

## Árvore de arquivos (parcial)
{arvore_resumida}

## Checklist técnico — retorne EXATAMENTE este JSON preenchido

{{
  "component_name": "{repo_data.get('repo_name')}",
  "linguagem_principal": "{repo_data.get('linguagem_principal') or 'nao_identificado'}",
  "bibliotecas": ["lista de bibliotecas/dependências encontradas nos manifestos"],
  "seguranca": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "evidência encontrada ou motivo de não identificação"
  }},
  "bancos_de_dados": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "quais bancos/vector stores, com evidência"
  }},
  "mensageria": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "ex: Kafka, RabbitMQ, SQS — com evidência"
  }},
  "tecnologia_principal": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "ex: FastAPI, Spring WebFlux, Spring Batch — com evidência"
  }},
  "uso_sicredi_flow": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "referências a padrões/bibliotecas internas Sicredi"
  }},
  "uso_s3": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "SDK de nuvem presente e/ou uso confirmado de S3"
  }},
  "containerizacao": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "Dockerfile, docker-compose, imagem base utilizada"
  }},
  "tags": ["tags geradas com base na análise — mínimo 3"],
  "classificacao_maturidade": "inicial|em-desenvolvimento|maduro|legado",
  "nivel_documentacao": "inexistente|basico|intermediario|completo",
  "resumo_executivo": "resumo de 1-2 frases para exibição no catálogo",
  "sugestoes_melhoria": ["lista de até 3 sugestões objetivas"]
}}"""