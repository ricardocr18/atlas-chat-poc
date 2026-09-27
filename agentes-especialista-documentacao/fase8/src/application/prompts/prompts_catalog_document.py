"""
agent_application/prompts/prompts_catalog_document.py
---------------------------------------------------------
Prompts utilizados pela LLM OpenAI nos nós de geração (Fase 8).

Fase 7: prompts recebiam README/manifesto em texto livre, exigindo
        muita inferência da LLM (ex: "esse Kafka é log ou negócio?").
Fase 8: prompts recebem document_context — dados estruturados e já
        normalizados pelo atlas-apis-ingestao. A LLM passa a atuar
        muito mais como REDATORA e ANALISTA do que como DETETIVE:
        a maior parte dos fatos já vem pronta, e o trabalho principal
        é traduzir isso em texto legível e aplicar julgamento
        qualitativo (maturidade, resumo executivo, sugestões).

Continua valendo a regra de ouro: NUNCA afirmar algo sem evidência no
document_context, e sinalizar claramente ausências (campos vazios ou
nulos) sem presumir o motivo por trás delas.
"""

import json
from typing import Any


def _formatar_document_context(document_context: dict[str, Any]) -> str:
    """
    Formata o document_context inteiro em texto legível para os prompts.

    Centraliza a formatação para não duplicar essa lógica nos dois
    prompts (documentação e checklist) — ambos recebem exatamente a
    mesma visão dos dados.
    """
    ownership = document_context.get("ownership", {})
    classification = document_context.get("classification", {})
    technology = document_context.get("technology", {})
    api = document_context.get("api", {})
    integrations = document_context.get("integrations", {})
    security = document_context.get("security", {})
    observability = document_context.get("observability", {})
    data = document_context.get("data", {})
    runtime = document_context.get("runtime", {})
    quality = document_context.get("quality", {})
    deployment = document_context.get("deployment", {})
    jira = document_context.get("jira", {})

    endpoints = api.get("exposed_endpoints", {})
    endpoints_resumo = []
    for metodo, lista in endpoints.items():
        for item in lista:
            endpoints_resumo.append(f"{metodo} {item.get('path')} ({item.get('operation_id')})")

    consumidos = integrations.get("consumed", {})
    consumidores = integrations.get("consumers", {})

    return f"""### Identificação
- Nome: {document_context.get('component_name')}
- Descrição: {document_context.get('description') or '(não informada)'}
- Status: {document_context.get('status')}
- Categoria: {document_context.get('category')}
- Visibilidade: {document_context.get('visibility')}
- Repositório: {document_context.get('repository')}

### Ownership (responsabilidade organizacional)
- Time responsável: {ownership.get('responsible_team') or '(não informado)'}
- Tribo: {ownership.get('tribe', {}).get('name') or '(não informada)'}
- Projeto: {ownership.get('project') or '(não informado)'}
- Aprovadores: {ownership.get('approvers') or '(lista vazia — não preenchido)'}
- Tech leads: {ownership.get('tech_leads') or '(lista vazia — não preenchido)'}
- Arquitetos: {ownership.get('architects') or '(lista vazia — não preenchido)'}
- Desenvolvedores: {ownership.get('developers') or '(lista vazia — não preenchido)'}

### Classificação técnica
- Tipo de aplicação: {classification.get('application_type')}
- Linguagem principal: {classification.get('main_language')}
- Framework principal: {classification.get('main_framework')}

### Tecnologias declaradas
{json.dumps(technology.get('technologies', []), ensure_ascii=False)}

### Estrutura de pacotes (parcial)
{json.dumps(technology.get('package_structure', [])[:30], ensure_ascii=False)}

### Endpoints expostos pela API
{chr(10).join(endpoints_resumo) if endpoints_resumo else '(nenhum endpoint listado)'}

Contrato OpenAPI formal preenchido: {'sim' if api.get('openapi_contract', {}).get('contents') else 'não'}

### Integrações — o que este componente CONSOME (por ambiente)
{json.dumps(consumidos, ensure_ascii=False, indent=2)}

### Integrações — quem CONSOME este componente (por ambiente)
{json.dumps(consumidores, ensure_ascii=False, indent=2)}

### Segurança
- Autenticação de aplicação: {json.dumps(security.get('authentication', {}).get('application', []), ensure_ascii=False)}
- Autenticação de infraestrutura: {json.dumps(security.get('authentication', {}).get('infrastructure', []), ensure_ascii=False)}

### Observabilidade
- Habilitados: {observability.get('enabled') or '(nenhum)'}
- Desabilitados: {observability.get('disabled') or '(nenhum)'}

### Dados
- Bancos de dados: {data.get('databases') or '(nenhum informado)'}

### Runtime e infraestrutura
- Funcionalidades habilitadas: {runtime.get('enabled_features') or '(nenhuma)'}
- Ambientes com recursos: {runtime.get('resources_by_environment') or '(nenhum)'}
- Provedor de nuvem: {runtime.get('cloud_provider') or '(não informado)'}
- Clusters: {json.dumps(runtime.get('clusters', {}), ensure_ascii=False)}

### Qualidade
- Criticidade: {quality.get('criticality') or '(não informada)'}
- Score: {quality.get('score')}

### Deploy
- Branch padrão: {deployment.get('default_branch')}
- Pipeline de deploy: {deployment.get('pipeline_deploy') or '(não informado)'}

### Jira
- Épicos: {jira.get('epics') or '(nenhum)'}
- Roadmap: {jira.get('roadmap') or '(nenhum)'}
- Responsável funcional: {jira.get('functional_owner') or '(não informado)'}"""


