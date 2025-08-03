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
    """
    PURPOSE: Register new user account with authentication credentials
    DESCRIPTION: Creates a new user account with authentication record and returns JWT tokens
                 for immediate login. Commits the transaction before returning tokens.
    ARGUMENTS:
        username: Annotated[str, Body()] - Unique username for the new account
        password: Annotated[str, Body()] - Password for authentication
        user_service: FromDishka[UserService] - User service for account creation
        session: FromDishka[AsyncSession] - Database session for transaction management
    RETURNS: JSONResponse - Access token in body, refresh token in HTTP-only cookie
    CONTRACTS:
        PRECONDITION:
            - username is unique and not already registered
        POSTCONDITION:
            - User and Auth records are committed to database
            - Valid JWT tokens are returned
        RAISES:
            - User.AlreadyExistError - when username is already taken
    """
    access_token, refresh_token = await user_service.register(username, password)
    await session.commit()
    return token_pair_to_response(access_token, refresh_token)
