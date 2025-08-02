from dishka import FromDishka

from auth.services import AuthService
from user.dal import UserRepo
from user.models import User


class UserService:
    def __init__(self, user_repo: UserRepo, auth_service: FromDishka[AuthService]):
        self.user_repo = user_repo
        self.auth_service = auth_service

    async def register(self, username: str, password: str) -> tuple[str, str]:
        user = await self.user_repo.create_and_get(User(username=username))
        auth = await self.auth_service.create_auth(user.id, username, password)
        access_token, refresh_token = self.auth_service.create_access_refresh_token_pair(auth)
        return access_token, refresh_token
