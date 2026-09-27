"""
agent_application/prompts/prompts_catalog_document.py
---------------------------------------------------------
Prompts utilizados pela LLM OpenAI/gpt-oss nos nós de geração (Fase 9).

Histórico de correções neste arquivo:
  C1) Detecção de contrato OpenAPI aceita "content" (string) e
      "contents" (array) — evita falso negativo.
  C2) Ordem de prioridade para detecção de mensageria: resource_type
      TOPIC > SASL/KAFKA na autenticação > KAFKA em enabled_features >
      heurística de porta (último recurso, nunca "confirmado").
  C3) Campos de CMDB e histórico de deploy por ambiente incorporados
      na formatação, antes ignorados.
  C4) NOVO — o diagrama Mermaid da seção de integrações estava saindo
      como campo extra "conteudo_diagrama" em vez de embutido dentro
      do próprio "conteudo_markdown". Reforçada regra explícita
      proibindo qualquer campo além dos 4 especificados.
  C5) NOVO — o campo "fontes_utilizadas" estava recebendo caminhos
      traduzidos/simplificados (ex: "identificacao.status",
      "endpoints.expostos") que não existem de verdade no
      document_context, inviabilizando o propósito de auditoria.
      Adicionada lista fechada dos caminhos reais válidos, com
      instrução explícita de nunca traduzir ou inventar variações.
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
    cmdb = document_context.get("cmdb", {})
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

    # --- Correção C1: aceita tanto "content" (string) quanto "contents" (array) ---
    openapi_contract = api.get("openapi_contract", {})
    openapi_preenchido = bool(openapi_contract.get("content")) or bool(
        openapi_contract.get("contents")
    )
    openapi_detalhe = ""
    if openapi_preenchido and openapi_contract.get("host"):
        openapi_detalhe = (
            f" (host: {openapi_contract.get('host')}, "
            f"ambiente: {openapi_contract.get('environment')})"
        )

    # --- Correção C3: bloco CMDB, antes ignorado ---
    cmdb_texto = "(nenhum dado de CMDB associado)"
    if cmdb:
        dominios = ", ".join(d.get("name", "") for d in cmdb.get("service_domains", []))
        cmdb_texto = f"""- Chave do componente no CMDB: {cmdb.get('component_key') or '(não informada)'}
- Nome oficial da aplicação: {cmdb.get('application', {}).get('name') or '(não informado)'}
- Código do time (CMDB): {cmdb.get('team', {}).get('code') or '(não informado)'}
- Grupo aprovador: {cmdb.get('team', {}).get('approving_group') or '(não informado)'}
- Domínios de serviço: {dominios or '(nenhum)'}"""

    # --- Correção C3: histórico de deploy por ambiente, antes ignorado ---
    deployments_por_ambiente = deployment.get("deployments", {})
    deployments_texto = "(sem histórico de deploy por ambiente)"
    if deployments_por_ambiente:
        linhas = []
        for ambiente, info in deployments_por_ambiente.items():
            linhas.append(
                f"- {ambiente}: versão {info.get('version')}, "
                f"último deploy em {info.get('created_at')} por {info.get('updated_by')}"
            )
        deployments_texto = "\n".join(linhas)

    return f"""### Identificação
- Nome: {document_context.get('component_name')}
- Descrição: {document_context.get('description') or '(não informada)'}
- Status: {document_context.get('status')}
- Categoria: {document_context.get('category')}
- Visibilidade: {document_context.get('visibility')}
- Repositório: {document_context.get('repository')}

### CMDB (dados de governança/inventário corporativo)
{cmdb_texto}

