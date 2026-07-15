import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")
#test
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
        
        # Create Indexes
        await create_indexes(db_instance.db)
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.error("Please ensure your MongoDB URI is correct and the database is accessible.")

async def create_indexes(db):
    import pymongo
    try:
        # Interviews collection
        await db["interviews"].create_index("session_id", unique=True)
        await db["interviews"].create_index("user_id")
        await db["interviews"].create_index("created_at")

        # Questions collection
        await db["questions"].create_index("session_id")
        await db["questions"].create_index("question_id")
        
        # Answers collection
        await db["answers"].create_index("session_id")
        await db["answers"].create_index("question_id")
        await db["answers"].create_index("answered_at")

        # Reports collection
        await db["reports"].create_index("session_id", unique=True)

        # Monitoring events collection
        await db["monitoring_events"].create_index("session_id")
        logger.info("MongoDB indexes created successfully.")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed.")

def get_db():
    return db_instance.db
