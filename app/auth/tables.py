from sqlalchemy import UUID, Boolean, Column, String, Table

from core.database import metadata

auth_table = Table(
    "auth",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("user_id", UUID, index=True),
    Column("username", String, unique=True, index=True, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("is_admin", Boolean, nullable=False),
)