# ===========================================================
# PROMPT 1: DOCUMENTAÇÃO WIKI MULTI-SEÇÃO
# Usado pelo documentation_node
# ===========================================================

SYSTEM_WIKI_DOCUMENTACAO = """Você é um especialista em documentação técnica de software, \
com profundo conhecimento em arquitetura de sistemas e boas práticas de engenharia.

Seu papel é analisar o contexto estruturado de um componente de software — já coletado e \
normalizado por um sistema interno de inventário — e gerar uma documentação completa em \
formato de WIKI, organizada em seções.

Regras obrigatórias:
- Escreva em português brasileiro formal e técnico
- Baseie-se APENAS nos dados fornecidos — a maior parte já é fato estruturado, não texto
  livre a ser interpretado; use-os diretamente, sem adicionar suposições
- NUNCA invente informações que não estejam nos dados fornecidos
- Quando um campo estiver vazio, nulo, ou com lista vazia, mencione isso de forma neutra
  (ex: "não há aprovadores cadastrados") — NÃO presuma o motivo (não diga que foi
  "esquecido" ou "negligenciado"; apenas registre o fato)
- Retorne APENAS um JSON válido — sem texto antes ou depois, sem blocos de código markdown

Sobre as seções:
- Gere exatamente 5 seções, na ordem abaixo — os dados fornecidos já vêm organizados
  nos mesmos grupos temáticos, facilitando o mapeamento:
  1. Visão Geral — o que é o componente, quem é responsável, status, criticidade
  2. Arquitetura e Endpoints — API exposta, rotas principais, contrato OpenAPI
  3. Integrações e Dependências — o que consome e quem consome este componente
  4. Segurança e Observabilidade — autenticação e ferramentas de observabilidade
  5. Dados e Infraestrutura — bancos de dados, runtime, deploy"""


def montar_prompt_wiki_documentacao(document_context: dict[str, Any]) -> str:
    """
    Monta o prompt human com o document_context para gerar a wiki.

    Args:
        document_context: dados buscados pelo ingestao_fetch_node

    Returns:
        String formatada com o contexto do componente para o prompt
    """
    return f"""Analise os dados abaixo de um componente e gere uma documentação completa \
em formato de wiki, organizada em seções.

{_formatar_document_context(document_context)}

## O que gerar

Retorne um JSON com este formato exato:

{{
  "titulo_geral": "nome do componente — Documentação Técnica",
  "secoes": [
    {{
      "titulo": "Visão Geral",
      "ordem": 1,
      "conteudo_markdown": "..."
    }},
    {{
      "titulo": "Arquitetura e Endpoints",
      "ordem": 2,
      "conteudo_markdown": "..."
    }},
    {{
      "titulo": "Integrações e Dependências",
      "ordem": 3,
      "conteudo_markdown": "..."
    }},
    {{
      "titulo": "Segurança e Observabilidade",
      "ordem": 4,
      "conteudo_markdown": "..."
    }},
    {{
      "titulo": "Dados e Infraestrutura",
      "ordem": 5,
      "conteudo_markdown": "..."
    }}
  ]
}}

Cada "conteudo_markdown" deve ter entre 1 e 3 parágrafos (ou listas, quando fizer mais \
sentido — por exemplo, para listar endpoints)."""


# ===========================================================
# PROMPT 2: CHECKLIST TÉCNICO (retorna JSON estruturado)
# Usado pelo cataloging_node
# ===========================================================

