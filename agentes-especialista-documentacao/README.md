# agentes-especialista-documentacao

Esta pasta preserva o **histórico completo de construção** do `atlas-agente-especialista-documentacao/catalogacao` — o agente responsável por gerar documentação e metadados de componentes da plataforma Atlas (Sicredi) usando LangGraph, LangChain e OpenAI.

Cada subpasta abaixo corresponde a uma **fase de desenvolvimento**, e contém uma cópia completa e funcional do projeto exatamente como estava ao final daquela fase — na mesma estrutura das branches `fase1` a `fase6` deste repositório.

> Para rodar o projeto, use sempre a pasta da **fase mais recente** (`fase6`), que contém a versão mais completa e atualizada.

---

## O que cada pasta contém

### `fase1/` — MongoDB + conexão Python
Estrutura base do projeto com Poetry. Conexão com MongoDB via `pymongo`, com padrão Repository para as collections `componentes_catalogados_metadados` e `documentos_gerados_previas`. Teste simples de inserção e leitura para validar a infraestrutura, sem nenhuma lógica de agente ainda.

### `fase2/` — Grafo LangGraph com nós mockados
Introduz o grafo LangGraph completo: `input_node`, `documentation_node`, `cataloging_node`, `persistence_node`, `supervisor_node`. O estado compartilhado (`DocumentacaoState`) evolui entre os nós. Os dados ainda são mockados — sem chamada real a nenhuma LLM.

### `fase3/` — Integração com LLM OpenAI
Os nós `documentation_node` e `cataloging_node` passam a chamar a OpenAI (`gpt-4o-mini`) via LangChain, usando prompts dedicados na pasta `prompts/`. A documentação passa a ser gerada de forma inteligente e contextualizada; os metadados ganham classificação de maturidade, tags semânticas e sugestões de melhoria geradas pela LLM.

### `fase4/` — Consumer Kafka
Adiciona o módulo `infrastructure/kafka/`, com suporte a três modos de entrada controlados pela variável `INPUT_MODE`: `file` (leitura de um JSON local), `mock_kafka` (simula o comportamento do Kafka usando o JSON local) e `kafka` (consumer real conectado ao broker, escutando o tópico `atlas-processamento-assincrono-dados`).

### `fase5/` — Persistência PostgreSQL
Adiciona um terceiro destino de persistência: a tabela `objetos_gerados_previas` no PostgreSQL, com o pré-cadastro do componente e IDs cruzados apontando para os documentos gerados no MongoDB — criando rastreabilidade entre os dois bancos.

### `fase6/` — Contrato de saída e preparação para versionamento
Adiciona a documentação formal do schema de saída (`docs/CONTRATO_SAIDA.md`) e os campos `versao`, `versao_ativa`, `motivo_reprovacao` e `avaliado_por` na tabela PostgreSQL — preparando a estrutura para suportar múltiplas tentativas de aprovação quando o próximo agente da plataforma (`atlas-agente-especialista-classificacao/pre-curadoria`) for construído e passar a consumir esses dados.

---

## Estrutura interna de cada pasta de fase

Cada pasta segue este padrão (varia conforme a fase, crescendo progressivamente):

```
faseN/
├── docs/                      (a partir da fase6)
├── mock_input/                (a partir da fase2)
├── src/
│   ├── agent_application/
│   │   ├── catalogacao/nodes/
│   │   ├── prompts/
│   │   ├── agent_service.py
│   │   ├── graph.py
│   │   └── state.py
│   ├── infrastructure/
│   │   ├── mongodb/
│   │   ├── postgresql/        (a partir da fase5)
│   │   └── kafka/             (a partir da fase4)
│   ├── main.py
│   └── settings.py
├── .env.example
├── poetry.lock
└── pyproject.toml
```

---

## Como executar qualquer fase

```bash
cd agentes-especialista-documentacao/fase6   # ou a fase desejada

poetry install
cp .env.example .env
# preencher .env com as credenciais necessárias (MongoDB, PostgreSQL, OpenAI)

poetry run python -m src.main
```

---

## Próximos passos da plataforma Atlas

O `atlas-agente-especialista-documentacao/catalogacao` está funcionalmente completo (fase6) e serve de base de dados/contrato para o próximo agente: **`atlas-agente-especialista-classificacao/pre-curadoria`**, responsável por avaliar — com dois juízes LLM, em sequência — a documentação gerada aqui e decidir sua aprovação ou reprovação.