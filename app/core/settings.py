import os.path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
