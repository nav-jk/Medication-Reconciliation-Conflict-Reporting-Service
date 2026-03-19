from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    API_BASE_URL: str = "http://127.0.0.1:8000"
    RECONCILE_ENDPOINT: str = "/api/v1/reconcile/"


    APP_NAME: str = "med-recon"
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "medicine"


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   
    )


settings = Settings()