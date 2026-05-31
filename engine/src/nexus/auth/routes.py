"""Rotas /auth — signup, login, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.db.models import User
from nexus.db.session import get_session

from .deps import get_current_user
from .jwt import create_access_token
from .schemas import LoginIn, SignupIn, TokenOut, UserOut
from .service import EmailAlreadyExists, InvalidCredentials, authenticate, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        oab_numero=user.oab_numero,
        oab_uf=user.oab_uf,
        oab_status=user.oab_status.value,
    )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupIn,
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    try:
        user = await create_user(session, payload)
    except EmailAlreadyExists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email já cadastrado")
    return _to_user_out(user)


@router.post("/login", response_model=TokenOut)
async def login(
    payload: LoginIn,
    session: AsyncSession = Depends(get_session),
) -> TokenOut:
    try:
        user = await authenticate(session, payload.email, payload.password)
    except InvalidCredentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha inválidos")
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return _to_user_out(user)
