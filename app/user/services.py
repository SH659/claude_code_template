from dishka import FromDishka

from auth.services import AuthService
from user.dal import UserRepo
from user.models import User


class UserService:
    """
    PURPOSE: Service layer for user management operations including registration
    DESCRIPTION: Handles user-related business logic including user registration with automatic
                 authentication setup. Coordinates between user and authentication services to
                 create complete user accounts with login capabilities.
    ATTRIBUTES:
        user_repo: UserRepo - Repository for user data access operations
        auth_service: AuthService - Service for authentication operations
    """
    def __init__(self, user_repo: UserRepo, auth_service: FromDishka[AuthService]):
        """
        PURPOSE: Initialize UserService with required dependencies
        DESCRIPTION: Sets up the user service with user repository for data operations and
                     authentication service for credential management.
        ARGUMENTS:
            user_repo: UserRepo - Repository instance for user data operations
            auth_service: FromDishka[AuthService] - Authentication service for credential handling
        RETURNS: None - Constructor method
        """
        self.user_repo = user_repo
        self.auth_service = auth_service

    async def register(self, username: str, password: str) -> tuple[str, str]:
        """
        PURPOSE: Register new user with credentials and return authentication tokens
        DESCRIPTION: Creates a new user account and corresponding authentication record,
                     then generates access and refresh tokens for immediate login.
        ARGUMENTS:
            username: str - Unique username for the new user account
            password: str - Plain text password for authentication
        RETURNS: tuple[str, str] - Access token and refresh token pair
        CONTRACTS:
            PRECONDITION:
                - username is unique and not already registered
                - password meets security requirements
            POSTCONDITION:
                - User record is created and persisted
                - Auth record is created with hashed password
                - Valid JWT access and refresh tokens are generated
            RAISES:
                - User.AlreadyExistError - when username is already registered
                - Auth.AlreadyExistError - when authentication record creation fails
        """
        user = await self.user_repo.create_and_get(User(username=username))
        auth = await self.auth_service.create_auth(user.id, username, password)
        access_token, refresh_token = self.auth_service.create_access_refresh_token_pair(auth)
        return access_token, refresh_token
