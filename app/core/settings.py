import os.path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    PURPOSE: Application configuration management using environment variables
    DESCRIPTION: Pydantic settings class that loads configuration from environment
    variables and .env file. Provides type-safe access to application settings
    including authentication, database, and API configuration parameters.
    ATTRIBUTES:
        SECRET_KEY: str - JWT signing secret key
        ALGORITHM: str - JWT signing algorithm, defaults to HS256
        ACCESS_TOKEN_EXPIRE_MINUTES: int - Access token expiration time in minutes
        REFRESH_TOKEN_EXPIRE_MINUTES: int - Refresh token expiration time in minutes
        DB_URI: str - Database connection URI
        API_URL: str - API server URL for external references
        QR_CODE_ENDPOINT: str - QR code endpoint URL template
        ADMIN_USERNAME: str - Default admin username
        ADMIN_PASSWORD: str - Default admin password
    """
    model_config = SettingsConfigDict(env_file=f'{os.path.dirname(__file__)}/../../.env')

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    DB_URI: str = "sqlite+aiosqlite:///./database.sqlite"

    API_URL: str = "127.0.0.1:8000"
    QR_CODE_ENDPOINT: str = "/qr_code/{uuid}"

    ADMIN_USERNAME: str = 'q'
    ADMIN_PASSWORD: str = 'q'


settings = Settings()  # noqa
