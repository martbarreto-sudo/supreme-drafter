"""Pydantic schemas para o fluxo de auth.

Validação de OAB no signup: número 3-7 dígitos, UF 2 maiúsculas. Não
substitui a validação real contra a base do CNA-OAB (fase posterior);
serve só para barrar lixo evidente.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints

OABNumero = Annotated[str, StringConstraints(pattern=r"^\d{3,7}$")]
UF = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
Senha = Annotated[str, StringConstraints(min_length=8, max_length=72)]
Nome = Annotated[str, StringConstraints(min_length=2, max_length=200)]


class SignupIn(BaseModel):
    email: EmailStr
    name: Nome
    oab_numero: OABNumero
    oab_uf: UF
    password: Senha
    aceito_tos: bool  # deve ser True; False → 422
    tos_version: int  # deve coincidir com TOS_VERSION_ATUAL; outras → 409


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    oab_numero: str
    oab_uf: str
    oab_status: str
