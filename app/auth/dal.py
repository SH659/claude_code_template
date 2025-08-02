from uuid import UUID

from sqlalchemy import select

from auth.models import Auth
from auth.tables import auth_table
from core.crud_base import CrudBase
from core.repo_base import RepoBase
from core.serializer import Serializer
from core.types import DTO


class AuthCrud(CrudBase[UUID, DTO]):
    table = auth_table

    async def get_by_username(self, username: str) -> DTO:
        res = await self.session.execute(select(self.table).where(self.table.c.username == username))
        return res.mappings().one()


class AuthRepo(RepoBase[UUID, Auth]):
    crud: AuthCrud

    def __init__(self, crud: AuthCrud, serializer: Serializer[Auth, DTO]):
        super().__init__(crud, serializer, Auth)

    async def get_by_username(self, username: str) -> Auth:
        dto = await self.crud.get_by_username(username)
        return self.serializer.deserialize(dto)
