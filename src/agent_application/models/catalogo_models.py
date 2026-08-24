"""
Models do Catálogo — Define o formato dos componentes de TI.

Estes são os contratos entre:
- O CMDB mock (que fornece os dados)
- O atlas_agente_catalogo (que processa e responde)
- O MongoDB (que armazena os resultados)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ResponsavelComponente(BaseModel):
    """
    Representa o responsável por um componente de TI.
    É um sub-modelo usado dentro de ComponenteCatalogo.
    """
    time: str = Field(..., description="Nome do time responsável")
    email: str = Field(..., description="E-mail do time")


class ComponenteCatalogo(BaseModel):
    """
    Representa um componente de TI no catálogo — servidor,
    API, microsserviço, banco de dados, etc.

    Exemplo de uso:
        comp = ComponenteCatalogo(
            id="COMP-001",
            nome="atlas-chat-rag",
            tipo="microsservico",
            descricao="Serviço principal de chat",
            versao="1.2.0",
            linguagem="Python",
            status="ativo",
            responsavel=ResponsavelComponente(
                time="Engenharia de IA",
                email="time-ia@sicredi.com.br"
            ),
        )
    """
    id: str = Field(..., description="ID único no CMDB", examples=["COMP-001"])
    nome: str = Field(..., description="Nome do componente")
    tipo: str = Field(
        ...,
        description="Tipo do componente",
        examples=["microsservico", "backend", "banco_dados", "api"],
    )
    descricao: str = Field(..., description="Descrição do componente")
    versao: Optional[str] = Field(default=None, description="Versão atual")
    linguagem: Optional[str] = Field(default=None, description="Linguagem de programação")
    framework: Optional[str] = Field(default=None, description="Framework utilizado")
    status: str = Field(
        default="ativo",
        description="Status atual",
        examples=["ativo", "em_manutencao", "descontinuado"],
    )
    ambiente: list[str] = Field(
        default=[],
        description="Ambientes onde está deployado",
        examples=[["desenvolvimento", "homologacao", "producao"]],
    )
    responsavel: Optional[ResponsavelComponente] = None
    repositorio: Optional[str] = Field(default=None, description="URL do repositório GitLab")
    dependencias: list[str] = Field(
        default=[],
        description="IDs dos componentes dos quais depende",
    )
    banco_dados: list[str] = Field(
        default=[],
        description="Bancos de dados utilizados",
    )
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None


class BuscaCatalogoRequest(BaseModel):
    """
    Formato da requisição de busca no catálogo.

    Exemplo de uso:
        busca = BuscaCatalogoRequest(
            termo="atlas",
            filtro_status="ativo",
            filtro_tipo="microsservico",
        )
    """
    termo: str = Field(
        ...,
        min_length=1,
        description="Termo de busca — nome ou descrição do componente",
        examples=["atlas-chat", "microsservico python"],
    )
    filtro_status: Optional[str] = Field(
        default=None,
        description="Filtrar por status",
        examples=["ativo", "em_manutencao"],
    )
    filtro_tipo: Optional[str] = Field(
        default=None,
        description="Filtrar por tipo de componente",
        examples=["microsservico", "backend"],
    )
    limite: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Máximo de resultados a retornar",
    )


class BuscaCatalogoResponse(BaseModel):
    """
    Formato da resposta de uma busca no catálogo.
    """
    termo_buscado: str
    total_encontrado: int
    componentes: list[ComponenteCatalogo]
    sucesso: bool = True
    erro: Optional[str] = None
    consultado_em: datetime = Field(default_factory=datetime.now)