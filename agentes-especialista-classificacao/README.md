# atlas-classificacao-agent

Agente especialista em classificação e pré-curadoria da solução Atlas.

## Fase atual: Fase 1 — Fundação e conectividade básica

Nesta fase, o agente ainda não tem grafo nem chama LLM. O único objetivo é
confirmar que ele consegue se conectar corretamente aos 5 pontos de dado
que vai precisar:

1. MongoDB `documentos_gerados_previas` (leitura — do `atlas-documentacao-agent`)
2. MongoDB `componentes_catalogados_metadados` (leitura — do `atlas-documentacao-agent`)
3. MongoDB `curadoria_controle_metadados` (escrita — próprio)
4. MongoDB `documentacao_avaliada` (escrita — próprio)
5. PostgreSQL `objetos_gerados_previas` (leitura e escrita — compartilhado)

## Como rodar

1. Instale as dependências:
   ```
   poetry install
   ```

2. Copie o `.env.example` para `.env` e preencha com os dados do seu
   MongoDB (Compass) e PostgreSQL (pgAdmin) locais:
   ```
   cp .env.example .env
   ```

3. Rode a verificação de conectividade:
   ```
   poetry run python -m src.main
   ```

Um resultado `[OK]` para as duas seções (MongoDB e PostgreSQL) confirma que
a Fase 1 está concluída.

## Estrutura do projeto

```
src/
├── application/
│   └── settings.py          # configurações via .env (pydantic-settings)
├── infrastructure/
│   ├── mongodb/
│   │   └── client.py         # conexão às 4 collections Mongo
│   └── postgresql/
│       └── client.py         # conexão à tabela Postgres compartilhada
└── main.py                    # script de verificação de conectividade
```

> Nota: esta estrutura espelha o scaffold oficial `atlas-classificacao-agent`
> do GitLab da Sicredi, adaptada para rodar localmente com `pydantic-settings`
> lendo `.env`, em vez de `engineering_commons` (Vault/Consul), que só existe
> dentro da rede da Sicredi.
