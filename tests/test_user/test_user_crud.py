from typing import Mapping
from uuid import UUID

import pytest
import sqlalchemy


async def test_user_crud_create(user_crud, user_dto):
    id_ = await user_crud.create(user_dto)
    assert isinstance(id_, UUID)


async def test_user_crud_get_by_id(user_crud, user_dto_in_db):
    user = await user_crud.get_by_id(user_dto_in_db['id'])
    assert isinstance(user, Mapping)
    assert user['id'] == user_dto_in_db['id']
    assert user['username'] == user_dto_in_db['username']


@pytest.mark.parametrize('users_number', [2])
async def test_user_crud_get_many_by_ids(user_crud, users_dto_in_db, users_number):
    ids = [dto['id'] for dto in users_dto_in_db]
    users = await user_crud.get_many_by_ids(ids)
    assert len(users) == len(users_dto_in_db)
    users_dto_in_db = sorted(users_dto_in_db, key=lambda x: x['id'])
    for dto, db_dto in zip(users, users_dto_in_db):
        assert isinstance(dto, Mapping)
        assert dto['username'] == db_dto['username']


@pytest.mark.parametrize('users_number', [2])
async def test_user_crud_create_many(user_crud, users_dto, users_number):
    ids = await user_crud.create_many(users_dto)
    assert len(ids) == len(users_dto)


async def test_user_crud_create_and_get(user_crud, user_dto):
    dto = await user_crud.create_and_get(user_dto)
    assert isinstance(dto, Mapping)
    assert dto["id"] == user_dto["id"]
    assert dto["username"] == user_dto["username"]


@pytest.mark.parametrize('users_number', [2])
async def test_user_crud_create_and_get_many(user_crud, users_dto, users_number):
    users = await user_crud.create_and_get_many(users_dto)
    assert len(users) == len(users_dto)
    for dto, payload in zip(users, users_dto):
        assert isinstance(dto, Mapping)
        assert dto['username'] == payload['username']


async def test_user_crud_update(user_crud, user_dto_in_db):
    await user_crud.update({"id": user_dto_in_db['id'], "username": f'{user_dto_in_db["username"]}_updated'})
    user = await user_crud.get_by_id(user_dto_in_db['id'])
    assert user['username'] == f'{user_dto_in_db["username"]}_updated'


@pytest.mark.parametrize('users_number', [2])
async def test_user_crud_update_many(user_crud, users_dto_in_db, users_number):
    payload = [dict(dto) | {"username": f'{dto["username"]}_updated'} for dto in users_dto_in_db]
    await user_crud.update_many(payload)
    users = await user_crud.get_many_by_ids([dto['id'] for dto in users_dto_in_db])
    payload = sorted(payload, key=lambda x: x['id'])
    for dto, payload in zip(users, payload):
        assert dto['username'] == payload['username']


async def test_user_crud_delete(user_crud, user_dto_in_db):
    await user_crud.delete(user_dto_in_db['id'])
    with pytest.raises(sqlalchemy.exc.NoResultFound):
        await user_crud.get_by_id(user_dto_in_db['id'])


@pytest.mark.parametrize('users_number', [2])
async def test_user_crud_delete_many(user_crud, users_dto_in_db, users_number):
    await user_crud.delete_many([dto['id'] for dto in users_dto_in_db])
    users = await user_crud.get_many_by_ids([dto['id'] for dto in users_dto_in_db])
    assert not users


@pytest.mark.parametrize('users_number', [0, 1, 2, 5, 10])
async def test_user_crud_count(user_crud, users_dto_in_db, users_number):
    assert await user_crud.count() == users_number


@pytest.mark.parametrize('users_number', [0, 1, 2, 5, 10])
async def test_user_crud_get_all(user_crud, users_dto_in_db, users_number):
    dtos = await user_crud.get_all()
    assert len(dtos) == users_number
    for dto, dto_in_db in zip(dtos, users_dto_in_db):
        assert dto['username'] == dto_in_db['username']
