from fastapi import FastAPI

from core.api_errors import ApiError, static_exception_handler
from qr_code.models import QrCode


class ApiErrors:
    """
    PURPOSE: Container for QR code-related API error definitions
    DESCRIPTION: Defines standardized error responses for QR code management operations including
                 QR code not found and duplicate QR code scenarios. Each error contains HTTP status code,
                 user message, and unique error code.
    ATTRIBUTES:
        QR_CODE_NOT_FOUND: ApiError - QR code not found error (404)
        QR_CODE_ALREADY_EXISTS: ApiError - QR code already exists error (409)
    """
    QR_CODE_NOT_FOUND = ApiError(404, "QrCode not found", "qr_code.0001")
    QR_CODE_ALREADY_EXISTS = ApiError(409, "QrCode already exists", "qr_code.0002")


def register_exception_handlers(app: FastAPI):
    """
    PURPOSE: Register QR code exception handlers with FastAPI application
    DESCRIPTION: Maps QR code domain exceptions to their corresponding API error responses.
                 Sets up automatic exception handling for QR code-related errors.
    ARGUMENTS:
        app: FastAPI - FastAPI application instance to register handlers with
    RETURNS: None - Side effect of registering exception handlers
    CONTRACTS:
        POSTCONDITION:
            - QrCode.NotFoundError maps to QR_CODE_NOT_FOUND (404)
            - QrCode.AlreadyExistError maps to QR_CODE_ALREADY_EXISTS (409)
    """
    static_exception_handler(app, QrCode.NotFoundError, ApiErrors.QR_CODE_NOT_FOUND)
    static_exception_handler(app, QrCode.AlreadyExistError, ApiErrors.QR_CODE_ALREADY_EXISTS)
