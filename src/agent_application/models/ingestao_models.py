"""
Models de Ingestão — Define o formato dos dados que entram
no sistema pelo atlas_inventario_ingestao.

Estes são os contratos entre:
- As origens de dados (APIs externas, CMDB, GitLab)
- O atlas_inventario_ingestao (que normaliza os dados)
- O PostgreSQL (que armazena os dados normalizados)
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class OrigemDados(BaseModel):
    """
    Representa uma origem de dados que será consultada
    durante o processo de ingestão.
    """
    nome: str = Field(
        ...,
        description="Nome da origem",
        examples=["CMDB", "GitLab", "API_Interna"],
    )
    tipo: str = Field(
        ...,
        description="Tipo da origem",
        examples=["api_rest", "banco_dados", "arquivo"],
    )
    url: Optional[str] = Field(
        default=None,
        description="URL da origem — para APIs REST",
    )
    ativa: bool = Field(
        default=True,
        description="Se a origem está disponível para consulta",
    )


class DadoBruto(BaseModel):
    """
    Representa um dado ainda não processado — exatamente
    como veio da origem, antes de qualquer tratamento.
    """
    origem: str = Field(..., description="De onde veio esse dado")
    conteudo: dict = Field(..., description="Dado bruto no formato original")
    coletado_em: datetime = Field(default_factory=datetime.now)
    sucesso_coleta: bool = Field(default=True)
    erro_coleta: Optional[str] = Field(default=None)


class DadoNormalizado(BaseModel):
    """
    Representa um dado após passar pelo processo de
    enriquecimento e normalização.

    Normalizar significa: pegar dados de formatos diferentes
    (CMDB tem um formato, GitLab tem outro) e converter
    todos para um formato único e padronizado.

    Exemplo:
        CMDB retorna:  {"nome": "atlas-chat", "responsavel": {...}}
        GitLab retorna: {"name": "atlas-chat", "maintainer": {...}}

        Normalizado:   {"nome": "atlas-chat", "responsavel": "time-ia"}
    """
    id_unico: str = Field(
        ...,
        description="ID gerado após normalização",
        examples=["norm_COMP001_20260820"],
    )
    origem: str = Field(..., description="Sistema de origem do dado")
    tipo_dado: str = Field(
        ...,
        description="Tipo do dado normalizado",
        examples=["componente", "repositorio", "pipeline"],
    )
    dados: dict = Field(
        ...,
        description="Dado normalizado no formato padrão Atlas",
    )
    qualidade: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Score de qualidade do dado — 1.0 é perfeito",
    )
    normalizado_em: datetime = Field(default_factory=datetime.now)
    versao_schema: str = Field(
        default="1.0",
        description="Versão do schema de normalização usado",
    )


class IngestaoRequest(BaseModel):
    """
    Requisição para iniciar um processo de ingestão de dados.

    Exemplo de uso:
        req = IngestaoRequest(
            origens=["CMDB", "GitLab"],
            tipo_dado="componente",
            forcar_atualizacao=True,
        )
    """
    origens: list[str] = Field(
        ...,
        min_length=1,
        description="Lista de origens para ingerir",
        examples=[["CMDB", "GitLab"]],
    )
    tipo_dado: Optional[str] = Field(
        default=None,
        description="Tipo específico de dado a ingerir",
        examples=["componente", "repositorio", "pipeline"],
    )
    forcar_atualizacao: bool = Field(
        default=False,
        description="Se True, reingere mesmo dados já existentes",
    )
    limite_por_origem: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Máximo de registros por origem",
    )


class IngestaoResponse(BaseModel):
    """
    Resposta após concluir um processo de ingestão.
    """
    sucesso: bool
    origens_processadas: list[str] = []
    total_brutos_coletados: int = 0
    total_normalizados: int = 0
    total_erros: int = 0
    detalhes_por_origem: dict = {}
    iniciado_em: Optional[datetime] = None
    concluido_em: datetime = Field(default_factory=datetime.now)
    erro: Optional[str] = None