from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from core.crud_base import CrudBase
from core.repo_base import RepoBase
from core.serializer import Serializer
from core.types import DTO
from qr_code.models import QrCode
from qr_code.tables import qr_code_table


class QrCodeCrud(CrudBase[UUID, DTO]):
    """
    PURPOSE: CRUD operations for QR code records with user-specific queries
    DESCRIPTION: Extends base CRUD functionality with QR code-specific database operations,
                 particularly user-filtered lookups for user-scoped QR code management.
    ATTRIBUTES:
        table: Table - SQLAlchemy table definition for qr_code_table
    """
    table = qr_code_table

    async def get_all_user_qr_codes(self, user_id: UUID) -> Sequence[DTO]:
        """
        PURPOSE: Retrieve all QR code records for a specific user
        DESCRIPTION: Executes database query to find all QR code records belonging to the specified user.
                     Returns the records as mapping dictionaries for serialization.
        ARGUMENTS:
            user_id: UUID - User identifier to filter QR codes by
        RETURNS: Sequence[DTO] - Collection of QR code records as mapping dictionaries
        """
        res = await self.session.execute(select(self.table).where(self.table.c.user_id == user_id))
        return res.mappings().all()


class QrCodeRepo(RepoBase[UUID, QrCode]):
    """
    PURPOSE: Repository for QrCode domain model with user-specific access
    DESCRIPTION: Provides domain-level QR code operations by combining CRUD operations
                 with model serialization. Extends base repository with user-filtered functionality.
    ATTRIBUTES:
        crud: QrCodeCrud - CRUD operations handler for QR code data
    """
    crud: QrCodeCrud

    def __init__(self, crud: QrCodeCrud, serializer: Serializer[QrCode, DTO]):
        """
        PURPOSE: Initialize QrCodeRepo with CRUD and serialization dependencies
        DESCRIPTION: Sets up the QR code repository with required dependencies for data access
                     and model conversion operations.
        ARGUMENTS:
            crud: QrCodeCrud - CRUD operations handler for QR code data
            serializer: Serializer[QrCode, DTO] - Converter between QrCode models and database DTOs
        RETURNS: None - Constructor method
        """
        super().__init__(crud, serializer, QrCode)

    async def get_all_user_qr_codes(self, user_id: UUID) -> Sequence[QrCode]:
        """
        PURPOSE: Retrieve QrCode domain models for a specific user
        DESCRIPTION: Fetches QR code data filtered by user ID and converts the DTOs to QrCode domain models
                     using flat deserialization for efficient batch processing.
        ARGUMENTS:
            user_id: UUID - User identifier to filter QR codes by
        RETURNS: Sequence[QrCode] - Collection of QR code domain models owned by the user
        """
        qr_code = await self.crud.get_all_user_qr_codes(user_id)
        return self.serializer.flat.deserialize(qr_code)
