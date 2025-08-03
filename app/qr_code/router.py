import io
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from auth.dependencies import logged_in_user_id
from qr_code.models import QrCode
from qr_code.services import QrCodeService

router = APIRouter(route_class=DishkaRoute)


@router.get("/{qr_code_id}/image")
async def read_item(qr_code_id: UUID, qr_code_service: FromDishka[QrCodeService]):
    """
    PURPOSE: Generate and return QR code image as PNG response
    DESCRIPTION: Retrieves QR code record and generates a PNG image containing the QR code.
                 Returns the image as a binary response with appropriate content type.
    ARGUMENTS:
        qr_code_id: UUID - Unique identifier of the QR code to generate image for
        qr_code_service: FromDishka[QrCodeService] - QR code service for image generation
    RETURNS: Response - PNG image data with image/png content type
    CONTRACTS:
        RAISES:
            - QrCode.NotFoundError - when QR code with specified ID does not exist
    """
    image = await qr_code_service.get_image_by_qr_code_id(qr_code_id)
    image_io = io.BytesIO()
    image.save(image_io, format='PNG')
    image_bytes = image_io.getvalue()
    return Response(content=image_bytes, media_type="image/png")


@router.get("/")
async def get_all_user_qr_codes(qr_code_service: FromDishka[QrCodeService], user_id: UUID = Depends(logged_in_user_id)):
    """
    PURPOSE: Retrieve all QR codes belonging to authenticated user
    DESCRIPTION: Fetches and returns all QR code records owned by the currently authenticated user.
    ARGUMENTS:
        qr_code_service: FromDishka[QrCodeService] - QR code service for data operations
        user_id: UUID - Authenticated user ID from access token
    RETURNS: Sequence[QrCode] - Collection of QR code records owned by the user
    """
    return await qr_code_service.get_all_user_qr_codes(user_id)


@router.post("/")
async def create_qr_code(
    qr_code_service: FromDishka[QrCodeService],
    session: FromDishka[AsyncSession],
    name: str,
    link: str,
    user_id: UUID = Depends(logged_in_user_id),
):
    """
    PURPOSE: Create new QR code record for authenticated user
    DESCRIPTION: Creates a new QR code with specified name and target link, owned by the authenticated user.
                 Commits the transaction and returns the created QR code record.
    ARGUMENTS:
        qr_code_service: FromDishka[QrCodeService] - QR code service for creation operations
        session: FromDishka[AsyncSession] - Database session for transaction management
        name: str - Descriptive name for the QR code
        link: str - Target URL that the QR code will redirect to
        user_id: UUID - Authenticated user ID from access token
    RETURNS: QrCode - Created QR code record with generated ID
    CONTRACTS:
        POSTCONDITION:
            - QR code record is committed to database
            - QR code is associated with authenticated user
    """
    qr_code = await qr_code_service.create_qr_code(user_id, name, link)
    await session.commit()
    return qr_code


@router.delete("/{qr_code_id}")
async def delete_qr_code(
    qr_code_service: FromDishka[QrCodeService],
    session: FromDishka[AsyncSession],
    qr_code_id: UUID,
    user_id: UUID = Depends(logged_in_user_id),
):
    """
    PURPOSE: Delete QR code with user ownership verification
    DESCRIPTION: Removes QR code from database after verifying the authenticated user owns it.
                 Commits the transaction and returns success confirmation.
    ARGUMENTS:
        qr_code_service: FromDishka[QrCodeService] - QR code service for deletion operations
        session: FromDishka[AsyncSession] - Database session for transaction management
        qr_code_id: UUID - Unique identifier of QR code to delete
        user_id: UUID - Authenticated user ID from access token
    RETURNS: dict - Success confirmation with {"ok": True}
    CONTRACTS:
        PRECONDITION:
            - QR code exists and is owned by authenticated user
        POSTCONDITION:
            - QR code is removed from database
        RAISES:
            - QrCode.NotFoundError - when QR code doesn't exist or user doesn't own it
    """
    await qr_code_service.delete_qr_code(user_id, qr_code_id)
    await session.commit()
    return {"ok": True}

@router.get("/{qr_code_id}")
async def redirect(qr_code_id: UUID, qr_code_service: FromDishka[QrCodeService]) -> RedirectResponse:
    """
    PURPOSE: Redirect to target URL for scanned QR code
    DESCRIPTION: Public endpoint that handles QR code scans by retrieving the QR code record
                 and redirecting to its target URL with HTTP 302 status.
    ARGUMENTS:
        qr_code_id: UUID - Unique identifier of the QR code being scanned
        qr_code_service: FromDishka[QrCodeService] - QR code service for data retrieval
    RETURNS: RedirectResponse - HTTP 302 redirect to the QR code's target URL
    CONTRACTS:
        RAISES:
            - QrCode.NotFoundError - when QR code with specified ID does not exist
    """
    qr_code = await qr_code_service.get_by_id(qr_code_id)
    return RedirectResponse(url=qr_code.link, status_code=status.HTTP_302_FOUND)


@router.put("/{qr_code_id}")
async def edit(
    qr_code_service: FromDishka[QrCodeService],
    session: FromDishka[AsyncSession],
    qr_code_id: UUID,
    name: str,
    link: str,
    user_id: UUID = Depends(logged_in_user_id),
) -> QrCode:
    """
    PURPOSE: Update QR code properties with user ownership verification
    DESCRIPTION: Modifies name and target link of existing QR code after verifying the authenticated
                 user owns it. Commits the transaction and returns the updated record.
    ARGUMENTS:
        qr_code_service: FromDishka[QrCodeService] - QR code service for update operations
        session: FromDishka[AsyncSession] - Database session for transaction management
        qr_code_id: UUID - Unique identifier of QR code to update
        name: str - New descriptive name for the QR code
        link: str - New target URL for the QR code
        user_id: UUID - Authenticated user ID from access token
    RETURNS: QrCode - Updated QR code record
    CONTRACTS:
        PRECONDITION:
            - QR code exists and is owned by authenticated user
        POSTCONDITION:
            - QR code name and link are updated in database
        RAISES:
            - QrCode.NotFoundError - when QR code doesn't exist or user doesn't own it
    """
    qr_code = await qr_code_service.update_qr_code(user_id, qr_code_id, name, link)
    await session.commit()
    return qr_code
