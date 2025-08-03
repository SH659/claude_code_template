from typing import Sequence
from uuid import UUID

from PIL import Image

from qr_code.dal import QrCodeRepo
from qr_code.models import QrCode


class QrCodeService:
    """
    PURPOSE: Service layer for QR code management operations
    DESCRIPTION: Handles QR code-related business logic including creation, retrieval, modification,
                 and deletion of QR codes. Provides user-scoped operations with proper authorization
                 checks to ensure users can only access their own QR codes.
    ATTRIBUTES:
        qr_code_repo: QrCodeRepo - Repository for QR code data access operations
    """
    def __init__(self, qr_code_repo: QrCodeRepo):
        """
        PURPOSE: Initialize QrCodeService with required dependencies
        DESCRIPTION: Sets up the QR code service with the QR code repository for data access operations.
        ARGUMENTS:
            qr_code_repo: QrCodeRepo - Repository instance for QR code data operations
        RETURNS: None - Constructor method
        """
        self.qr_code_repo = qr_code_repo

    async def get_image_by_qr_code_id(self, id: UUID) -> Image.Image:
        """
        PURPOSE: Generate QR code image for the specified QR code ID
        DESCRIPTION: Retrieves the QR code record and generates a PIL Image containing the QR code
                     that redirects to the configured endpoint URL.
        ARGUMENTS:
            id: UUID - Unique identifier of the QR code record
        RETURNS: Image.Image - PIL Image object containing the generated QR code
        CONTRACTS:
            RAISES:
                - QrCode.NotFoundError - when QR code with specified ID does not exist
        """
        qr_code = await self.qr_code_repo.get_by_id(id)
        return qr_code.get_image()

    async def get_all(self) -> Sequence[QrCode]:
        """
        PURPOSE: Retrieve all QR codes in the system
        DESCRIPTION: Fetches all QR code records from the database without user filtering.
                     Primarily used for administrative purposes.
        RETURNS: Sequence[QrCode] - Collection of all QR code domain models
        """
        return await self.qr_code_repo.get_all()

    async def get_all_user_qr_codes(self, user_id: UUID) -> Sequence[QrCode]:
        """
        PURPOSE: Retrieve all QR codes belonging to a specific user
        DESCRIPTION: Fetches QR code records filtered by user ID to ensure users only see
                     their own QR codes.
        ARGUMENTS:
            user_id: UUID - Unique identifier of the user
        RETURNS: Sequence[QrCode] - Collection of QR code domain models owned by the user
        """
        return await self.qr_code_repo.get_all_user_qr_codes(user_id)

    async def create_qr_code(self, user_id: UUID, name: str, link: str) -> QrCode:
        """
        PURPOSE: Create a new QR code record for a user
        DESCRIPTION: Creates and persists a new QR code with the specified name and target link,
                     associated with the given user ID.
        ARGUMENTS:
            user_id: UUID - Unique identifier of the user creating the QR code
            name: str - Descriptive name for the QR code
            link: str - Target URL that the QR code will redirect to
        RETURNS: QrCode - Created QR code domain model with generated ID
        CONTRACTS:
            POSTCONDITION:
                - QR code record is persisted in database
                - Generated QR code ID is unique
        """
        qr_code = QrCode(user_id=user_id, name=name, link=link)
        return await self.qr_code_repo.create_and_get(qr_code)

    async def delete_qr_code(self, user_id: UUID, qr_code_id: UUID) -> None:
        """
        PURPOSE: Delete a QR code with user authorization check
        DESCRIPTION: Removes a QR code from the database after verifying that the requesting
                     user is the owner of the QR code.
        ARGUMENTS:
            user_id: UUID - Unique identifier of the user requesting deletion
            qr_code_id: UUID - Unique identifier of the QR code to delete
        RETURNS: None - Side effect of deleting the QR code
        CONTRACTS:
            PRECONDITION:
                - QR code exists in database
                - User is the owner of the QR code
            POSTCONDITION:
                - QR code is removed from database
            RAISES:
                - QrCode.NotFoundError - when QR code doesn't exist or user doesn't own it
        """
        qr_code = await self.qr_code_repo.get_by_id(qr_code_id)
        if qr_code.user_id != user_id:
            raise QrCode.NotFoundError
        await self.qr_code_repo.delete(qr_code.id)

    async def get_by_id(self, id: UUID) -> QrCode:
        """
        PURPOSE: Retrieve QR code by its unique identifier
        DESCRIPTION: Fetches a single QR code record by ID without user authorization checks.
                     Used for public operations like QR code redirection.
        ARGUMENTS:
            id: UUID - Unique identifier of the QR code
        RETURNS: QrCode - QR code domain model
        CONTRACTS:
            RAISES:
                - QrCode.NotFoundError - when QR code with specified ID does not exist
        """
        return await self.qr_code_repo.get_by_id(id)

    async def update_qr_code(self, user_id: UUID, qr_code_id: UUID, name: str, link: str) -> QrCode:
        """
        PURPOSE: Update QR code properties with user authorization check
        DESCRIPTION: Modifies the name and link of an existing QR code after verifying that
                     the requesting user is the owner of the QR code.
        ARGUMENTS:
            user_id: UUID - Unique identifier of the user requesting the update
            qr_code_id: UUID - Unique identifier of the QR code to update
            name: str - New descriptive name for the QR code
            link: str - New target URL for the QR code
        RETURNS: QrCode - Updated QR code domain model
        CONTRACTS:
            PRECONDITION:
                - QR code exists in database
                - User is the owner of the QR code
            POSTCONDITION:
                - QR code name and link are updated in database
            RAISES:
                - QrCode.NotFoundError - when QR code doesn't exist or user doesn't own it
        """
        qr_code = await self.qr_code_repo.get_by_id(qr_code_id)
        if qr_code.user_id != user_id:
            raise QrCode.NotFoundError
        qr_code.link = link
        qr_code.name = name
        return await self.qr_code_repo.update_and_get(qr_code)
