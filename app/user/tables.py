from sqlalchemy import UUID, Column, String, Table

from core.database import metadata

user_table = Table(
    'user',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True),
    Column('username', String, unique=True, nullable=False),
)
