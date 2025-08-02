import dataclasses
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi.encoders import jsonable_encoder
from jwt import DecodeError, ExpiredSignatureError
from passlib.context import CryptContext

from auth.dal import AuthRepo
from auth.errors import InvalidLoginOrPasswordError, NotAuthorizedError, RefreshTokenRequiredError
from auth.models import Auth
from core.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class AccessTokenPayload:
    user_id: UUID
    username: str
    is_admin: bool = False
    token_type: str = "access"


class AuthService:
    def __init__(self, auth_repo: AuthRepo):
        self.auth_repo = auth_repo

    async def create_auth(self, user_id: UUID, username: str, password: str) -> Auth:
        password_hash = self.get_password_hash(password)
        auth = Auth(user_id=user_id, username=username, password_hash=password_hash)
        auth = await self.auth_repo.create_and_get(auth)
        return auth

    async def login(self, username: str, password: str):
        try:
            user = await self.auth_repo.get_by_username(username)
        except Auth.NotFoundError:
            raise InvalidLoginOrPasswordError

        if not self.verify_password(password, user.password_hash):
            raise InvalidLoginOrPasswordError

        token_pair = self.create_access_refresh_token_pair(user)
        return token_pair

    async def refresh(self, refresh_token: str | None):
        if not refresh_token:
            raise RefreshTokenRequiredError
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("token_type") != "refresh":
            raise NotAuthorizedError
        auth_id = payload.get("id")
        if auth_id is None:
            raise NotAuthorizedError
        auth = await self.auth_repo.get_by_id(UUID(auth_id))
        token_pair = self.create_access_refresh_token_pair(auth)
        return token_pair

    def create_access_refresh_token_pair(self, auth: Auth):
        access_token_exp = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = AccessTokenPayload(user_id=auth.user_id, username=auth.username, is_admin=auth.is_admin)
        at_payload = dataclasses.asdict(payload)  # noqa
        access_token = self.create_jwt_token(jsonable_encoder(at_payload), access_token_exp)

        refresh_token_exp = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_token_payload = {"id": str(auth.id), 'token_type': 'refresh'}
        refresh_token = self.create_jwt_token(refresh_token_payload, refresh_token_exp)
        return access_token, refresh_token

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

    @staticmethod
    def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_jwt_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except DecodeError:
            raise NotAuthorizedError
        except ExpiredSignatureError:
            raise NotAuthorizedError
        return payload

    @staticmethod
    def decode_access_token(token: str) -> AccessTokenPayload:
        payload = AuthService.decode_jwt_token(token)
        if payload.get("token_type") != "access":
            raise NotAuthorizedError
        return AccessTokenPayload(user_id=UUID(payload["user_id"]), username=payload["username"])
