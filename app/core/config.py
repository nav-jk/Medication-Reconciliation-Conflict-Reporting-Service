from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 🔥 Add all env vars you use
    API_BASE_URL: str = "http://127.0.0.1:8000"
    RECONCILE_ENDPOINT: str = "/api/v1/reconcile/"

    # 🔥 Mongo (if you already have it, keep it)
    APP_NAME: str = "med-recon"
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "medicine"

    # 🔥 Required for pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   # 🔥 THIS FIXES YOUR ERROR
    )


settings = Settings()