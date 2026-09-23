"""
agent_application/prompts/prompts_catalog_document.py
---------------------------------------------------------
Prompts utilizados pela LLM OpenAI nos nós de geração (Fase 7).

Incremento na Fase 7: os prompts agora recebem os sinais determinísticos
coletados pelos clients (registros_internos_detectados, modulos_detectados,
multi_modulo_detectado, readme_estruturado_detectado) e usam regras mais
específicas para evitar erros observados em repositórios corporativos
reais:

  1. Distinguir uso técnico/observabilidade de uso funcional/negócio
     da mesma tecnologia (ex: Kafka usado só para transporte de logs
     não é mensageria de negócio)
  2. Detectar "Sicredi Flow" por padrão de evidência (domínios internos,
     namespaces organizacionais), não por nome de biblioteca específica
  3. Reconhecer containerização declarada via plugin de build
     (ex: Jib no Gradle), não só por Dockerfile
  4. Priorizar extração literal quando o README já segue um template
     corporativo estruturado, em vez de resumir livremente
  5. Classificar o tipo de componente (serviço/biblioteca/batch/módulo
     compartilhado) antes de gerar instruções de "Como Rodar"
  6. Declarar limitações conhecidas da própria análise — importante
     porque o agente de classificação (dois juízes LLM) nunca vê o
     repositório original, só o que este agente produzir

Ajuste posterior: o campo antigo "uso_s3" foi renomeado para
"armazenamento_objetos" — o nome antigo presumia AWS como único
provedor. O checklist agora orienta a LLM a identificar QUALQUER
serviço de armazenamento de objetos (AWS S3, Azure Blob Storage,
Google Cloud Storage, MinIO ou equivalente on-premises), registrando
qual foi encontrado no campo "detalhe" — sem enviesar a pergunta
para um único vendor.
"""

import json
from typing import Any


def _formatar_sinais_deterministicos(repo_data: dict[str, Any]) -> str:
    """
    Formata os sinais determinísticos coletados pelo client em texto
    para incluir nos prompts — funciona igual para os dois prompts
    (documentação e checklist), evitando duplicar essa lógica duas vezes.
    """
    registros = repo_data.get("registros_internos_detectados", [])
    modulos = repo_data.get("modulos_detectados", [])
    multi_modulo = repo_data.get("multi_modulo_detectado", False)
    readme_estruturado = repo_data.get("readme_estruturado_detectado", False)

    linhas = [
        f"- Domínios internos detectados nos manifestos/README: "
        f"{', '.join(registros) if registros else '(nenhum encontrado)'}",
        f"- Projeto multi-módulo: {'SIM — módulos: ' + ', '.join(modulos) if multi_modulo else 'não detectado'}",
        f"- README segue template corporativo estruturado: "
        f"{'SIM — priorize extração literal das seções nomeadas' if readme_estruturado else 'não detectado'}",
    ]
    return "\n".join(linhas)


# ===========================================================
# PROMPT 1: DOCUMENTAÇÃO WIKI MULTI-SEÇÃO
# Usado pelo documentation_node
# ===========================================================
# (sem alterações neste incremento — mantido igual ao já existente)

SYSTEM_WIKI_DOCUMENTACAO = """Você é um especialista em documentação técnica de software, \
com profundo conhecimento em arquitetura de sistemas e boas práticas de engenharia, incluindo \
convenções usadas em repositórios corporativos de grandes organizações.

Seu papel é analisar o conteúdo de um repositório de código e gerar uma documentação \
completa em formato de WIKI, organizada em múltiplas seções — não um texto corrido único.

Regras obrigatórias:
- Escreva em português brasileiro formal e técnico
- Baseie-se APENAS no conteúdo fornecido (README, árvore de arquivos, manifestos)
- NUNCA invente funcionalidades, tecnologias ou informações que não estejam
  explícitas ou razoavelmente inferíveis do conteúdo fornecido
- Se uma seção não tiver informação suficiente, escreva isso claramente
  em vez de inventar

Regras sobre README estruturado:
- Se os sinais indicarem que o README segue um template corporativo conhecido
  (seções nomeadas como "Objetivo", "Responsáveis", "Build"), EXTRAIA e adapte
  diretamente essas seções em vez de resumir livremente — são mais confiáveis
  que qualquer inferência sua
- Se o README não for estruturado, gere as seções com base no conjunto do
  conteúdo disponível (README livre, árvore de arquivos, manifestos)

Regras sobre classificação do componente e a seção "Como Rodar":
- Antes de escrever "Como Rodar", identifique que TIPO de componente é este:
  * serviço implantável (tem servidor web, porta exposta, ou definição de imagem)
  * biblioteca/SDK (é publicado como dependência para outros consumirem)
  * job/processo batch (processamento agendado, sem servidor exposto)
  * módulo compartilhado dentro de um projeto multi-módulo
- Adapte as instruções ao tipo: para uma biblioteca, explique como ADICIONAR
  como dependência, não como "rodar um servidor"; para um serviço, explique
  como executá-lo

Regras sobre projetos multi-módulo:
- Se os sinais indicarem que o projeto é multi-módulo, mencione isso
  explicitamente na seção "Visão Geral" — deixe claro que a análise pode
  não cobrir o detalhe interno de cada módulo individualmente

Regras sobre a data de criação do repositório:
- Se a data de criação estiver disponível, mencione-a na seção "Visão Geral"
  de forma natural (ex: "criado em [mês/ano]") — isso dá contexto temporal
  para quem lê a documentação
- Use a idade do repositório para calibrar o tom: um repositório recente
  sendo descrito como "em desenvolvimento inicial" é esperado; um repositório
  antigo no mesmo estado merece ser descrito com mais neutralidade, sem
  presumir o motivo

Regras de formato:
- Retorne APENAS um JSON válido — sem texto antes ou depois, sem blocos
  de código markdown (sem ```json)
- Cada seção deve ter conteúdo em Markdown (pode usar títulos, listas, negrito)"""


