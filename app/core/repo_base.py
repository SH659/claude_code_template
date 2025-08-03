import functools
import inspect
from typing import Sequence, Type

import sqlalchemy

from core.crud_base import CrudBase
from core.models import Model
from core.serializer import Serializer
from core.types import DTO


def handle_exceptions(func):
    """
    PURPOSE: Decorator that converts SQLAlchemy exceptions to model-specific exceptions
    DESCRIPTION: Wraps async repository methods to catch common SQLAlchemy exceptions and convert them
    to domain-specific exceptions. Handles NoResultFound by raising the model's NotFoundError and
    IntegrityError by detecting unique constraint violations and raising AlreadyExistError.
    ARGUMENTS:
        func: callable - The async function to wrap with exception handling
    RETURNS: callable - Wrapped function with exception handling logic
    CONTRACTS:
        PRECONDITION:
            - func is an async callable
        POSTCONDITION:
            - Returned wrapper function has __handle_exceptions__ attribute set to True
            - SQLAlchemy NoResultFound exceptions are converted to model NotFoundError
            - SQLAlchemy IntegrityError with unique constraint violations are converted to AlreadyExistError
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        """
        PURPOSE: Inner wrapper function that performs exception handling
        DESCRIPTION: Executes the wrapped function and catches SQLAlchemy exceptions,
        converting them to appropriate model-specific exceptions based on error type.
        ARGUMENTS:
            self: RepoBase - Repository instance
            *args: tuple - Positional arguments passed to wrapped function
            **kwargs: dict - Keyword arguments passed to wrapped function
        RETURNS: Any - Result from the wrapped function
        CONTRACTS:
            RAISES:
                - self.entity_cls.NotFoundError - when SQLAlchemy NoResultFound is caught
                - self.entity_cls.AlreadyExistError - when SQLAlchemy IntegrityError indicates unique constraint violation
        """
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
    """
    PURPOSE: Metaclass that automatically applies exception handling to repository methods
    DESCRIPTION: Custom metaclass for repository classes that automatically wraps all async methods
    with the handle_exceptions decorator, unless they already have exception handling applied.
    This ensures consistent exception handling across all repository methods without requiring
    explicit decoration of each method.
    """
    def __new__(mcs, name, bases, namespace):
        """
        PURPOSE: Create new repository class with automatic exception handling
        DESCRIPTION: Examines all async methods in the class namespace and applies the handle_exceptions
        decorator to those that don't already have it. This ensures all repository methods have
        consistent exception handling without manual decoration.
        ARGUMENTS:
            mcs: type - The metaclass itself
            name: str - Name of the class being created
            bases: tuple - Base classes
            namespace: dict - Class namespace containing attributes and methods
        RETURNS: type - The newly created class with exception handling applied
        CONTRACTS:
            POSTCONDITION:
                - All async methods in namespace have exception handling applied
                - Methods already marked with __handle_exceptions__ are not double-wrapped
        """
        for attr_name, attr_value in namespace.items():
            if inspect.iscoroutinefunction(attr_value) and getattr(attr_value, '__handle_exceptions__', False) is False:
                namespace[attr_name] = handle_exceptions(attr_value)
        return super().__new__(mcs, name, bases, namespace)


class RepoBase[ID, MODEL: Model](metaclass=RepoMeta):
    """
    PURPOSE: Provides standardized repository interface for domain model operations
    DESCRIPTION: Abstract base class that implements repository pattern for domain models, 
    handling serialization between domain models and DTOs, and providing type-safe 
    database operations through composition with CRUD and serializer components.
    ATTRIBUTES:
        crud: CrudBase[ID, DTO] - Database operations handler for the entity
        serializer: Serializer[MODEL, DTO] - Converts between domain models and DTOs
        entity_cls: Type[MODEL] - Domain model class for exception generation
    """
    def __init__(self, crud: CrudBase[ID, DTO], serializer: Serializer[MODEL, DTO], entity_cls: Type[MODEL]):
        """
        PURPOSE: Initialize repository with required dependencies for data operations
        DESCRIPTION: Sets up the repository with its dependencies for data access operations. 
        The CRUD instance handles database operations, serializer manages model/DTO conversion, 
        and entity_cls provides access to model-specific exception types.
        ARGUMENTS:
            crud: CrudBase[ID, DTO] - Database operations handler
            serializer: Serializer[MODEL, DTO] - Model to DTO conversion handler
            entity_cls: Type[MODEL] - Domain model class for exception generation
        """
        self.crud = crud
        self.serializer = serializer
        self.entity_cls = entity_cls

    async def get_by_id(self, id_: ID) -> MODEL:
        """
        PURPOSE: Retrieve a single domain model by its unique identifier
        DESCRIPTION: Fetches a DTO from the database using CRUD operations and converts
        it to a domain model using the serializer.
        ARGUMENTS:
            id_: ID - Unique identifier of the entity to retrieve
        RETURNS: MODEL - The domain model instance
        CONTRACTS:
            RAISES:
                - entity_cls.NotFoundError - when no entity exists with the given ID
        """
        dto = await self.crud.get_by_id(id_)
        return self.serializer.deserialize(dto)

    async def create(self, model: MODEL) -> ID:
        """
        PURPOSE: Create a new entity in the database and return its ID
        DESCRIPTION: Converts the domain model to a DTO using the serializer and
        persists it using CRUD operations.
        ARGUMENTS:
            model: MODEL - Domain model instance to create
        RETURNS: ID - Unique identifier of the created entity
        CONTRACTS:
            RAISES:
                - entity_cls.AlreadyExistError - when entity with unique constraints already exists
        """
        dto = self.serializer.serialize(model)
        return await self.crud.create(dto)

    async def create_and_get(self, model: MODEL) -> MODEL:
        """
        PURPOSE: Create a new entity and return the created domain model
        DESCRIPTION: Converts the domain model to DTO, persists it, and returns
        the created entity as a domain model with any database-generated values.
        ARGUMENTS:
            model: MODEL - Domain model instance to create
        RETURNS: MODEL - The created domain model with database-generated values
        CONTRACTS:
            RAISES:
                - entity_cls.AlreadyExistError - when entity with unique constraints already exists
        """
        dto = self.serializer.serialize(model)
        dto = await self.crud.create_and_get(dto)
        return self.serializer.deserialize(dto)

    async def create_many(self, models: Sequence[MODEL]) -> list[ID]:
        """
        PURPOSE: Create multiple entities in a batch operation and return their IDs
        DESCRIPTION: Converts a sequence of domain models to DTOs using flat serialization
        and persists them in a single database operation for efficiency.
        ARGUMENTS:
            models: Sequence[MODEL] - Collection of domain models to create
        RETURNS: list[ID] - List of unique identifiers for the created entities
        CONTRACTS:
            RAISES:
                - entity_cls.AlreadyExistError - when any entity with unique constraints already exists
        """
        dtos = self.serializer.flat.serialize(models)
        return await self.crud.create_many(dtos)

    async def create_and_get_many(self, models: Sequence[MODEL]) -> Sequence[MODEL]:
        """
        PURPOSE: Create multiple entities and return the created domain models
        DESCRIPTION: Converts domain models to DTOs, persists them in batch,
        and returns the created entities with any database-generated values.
        ARGUMENTS:
            models: Sequence[MODEL] - Collection of domain models to create
        RETURNS: Sequence[MODEL] - Collection of created domain models with database values
        CONTRACTS:
            RAISES:
                - entity_cls.AlreadyExistError - when any entity with unique constraints already exists
        """
        dtos = self.serializer.flat.serialize(models)
        dtos = await self.crud.create_and_get_many(dtos)
        return self.serializer.flat.deserialize(dtos)

    async def update(self, values: MODEL) -> None:
        """
        PURPOSE: Update an existing entity with new values
        DESCRIPTION: Converts the domain model to DTO and updates the corresponding
        database record using CRUD operations.
        ARGUMENTS:
            values: MODEL - Domain model with updated values
        RETURNS: None
        CONTRACTS:
            RAISES:
                - entity_cls.NotFoundError - when entity to update does not exist
                - entity_cls.AlreadyExistError - when update violates unique constraints
        """
        dto = self.serializer.serialize(values)
        await self.crud.update(dto)

    async def update_and_get(self, values: MODEL) -> MODEL:
        """
        PURPOSE: Update an existing entity and return the updated domain model
        DESCRIPTION: Converts domain model to DTO, updates the database record,
        and returns the updated entity with any database-computed values.
        ARGUMENTS:
            values: MODEL - Domain model with updated values
        RETURNS: MODEL - Updated domain model with current database values
        CONTRACTS:
            RAISES:
                - entity_cls.NotFoundError - when entity to update does not exist
                - entity_cls.AlreadyExistError - when update violates unique constraints
        """
        dto = self.serializer.serialize(values)
        dto = await self.crud.update_and_get(dto)
        return self.serializer.deserialize(dto)

    async def update_many(self, models: Sequence[MODEL]) -> None:
        """
        PURPOSE: Update multiple entities in a batch operation
        DESCRIPTION: Converts sequence of domain models to DTOs using flat serialization
        and updates multiple database records in a single operation.
        ARGUMENTS:
            models: Sequence[MODEL] - Collection of domain models with updated values
        RETURNS: None
        CONTRACTS:
            RAISES:
                - entity_cls.NotFoundError - when any entity to update does not exist
                - entity_cls.AlreadyExistError - when any update violates unique constraints
        """
        dtos = self.serializer.flat.serialize(models)
        await self.crud.update_many(dtos)

    async def get_many_by_ids(self, ids: Sequence[ID]) -> Sequence[MODEL]:
        """
        PURPOSE: Retrieve multiple domain models by their unique identifiers
        DESCRIPTION: Fetches multiple DTOs from database using CRUD operations
        and converts them to domain models using flat deserialization.
        ARGUMENTS:
            ids: Sequence[ID] - Collection of unique identifiers to retrieve
        RETURNS: Sequence[MODEL] - Collection of domain model instances
        CONTRACTS:
            POSTCONDITION:
                - Returned sequence contains only entities that exist in database
                - Order of returned models may not match order of input IDs
        """
        dtos = await self.crud.get_many_by_ids(ids)
        return self.serializer.flat.deserialize(dtos)

    async def delete(self, id_: ID) -> None:
        """
        PURPOSE: Delete a single entity by its unique identifier
        DESCRIPTION: Removes the entity with the specified ID from the database
        using CRUD operations.
        ARGUMENTS:
            id_: ID - Unique identifier of the entity to delete
        RETURNS: None
        CONTRACTS:
            POSTCONDITION:
                - Entity with given ID no longer exists in database
        """
        await self.crud.delete(id_)

    async def delete_many(self, ids: Sequence[ID]) -> None:
        """
        PURPOSE: Delete multiple entities in a batch operation
        DESCRIPTION: Removes all entities with the specified IDs from the database
        in a single operation for efficiency.
        ARGUMENTS:
            ids: Sequence[ID] - Collection of unique identifiers to delete
        RETURNS: None
        CONTRACTS:
            POSTCONDITION:
                - All entities with given IDs no longer exist in database
        """
        await self.crud.delete_many(ids)

    async def count(self) -> int:
        """
        PURPOSE: Get the total count of entities in the repository
        DESCRIPTION: Returns the number of entities currently stored in the database
        for this repository's entity type.
        RETURNS: int - Total count of entities
        CONTRACTS:
            POSTCONDITION:
                - Returned value is non-negative integer
        """
        return await self.crud.count()

    async def get_all(self) -> Sequence[MODEL]:
        """
        PURPOSE: Retrieve all entities from the repository
        DESCRIPTION: Fetches all DTOs from database and converts them to
        domain models using flat deserialization.
        RETURNS: Sequence[MODEL] - Collection of all domain model instances
        CONTRACTS:
            POSTCONDITION:
                - Returned sequence contains all entities currently in database
        """
        dto = await self.crud.get_all()
        return self.serializer.flat.deserialize(dto)
