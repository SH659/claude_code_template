import functools
import inspect
from typing import Sequence, Type

import sqlalchemy

from core.crud_base import CrudBase
from core.models import Model
from core.serializer import Serializer
from core.types import DTO


def handle_exceptions(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except sqlalchemy.exc.NoResultFound:
            raise self.entity_cls.NotFoundError
        except sqlalchemy.exc.IntegrityError as e:
            error_message = str(e)
            match error_message:
                case msg if msg.startswith('(sqlite3.IntegrityError) UNIQUE constraint failed:'):
                    raise self.entity_cls.AlreadyExistError
                case msg if 'duplicate key value violates unique constraint' in msg:
                    raise self.entity_cls.AlreadyExistError
                case _:
                    raise

    wrapper.__handle_exceptions__ = True
    return wrapper


class RepoMeta(type):
    def __new__(mcs, name, bases, namespace):
        for attr_name, attr_value in namespace.items():
            if inspect.iscoroutinefunction(attr_value) and getattr(attr_value, '__handle_exceptions__', False) is False:
                namespace[attr_name] = handle_exceptions(attr_value)
        return super().__new__(mcs, name, bases, namespace)


class RepoBase[ID, MODEL: Model](metaclass=RepoMeta):
    def __init__(self, crud: CrudBase[ID, DTO], serializer: Serializer[MODEL, DTO], entity_cls: Type[MODEL]):
        self.crud = crud
        self.serializer = serializer
        self.entity_cls = entity_cls

    async def get_by_id(self, id_: ID) -> MODEL:
        dto = await self.crud.get_by_id(id_)
        return self.serializer.deserialize(dto)

    async def create(self, model: MODEL) -> ID:
        dto = self.serializer.serialize(model)
        return await self.crud.create(dto)

    async def create_and_get(self, model: MODEL) -> MODEL:
        dto = self.serializer.serialize(model)
        dto = await self.crud.create_and_get(dto)
        return self.serializer.deserialize(dto)

    async def create_many(self, models: Sequence[MODEL]) -> list[ID]:
        dtos = self.serializer.flat.serialize(models)
        return await self.crud.create_many(dtos)

    async def create_and_get_many(self, models: Sequence[MODEL]) -> Sequence[MODEL]:
        dtos = self.serializer.flat.serialize(models)
        dtos = await self.crud.create_and_get_many(dtos)
        return self.serializer.flat.deserialize(dtos)

    async def update(self, values: MODEL) -> None:
        dto = self.serializer.serialize(values)
        await self.crud.update(dto)

    async def update_and_get(self, values: MODEL) -> MODEL:
        dto = self.serializer.serialize(values)
        dto = await self.crud.update_and_get(dto)
        return self.serializer.deserialize(dto)

    async def update_many(self, models: Sequence[MODEL]) -> None:
        dtos = self.serializer.flat.serialize(models)
        await self.crud.update_many(dtos)

    async def get_many_by_ids(self, ids: Sequence[ID]) -> Sequence[MODEL]:
        dtos = await self.crud.get_many_by_ids(ids)
        return self.serializer.flat.deserialize(dtos)

    async def delete(self, id_: ID) -> None:
        await self.crud.delete(id_)

    async def delete_many(self, ids: Sequence[ID]) -> None:
        await self.crud.delete_many(ids)

    async def count(self) -> int:
        return await self.crud.count()

    async def get_all(self) -> Sequence[MODEL]:
        dto = await self.crud.get_all()
        return self.serializer.flat.deserialize(dto)
