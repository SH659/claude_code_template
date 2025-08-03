from datetime import timedelta

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.requests import Request
from starlette.responses import JSONResponse

from auth.services import AuthService
from core.settings import settings

router = APIRouter(route_class=DishkaRoute)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/login")
async def login(auth_service: FromDishka[AuthService], form_data: OAuth2PasswordRequestForm = Depends()):
    """
    PURPOSE: Authenticate user credentials and return access/refresh token pair
    DESCRIPTION: Validates user login credentials and generates JWT tokens for successful authentication.
                 Returns tokens in response body and sets refresh token as HTTP-only cookie.
    ARGUMENTS:
        auth_service: FromDishka[AuthService] - Authentication service for credential validation
        form_data: OAuth2PasswordRequestForm - OAuth2 form containing username and password
    RETURNS: JSONResponse - Access token in body, refresh token in HTTP-only cookie
    CONTRACTS:
        RAISES:
            - InvalidLoginOrPasswordError - when credentials are invalid or user not found
    """
    access_token, refresh_token = await auth_service.login(form_data.username, form_data.password)
    return token_pair_to_response(access_token, refresh_token)


@router.post("/refresh")
async def refresh(request: Request, auth_service: FromDishka[AuthService]):
    """
    PURPOSE: Generate new token pair using refresh token from cookie
    DESCRIPTION: Validates refresh token from HTTP-only cookie and generates new access/refresh token pair
                 for continued authentication. Updates both tokens in response.
    ARGUMENTS:
        request: Request - HTTP request containing refresh token cookie
        auth_service: FromDishka[AuthService] - Authentication service for token operations
    RETURNS: JSONResponse - New access token in body, new refresh token in HTTP-only cookie
    CONTRACTS:
        RAISES:
            - RefreshTokenRequiredError - when refresh token cookie is missing
            - NotAuthorizedError - when refresh token is invalid or expired
    """
    refresh_token = request.cookies.get("refresh_token")
    access_token, refresh_token = await auth_service.refresh(refresh_token)
    return token_pair_to_response(access_token, refresh_token)


def token_pair_to_response(access_token: str, refresh_token: str):
    """
    PURPOSE: Create JSON response with access token and refresh token cookie
    DESCRIPTION: Formats authentication tokens into a standardized response with access token
                 in JSON body and refresh token as secure HTTP-only cookie.
    ARGUMENTS:
        access_token: str - JWT access token for API authentication
        refresh_token: str - JWT refresh token for token renewal
    RETURNS: JSONResponse - Response with access token in body and refresh token cookie
    CONTRACTS:
        POSTCONDITION:
            - Access token included in response body with token type and expiration
            - Refresh token set as HTTP-only cookie with proper security settings
            - Cookie expires according to REFRESH_TOKEN_EXPIRE_MINUTES setting
    """
    response = JSONResponse(
        content={
            'access_token': access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="none",
        path="/",
        max_age=int(timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES).total_seconds()),
    )
    return response
