
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base
from ..object.enums import ChartEventType


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
    # TODO: As of Jan 19, I am unsure that I need this column. Could take it out.
    detail = Column(String)
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

# ###
# ###


class DailyProgramSummary(Base):
    __tablename__ = "daily_program_summaries"

    id = Column(Integer, primary_key=True, index=True)
    program_name = Column(String)
    hours_spent = Column(Float)
    # The date on which the program data was gathered
    gathering_date = Column(DateTime)


class TimelineEntryObj(Base):
    """
    Note: This table uses camelCase column names (rather than snake_case) 
    to avoid expensive case conversion of thousands of records before sending 
    to the client. This is an intentional performance optimization.

    It *intentionally* has the same name and fields as the server.py Pydantic model.
    Both *intentionally* have the same fields as the client's interface.
    """
    __tablename__ = "client_timeline_entries"

    id = Column(Integer, primary_key=True, index=True)
    # clientFacingId ex: `mouse-${log.mouseEventId}`, ex2: `keyboard-${log.keyboardEventId}`,
    clientFacingId = Column(String, index=True)

    group = Column(SQLAlchemyEnum(ChartEventType))  # "mouse" or "keyboard"
    # content ex: `Mouse Event ${log.mouseEventId}`, content: `Typing Session ${log.keyboardEventId}`,
    content = Column(String)
    start = Column(DateTime)  # "start" like start_time
    end = Column(DateTime)  # "end" like end_time
    # TODO: make it *come out of the db* ready to go