SYSTEM_CHECKLIST_TECNICO = """Você é um especialista em análise técnica e catalogação \
de componentes de software em grandes organizações de tecnologia.

Seu papel é preencher um checklist técnico fixo para um componente, usando SOMENTE os \
dados estruturados fornecidos — que já vêm normalizados e confiáveis, coletados por um \
sistema interno de inventário.

Regras obrigatórias:
- Para os itens de status ("seguranca", "bancos_de_dados", "mensageria",
  "tecnologia_principal", "uso_sicredi_flow", "armazenamento_objetos", "containerizacao"),
  responda com um dos três status:
  "confirmado"      → o dado estruturado confirma diretamente
  "parcial"         → há indício mas não certeza total
  "nao_identificado" → nenhuma evidência encontrada nos dados
- Sempre cite no campo "detalhe" o dado exato que embasou a resposta
- É esperado e correto que vários itens sejam "nao_identificado" quando o dado
  estruturado simplesmente não contempla aquele item — não force uma resposta

Como localizar cada item nos dados estruturados fornecidos:
- "seguranca": campo de autenticação (tipo e provedor)
- "bancos_de_dados": lista de bancos de dados
- "mensageria": procure nas integrações por endpoints cuja porta ou nome sugiram um
  broker de mensageria (ex: porta 9093 é característica de Kafka); NÃO marque
  "confirmado" só por existir uma integração HTTP comum
- "tecnologia_principal": framework principal e lista de tecnologias declaradas
- "uso_sicredi_flow": procure por funcionalidades de plataforma habilitadas (ex:
  Consul, Vault, Kubernetes) — esses são sinais diretos de uso da plataforma
  corporativa interna, não de uma biblioteca específica
- "armazenamento_objetos": procure evidência de QUALQUER serviço de armazenamento de
  objetos (AWS S3, Azure Blob Storage, Google Cloud Storage, ou equivalente interno) —
  se os dados não mencionarem nada disso, marque "nao_identificado"
- "containerizacao": procure no pipeline de deploy por ferramentas de build de imagem
  (ex: Jib) ou orquestração de containers (ex: Kubernetes)

Sobre "tipo_componente":
- Use o tipo de aplicação informado nos dados para classificar como
  "servico", "biblioteca", "batch" ou "modulo-compartilhado"

Sobre "limitacoes_detectadas":
- Registre aqui qualquer lacuna relevante nos próprios dados fornecidos, por exemplo:
  contrato OpenAPI não preenchido, lista de aprovadores vazia, responsável funcional
  não informado no Jira — sem especular a razão dessas lacunas
- Deixe como lista vazia [] se não houver nenhuma lacuna relevante

Regras de formato:
- Retorne APENAS um JSON válido — sem texto antes ou depois, sem blocos
  de código markdown"""


def montar_prompt_checklist_tecnico(document_context: dict[str, Any]) -> str:
    """
    Monta o prompt human com o document_context para o checklist técnico.

    Args:
        document_context: dados buscados pelo ingestao_fetch_node

    Returns:
        String formatada com o contexto do componente e o schema esperado
    """
    return f"""Analise os dados abaixo e preencha o checklist técnico deste componente.

{_formatar_document_context(document_context)}

## Checklist técnico — retorne EXATAMENTE este JSON preenchido

{{
  "component_name": "{document_context.get('component_name')}",
  "linguagem_principal": "{document_context.get('classification', {}).get('main_language') or 'nao_identificado'}",
  "tipo_componente": "servico|biblioteca|batch|modulo-compartilhado",
  "bibliotecas": {json.dumps(document_context.get('technology', {}).get('technologies', []), ensure_ascii=False)},
  "seguranca": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "cite o tipo e provedor de autenticação encontrado"
  }},
  "bancos_de_dados": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "cite os bancos de dados encontrados"
  }},
  "mensageria": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "cite o endpoint/evidência encontrada, ou a ausência dela"
  }},
  "tecnologia_principal": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "cite o framework principal encontrado"
  }},
  "uso_sicredi_flow": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "cite as funcionalidades de plataforma (Consul, Vault, Kubernetes etc) encontradas"
  }},
  "armazenamento_objetos": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "identifique o provedor encontrado (AWS S3, Azure Blob Storage, Google Cloud Storage, ou outro), ou a ausência de evidência"
  }},
  "containerizacao": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "cite a evidência do pipeline de deploy encontrada"
  }},
  "limitacoes_detectadas": ["lacunas relevantes nos próprios dados fornecidos — lista vazia [] se não houver"],
  "tags": ["tags geradas com base na análise — mínimo 3"],
  "classificacao_maturidade": "inicial|em-desenvolvimento|maduro|legado",
  "nivel_documentacao": "inexistente|basico|intermediario|completo",
  "resumo_executivo": "resumo de 1-2 frases para exibição no catálogo",
  "sugestoes_melhoria": ["lista de até 3 sugestões objetivas"],
  "team_id": {json.dumps(document_context.get('ownership', {}).get('team_id'), ensure_ascii=False)},
  "time_responsavel": {json.dumps(document_context.get('ownership', {}).get('responsible_team'), ensure_ascii=False)},
  "projeto": {json.dumps(document_context.get('ownership', {}).get('project') or None, ensure_ascii=False)},
  "tribo": {json.dumps(document_context.get('ownership', {}).get('tribe', {}).get('name'), ensure_ascii=False)},
  "criticidade": {json.dumps(document_context.get('quality', {}).get('criticality'), ensure_ascii=False)},
  "environment": {json.dumps(document_context.get('runtime', {}).get('resources_by_environment'), ensure_ascii=False)},
  "status_aplicacao": {json.dumps(document_context.get('status'), ensure_ascii=False)},
  "categoria_aplicacao": {json.dumps(document_context.get('classification', {}).get('application_type'), ensure_ascii=False)}
}}"""