import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    try:
        # Reduced timeout so it doesn't hang for 30s if DB is offline
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        db_instance.db = db_instance.client[settings.MONGODB_NAME]
        # Verify connection
        await db_instance.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB database: '{settings.MONGODB_NAME}'!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.error("Please ensure your MongoDB URI is correct and the database is accessible.")

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_db():
    return db_instance.db
