from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "med-recon"
    MONGO_URI: str
    DB_NAME: str = "medicine"

    class Config:
        env_file = ".env"


settings = Settings()