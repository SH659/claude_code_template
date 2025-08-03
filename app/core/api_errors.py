from dataclasses import dataclass

from fastapi import FastAPI
from starlette import status
from starlette.responses import JSONResponse

from core.errors import AlreadyExistError, ApplicationError, NotFoundError


@dataclass
class ApiError:
    """
    PURPOSE: Data structure for API error response configuration
    DESCRIPTION: Simple dataclass that encapsulates the components needed for consistent
    API error responses including HTTP status code, user-friendly error message, and
    unique error code for client error identification and handling.
    """
    status_code: int
    error_message: str
    error_code: str

    def json(self):
        """
        PURPOSE: Convert error configuration to JSON-serializable dictionary
        DESCRIPTION: Creates a dictionary containing the error message and error code
        suitable for JSON response bodies. Excludes the HTTP status code as that
        is handled separately in the HTTP response.
        RETURNS: dict - Dictionary with 'error_message' and 'error_code' keys
        CONTRACTS:
            POSTCONDITION:
                - Returned dictionary contains 'error_message' and 'error_code' keys
                - Values match the instance's error_message and error_code attributes
        """
        return {"error_message": self.error_message, "error_code": self.error_code}


class ApiErrors:
    """
    PURPOSE: Centralized collection of predefined API error configurations for common HTTP error scenarios
    DESCRIPTION: Container class that defines standard API error responses used throughout the application.
    Each error includes HTTP status code, user-friendly message, and unique error code for client identification.
    Used by exception handlers to provide consistent error responses across all API endpoints.
    """
    NOT_FOUND = ApiError(status.HTTP_404_NOT_FOUND, "Resource not found", "core.0001")
    ALREADY_EXIST = ApiError(status.HTTP_409_CONFLICT, "Resource already exists", "core.0002")
    INTERNAL_SERVER_ERROR = ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error", "core.0003")


def static_exception_handler(app: FastAPI, exc: type[ApplicationError], api_err: ApiError):
    """
    PURPOSE: Creates and registers an exception handler for a specific exception type with predefined API error response
    DESCRIPTION: Factory function that creates an async exception handler and registers it with the FastAPI application.
    The handler converts application exceptions to standardized JSON responses with appropriate HTTP status codes.
    Returns the created handler function for potential further use.
    ARGUMENTS:
        app: FastAPI - The FastAPI application instance to register the handler with
        exc: type[ApplicationError] - The exception class type to handle
        api_err: ApiError - The predefined API error configuration to use for responses
    RETURNS: function - The created async exception handler function
    CONTRACTS:
        POSTCONDITION:
            - Exception handler is registered with the FastAPI app for the specified exception type
            - Handler converts exceptions to JSON responses with api_err configuration
    """
    @app.exception_handler(exc)
    async def handle_error(request, e):
        """
        PURPOSE: Async exception handler that converts application errors to standardized JSON responses
        DESCRIPTION: Inner handler function created by static_exception_handler that processes caught exceptions
        and returns a JSONResponse with the predefined error configuration. Ignores the specific exception details
        and uses the standard error message and code from the ApiError configuration.
        ARGUMENTS:
            request: Request - The incoming HTTP request that triggered the exception (unused)
            e: ApplicationError - The caught exception instance (unused in response generation)
        RETURNS: JSONResponse - JSON response with error message, error code, and appropriate HTTP status
        """
        return JSONResponse(status_code=api_err.status_code, content=api_err.json())

    return handle_error


def register_exception_handlers(app: FastAPI):
    """
    PURPOSE: Registers all core application exception handlers with the FastAPI application
    DESCRIPTION: Convenience function that sets up exception handling for the three main application error types.
    Maps NotFoundError to 404 responses, AlreadyExistError to 409 conflict responses, and generic
    ApplicationError to 500 internal server error responses. Must be called during application startup.
    ARGUMENTS:
        app: FastAPI - The FastAPI application instance to configure with exception handlers
    CONTRACTS:
        POSTCONDITION:
            - NotFoundError exceptions return 404 responses with "core.0001" error code
            - AlreadyExistError exceptions return 409 responses with "core.0002" error code  
            - ApplicationError exceptions return 500 responses with "core.0003" error code
    """
    static_exception_handler(app, NotFoundError, ApiErrors.NOT_FOUND)
    static_exception_handler(app, AlreadyExistError, ApiErrors.ALREADY_EXIST)
    static_exception_handler(app, ApplicationError, ApiErrors.INTERNAL_SERVER_ERROR)
