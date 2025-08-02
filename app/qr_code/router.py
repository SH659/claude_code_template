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
    image = await qr_code_service.get_image_by_qr_code_id(qr_code_id)
    image_io = io.BytesIO()
    image.save(image_io, format='PNG')
    image_bytes = image_io.getvalue()
    return Response(content=image_bytes, media_type="image/png")


@router.get("/")
async def get_all_user_qr_codes(qr_code_service: FromDishka[QrCodeService], user_id: UUID = Depends(logged_in_user_id)):
    return await qr_code_service.get_all_user_qr_codes(user_id)


@router.post("/")
async def create_qr_code(
    qr_code_service: FromDishka[QrCodeService],
    session: FromDishka[AsyncSession],
    name: str,
    link: str,
    user_id: UUID = Depends(logged_in_user_id),
):
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
    await qr_code_service.delete_qr_code(user_id, qr_code_id)
    await session.commit()
    return {"ok": True}

@router.get("/{qr_code_id}")
async def redirect(qr_code_id: UUID, qr_code_service: FromDishka[QrCodeService]) -> RedirectResponse:
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
    qr_code = await qr_code_service.update_qr_code(user_id, qr_code_id, name, link)
    await session.commit()
    return qr_code
