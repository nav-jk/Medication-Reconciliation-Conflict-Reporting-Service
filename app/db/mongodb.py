from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = None


def get_client():
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGO_URI)
    return client


def get_database():
    return get_client()[settings.DB_NAME]