import pytest

from user.models import User


def test_user_serializer_serialize(user_serializer, user):
    user_dto = user_serializer.serialize(user)
    assert user_dto['id'] == user.id
    assert user_dto['username'] == user.username


def test_user_serializer_deserialize(user_serializer, user_dto):
    user = user_serializer.deserialize(user_dto)
    assert isinstance(user, User)
    assert user.id == user_dto['id']
    assert user.username == user_dto['username']


@pytest.mark.parametrize('users_number', [2])
def test_user_serializer_flat_serialize(user_serializer, users, users_number):
    users_dto = user_serializer.flat.serialize(users)
    assert len(users_dto) == len(users)
    for u, dto in zip(users, users_dto):
        assert dto['id'] == u.id
        assert dto['username'] == u.username


@pytest.mark.parametrize('users_number', [2])
def test_user_serializer_flat_deserialize(user_serializer, users_dto, users_number):
    users = user_serializer.flat.deserialize(users_dto)
    assert len(users) == len(users_dto)
    for u, dto in zip(users, users_dto):
        assert isinstance(u, User)
        assert u.id == dto['id']
        assert u.username == dto['username']
