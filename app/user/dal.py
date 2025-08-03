from uuid import UUID

from sqlalchemy import select

from core.crud_base import CrudBase
from core.repo_base import RepoBase
from core.serializer import Serializer
from core.types import DTO
from user.models import User
from user.tables import user_table


class UserCrud(CrudBase[UUID, DTO]):
    """
    PURPOSE: CRUD operations for user records with username-based queries
    DESCRIPTION: Extends base CRUD functionality with user-specific database operations,
                 particularly username-based lookups for user management operations.
    ATTRIBUTES:
        table: Table - SQLAlchemy table definition for user_table
    """
    table = user_table

    async def get_by_username(self, username: str) -> DTO | None:
        """
        PURPOSE: Retrieve user record by username with optional result
        DESCRIPTION: Executes database query to find user record matching the specified username.
                     Returns None if no matching user is found.
        ARGUMENTS:
            username: str - Username to search for in user records
        RETURNS: DTO | None - User record data as mapping dictionary, or None if not found
        """
        res = await self.session.execute(select(self.table).where(self.table.c.username == username))
        return res.mappings().one_or_none()


class UserRepo(RepoBase[UUID, User]):
    """
    PURPOSE: Repository for User domain model with username-based access
    DESCRIPTION: Provides domain-level user operations by combining CRUD operations
                 with model serialization. Extends base repository with username lookup functionality.
    ATTRIBUTES:
        crud: UserCrud - CRUD operations handler for user data
    """
    crud: UserCrud

    def __init__(self, crud: UserCrud, serializer: Serializer[User, DTO]):
        """
        PURPOSE: Initialize UserRepo with CRUD and serialization dependencies
        DESCRIPTION: Sets up the user repository with required dependencies for data access
                     and model conversion operations.
        ARGUMENTS:
            crud: UserCrud - CRUD operations handler for user data
            serializer: Serializer[User, DTO] - Converter between User models and database DTOs
        RETURNS: None - Constructor method
        """
        super().__init__(crud, serializer, User)

    async def get_by_username(self, username: str) -> User | None:
        """
        PURPOSE: Retrieve User domain model by username with exception handling
        DESCRIPTION: Fetches user data by username and converts the DTO to User domain model.
                     Raises NotFoundError if user doesn't exist instead of returning None.
        ARGUMENTS:
            username: str - Username to search for in user records
        RETURNS: User | None - User domain model instance (note: always raises exception instead of returning None)
        CONTRACTS:
            RAISES:
                - User.NotFoundError - when no user record exists for the username
        """
        dto = await self.crud.get_by_username(username)
        if dto is None:
            raise self.entity_cls.NotFoundError
        return self.serializer.deserialize(dto)  # noqa
