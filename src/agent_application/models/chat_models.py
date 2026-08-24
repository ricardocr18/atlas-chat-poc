"""
Models do Chat — Define o formato de entrada e saída do chat principal.

Estes são os "contratos" entre:
- O usuário (que envia uma mensagem)
- O atlas_chat_rag (que processa e responde)

Usando Pydantic, garantimos que os dados sempre chegam
no formato correto — se algo estiver errado, o erro
aparece imediatamente com uma mensagem clara.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Formato da mensagem que o usuário envia para o chat.

    Exemplo de uso:
        request = ChatRequest(
            mensagem="Quais componentes estão ativos no catálogo?",
            user_id="user_atlas_01",
        )
    """
    mensagem: str = Field(
        ...,                          # ... significa obrigatório
        min_length=1,
        max_length=2000,
        description="Mensagem enviada pelo usuário",
        examples=["Quais componentes estão ativos no catálogo?"],
    )
    user_id: str = Field(
        ...,
        description="ID do usuário autenticado no WSO2",
        examples=["user_atlas_01"],
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID da sessão — se nulo, cria uma nova sessão",
        examples=["sess_abc123"],
    )
    contexto_extra: Optional[dict] = Field(
        default=None,
        description="Informações adicionais opcionais para o agente",
    )


class FonteConsultada(BaseModel):
    """
    Representa uma fonte de dados que o agente consultou
    para montar a resposta — CMDB, GitLab, Jira, etc.
    """
    sistema: str = Field(
        ...,
        description="Sistema consultado",
        examples=["CMDB", "GitLab", "Jira"],
    )
    dados_encontrados: bool = Field(
        ...,
        description="Se encontrou dados relevantes nessa fonte",
    )
    resumo: Optional[str] = Field(
        default=None,
        description="Resumo do que foi encontrado nessa fonte",
    )


class ChatResponse(BaseModel):
    """
    Formato da resposta que o chat devolve ao usuário.

    Exemplo de resposta:
        ChatResponse(
            resposta="Encontrei 3 componentes ativos no catálogo...",
            session_id="sess_abc123",
            intencao_detectada="consulta_catalogo",
            fontes_consultadas=[
                FonteConsultada(sistema="CMDB", dados_encontrados=True)
            ],
            sucesso=True,
        )
    """
    resposta: str = Field(
        ...,
        description="Resposta gerada pelo agente para o usuário",
    )
    session_id: str = Field(
        ...,
        description="ID da sessão — usar nas próximas mensagens",
    )
    intencao_detectada: Optional[str] = Field(
        default=None,
        description="Intenção identificada pelo classificador",
        examples=["consulta_catalogo", "abrir_card_jira", "consulta_gitlab"],
    )
    fontes_consultadas: list[FonteConsultada] = Field(
        default=[],
        description="Lista de sistemas que o agente consultou",
    )
    tempo_processamento_ms: Optional[int] = Field(
        default=None,
        description="Tempo de processamento em milissegundos",
    )
    sucesso: bool = Field(
        default=True,
        description="Se o processamento foi bem-sucedido",
    )
    erro: Optional[str] = Field(
        default=None,
        description="Mensagem de erro — preenchida apenas se sucesso=False",
    )
    criado_em: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp da resposta",
    )


class MensagemHistorico(BaseModel):
    """
    Representa uma mensagem no histórico da conversa.
    Usada para montar o contexto de conversa no PostgreSQL.
    """
    role: str = Field(
        ...,
        description="Quem enviou: 'user' ou 'assistant'",
        examples=["user", "assistant"],
    )
    content: str = Field(
        ...,
        description="Conteúdo da mensagem",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
    )