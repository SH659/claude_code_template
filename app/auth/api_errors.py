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
    """
    PURPOSE: Container for authentication-related API error definitions
    DESCRIPTION: Defines standardized error responses for authentication failures including
                 authorization errors, login failures, and admin permission requirements.
                 Each error contains HTTP status code, user message, and unique error code.
    ATTRIBUTES:
        AUTH_ERROR: ApiError - General authentication error (403)
        NOT_AUTHORIZED: ApiError - Authorization token invalid or missing (401)
        REFRESH_TOKEN_REQUIRED: ApiError - Refresh token missing for token renewal (401)
        INVALID_LOGIN_OR_PASSWORD: ApiError - Login credentials validation failed (401)
        ADMIN_RIGHTS_REQUIRED: ApiError - Administrative privileges required (403)
    """
    AUTH_ERROR = ApiError(status.HTTP_403_FORBIDDEN, "Auth error", "auth.0001")
    NOT_AUTHORIZED = ApiError(status.HTTP_401_UNAUTHORIZED, "Not authorized", "auth.0002")
    REFRESH_TOKEN_REQUIRED = ApiError(status.HTTP_401_UNAUTHORIZED, "Refresh token required", "auth.0003")
    INVALID_LOGIN_OR_PASSWORD = ApiError(status.HTTP_401_UNAUTHORIZED, "Invalid login or password", "auth.0004")
    ADMIN_RIGHTS_REQUIRED = ApiError(status.HTTP_403_FORBIDDEN, "Admin rights required", "auth.0005")


def register_exception_handlers(app: FastAPI):
    """
    PURPOSE: Register authentication exception handlers with FastAPI application
    DESCRIPTION: Maps authentication domain exceptions to their corresponding API error responses.
                 Sets up automatic exception handling for all authentication-related errors.
    ARGUMENTS:
        app: FastAPI - FastAPI application instance to register handlers with
    RETURNS: None - Side effect of registering exception handlers
    CONTRACTS:
        POSTCONDITION:
            - AuthError maps to AUTH_ERROR (403)
            - NotAuthorizedError maps to NOT_AUTHORIZED (401)
            - RefreshTokenRequiredError maps to REFRESH_TOKEN_REQUIRED (401)
            - InvalidLoginOrPasswordError maps to INVALID_LOGIN_OR_PASSWORD (401)
            - AdminRightsRequiredError maps to ADMIN_RIGHTS_REQUIRED (403)
    """
    static_exception_handler(app, AuthError, ApiErrors.AUTH_ERROR)
    static_exception_handler(app, NotAuthorizedError, ApiErrors.NOT_AUTHORIZED)
    static_exception_handler(app, RefreshTokenRequiredError, ApiErrors.REFRESH_TOKEN_REQUIRED)
    static_exception_handler(app, InvalidLoginOrPasswordError, ApiErrors.INVALID_LOGIN_OR_PASSWORD)
    static_exception_handler(app, AdminRightsRequiredError, ApiErrors.ADMIN_RIGHTS_REQUIRED)