def montar_prompt_wiki_documentacao(repo_data: dict[str, Any]) -> str:
    """
    Monta o prompt human com os dados do repositório para gerar a wiki.

    Args:
        repo_data: dados buscados pelo repository_fetch_node, incluindo
                   os sinais determinísticos coletados pelo client

    Returns:
        String formatada com o conteúdo do repositório para o prompt
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
- Criado em: {repo_data.get('repositorio_criado_em') or 'não informado'}
- Descrição (metadados da plataforma): {repo_data.get('descricao') or 'não informada'}

## Sinais detectados automaticamente (use como pistas, não como verdade absoluta)
{_formatar_sinais_deterministicos(repo_data)}

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
  "parcial"         → há indício mas não certeza total
  "nao_identificado" → nenhuma evidência encontrada
- NUNCA marque algo como "confirmado" sem citar a evidência no campo "detalhe"
- É esperado e correto que vários itens sejam "nao_identificado" — não force
  a encontrar tecnologia que não está lá

Regra crítica de desambiguação — uso técnico vs uso funcional:
- Uma tecnologia pode aparecer no projeto para fins de infraestrutura/observabilidade
  (logging, tracing, métricas) sem que o componente a use para lógica de negócio
- Exemplo real: uma dependência de "logback-kafka" transporta LOGS via Kafka —
  isso NÃO significa que o componente usa Kafka como mensageria de negócio
- Ao avaliar "mensageria", "bancos_de_dados" e itens similares, verifique se a
  dependência está associada a nomes/pacotes de logging, tracing ou métricas —
  se estiver, NÃO marque como "confirmado" para uso funcional; explique a
  distinção no campo "detalhe" (ex: "presente apenas para transporte de logs,
  não para mensageria de negócio")

Regra sobre detecção de "uso_sicredi_flow" — por padrão, não por nome:
- NÃO procure apenas por bibliotecas com "sicredi" no nome
- Considere evidência de plataforma interna corporativa quando encontrar:
  (a) domínios internos informados nos sinais detectados (ex: *.sicredi.net)
  (b) pacotes/grupos com namespace organizacional (ex: devops.sicredi,
      io.sicredi, br.com.sicredi, ou variações de nome de grupo interno)
  (c) plugins ou ferramentas de build específicos de uma organização
- Essa abordagem funciona para qualquer linguagem — não é específica de Java

Regra sobre containerização — considere também plugins de build:
- Além de procurar por Dockerfile/docker-compose, verifique se o manifesto de
  build declara uma imagem de container por plugin (ex: bloco "jib" no Gradle,
  Cloud Native Buildpacks, ou equivalentes em outros ecossistemas)
- Se encontrar isso, marque "confirmado" e cite a imagem base encontrada, se houver

Regra sobre armazenamento de objetos — não presuma um único provedor de nuvem:
- O item "armazenamento_objetos" NÃO é exclusivo da AWS — avalie evidência de
  QUALQUER serviço de armazenamento de objetos, entre eles:
  * AWS S3 (SDKs como boto3, aws-sdk, @aws-sdk/client-s3)
  * Azure Blob Storage (SDKs como azure-storage-blob, Azure.Storage.Blobs)
  * Google Cloud Storage (SDKs como google-cloud-storage)
  * MinIO ou outro armazenamento compatível com S3 hospedado internamente
- Identifique QUAL provedor foi encontrado e cite isso explicitamente no
  campo "detalhe" (ex: "Azure Blob Storage via azure-storage-blob", não
  apenas "confirmado" sem dizer qual serviço)
- Se encontrar apenas um SDK de nuvem genérico (ex: boto3 usado só para
  outro serviço, como um LLM hospedado na nuvem) sem evidência de uso
  para armazenamento de arquivos, marque como "parcial" e explique a
  distinção — o mesmo cuidado da regra de desambiguação técnico vs funcional

Regra sobre uso da data de criação na classificação de maturidade:
- Considere a idade do repositório (informada nos dados) ao definir
  "classificacao_maturidade" — um repositório recente com poucas
  funcionalidades é naturalmente "inicial"; o mesmo estado em um
  repositório com anos de existência pode indicar "legado" ou abandono,
  não "inicial"
- Não presuma o motivo (abandono, baixa prioridade, etc) — apenas use a
  idade como um dos fatores objetivos da classificação, junto com o
  nível de documentação e a estrutura encontrada

Regras de formato:
- Retorne APENAS um JSON válido — sem texto antes ou depois, sem blocos
  de código markdown"""


