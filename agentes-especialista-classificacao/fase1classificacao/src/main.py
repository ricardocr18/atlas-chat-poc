"""Ponto de entrada da Fase 1 — verificacao de conectividade basica.

Nao ha grafo, nao ha LLM ainda nesta fase. O unico objetivo aqui e'
confirmar que o agente consegue se conectar corretamente aos 5 pontos
de dado que ele vai precisar:

  1. MongoDB - documentos_gerados_previas          (leitura)
  2. MongoDB - componentes_catalogados_metadados    (leitura)
  3. MongoDB - curadoria_controle_metadados         (escrita, propria)
  4. MongoDB - documentacao_avaliada                (escrita, propria)
  5. PostgreSQL - objetos_gerados_previas           (leitura + escrita)
"""

from __future__ import annotations

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def _imprimir_resultado(nome: str, resultado: dict) -> bool:
    status = "OK" if resultado["ok"] else "FALHOU"
    print(f"\n[{status}] {nome}")
    for chave, valor in resultado["detalhes"].items():
        print(f"    - {chave}: {valor}")
    return resultado["ok"]


def main() -> None:
    print("=" * 70)
    print("atlas-classificacao-agent — Fase 1: verificacao de conectividade")
    print("=" * 70)

    from fase1classificacao.src.infrastructure.mongodb.client import check_mongo_connection
    from fase1classificacao.src.infrastructure.postgresql.client import check_postgres_connection

    mongo_ok = _imprimir_resultado("MongoDB (4 collections)", check_mongo_connection())
    postgres_ok = _imprimir_resultado("PostgreSQL (objetos_gerados_previas)", check_postgres_connection())

    print("\n" + "=" * 70)
    if mongo_ok and postgres_ok:
        print("RESULTADO: todas as conexoes funcionando. Fase 1 concluida.")
        sys.exit(0)
    else:
        print("RESULTADO: uma ou mais conexoes falharam. Revise o .env e "
              "confirme que o MongoDB e o PostgreSQL locais estao rodando.")
        sys.exit(1)


if __name__ == "__main__":
    main()
