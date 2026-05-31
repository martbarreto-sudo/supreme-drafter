"""Regras de negócio do auth — não conhece HTTP, recebe AsyncSession."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus.db.models import User

from .passwords import hash_password, verify_password
from .schemas import SignupIn


class EmailAlreadyExists(Exception):
    pass


class InvalidCredentials(Exception):
    pass


async def create_user(session: AsyncSession, signup: SignupIn) -> User:
    email = signup.email.lower()
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise EmailAlreadyExists()
    user = User(
        email=email,
        name=signup.name,
        oab_numero=signup.oab_numero,
        oab_uf=signup.oab_uf,
        password_hash=hash_password(signup.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    result = await session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        raise InvalidCredentials()
    if not verify_password(password, user.password_hash):
        raise InvalidCredentials()
    return user
