from typing import ClassVar, Sequence

from sqlalchemy import Table, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class CrudBase[ID, DTO]:
    """
    PURPOSE: Generic base class for database CRUD operations using SQLAlchemy
    DESCRIPTION: Provides standard Create, Read, Update, Delete operations for database tables.
    Uses SQLAlchemy async operations with generic type parameters for ID and DTO types.
    Subclasses must define a 'table' class variable pointing to the SQLAlchemy Table object.
    All operations work with DTO (Data Transfer Object) dictionaries for database interaction.
    """
    table: ClassVar[Table]

    def __init__(self, session: AsyncSession):
        """
        PURPOSE: Initialize CRUD operations with database session
        DESCRIPTION: Sets up the CRUD instance with an async SQLAlchemy session
        for database operations.
        ARGUMENTS:
            session: AsyncSession - SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(self, id_: ID) -> DTO:
        """
        PURPOSE: Retrieve a single record by its primary key
        DESCRIPTION: Executes a SELECT query to fetch one record matching the given ID.
        Returns the result as a mapping dictionary.
        ARGUMENTS:
            id_: ID - Primary key value to search for
        RETURNS: DTO - Dictionary mapping of the database record
        CONTRACTS:
            RAISES:
                - sqlalchemy.exc.NoResultFound - when no record exists with the given ID
        """
        res = await self.session.execute(select(self.table).where(self.table.c.id == id_))
        return res.mappings().one()

    async def create(self, obj: DTO) -> ID:
        """
        PURPOSE: Insert a new record and return its primary key
        DESCRIPTION: Executes an INSERT statement with the provided data and returns
        the generated or inserted primary key value.
        ARGUMENTS:
            obj: DTO - Dictionary containing field values for the new record
        RETURNS: ID - Primary key of the created record
        CONTRACTS:
            RAISES:
                - sqlalchemy.exc.IntegrityError - when insert violates database constraints
        """
        res = await self.session.execute(insert(self.table).values(**obj))
        pk = res.inserted_primary_key
        return pk[0] if len(pk) == 1 else pk

    async def create_and_get(self, obj: DTO) -> DTO:
        """
        PURPOSE: Insert a new record and return the complete created record
        DESCRIPTION: Executes an INSERT statement with RETURNING clause to get
        the complete record including any database-generated values.
        ARGUMENTS:
            obj: DTO - Dictionary containing field values for the new record
        RETURNS: DTO - Complete dictionary mapping of the created record
        CONTRACTS:
            RAISES:
                - sqlalchemy.exc.IntegrityError - when insert violates database constraints
        """
        res = await self.session.execute(insert(self.table).values(**obj).returning(self.table))
        return res.mappings().one()

    async def create_many(self, objs: Sequence[DTO]) -> list[ID]:
        """
        PURPOSE: Insert multiple records in a batch and return their primary keys
        DESCRIPTION: Executes a batch INSERT statement for efficiency when creating
        multiple records. Returns list of generated primary keys in insertion order.
        ARGUMENTS:
            objs: Sequence[DTO] - Collection of dictionaries containing field values
        RETURNS: list[ID] - List of primary keys for created records
        CONTRACTS:
            PRECONDITION:
                - objs sequence can be empty
            POSTCONDITION:
                - Returns empty list when objs is empty
                - Length of returned list equals length of objs when non-empty
            RAISES:
                - sqlalchemy.exc.IntegrityError - when any insert violates database constraints
        """
        objs = list(objs)
        if len(objs) == 0:
            return []
        res = await self.session.execute(insert(self.table).values(objs).returning(self.table.c.id))
        return [row[0] for row in res.all()]

    async def create_and_get_many(self, objs: Sequence[DTO]) -> Sequence[DTO]:
        """
        PURPOSE: Insert multiple records and return complete created records
        DESCRIPTION: Executes a batch INSERT with RETURNING clause to get complete
        records including database-generated values for all inserted records.
        ARGUMENTS:
            objs: Sequence[DTO] - Collection of dictionaries containing field values
        RETURNS: Sequence[DTO] - Collection of complete dictionary mappings for created records
        CONTRACTS:
            PRECONDITION:
                - objs sequence can be empty
            POSTCONDITION:
                - Returns empty sequence when objs is empty
                - Length of returned sequence equals length of objs when non-empty
            RAISES:
                - sqlalchemy.exc.IntegrityError - when any insert violates database constraints
        """
        objs = list(objs)
        if len(objs) == 0:
            return []
        res = await self.session.execute(insert(self.table).values(objs).returning(self.table))
        return res.mappings().all()

    async def update(self, values: DTO) -> ID:
        """
        PURPOSE: Update a record by ID and return the updated record's primary key
        DESCRIPTION: Executes an UPDATE statement for the record matching the ID in values.
        Uses RETURNING clause to confirm the update and return the primary key.
        ARGUMENTS:
            values: DTO - Dictionary containing 'id' field and updated values
        RETURNS: ID - Primary key of the updated record
        CONTRACTS:
            PRECONDITION:
                - values contains 'id' key
            RAISES:
                - sqlalchemy.exc.NoResultFound - when no record exists with the given ID
                - sqlalchemy.exc.IntegrityError - when update violates database constraints
        """
        id_ = values["id"]
        res = await self.session.execute(
            update(self.table).where(self.table.c.id == id_).values(values).returning(self.table.c.id)
        )
        res = res.scalars().one()
        return res

    async def update_and_get(self, values: DTO) -> DTO:
        """
        PURPOSE: Update a record by ID and return the complete updated record
        DESCRIPTION: Executes an UPDATE statement with RETURNING clause to get
        the complete updated record including any database-computed values.
        ARGUMENTS:
            values: DTO - Dictionary containing 'id' field and updated values
        RETURNS: DTO - Complete dictionary mapping of the updated record
        CONTRACTS:
            PRECONDITION:
                - values contains 'id' key
            RAISES:
                - sqlalchemy.exc.NoResultFound - when no record exists with the given ID
                - sqlalchemy.exc.IntegrityError - when update violates database constraints
        """
        id_ = values["id"]
        res = await self.session.execute(
            update(self.table).where(self.table.c.id == id_).values(values).returning(self.table)
        )
        return res.mappings().one()

    async def update_many(self, objs: Sequence[DTO]) -> None:
        """
        PURPOSE: Update multiple records using individual update operations
        DESCRIPTION: Iterates through the sequence and updates each record individually.
        Not optimized for large batches but ensures each update is processed.
        ARGUMENTS:
            objs: Sequence[DTO] - Collection of dictionaries containing 'id' and updated values
        RETURNS: None
        CONTRACTS:
            PRECONDITION:
                - Each DTO in objs contains 'id' key
            RAISES:
                - sqlalchemy.exc.NoResultFound - when any record with given ID does not exist
                - sqlalchemy.exc.IntegrityError - when any update violates database constraints
        """
        for obj in objs:
            await self.update(obj)

    async def get_many_by_ids(self, ids: Sequence[ID]) -> Sequence[DTO]:
        """
        PURPOSE: Retrieve multiple records by their primary keys
        DESCRIPTION: Executes a SELECT query with IN clause to fetch all records
        matching the provided IDs.
        ARGUMENTS:
            ids: Sequence[ID] - Collection of primary key values to retrieve
        RETURNS: Sequence[DTO] - Collection of dictionary mappings for found records
        CONTRACTS:
            POSTCONDITION:
                - Returned sequence contains only records that exist in database
                - May return fewer records than requested IDs if some don't exist
        """
        res = await self.session.execute(select(self.table).where(self.table.c.id.in_(ids)))
        return res.mappings().all()

    async def delete(self, id_: ID) -> None:
        """
        PURPOSE: Delete a single record by its primary key
        DESCRIPTION: Executes a DELETE statement for the record with the specified ID.
        Does not raise error if record doesn't exist.
        ARGUMENTS:
            id_: ID - Primary key of the record to delete
        RETURNS: None
        CONTRACTS:
            POSTCONDITION:
                - Record with given ID no longer exists in database
        """
        await self.session.execute(delete(self.table).where(self.table.c.id == id_))

    async def delete_many(self, ids: Sequence[ID]) -> None:
        """
        PURPOSE: Delete multiple records by their primary keys
        DESCRIPTION: Executes a DELETE statement with IN clause to remove all records
        matching the provided IDs in a single operation.
        ARGUMENTS:
            ids: Sequence[ID] - Collection of primary keys to delete
        RETURNS: None
        CONTRACTS:
            POSTCONDITION:
                - All records with given IDs no longer exist in database
        """
        await self.session.execute(delete(self.table).where(self.table.c.id.in_(ids)))

    async def count(self) -> int:
        """
        PURPOSE: Get the total number of records in the table
        DESCRIPTION: Executes a COUNT query to determine how many records
        currently exist in the table.
        RETURNS: int - Total number of records in the table
        CONTRACTS:
            POSTCONDITION:
                - Returned value is non-negative integer
        """
        res = await self.session.execute(select(func.count()).select_from(self.table))
        return res.scalar()

    async def get_all(self) -> Sequence[DTO]:
        """
        PURPOSE: Retrieve all records from the table
        DESCRIPTION: Executes a SELECT query without WHERE clause to fetch
        all records from the table.
        RETURNS: Sequence[DTO] - Collection of all records as dictionary mappings
        CONTRACTS:
            POSTCONDITION:
                - Returned sequence contains all records currently in table
        """
        res = await self.session.execute(select(self.table))
        return res.mappings().all()