### Ownership (responsabilidade organizacional) — use campos ricos quando presentes
- Time responsável: {ownership.get('responsible_team') or '(não informado)'}
- Tribo: {ownership.get('tribe', {}).get('name') or '(não informada)'}
- Projeto: {ownership.get('project') or '(não informado)'}
- Aprovadores: {json.dumps(ownership.get('approvers') or [], ensure_ascii=False)}
- Tech leads: {json.dumps(ownership.get('tech_leads') or [], ensure_ascii=False)}
- Arquitetos: {json.dumps(ownership.get('architects') or [], ensure_ascii=False)}
- Desenvolvedores: {json.dumps(ownership.get('developers') or [], ensure_ascii=False)}
- QA: {json.dumps(ownership.get('qa') or [], ensure_ascii=False)}
- UX: {json.dumps(ownership.get('ux') or [], ensure_ascii=False)}
- Colaboradores temporários: {json.dumps(ownership.get('temporary_contributors') or [], ensure_ascii=False)}
- Times colaboradores: {json.dumps(ownership.get('contributor_teams') or [], ensure_ascii=False)}

### Classificação técnica
- Tipo de aplicação: {classification.get('application_type')}
- Linguagem principal: {classification.get('main_language')}
- Framework principal: {classification.get('main_framework')}

### Tecnologias declaradas
{json.dumps(technology.get('technologies', []), ensure_ascii=False)}

### Estrutura de pacotes (parcial)
{json.dumps(technology.get('package_structure', [])[:30], ensure_ascii=False)}

### Endpoints expostos pela API (total: {len(endpoints_resumo)})
{chr(10).join(endpoints_resumo) if endpoints_resumo else '(nenhum endpoint listado)'}

Contrato OpenAPI formal preenchido: {'sim' + openapi_detalhe if openapi_preenchido else 'não'}

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
- Histórico de deploy por ambiente:
{deployments_texto}

### Jira
- Épicos: {jira.get('epics') or '(nenhum)'}
- Roadmap: {jira.get('roadmap') or '(nenhum)'}
- Responsável funcional: {jira.get('functional_owner') or '(não informado)'}"""


# Lista fechada dos caminhos reais válidos no document_context — usada na
# regra de "fontes_utilizadas" (Correção C5). A LLM deve citar SOMENTE
# caminhos desta lista, exatamente como escritos aqui.
CAMINHOS_VALIDOS_DOCUMENT_CONTEXT = """component_name, description, status, category, visibility, repository,
cmdb.component_key, cmdb.application.name, cmdb.team.code, cmdb.team.approving_group, cmdb.service_domains,
ownership.responsible_team, ownership.tribe.name, ownership.project, ownership.approvers,
ownership.tech_leads, ownership.architects, ownership.developers, ownership.qa, ownership.ux,
ownership.temporary_contributors, ownership.contributor_teams,
classification.application_type, classification.main_language, classification.main_framework,
technology.technologies, technology.package_structure,
api.exposed_endpoints, api.openapi_contract,
integrations.consumed, integrations.consumers,
security.authentication.application, security.authentication.infrastructure,
observability.enabled, observability.disabled,
data.databases,
runtime.enabled_features, runtime.resources_by_environment, runtime.cloud_provider, runtime.clusters,
quality.criticality, quality.score,
deployment.default_branch, deployment.pipeline_deploy, deployment.deployments,
jira.epics, jira.roadmap, jira.functional_owner"""


# ===========================================================
# PROMPT 1: DOCUMENTAÇÃO WIKI MULTI-SEÇÃO
# Usado pelo documentation_node
# ===========================================================

SYSTEM_WIKI_DOCUMENTACAO = f"""Você é um especialista em documentação técnica de software, \
com profundo conhecimento em arquitetura de sistemas e boas práticas de engenharia.

Seu papel é analisar o contexto estruturado de um componente de software — já coletado e \
normalizado por um sistema interno de inventário — e gerar uma documentação completa em \
formato de WIKI, organizada em seções.

Regra crítica de ESTILO — leia com atenção, ela evita um erro observado na prática:
- Escreva SEMPRE em prosa corrida e sintetizada, como um redator humano escreveria
- NUNCA use o formato de rótulo "Campo: valor" ou listas de "**Nome:** valor" — um leitor
  não deve perceber que os dados vieram de uma estrutura de campos; a documentação deve
  ler como texto, não como uma reformatação do JSON de origem
