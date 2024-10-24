from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PG_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    AUTH_SERVER: str
    SECRET_KEY: str
    TOKEN_LIFETIME: int
    PROD: bool | None = False  # Для прода можно отдельные настройки докрутить через if PROD:... else

    class Config:
        env_file = "./.env"
        env_file_encoding = "utf-8"


settings = Settings()

db_url = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.PG_URL}/{settings.POSTGRES_DB}"

auth_server = settings.AUTH_SERVER

secret_key = settings.SECRET_KEY

dt_format = "%d/%m/%Y %H:%M:%S"
token_lifetime = settings.TOKEN_LIFETIME

