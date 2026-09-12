# atlas-chat-poc

POC de sistema multi-agente com LangGraph, LangChain e FastAPI, desenvolvido para a plataforma **Atlas** da Sicredi.

## Estrutura do repositório

### `agentes-especialista-documentacao/`

Histórico completo de construção do **atlas-agente-especialista-documentacao/catalogacao** — agente responsável por gerar documentação e metadados de componentes de software usando LangGraph, LangChain e OpenAI, persistindo os resultados em MongoDB e PostgreSQL.

Organizado em subpastas por fase de desenvolvimento, cada uma com uma cópia completa e funcional do projeto:

| Pasta | Conteúdo |
|---|---|
| `fase1/` | Estrutura base do projeto + conexão com MongoDB |
| `fase2/` | Grafo LangGraph com nós mockados (sem LLM) |
| `fase3/` | Integração real com LLM OpenAI para geração de documentação e metadados |
| `fase4/` | Consumer Kafka (modos file, mock_kafka e kafka real) |
| `fase5/` | Persistência de dados no PostgreSQL |
| `fase6/` | Contrato de saída documentado + preparação para versionamento |

Para rodar o projeto, use sempre a pasta da fase mais recente (`fase6/`). Detalhes de cada fase estão em [`agentes-especialista-documentacao/README.md`](./agentes-especialista-documentacao/README.md).
