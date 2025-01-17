from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base

class Program(Base):
    __tablename__ = "program"

    id = Column(Integer, primary_key=True, index=True)
    window = Column(String, unique=False, index=True)    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now)    
    
    def __repr__(self):
        return f"Program(id={self.id}, window='{self.window}', productive={self.productive})"

class Chrome(Base):
    __tablename__ = "chrome"

    id = Column(Integer, primary_key=True, index=True)
    tab_title = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)
    
    def __repr__(self):
        return f"Chrome(id={self.id}, tab_title='{self.tab_title}', productive={self.productive})"

class MouseMove(Base):
    __tablename__ = "mouse"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    def __repr__(self):
        return f"MouseMove(id={self.id}, start_time={self.start_time})"

class Keystroke(Base):
    __tablename__ = "keystroke"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime)
    
    def __repr__(self):
        return f"Keystroke(id={self.id}, timestamp={self.timestamp})"