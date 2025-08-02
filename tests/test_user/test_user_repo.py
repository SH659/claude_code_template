from uuid import UUID

import pytest

from user.models import User


async def test_user_repo_get_by_id(user_repo, user_dto_in_db):
    u = await user_repo.get_by_id(user_dto_in_db["id"])
    assert isinstance(u, User)
    assert u.id == user_dto_in_db["id"]
    assert u.username == user_dto_in_db["username"]


async def test_user_repo_create(user_repo, user):
    id_ = await user_repo.create(user)
    assert isinstance(id_, UUID)


@pytest.mark.parametrize("users_number", [2])
async def test_user_repo_create_many(user_repo, users, users_number):
    users_ = await user_repo.create_many(users)
    assert len(users_) == len(users)


async def test_user_repo_create_and_get(user_repo, user):
    user_in_db = await user_repo.create_and_get(user)
    assert user_in_db.id == user.id
    assert user_in_db.username == user.username


@pytest.mark.parametrize('users_number', [2])
async def test_user_repo_create_and_get_many(user_repo, users, users_number):
    users_ = await user_repo.create_and_get_many(users)
    assert len(users_) == len(users)
    for users_in_db, payload in zip(users_, users):
        assert users_in_db.username == payload.username


async def test_user_repo_update(user_repo, user_dto_in_db):
    new_data = {**user_dto_in_db, 'username': f"{user_dto_in_db["username"]}_update"}
    await user_repo.update(User(**new_data))
    user = await user_repo.get_by_id(user_dto_in_db['id'])
    assert user.username == f"{user_dto_in_db["username"]}_update"


@pytest.mark.parametrize('users_number', [2])
async def test_user_repo_update_many(user_repo, users_dto_in_db, users_number):
    new_data = [{**dto, 'username': f"{dto["username"]}_update"} for dto in users_dto_in_db]
    payload = [User(**d) for d in new_data]
    payload = sorted(payload, key=lambda x: x.id)
    await user_repo.update_many(payload)

    users = await user_repo.get_many_by_ids([dto['id'] for dto in users_dto_in_db])
    for user, payload in zip(users, payload):
        assert user.username == payload.username


@pytest.mark.parametrize('users_number', [2])
async def test_user_repo_get_many_by_ids(user_repo, users_dto_in_db, users_number):
    ids = [dto['id'] for dto in users_dto_in_db]
    users = await user_repo.get_many_by_ids(ids)
    assert len(users) == len(users_dto_in_db)
    users_dto_in_db = sorted(users_dto_in_db, key=lambda x: x['id'])
    for user, db_dto in zip(users, users_dto_in_db):
        assert isinstance(user, User)
        assert user.username == db_dto['username']


async def test_user_repo_delete(user_repo, user_dto_in_db):
    await user_repo.delete(user_dto_in_db['id'])
    with pytest.raises(User.NotFoundError):
        await user_repo.get_by_id(user_dto_in_db['id'])


@pytest.mark.parametrize('users_number', [2])
async def test_user_repo_delete_many(user_repo, users_dto_in_db, users_number):
    await user_repo.delete_many([dto['id'] for dto in users_dto_in_db])
    users = await user_repo.get_many_by_ids([dto['id'] for dto in users_dto_in_db])
    assert not users


@pytest.mark.parametrize('users_number', [0, 1, 2, 5, 10])
async def test_user_repo_count(user_repo, users_dto_in_db, users_number):
    assert await user_repo.count() == users_number


@pytest.mark.parametrize('users_number', [0, 1, 2, 5, 10])
async def test_user_repo_get_all(user_repo, users_dto_in_db, users_number):
    users = await user_repo.get_all()
    assert len(users) == users_number
    for user, dto_in_db in zip(users, users_dto_in_db):
        assert isinstance(user, User)
        assert user.username == dto_in_db['username']
