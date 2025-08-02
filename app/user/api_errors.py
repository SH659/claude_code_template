from fastapi import FastAPI

from core.api_errors import ApiError, static_exception_handler
from user.models import User


class ApiErrors:
    USER_NOT_FOUND = ApiError(404, "User not found", "user.0001")
    USER_ALREADY_EXIST = ApiError(409, "User already exists", "user.0002")


def register_exception_handlers(app: FastAPI):
    static_exception_handler(app, User.NotFoundError, ApiErrors.USER_NOT_FOUND)
    static_exception_handler(app, User.AlreadyExistError, ApiErrors.USER_ALREADY_EXIST)
