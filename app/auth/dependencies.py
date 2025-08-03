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
    """
    PURPOSE: Extract user ID from authenticated request
    DESCRIPTION: Dependency function that extracts the user ID from a validated access token payload.
                 Used to identify the current authenticated user in API endpoints.
    ARGUMENTS:
        payload: AccessTokenPayload - Validated access token payload containing user information
    RETURNS: UUID - User ID of the authenticated user
    """
    return payload.user_id


def logged_in_admin_id(payload: AccessTokenPayload = Depends(access_token_payload)) -> UUID:
    """
    PURPOSE: Extract admin user ID from authenticated request with permission check
    DESCRIPTION: Dependency function that extracts user ID from access token payload after verifying
                 the user has administrative privileges. Used for admin-only endpoints.
    ARGUMENTS:
        payload: AccessTokenPayload - Validated access token payload containing user information
    RETURNS: UUID - User ID of the authenticated admin user
    CONTRACTS:
        PRECONDITION:
            - payload.is_admin is True
        RAISES:
            - AdminRightsRequiredError - when user lacks administrative privileges
    """
    if not payload.is_admin:
        raise AdminRightsRequiredError
    return payload.user_id
