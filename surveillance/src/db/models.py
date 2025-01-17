
# src/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base

class Program(Base):
    # 'start_time', 'end_time', 'duration', 'window', 'productive'
    __tablename__ = "program"

    id = Column(Integer, primary_key=True, index=True)
    window = Column(String, unique=False, index=True)    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now)    

class Chrome(Base):
    __tablename__ = "chrome"

    id = Column(Integer, primary_key=True, index=True)
    tab_title = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)

class MouseMove(Base):
    __tablename__ = "mouse"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

class Keystroke(Base):
    __tablename__ = "keystroke"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)  # FIXME: EVERY keytroke = like 50,000 keystrokes a day. Grouping into sessions, probably 5000

# class Item(Base):
#     __tablename__ = "items"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
