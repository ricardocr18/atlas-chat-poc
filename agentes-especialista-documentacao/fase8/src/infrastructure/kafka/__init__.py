"""
infrastructure/kafka
----------------------
Módulo de infraestrutura Kafka.

Expõe apenas o necessário para o restante da aplicação:
  - iniciar_consumer: ponto de entrada do consumer
"""

from src.infrastructure.kafka.consumer import iniciar_consumer

__all__ = ["iniciar_consumer"]