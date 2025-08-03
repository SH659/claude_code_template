import dataclasses
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi.encoders import jsonable_encoder
from jwt import DecodeError, ExpiredSignatureError
from passlib.context import CryptContext

from auth.dal import AuthRepo
from auth.errors import InvalidLoginOrPasswordError, NotAuthorizedError, RefreshTokenRequiredError
from auth.models import Auth
from core.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class AccessTokenPayload:
    user_id: UUID
    username: str
    is_admin: bool = False
    token_type: str = "access"


class AuthService:
    """
    PURPOSE: Service layer for authentication operations including user login, token management, and password handling
    DESCRIPTION: Handles authentication business logic including password verification, JWT token creation and validation, 
                 user login flow, and token refresh operations. Manages both access and refresh tokens with proper expiration 
                 handling and integrates with the Auth repository for user data persistence.
    ATTRIBUTES:
        auth_repo: AuthRepo - Repository for authentication data access operations
    """
    def __init__(self, auth_repo: AuthRepo):
        """
        PURPOSE: Initialize the AuthService with required dependencies
        DESCRIPTION: Sets up the authentication service with the authentication repository for data access operations.
        ARGUMENTS:
            auth_repo: AuthRepo - Repository instance for authentication data operations
        RETURNS: None - Constructor method
        """
        self.auth_repo = auth_repo

    async def create_auth(self, user_id: UUID, username: str, password: str) -> Auth:
        """
        PURPOSE: Create a new authentication record for a user with hashed password
        DESCRIPTION: Creates a new Auth entity with the provided user credentials, hashes the password for secure storage,
                     and persists the authentication record to the database.
        ARGUMENTS:
            user_id: UUID - Unique identifier for the user
            username: str - Username for authentication
            password: str - Plain text password to be hashed
        RETURNS: Auth - Created authentication record with generated ID and hashed password
        CONTRACTS:
            PRECONDITION:
                - password is non-empty string
                - username is non-empty string
            POSTCONDITION:
                - Auth record is persisted in database
                - Password is securely hashed using bcrypt
            RAISES:
                - Auth.AlreadyExistError - when authentication record for username already exists
        """
        password_hash = self.get_password_hash(password)
        auth = Auth(user_id=user_id, username=username, password_hash=password_hash)
        auth = await self.auth_repo.create_and_get(auth)
        return auth

    async def login(self, username: str, password: str):
        """
        PURPOSE: Authenticate user credentials and generate access/refresh token pair
        DESCRIPTION: Validates user credentials by verifying the provided password against the stored hash,
                     and generates both access and refresh tokens for successful authentication.
        ARGUMENTS:
            username: str - Username for authentication
            password: str - Plain text password for verification
        RETURNS: tuple[str, str] - Access token and refresh token pair
        CONTRACTS:
            PRECONDITION:
                - username exists in authentication records
                - password matches stored hash
            POSTCONDITION:
                - Valid JWT access token with user payload is generated
                - Valid JWT refresh token is generated
            RAISES:
                - InvalidLoginOrPasswordError - when username not found or password verification fails
        """
        try:
            user = await self.auth_repo.get_by_username(username)
        except Auth.NotFoundError:
            raise InvalidLoginOrPasswordError

        if not self.verify_password(password, user.password_hash):
            raise InvalidLoginOrPasswordError

        token_pair = self.create_access_refresh_token_pair(user)
        return token_pair

    async def refresh(self, refresh_token: str | None):
        """
        PURPOSE: Generate new access/refresh token pair using valid refresh token
        DESCRIPTION: Validates the provided refresh token, extracts the user identity, and generates a new
                     access/refresh token pair for continued authentication.
        ARGUMENTS:
            refresh_token: str | None - JWT refresh token to validate and use for token generation
        RETURNS: tuple[str, str] - New access token and refresh token pair
        CONTRACTS:
            PRECONDITION:
                - refresh_token is provided and not None
                - refresh_token is valid JWT with correct signature
                - token_type in payload equals 'refresh'
                - auth_id exists in database
            POSTCONDITION:
                - New valid JWT access token is generated
                - New valid JWT refresh token is generated
            RAISES:
                - RefreshTokenRequiredError - when refresh_token is None or empty
                - NotAuthorizedError - when token is invalid, expired, or has wrong type
                - Auth.NotFoundError - when auth_id from token does not exist in database
        """
        if not refresh_token:
            raise RefreshTokenRequiredError
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("token_type") != "refresh":
            raise NotAuthorizedError
        auth_id = payload.get("id")
        if auth_id is None:
            raise NotAuthorizedError
        auth = await self.auth_repo.get_by_id(UUID(auth_id))
        token_pair = self.create_access_refresh_token_pair(auth)
        return token_pair

    def create_access_refresh_token_pair(self, auth: Auth):
        """
        PURPOSE: Generate paired access and refresh JWT tokens for authenticated user
        DESCRIPTION: Creates both access token containing user information and refresh token for token renewal.
                     Access token includes user ID, username, and admin status with shorter expiration.
                     Refresh token contains only auth ID with longer expiration.
        ARGUMENTS:
            auth: Auth - Authentication record containing user credentials and permissions
        RETURNS: tuple[str, str] - Access token and refresh token pair
        CONTRACTS:
            POSTCONDITION:
                - Access token contains user_id, username, is_admin, and token_type='access'
                - Refresh token contains auth ID and token_type='refresh'
                - Access token expires per ACCESS_TOKEN_EXPIRE_MINUTES setting
                - Refresh token expires per REFRESH_TOKEN_EXPIRE_MINUTES setting
        """
        access_token_exp = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = AccessTokenPayload(user_id=auth.user_id, username=auth.username, is_admin=auth.is_admin)
        at_payload = dataclasses.asdict(payload)  # noqa
        access_token = self.create_jwt_token(jsonable_encoder(at_payload), access_token_exp)

        refresh_token_exp = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_token_payload = {"id": str(auth.id), 'token_type': 'refresh'}
        refresh_token = self.create_jwt_token(refresh_token_payload, refresh_token_exp)
        return access_token, refresh_token

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        PURPOSE: Verify plain text password against hashed password using bcrypt
        DESCRIPTION: Uses bcrypt password context to securely verify that the provided plain text password
                     matches the stored hashed password.
        ARGUMENTS:
            plain_password: str - Plain text password to verify
            hashed_password: str - Bcrypt hashed password from database
        RETURNS: bool - True if password matches hash, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        """
        PURPOSE: Generate bcrypt hash for plain text password
        DESCRIPTION: Uses bcrypt password context to generate a secure hash of the provided password
                     for safe storage in the database.
        ARGUMENTS:
            password: str - Plain text password to hash
        RETURNS: str - Bcrypt hashed password suitable for database storage
        """
        return pwd_context.hash(password)

    @staticmethod
    def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """
        PURPOSE: Create JWT token with payload and expiration time
        DESCRIPTION: Generates a signed JWT token containing the provided data payload with configurable
                     expiration time. Uses application secret key and algorithm from settings.
        ARGUMENTS:
            data: dict - Payload data to encode in the JWT token
            expires_delta: timedelta | None - Token expiration duration, defaults to 15 minutes if None
        RETURNS: str - Signed JWT token string
        CONTRACTS:
            POSTCONDITION:
                - Token is signed with SECRET_KEY using configured algorithm
                - Token contains 'exp' claim with calculated expiration time
                - Token payload includes all provided data
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_jwt_token(token: str) -> dict:
        """
        PURPOSE: Decode and validate JWT token returning payload data
        DESCRIPTION: Verifies JWT token signature and expiration, then returns the decoded payload.
                     Handles token validation errors by converting them to application-specific exceptions.
        ARGUMENTS:
            token: str - JWT token string to decode and validate
        RETURNS: dict - Decoded token payload data
        CONTRACTS:
            PRECONDITION:
                - token is valid JWT format
                - token signature is valid
                - token is not expired
            RAISES:
                - NotAuthorizedError - when token is invalid, malformed, or expired
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except DecodeError:
            raise NotAuthorizedError
        except ExpiredSignatureError:
            raise NotAuthorizedError
        return payload

    @staticmethod
    def decode_access_token(token: str) -> AccessTokenPayload:
        """
        PURPOSE: Decode JWT access token and return structured payload
        DESCRIPTION: Validates JWT token, verifies it's an access token type, and returns the payload
                     as a structured AccessTokenPayload object for type-safe access to user information.
        ARGUMENTS:
            token: str - JWT access token string to decode
        RETURNS: AccessTokenPayload - Structured access token payload with user information
        CONTRACTS:
            PRECONDITION:
                - token is valid JWT access token
                - token contains token_type='access'
            RAISES:
                - NotAuthorizedError - when token is invalid or not an access token
        """
        payload = AuthService.decode_jwt_token(token)
        if payload.get("token_type") != "access":
            raise NotAuthorizedError
        return AccessTokenPayload(user_id=UUID(payload["user_id"]), username=payload["username"])
