import functools
from contextlib import asynccontextmanager, suppress

from dishka import AsyncContainer, Scope, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from starlette.middleware.cors import CORSMiddleware

import auth.api_errors
import auth.errors
import core.api_errors
import core.errors
import qr_code.api_errors
import user.api_errors
from auth.providers import AuthProvider
from auth.router import router as auth_router
from core.database import ConnectionProvider, create_tables
from core.providers import DataclassSerializerProvider
from core.settings import settings
from qr_code.providers import QrCodeProvider
from qr_code.router import router as qr_code_router
from user.models import User
from user.providers import UserProvider
from user.router import router as user_router
from user.services import UserService


@asynccontextmanager
async def lifespan(app: FastAPI, container: AsyncContainer):
    async with container(scope=Scope.REQUEST) as request_container:
        await create_tables(await container.get(AsyncEngine))
        user_service = await request_container.get(UserService)
        session = await request_container.get(AsyncSession)

        if settings.ADMIN_USERNAME is not None and settings.ADMIN_PASSWORD is not None:
            with suppress(User.AlreadyExistError):
                await user_service.register(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)

        await session.commit()

    yield
    await container.close()


# noinspection PyShadowingNames
def create_app():
    app = FastAPI(lifespan=functools.partial(lifespan, container=container))

    app.add_middleware(
        CORSMiddleware,  # noqa
        allow_origins=[],
        allow_origin_regex=r".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(qr_code_router, prefix="/qr_code")
    app.include_router(auth_router, prefix="/auth")
    app.include_router(user_router, prefix="/user")

    auth.api_errors.register_exception_handlers(app)
    user.api_errors.register_exception_handlers(app)
    qr_code.api_errors.register_exception_handlers(app)
    core.api_errors.register_exception_handlers(app)
    return app


container = make_async_container(
    ConnectionProvider(settings.DB_URI),
    DataclassSerializerProvider(),
    UserProvider(),
    AuthProvider(),
    QrCodeProvider(),
)
app = create_app()
setup_dishka(container=container, app=app)
