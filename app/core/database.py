from typing import AsyncIterable, NewType

import sqlalchemy
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

metadata = sqlalchemy.MetaData()

DatabaseUrl = NewType("DatabaseUrl", str)


class ConnectionProvider(Provider):
    """
    PURPOSE: Dependency injection provider for database connection components
    DESCRIPTION: Dishka provider that manages database connection lifecycle including 
    database URL, async engine, and session management. Provides scoped instances 
    with proper resource cleanup for SQLAlchemy async operations.
    ATTRIBUTES:
        uri: str - Database connection URI
    """
    def __init__(self, uri):
        """
        PURPOSE: Initialize provider with database connection URI
        DESCRIPTION: Sets up the provider with the database connection string
        for creating database components.
        ARGUMENTS:
            uri: str - Database connection URI
        """
        super().__init__()
        self.uri = uri

    @provide(scope=Scope.APP)
    def db_url(self) -> DatabaseUrl:
        """
        PURPOSE: Provide typed database URL for dependency injection
        DESCRIPTION: Returns the database connection URI wrapped in DatabaseUrl type
        for type safety and dependency injection.
        RETURNS: DatabaseUrl - Typed database connection string
        """
        return DatabaseUrl(self.uri)

    @provide(scope=Scope.APP)
    def engine(self, db_url: DatabaseUrl) -> AsyncEngine:
        """
        PURPOSE: Create and provide SQLAlchemy async engine
        DESCRIPTION: Creates an async database engine from the database URL with
        echo disabled for production use.
        ARGUMENTS:
            db_url: DatabaseUrl - Typed database connection string
        RETURNS: AsyncEngine - SQLAlchemy async database engine
        """
        return create_async_engine(str(db_url), echo=False)

    @provide(scope=Scope.REQUEST)
    async def session(self, engine: AsyncEngine) -> AsyncIterable[AsyncSession]:
        """
        PURPOSE: Provide request-scoped database session with automatic cleanup
        DESCRIPTION: Creates and yields an async database session with automatic
        resource cleanup when the request completes.
        ARGUMENTS:
            engine: AsyncEngine - SQLAlchemy async database engine
        RETURNS: AsyncIterable[AsyncSession] - Request-scoped database session
        CONTRACTS:
            POSTCONDITION:
                - Session is automatically closed when request ends
                - All pending transactions are properly handled
        """
        async with AsyncSession(engine) as session:
            yield session


async def create_tables(engine: AsyncEngine):
    """
    PURPOSE: Create database tables using SQLAlchemy metadata
    DESCRIPTION: Executes DDL statements to create all database tables defined in the application's
                 SQLAlchemy metadata. Uses async engine connection to perform the operations.
    ARGUMENTS:
        engine: AsyncEngine - SQLAlchemy async engine for database operations
    RETURNS: None - Side effect of creating database schema
    CONTRACTS:
        POSTCONDITION:
            - All tables defined in metadata are created in the database
            - Existing tables are not modified (CREATE IF NOT EXISTS behavior)
    """
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
