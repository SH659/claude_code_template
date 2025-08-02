from dataclasses import dataclass

from fastapi import FastAPI
from starlette import status
from starlette.responses import JSONResponse

from core.errors import AlreadyExistError, ApplicationError, NotFoundError


@dataclass
class ApiError:
    status_code: int
    error_message: str
    error_code: str

    def json(self):
        return {"error_message": self.error_message, "error_code": self.error_code}


class ApiErrors:
    NOT_FOUND = ApiError(status.HTTP_404_NOT_FOUND, "Resource not found", "core.0001")
    ALREADY_EXIST = ApiError(status.HTTP_409_CONFLICT, "Resource already exists", "core.0002")
    INTERNAL_SERVER_ERROR = ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error", "core.0003")


def static_exception_handler(app: FastAPI, exc: type[ApplicationError], api_err: ApiError):
    @app.exception_handler(exc)
    async def handle_error(request, e):
        return JSONResponse(status_code=api_err.status_code, content=api_err.json())

    return handle_error


def register_exception_handlers(app: FastAPI):
    static_exception_handler(app, NotFoundError, ApiErrors.NOT_FOUND)
    static_exception_handler(app, AlreadyExistError, ApiErrors.ALREADY_EXIST)
    static_exception_handler(app, ApplicationError, ApiErrors.INTERNAL_SERVER_ERROR)
