from fastapi import FastAPI

from core.api_errors import ApiError, static_exception_handler
from qr_code.models import QrCode


class ApiErrors:
    QR_CODE_NOT_FOUND = ApiError(404, "QrCode not found", "qr_code.0001")
    QR_CODE_ALREADY_EXISTS = ApiError(409, "QrCode already exists", "qr_code.0002")


def register_exception_handlers(app: FastAPI):
    static_exception_handler(app, QrCode.NotFoundError, ApiErrors.QR_CODE_NOT_FOUND)
    static_exception_handler(app, QrCode.AlreadyExistError, ApiErrors.QR_CODE_ALREADY_EXISTS)
