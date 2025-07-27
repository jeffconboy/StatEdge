"""
Database Connection
==================

PostgreSQL database connection for betting service.
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
import asyncpg
import asyncio
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "BETTING_DATABASE_URL", 
    "postgresql://betting_user:betting_secure_2025@localhost:5432/betting_data"
)

# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Session:
    """Get database session (synchronous)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_session() -> AsyncGenerator[None, None]:
    """Get async database session"""
    try:
        # Parse connection string for asyncpg
        url_parts = DATABASE_URL.replace("postgresql://", "").split("@")
        user_pass = url_parts[0].split(":")
        host_db = url_parts[1].split("/")
        host_port = host_db[0].split(":")
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        database = host_db[1]
        
        # Create async connection
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=database,
            host=host,
            port=port
        )
        
        try:
            yield conn
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

async def init_database():
    """Initialize database with schema"""
    try:
        async for conn in get_db_session():
            # Check if tables exist
            result = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'bets'
            """)
            
            if result == 0:
                logger.info("Creating betting database schema...")
                
                # Read and execute schema file
                schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema creation
                await conn.execute(schema_sql)
                logger.info("✅ Betting database schema created successfully")
            else:
                logger.info("✅ Betting database schema already exists")
            
            break
            
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise

async def test_connection():
    """Test database connection"""
    try:
        async for conn in get_db_session():
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                logger.info("✅ Database connection successful")
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
            
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False

def create_tables():
    """Create all tables using SQLAlchemy (fallback method)"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    # Test connection when run directly
    async def main():
        await test_connection()
        await init_database()
    
    asyncio.run(main())