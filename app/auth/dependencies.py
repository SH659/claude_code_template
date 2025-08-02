from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from auth.errors import AdminRightsRequiredError
from auth.services import AccessTokenPayload, AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@inject
async def access_token_payload(
    auth_service: FromDishka[AuthService], token: str = Depends(oauth2_scheme)
) -> AccessTokenPayload:
    payload = auth_service.decode_access_token(token)
    return payload


def logged_in_user_id(payload: AccessTokenPayload = Depends(access_token_payload)) -> UUID:
    return payload.user_id


def logged_in_admin_id(payload: AccessTokenPayload = Depends(access_token_payload)) -> UUID:
    if not payload.is_admin:
        raise AdminRightsRequiredError
    return payload.user_id
