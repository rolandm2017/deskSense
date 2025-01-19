from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base


class TypingSession(Base):
    __tablename__ = "typing_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    def __repr__(self):
        return f"TypingSession(id={self.id}, start_time={self.start_time}, end_time={self.end_time})"

class MouseMove(Base):
    __tablename__ = "mouse_moves"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    def __repr__(self):
        return f"MouseMove(id={self.id}, start_time={self.start_time})"

class Program(Base):
    __tablename__ = "program_changes"

    id = Column(Integer, primary_key=True, index=True)
    window = Column(String, unique=False, index=True)    
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now)    
    
    def __repr__(self):
        return f"Program(id={self.id}, window='{self.window}', productive={self.productive})"

class Chrome(Base):
    __tablename__ = "chrome_tabs"

    id = Column(Integer, primary_key=True, index=True)
    tab_title = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    productive = Column(Boolean)
    
    def __repr__(self):
        return f"Chrome(id={self.id}, tab_title='{self.tab_title}', productive={self.productive})"
