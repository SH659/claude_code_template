from fastapi import FastAPI
from starlette import status

from auth.errors import (
    AdminRightsRequiredError,
    AuthError,
    InvalidLoginOrPasswordError,
    NotAuthorizedError,
    RefreshTokenRequiredError,
)
from core.api_errors import ApiError, static_exception_handler


class ApiErrors:
    AUTH_ERROR = ApiError(status.HTTP_403_FORBIDDEN, "Auth error", "auth.0001")
    NOT_AUTHORIZED = ApiError(status.HTTP_401_UNAUTHORIZED, "Not authorized", "auth.0002")
    REFRESH_TOKEN_REQUIRED = ApiError(status.HTTP_401_UNAUTHORIZED, "Refresh token required", "auth.0003")
    INVALID_LOGIN_OR_PASSWORD = ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid login or password", "auth.0004")
    ADMIN_RIGHTS_REQUIRED = ApiError(status.HTTP_403_FORBIDDEN, "Admin rights required", "auth.0005")


def register_exception_handlers(app: FastAPI):
    static_exception_handler(app, AuthError, ApiErrors.AUTH_ERROR)
    static_exception_handler(app, NotAuthorizedError, ApiErrors.NOT_AUTHORIZED)
    static_exception_handler(app, RefreshTokenRequiredError, ApiErrors.REFRESH_TOKEN_REQUIRED)
    static_exception_handler(app, InvalidLoginOrPasswordError, ApiErrors.INVALID_LOGIN_OR_PASSWORD)
    static_exception_handler(app, AdminRightsRequiredError, ApiErrors.ADMIN_RIGHTS_REQUIRED)
