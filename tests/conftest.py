import pytest
import pytest_asyncio
from dishka import Provider, decorate, make_async_container
from dishka.integrations.fastapi import setup_dishka
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from starlette.testclient import TestClient

from auth.providers import AuthProvider
from core.database import ConnectionProvider, create_tables
from core.providers import DataclassSerializerProvider
from qr_code.providers import QrCodeProvider
from user.providers import UserProvider


class DatabaseWithTablesProvider(Provider):
    @decorate
    async def create_tables_on_connection(self, engine: AsyncEngine) -> AsyncEngine:
        await create_tables(engine)
        return engine


@pytest.fixture
async def container():
    container = make_async_container(
        ConnectionProvider("sqlite+aiosqlite:///:memory:"),
        DatabaseWithTablesProvider(),
        DataclassSerializerProvider(),
        UserProvider(),
        AuthProvider(),
        QrCodeProvider(),
    )
    yield container
    await container.close()


@pytest_asyncio.fixture
async def request_container(container):
    async with container() as request_container:
        yield request_container


@pytest_asyncio.fixture
async def session(request_container) -> AsyncSession:
    return await request_container.get(AsyncSession)


@pytest.fixture
def app(container):
    from main import create_app

    app = create_app()
    setup_dishka(container=container, app=app)
    return app


@pytest.fixture
def test_client(app):
    with TestClient(app) as client:
        yield client
