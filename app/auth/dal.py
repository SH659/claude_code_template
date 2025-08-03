from uuid import UUID

from sqlalchemy import select

from auth.models import Auth
from auth.tables import auth_table
from core.crud_base import CrudBase
from core.repo_base import RepoBase
from core.serializer import Serializer
from core.types import DTO


class AuthCrud(CrudBase[UUID, DTO]):
    """
    PURPOSE: CRUD operations for authentication records with username-based queries
    DESCRIPTION: Extends base CRUD functionality with authentication-specific database operations,
                 particularly username-based lookups for authentication flows.
    ATTRIBUTES:
        table: Table - SQLAlchemy table definition for auth_table
    """
    table = auth_table

    async def get_by_username(self, username: str) -> DTO:
        """
        PURPOSE: Retrieve authentication record by username
        DESCRIPTION: Executes database query to find authentication record matching the specified username.
                     Returns the record as a mapping dictionary for serialization.
        ARGUMENTS:
            username: str - Username to search for in authentication records
        RETURNS: DTO - Authentication record data as mapping dictionary
        CONTRACTS:
            RAISES:
                - NoResultFound - when no authentication record exists for the username
        """
        res = await self.session.execute(select(self.table).where(self.table.c.username == username))
        return res.mappings().one()


class AuthRepo(RepoBase[UUID, Auth]):
    """
    PURPOSE: Repository for Auth domain model with username-based access
    DESCRIPTION: Provides domain-level authentication operations by combining CRUD operations
                 with model serialization. Extends base repository with username lookup functionality.
    ATTRIBUTES:
        crud: AuthCrud - CRUD operations handler for authentication data
    """
    crud: AuthCrud

    def __init__(self, crud: AuthCrud, serializer: Serializer[Auth, DTO]):
        """
        PURPOSE: Initialize AuthRepo with CRUD and serialization dependencies
        DESCRIPTION: Sets up the authentication repository with required dependencies for data access
                     and model conversion operations.
        ARGUMENTS:
            crud: AuthCrud - CRUD operations handler for authentication data
            serializer: Serializer[Auth, DTO] - Converter between Auth models and database DTOs
        RETURNS: None - Constructor method
        """
        super().__init__(crud, serializer, Auth)

    async def get_by_username(self, username: str) -> Auth:
        """
        PURPOSE: Retrieve Auth domain model by username
        DESCRIPTION: Fetches authentication data by username and converts the DTO to Auth domain model
                     for business logic operations.
        ARGUMENTS:
            username: str - Username to search for in authentication records
        RETURNS: Auth - Authentication domain model instance
        CONTRACTS:
            RAISES:
                - Auth.NotFoundError - when no authentication record exists for the username
        """
        dto = await self.crud.get_by_username(username)
        return self.serializer.deserialize(dto)
