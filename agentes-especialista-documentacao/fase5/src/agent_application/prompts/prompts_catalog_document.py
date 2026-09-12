"""
agents/documentacao/prompts.py
--------------------------------
Prompts utilizados pela LLM OpenAI nos nós de geração.

Por que separar os prompts do código dos nós?
  Os prompts são o "roteiro" que a LLM segue. Eles mudam com
  frequência durante o desenvolvimento e ajuste fino do agente.
  Mantê-los aqui permite:
    - Ajustar o comportamento da LLM sem tocar na lógica dos nós
    - Versionar e comparar prompts diferentes facilmente
    - Testar prompts isoladamente sem executar o grafo inteiro
    - Manter os nós limpos e focados na orquestração

Estrutura de cada prompt:
  SYSTEM: define o papel e as regras que a LLM deve seguir
  HUMAN:  fornece os dados concretos e o que deve ser gerado

Temperatura recomendada: 0.3
  Documentação técnica precisa de consistência, não criatividade.
  Valores baixos (0.0-0.4) produzem respostas mais previsíveis.
"""

import json
from typing import Any


# ===========================================================
# PROMPT: DOCUMENTAÇÃO
# Usado pelo documentation_node
# ===========================================================

SYSTEM_DOCUMENTACAO = """Você é um especialista em documentação técnica de software, \
com profundo conhecimento em arquitetura de sistemas, APIs e boas práticas de engenharia.

Seu papel é analisar os dados de um componente de software e gerar uma prévia de \
documentação clara, objetiva e tecnicamente precisa.

Regras obrigatórias:
- Escreva em português brasileiro formal e técnico
- Seja objetivo e direto — evite textos genéricos ou redundantes
- Baseie-se APENAS nos dados fornecidos — não invente informações
- Use linguagem adequada para desenvolvedores e arquitetos de software
- Estruture o conteúdo de forma hierárquica e legível
- Destaque informações críticas como criticidade, ambiente e responsáveis"""


def montar_prompt_documentacao(json_entrada: dict[str, Any]) -> str:
    """
    Monta o prompt human com os dados do componente para geração de documentação.

    Converte o JSON do inventário em um prompt estruturado que
    a LLM usará para gerar a prévia de documentação.

    Args:
        json_entrada: JSON normalizado do inventário

    Returns:
        String formatada com os dados do componente para o prompt
    """
    application = json_entrada.get("application", {})
    team = json_entrada.get("team", {})
    people = json_entrada.get("people", {})
    devconsole = json_entrada.get("devconsole", {})
    gitlab = json_entrada.get("gitlab", {})
    processing = json_entrada.get("processing", {})

    return f"""Analise os dados abaixo e gere uma prévia de documentação técnica completa \
para este componente de software.

## Dados do Componente

**Identificação:**
- Nome do componente: {application.get('component_name')}
- Nome da aplicação: {application.get('application_name')}
- Tipo: {application.get('tipo_aplicacao')}
- Categoria: {application.get('categoria_aplicacao')}
- Versão atual: {devconsole.get('version')}
- Criticidade: {devconsole.get('criticality')}
- Status: {application.get('status_aplicacao')}
- Ambiente: {application.get('environment')}
- Cloud Provider: {devconsole.get('cloud_provider')}

**Time Responsável:**
- Time: {team.get('time_responsavel')}
- Projeto: {team.get('projeto')}
- Tribo: {team.get('tribo')}
- Tech Leads: {', '.join(people.get('tech_leads', []))}
- Arquitetos: {', '.join(people.get('arquitetos', []))}
- Aprovadores: {', '.join(people.get('aprovadores', []))}
- Desenvolvedores: {', '.join(people.get('desenvolvedores', []))}
- QA: {', '.join(people.get('qa', []))}

**Repositório:**
- Repositório: {application.get('repository')}
- Branch padrão: {application.get('default_branch')}
- Total de branches: {gitlab.get('branch_count')}
- Arquivos detectados: {', '.join(gitlab.get('repository_tree', []))}

**Evento de origem:**
- ID do evento: {processing.get('event_id')}
- Tipo: {processing.get('event_type')}
- Data: {processing.get('event_date')}

## O que gerar

Produza uma prévia de documentação com as seguintes seções:

1. **Título** — nome técnico do componente (uma linha)
2. **Descrição geral** — o que é este componente e qual seu papel no ecossistema (2-3 parágrafos)
3. **Informações técnicas** — tipo, categoria, versão, ambiente, criticidade
4. **Equipe responsável** — quem mantém e é responsável pelo componente
5. **Repositório** — localização, branch padrão e estrutura detectada
6. **Observações** — pontos relevantes detectados nos dados fornecidos

Responda em texto corrido e bem formatado, sem blocos de código JSON."""


# ===========================================================
# PROMPT: CATALOGAÇÃO (retorna JSON estruturado)
# Usado pelo cataloging_node
# ===========================================================

SYSTEM_CATALOGACAO = """Você é um especialista em catalogação e classificação de \
componentes de software em grandes organizações de tecnologia.

Seu papel é analisar os dados de um componente e extrair/gerar metadados \
estruturados para um catálogo interno de componentes.

Regras obrigatórias:
- Retorne APENAS um objeto JSON válido — sem texto antes ou depois
- Não use blocos de código markdown (sem ```json)
- Baseie-se nos dados fornecidos e use seu conhecimento para enriquecer
- Seja preciso nas classificações — evite categorias genéricas demais
- Tags devem ser em minúsculas, sem espaços (use hífens)
- Strings em português brasileiro"""


def montar_prompt_catalogacao(json_entrada: dict[str, Any]) -> str:
    """
    Monta o prompt human com os dados do componente para geração de metadados.

    Solicita à LLM que retorne um JSON estruturado com metadados
    enriquecidos para o catálogo de componentes.

    Args:
        json_entrada: JSON normalizado do inventário

    Returns:
        String formatada com os dados e schema esperado de retorno
    """
    return f"""Analise os dados abaixo e gere os metadados estruturados para \
catalogação deste componente.

## Dados de entrada
{json.dumps(json_entrada, ensure_ascii=False, indent=2)}

## Schema de retorno esperado

Retorne EXATAMENTE este JSON preenchido (sem texto adicional):

{{
  "component_name": "nome do componente",
  "application_name": "nome da aplicação",
  "team_id": "id do time",
  "time_responsavel": "nome do time",
  "projeto": "nome do projeto",
  "tribo": "nome da tribo",
  "tipo_aplicacao": "tipo extraído dos dados",
  "categoria_aplicacao": "categoria extraída",
  "criticidade": "criticidade extraída",
  "cloud_provider": "provider extraído",
  "environment": "ambiente extraído",
  "status_aplicacao": "status extraído",
  "version": "versão extraída",
  "repository": "repositório extraído",
  "default_branch": "branch padrão",
  "branch_count": 0,
  "tech_leads": ["lista de tech leads"],
  "aprovadores": ["lista de aprovadores"],
  "arquitetos": ["lista de arquitetos"],
  "tags": ["tags geradas pela LLM baseadas nos dados — mínimo 5"],
  "classificacao_maturidade": "inicial|em-desenvolvimento|maduro|legado",
  "nivel_documentacao": "inexistente|basico|intermediario|completo",
  "resumo_executivo": "resumo de 1-2 frases para exibição no catálogo",
  "sugestoes_melhoria": ["lista de até 3 sugestões objetivas"],
  "event_id": "id do evento de origem",
  "tipo_evento": "tipo do evento"
}}"""