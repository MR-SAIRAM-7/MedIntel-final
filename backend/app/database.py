"""
Database configuration and connection management.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import config
import logging

logger = logging.getLogger("medintel.database")


class Database:
    """Database connection manager."""
    
    client: AsyncIOMotorClient = None
    db = None
    
    @classmethod
    def connect(cls):
        """Connect to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(config.MONGO_URL)
            cls.db = cls.client[config.DB_NAME]
            logger.info(f"Connected to MongoDB: {config.DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    def close(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_db(cls):
        """Get database instance."""
        if cls.db is None:
            cls.connect()
        return cls.db


# Initialize database connection
def get_database():
    """Dependency to get database instance."""
    return Database.get_db()


# Collections helper functions
async def get_collection(collection_name: str):
    """Get a specific collection."""
    db = Database.get_db()
    return db[collection_name]
