from fastapi import FastAPI

from core.api_errors import ApiError, static_exception_handler
from user.models import User


class ApiErrors:
    """
    PURPOSE: Container for user-related API error definitions
    DESCRIPTION: Defines standardized error responses for user management operations including
                 user not found and duplicate user scenarios. Each error contains HTTP status code,
                 user message, and unique error code.
    ATTRIBUTES:
        USER_NOT_FOUND: ApiError - User not found error (404)
        USER_ALREADY_EXIST: ApiError - User already exists error (409)
    """
    USER_NOT_FOUND = ApiError(404, "User not found", "user.0001")
    USER_ALREADY_EXIST = ApiError(409, "User already exists", "user.0002")


def register_exception_handlers(app: FastAPI):
    """
    PURPOSE: Register user exception handlers with FastAPI application
    DESCRIPTION: Maps user domain exceptions to their corresponding API error responses.
                 Sets up automatic exception handling for user-related errors.
    ARGUMENTS:
        app: FastAPI - FastAPI application instance to register handlers with
    RETURNS: None - Side effect of registering exception handlers
    CONTRACTS:
        POSTCONDITION:
            - User.NotFoundError maps to USER_NOT_FOUND (404)
            - User.AlreadyExistError maps to USER_ALREADY_EXIST (409)
    """
    static_exception_handler(app, User.NotFoundError, ApiErrors.USER_NOT_FOUND)
    static_exception_handler(app, User.AlreadyExistError, ApiErrors.USER_ALREADY_EXIST)
