from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import Generator
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Define your models
class Program(Base):
    # 'start_time', 'end_time', 'duration', 'window', 'productive'
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    window = Column(String, unique=False, index=True)    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship
    # items = relationship("Item", back_populates="owner")

class Chrome(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    tab_title = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)
    # Relationship
    # owner = relationship("User", back_populates="items")

class MouseMove(Base):
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

class Keystroke(Base):
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)

# Database dependency
# def get_db() -> Generator[Session, None, None]:
#     """
#     Dependency that creates a new SQLAlchemy SessionLocal
#     that will be used in a single request, then closes it
#     once the request is finished
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Initialize the database by creating all tables if they don't exist.
    This should be called when your application starts.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
