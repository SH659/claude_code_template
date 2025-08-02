from uuid import UUID

from sqlalchemy import select

from core.crud_base import CrudBase
from core.repo_base import RepoBase
from core.serializer import Serializer
from core.types import DTO
from user.models import User
from user.tables import user_table


class UserCrud(CrudBase[UUID, DTO]):
    table = user_table

    async def get_by_username(self, username: str) -> DTO | None:
        res = await self.session.execute(select(self.table).where(self.table.c.username == username))
        return res.mappings().one_or_none()


class UserRepo(RepoBase[UUID, User]):
    crud: UserCrud

    def __init__(self, crud: UserCrud, serializer: Serializer[User, DTO]):
        super().__init__(crud, serializer, User)

    async def get_by_username(self, username: str) -> User | None:
        dto = await self.crud.get_by_username(username)
        if dto is None:
            raise self.entity_cls.NotFoundError
        return self.serializer.deserialize(dto)  # noqa
