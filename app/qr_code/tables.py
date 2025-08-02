from sqlalchemy import UUID, Column, ForeignKey, String, Table

from core.database import metadata

qr_code_table = Table(
    'qr_code',
    metadata,
    Column('id', UUID(as_uuid=True), primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True),
    Column("name", String, nullable=False),
    Column("link", String, nullable=False),
)