def montar_prompt_checklist_tecnico(repo_data: dict[str, Any]) -> str:
    """
    Monta o prompt human com os dados do repositório para o checklist técnico.

    Args:
        repo_data: dados buscados pelo repository_fetch_node, incluindo
                   os sinais determinísticos coletados pelo client

    Returns:
        String formatada com o conteúdo do repositório e o schema esperado
    """
    manifestos = repo_data.get("manifestos", {})
    manifestos_texto = "\n\n".join(
        f"### {nome}\n```\n{conteudo[:3000]}\n```"
        for nome, conteudo in manifestos.items()
    ) or "(nenhum arquivo de manifesto encontrado)"

    arquivos = repo_data.get("arquivos", [])
    arvore_resumida = "\n".join(f"- {a}" for a in arquivos[:80])

    registros_internos = repo_data.get("registros_internos_detectados", [])
    multi_modulo = repo_data.get("multi_modulo_detectado", False)
    modulos = repo_data.get("modulos_detectados", [])

    return f"""Analise os dados abaixo e responda ao checklist técnico deste componente.

## Repositório
- Nome: {repo_data.get('repo_name')}
- Linguagem principal: {repo_data.get('linguagem_principal') or 'não identificada'}
- Criado em: {repo_data.get('repositorio_criado_em') or 'não informado'}

## Sinais detectados automaticamente (use como pistas para os campos correspondentes)
{_formatar_sinais_deterministicos(repo_data)}

## Arquivos de manifesto
{manifestos_texto}

## Árvore de arquivos (parcial)
{arvore_resumida}

## Checklist técnico — retorne EXATAMENTE este JSON preenchido

{{
  "component_name": "{repo_data.get('repo_name')}",
  "linguagem_principal": "{repo_data.get('linguagem_principal') or 'nao_identificado'}",
  "repositorio_criado_em": {json.dumps(repo_data.get('repositorio_criado_em'), ensure_ascii=False)},
  "tipo_componente": "servico|biblioteca|batch|modulo-compartilhado",
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
    "detalhe": "ex: Kafka, RabbitMQ, SQS — com evidência. Se a única evidência for uso em logging/observabilidade, explique isso aqui e marque como nao_identificado ou parcial, não confirmado"
  }},
  "tecnologia_principal": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "ex: FastAPI, Spring WebFlux, Spring Batch — com evidência"
  }},
  "uso_sicredi_flow": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "cite o domínio interno, namespace ou plugin encontrado como evidência"
  }},
  "armazenamento_objetos": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "identifique o PROVEDOR encontrado — AWS S3, Azure Blob Storage, Google Cloud Storage, MinIO ou outro — com a evidência (SDK/dependência). Nunca assuma que é AWS S3 por padrão"
  }},
  "containerizacao": {{
    "status": "confirmado|parcial|nao_identificado",
    "detalhe": "Dockerfile, docker-compose, ou plugin de build (ex: jib) com a imagem base, se houver"
  }},
  "registros_internos_detectados": {json.dumps(registros_internos, ensure_ascii=False)},
  "multi_modulo_detectado": {str(multi_modulo).lower()},
  "modulos_detectados": {json.dumps(modulos, ensure_ascii=False)},
  "limitacoes_detectadas": ["liste aqui qualquer limitação da sua própria análise, ex: 'projeto multi-módulo, análise cobriu apenas a raiz' — deixe vazio [] se não houver nenhuma"],
  "tags": ["tags geradas com base na análise — mínimo 3"],
  "classificacao_maturidade": "inicial|em-desenvolvimento|maduro|legado",
  "nivel_documentacao": "inexistente|basico|intermediario|completo",
  "resumo_executivo": "resumo de 1-2 frases para exibição no catálogo",
  "sugestoes_melhoria": ["lista de até 3 sugestões objetivas"]
}}"""