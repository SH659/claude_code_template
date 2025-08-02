from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Body
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import token_pair_to_response
from user.services import UserService

router = APIRouter(route_class=DishkaRoute)


@router.post("/register")
async def register(
    username: Annotated[str, Body()],
    password: Annotated[str, Body()],
    user_service: FromDishka[UserService],
    session: FromDishka[AsyncSession],
):
    access_token, refresh_token = await user_service.register(username, password)
    await session.commit()
    return token_pair_to_response(access_token, refresh_token)
