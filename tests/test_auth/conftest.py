import uuid

import pytest
import pytest_asyncio

from auth.dal import AuthRepo
from auth.models import Auth
from auth.services import AuthService


@pytest_asyncio.fixture
async def auth_service(request_container):
    return await request_container.get(AuthService)


@pytest_asyncio.fixture
async def auth_repo(request_container):
    return await request_container.get(AuthRepo)


@pytest.fixture(scope='session')
def password():
    return 'test_password'


@pytest.fixture(scope='session')
def password_hash(password):
    return AuthService.get_password_hash(password)


@pytest.fixture
def auth(password_hash):
    return Auth(user_id=uuid.uuid4(), username='test_auth_user', password_hash=password_hash)


@pytest_asyncio.fixture
async def auth_in_db(auth_repo, auth, session):
    return await auth_repo.create_and_get(auth)


@pytest.fixture
def token_pair(auth_service, auth_in_db):
    return auth_service.create_access_refresh_token_pair(auth_in_db)


@pytest.fixture
def access_token(token_pair):
    return token_pair[0]


@pytest.fixture
def refresh_token(token_pair):
    return token_pair[1]