- Quando uma lista tiver mais de 5 itens (ex: endpoints, tecnologias), NÃO liste todos —
  agrupe por padrão/categoria, mencione a contagem total, e cite apenas os mais
  representativos como exemplo (ex: "a API expõe 19 endpoints, majoritariamente de
  consulta (GET), como listagem de componentes e times")

Regras obrigatórias de conteúdo:
- Escreva em português brasileiro formal e técnico
- Baseie-se APENAS nos dados fornecidos — não adicione suposições
- NUNCA invente informações que não estejam nos dados fornecidos
- Quando um campo estiver vazio, nulo, ou com lista vazia, mencione isso de forma neutra
  (ex: "não há aprovadores cadastrados") — NÃO presuma o motivo
- Quando os campos de ownership detalhado estiverem preenchidos (aprovadores, QA, UX,
  colaboradores temporários, times colaboradores), aproveite-os na Visão Geral para
  descrever a composição real do time (ex: "squad multidisciplinar com QA e UX dedicados")
  — só mencione o que realmente estiver presente nos dados
- Quando houver dados de CMDB, use o nome oficial da aplicação (application.name) e o
  grupo aprovador para enriquecer a Visão Geral, se agregarem contexto útil
- Quando houver histórico de deploy por ambiente, mencione na seção de Dados e
  Infraestrutura em qual ambiente o componente está mais atualizado e se há
  defasagem de versão entre ambientes (isso é fato observável, não invenção)

Regra crítica de ESTRUTURA DE SAÍDA — leia com atenção, ela evita um erro observado na prática:
- Cada seção do JSON de resposta deve ter EXATAMENTE estes 4 campos, nenhum a mais:
  "titulo", "ordem", "conteudo_markdown", "fontes_utilizadas"
- NUNCA crie campos adicionais como "conteudo_diagrama", "resumo", "detalhes" ou qualquer
  outro nome — se você gerar um diagrama Mermaid (seção 3), ele deve ficar DENTRO da
  própria string de "conteudo_markdown" daquela seção, como parte do mesmo texto
  markdown (prosa seguida do bloco ```mermaid ... ``` no final do mesmo campo)

Regra sobre o campo "fontes_utilizadas" — leia com atenção, ela evita um erro observado
na prática (a LLM às vezes traduz ou simplifica nomes de campos, tornando a citação inútil
para auditoria):
- Cite SOMENTE caminhos EXATOS da lista abaixo, escritos exatamente como aparecem aqui
  (em inglês, com a pontuação e capitalização exatas) — NUNCA traduza para português,
  NUNCA invente sub-caminhos, NUNCA simplifique (ex: "status" está certo; "identificacao.status"
  está errado e não deve ser usado)
- Lista de caminhos válidos:
  {CAMINHOS_VALIDOS_DOCUMENT_CONTEXT}
- Se uma seção não usar diretamente nenhum desses campos, use uma lista vazia []

Auto-checagem antes de responder (aplique mentalmente, sem custo de nova chamada):
- Releia cada frase que você escreveu: ela corresponde a um fato presente nos dados
  fornecidos? "Corresponder" significa que o fato é verdadeiro segundo os dados —
  NÃO significa copiar o campo literalmente. Reescrever com suas palavras continua
  correspondendo ao fato, e é o comportamento esperado
- Se uma frase não tiver correspondência com nenhum dado fornecido, remova-a
- Confira se cada "fontes_utilizadas" citada está literalmente na lista de caminhos válidos
  acima — se não estiver, corrija ou remova antes de responder
- Confira se cada seção tem exatamente os 4 campos esperados, sem nenhum campo extra

Retorne APENAS um JSON válido — sem texto antes ou depois, sem blocos de código markdown \
fora da estrutura pedida.

Sobre as seções — gere exatamente 5, na ordem abaixo:
  1. Visão Geral — o que é o componente, quem é responsável, status, criticidade
  2. Arquitetura e Endpoints — API exposta, rotas principais (resumidas por padrão se
     forem muitas), contrato OpenAPI
  3. Integrações e Dependências — o que consome e quem consome este componente, em
     prosa, seguida (dentro do MESMO conteudo_markdown desta seção) de um diagrama
     Mermaid (```mermaid ... ```) do tipo "graph LR" representando essas mesmas
     relações (ex: A --> B para cada integração consumida ou consumidora) — o
     diagrama é só uma representação visual do mesmo dado já descrito em texto,
     não uma informação nova, e não deve virar um campo separado
  4. Segurança e Observabilidade — autenticação e ferramentas de observabilidade
  5. Dados e Infraestrutura — bancos de dados, runtime, deploy (incluindo o histórico
     de versões por ambiente, quando disponível)"""


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

Retorne um JSON com este formato exato — cada seção tem EXATAMENTE 4 campos, nunca mais:

{{
  "titulo_geral": "nome do componente — Documentação Técnica",
  "secoes": [
    {{
      "titulo": "Visão Geral",
      "ordem": 1,
      "conteudo_markdown": "...",
      "fontes_utilizadas": ["ownership.responsible_team", "quality.criticality"]
    }},
    {{
      "titulo": "Arquitetura e Endpoints",
      "ordem": 2,
      "conteudo_markdown": "...",
      "fontes_utilizadas": ["api.exposed_endpoints", "api.openapi_contract"]
    }},
    {{
      "titulo": "Integrações e Dependências",
      "ordem": 3,
      "conteudo_markdown": "texto em prosa descrevendo as integrações...\\n\\n```mermaid\\ngraph LR\\nA --> B\\n```",
      "fontes_utilizadas": ["integrations.consumed", "integrations.consumers"]
    }},
    {{
      "titulo": "Segurança e Observabilidade",
      "ordem": 4,
      "conteudo_markdown": "...",
      "fontes_utilizadas": ["security.authentication.application", "observability.enabled"]
    }},
    {{
      "titulo": "Dados e Infraestrutura",
      "ordem": 5,
      "conteudo_markdown": "...",
      "fontes_utilizadas": ["data.databases", "deployment.deployments"]
    }}
  ]
}}

Repare no exemplo da seção 3: o bloco ```mermaid``` está DENTRO da mesma string de \
"conteudo_markdown", não em um campo separado. Siga exatamente esse padrão.

Lembre-se: prosa corrida, sem rótulos "Campo: valor", listas longas resumidas por \
categoria, e fontes_utilizadas usando apenas os caminhos exatos da lista fornecida \
nas instruções do sistema."""


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
- "mensageria": siga esta ORDEM DE PRIORIDADE, do sinal mais forte para o mais fraco —
  pare no primeiro que encontrar evidência:
  1. Nas integrações (consumidas ou consumidoras), procure algum item com
     "resource_type": "TOPIC" — esse é o sinal MAIS DIRETO possível, cite o
     resource_name encontrado
  2. Na autenticação de infraestrutura, procure entradas com "target": "KAFKA" ou
     mecanismo SASL associado a Kafka — também um sinal direto e confiável
  3. Em runtime.enabled_features, procure literalmente "KAFKA" — sinal direto de que
     a plataforma está habilitada para o componente, mesmo sem uso explícito nas
     integrações
  4. SOMENTE se nenhum dos três sinais acima existir, procure nas integrações por
     endpoints cuja porta sugira um broker (porta 9093 é característica de Kafka) —
     esta é uma heurística fraca; ao usá-la, marque no máximo "parcial", nunca
     "confirmado", e explique que é uma inferência por porta, não confirmação direta
  Se nenhum dos quatro sinais existir, marque "nao_identificado"
- "tecnologia_principal": framework principal e lista de tecnologias declaradas
- "uso_sicredi_flow": procure por funcionalidades de plataforma habilitadas (ex:
  Consul, Vault, Kubernetes) — esses são sinais diretos de uso da plataforma
  corporativa interna, não de uma biblioteca específica. Contas de automação
  responsáveis por deploys (ex: um "updated_by" que parece um usuário de sistema/bot,
  não uma pessoa) também são um sinal complementar de pipeline corporativo padronizado
- "armazenamento_objetos": procure evidência de QUALQUER serviço de armazenamento de
  objetos (AWS S3, Azure Blob Storage, Google Cloud Storage, ou equivalente interno) —
  se os dados não mencionarem nada disso, marque "nao_identificado"
- "containerizacao": procure no pipeline de deploy por ferramentas de build de imagem
  (ex: Jib) ou orquestração de containers (ex: Kubernetes)

Sobre o contrato OpenAPI: o texto fornecido já indica de forma confiável se o contrato
está preenchido ("sim"/"não") — use essa informação diretamente, ela já trata as duas
formas possíveis em que o dado de origem pode vir estruturado.

Sobre "tipo_componente":
- Use o tipo de aplicação informado nos dados para classificar como
  "servico", "biblioteca", "batch" ou "modulo-compartilhado"

Distinção crítica — fato ausente vs. opinião técnica (não misture os dois campos):
- "limitacoes_detectadas": SOMENTE lacunas objetivas e verificáveis nos DADOS fornecidos
  (ex: "contrato OpenAPI não preenchido", "responsável funcional não informado") — é
  um registro de fato, sem juízo de valor sobre se isso é bom ou ruim
- "sugestoes_melhoria": aqui SIM cabe julgamento técnico seu, com base na sua experiência
  (ex: "considerar adicionar cache" é uma recomendação, não um fato observado)
- Não coloque a mesma informação nos dois campos com fraseado diferente — se é uma
  lacuna de dado, vai em limitacoes_detectadas; se é um conselho de melhoria técnica,
  vai em sugestoes_melhoria
- Deixe limitacoes_detectadas como lista vazia [] se não houver nenhuma lacuna relevante

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
    "detalhe": "cite qual dos 4 sinais (TOPIC nas integrações / SASL-KAFKA na autenticação / KAFKA em enabled_features / porta 9093) foi usado, ou a ausência de todos"
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
  "limitacoes_detectadas": ["APENAS lacunas objetivas nos dados — lista vazia [] se não houver"],
  "tags": ["tags geradas com base na análise — mínimo 3"],
  "classificacao_maturidade": "inicial|em-desenvolvimento|maduro|legado",
  "nivel_documentacao": "inexistente|basico|intermediario|completo",
  "resumo_executivo": "resumo de 1-2 frases para exibição no catálogo",
  "sugestoes_melhoria": ["APENAS julgamento técnico/recomendações — até 3"],
  "team_id": {json.dumps(document_context.get('ownership', {}).get('team_id'), ensure_ascii=False)},
  "time_responsavel": {json.dumps(document_context.get('ownership', {}).get('responsible_team'), ensure_ascii=False)},
  "projeto": {json.dumps(document_context.get('ownership', {}).get('project') or None, ensure_ascii=False)},
  "tribo": {json.dumps(document_context.get('ownership', {}).get('tribe', {}).get('name'), ensure_ascii=False)},
  "criticidade": {json.dumps(document_context.get('quality', {}).get('criticality'), ensure_ascii=False)},
  "environment": {json.dumps(document_context.get('runtime', {}).get('resources_by_environment'), ensure_ascii=False)},
  "status_aplicacao": {json.dumps(document_context.get('status'), ensure_ascii=False)},
  "categoria_aplicacao": {json.dumps(document_context.get('classification', {}).get('application_type'), ensure_ascii=False)}
}}"""