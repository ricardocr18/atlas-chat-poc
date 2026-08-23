"""
Mock do WSO2 — Simula o gateway de autenticação do Sicredi.

O WSO2 real é responsável por:
- Validar se o usuário tem permissão para usar o sistema
- Gerar tokens de acesso (JWT)
- Controlar quais APIs cada usuário pode chamar

Neste mock, simulamos essas respostas sem precisar do WSO2 real.
"""

from datetime import datetime, timedelta
from typing import Optional


# Usuários simulados que "existem" no WSO2 mock
USUARIOS_MOCK = {
    "user_atlas_01": {
        "nome": "Ricardo Ribeiro",
        "email": "ricardo@sicredi.com.br",
        "perfil": "desenvolvedor",
        "ativo": True,
    },
    "user_atlas_02": {
        "nome": "Programador B",
        "email": "prog_b@sicredi.com.br",
        "perfil": "analista",
        "ativo": True,
    },
    "user_inativo": {
        "nome": "Usuário Inativo",
        "email": "inativo@sicredi.com.br",
        "perfil": "visitante",
        "ativo": False,
    },
}


def autenticar_usuario(user_id: str, senha: str) -> dict:
    """
    Simula a autenticação de um usuário no WSO2.

    No WSO2 real: faria uma chamada HTTP para o servidor de identidade.
    No mock: apenas verifica se o usuário existe na nossa lista e
             se a senha é "senha_mock" (simplificação para testes).

    Retorna um token JWT simulado se autenticado com sucesso.
    """
    usuario = USUARIOS_MOCK.get(user_id)

    # Verifica se usuário existe
    if not usuario:
        return {
            "sucesso": False,
            "erro": "Usuário não encontrado",
            "codigo": 404,
        }

    # Verifica se usuário está ativo
    if not usuario["ativo"]:
        return {
            "sucesso": False,
            "erro": "Usuário inativo no sistema",
            "codigo": 403,
        }

    # Verifica senha (no mock, a senha sempre é "senha_mock")
    if senha != "senha_mock":
        return {
            "sucesso": False,
            "erro": "Senha incorreta",
            "codigo": 401,
        }

    # Autenticação bem-sucedida — gera token simulado
    expiracao = datetime.now() + timedelta(hours=8)

    return {
        "sucesso": True,
        "token": f"mock_jwt_token_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "tipo": "Bearer",
        "expira_em": expiracao.isoformat(),
        "usuario": {
            "id": user_id,
            "nome": usuario["nome"],
            "email": usuario["email"],
            "perfil": usuario["perfil"],
        },
    }


def validar_token(token: str) -> dict:
    """
    Simula a validação de um token JWT pelo WSO2.

    No WSO2 real: verificaria a assinatura criptográfica do token.
    No mock: apenas verifica se o token começa com "mock_jwt_token_".
    """
    if token.startswith("mock_jwt_token_"):
        return {
            "valido": True,
            "mensagem": "Token válido",
        }

    return {
        "valido": False,
        "mensagem": "Token inválido ou expirado",
    }


def listar_permissoes(user_id: str) -> dict:
    """
    Simula a consulta de permissões de um usuário no WSO2.

    Retorna quais APIs e recursos o usuário pode acessar.
    """
    permissoes_por_perfil = {
        "desenvolvedor": [
            "atlas.chat.read",
            "atlas.chat.write",
            "atlas.catalogo.read",
            "atlas.catalogo.write",
            "atlas.jira.create",
            "atlas.gitlab.read",
        ],
        "analista": [
            "atlas.chat.read",
            "atlas.chat.write",
            "atlas.catalogo.read",
            "atlas.jira.create",
        ],
        "visitante": [
            "atlas.chat.read",
        ],
    }

    usuario = USUARIOS_MOCK.get(user_id)
    if not usuario:
        return {"erro": "Usuário não encontrado"}

    perfil = usuario["perfil"]
    return {
        "user_id": user_id,
        "perfil": perfil,
        "permissoes": permissoes_por_perfil.get(perfil, []),
    }