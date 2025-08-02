from typing import Any, Mapping, Sequence
from uuid import uuid4

import pytest
import pytest_asyncio

from core.serializer import Serializer
from core.types import DTO
from user.dal import UserCrud, UserRepo
from user.models import User
from user.services import UserService

pytest_plugins = [
    "tests.test_auth.conftest",
]


@pytest_asyncio.fixture
async def user_service(request_container) -> UserService:
    return await request_container.get(UserService)


@pytest_asyncio.fixture
async def user_crud(request_container) -> UserCrud:
    return await request_container.get(UserCrud)


@pytest_asyncio.fixture
async def user_serializer(request_container) -> Serializer[User, DTO]:
    return await request_container.get(Serializer[User, DTO])


@pytest_asyncio.fixture
async def user_repo(request_container) -> UserRepo:
    return await request_container.get(UserRepo)


@pytest.fixture
def users_dto(users_number) -> list[Mapping[str, Any]]:
    return [{"id": uuid4(), "username": f"test_user_{i}"} for i in range(users_number)]


@pytest.fixture
def user_dto(users_dto) -> Mapping[str, Any]:
    assert len(users_dto) == 1
    return users_dto[0]


@pytest.fixture
def users_number() -> int:
    return 1


@pytest_asyncio.fixture
async def user_dto_in_db(user_crud, user_dto) -> Mapping[str, Any]:
    return await user_crud.create_and_get(user_dto)


@pytest_asyncio.fixture
async def users_dto_in_db(user_crud, users_dto) -> Sequence[Mapping[str, Any]]:
    return await user_crud.create_and_get_many(users_dto)


@pytest.fixture
def username():
    return "test_user"


@pytest.fixture
def user(username) -> User:
    return User(id=uuid4(), username=username)


@pytest.fixture
def users(users_number) -> list[User]:
    return [User(id=uuid4(), username=f"test_user_{i}") for i in range(users_number)]
