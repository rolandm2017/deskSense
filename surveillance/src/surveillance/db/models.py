# models.py
from datetime import datetime
from typing import Any, Optional, Union

from sqlalchemy import Column
from sqlalchemy import Column as SQLAlchemyColumn
from sqlalchemy import Computed, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Float, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from surveillance.config.definitions import max_content_len
from surveillance.db.database import Base
from surveillance.object.enums import ChartEventType, SystemStatusType


class DailySummaryBase(Base):
    """
    Base class for summary models with common fields
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    hours_spent: Mapped[float] = mapped_column(Float)
    # The date on which the program data was gathered, without hh:mm:ss
    # MUST be the date FOR THE USER. Otherwise, the program doesn't make sense
    gathering_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gathering_date_local: Mapped[datetime] = mapped_column(
        DateTime(timezone=False))
    # TODO: Try gathering_date not as .date() but the full hh:mm:ss thing. Until you figure out why it isn't like that already


class DailyProgramSummary(DailySummaryBase):
    """
    A summation of every instance of time spent on a program
    """
    __tablename__ = "daily_program_summaries"

    exe_path_as_id: Mapped[str] = mapped_column(String)  # unique identifier
    process_name: Mapped[str] = mapped_column(String)
    program_name: Mapped[str] = mapped_column(String)

    def get_name(self):
        return self.process_name

    def __str__(self):
        formatted_date = self.gathering_date.strftime(
            "%Y-%m-%d %H:%M") if self.gathering_date is not None else "No date"
        return f"Program: {self.program_name}, \tHours: {self.hours_spent}, \tDate: {formatted_date}"


class DailyDomainSummary(DailySummaryBase):
    """
    A summation of every instance of time spent on a domain
    """
    __tablename__ = "daily_chrome_summaries"

    domain_name: Mapped[str] = mapped_column(String)

    def get_name(self):
        return self.domain_name

    def __str__(self):
        formatted_date = self.gathering_date.strftime(
            "%Y-%m-%d") if self.gathering_date is not None else "No date"
        return f"Domain: {self.domain_name}, \tHours: {self.hours_spent}, \tDate: {formatted_date}"


class SummaryLogBase(Base):
    """
    Base class for summary logs with common fields
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    hours_spent: Mapped[float] = mapped_column(Float)
    # time stuff
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    start_time_local: Mapped[datetime] = mapped_column(
        DateTime(timezone=False))
    end_time_local: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    duration_in_sec: Mapped[float] = mapped_column(Float, nullable=True)
    # The date on which the data was gathered
    gathering_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gathering_date_local: Mapped[datetime] = mapped_column(
        DateTime(timezone=False))

    created_at = Column(DateTime(timezone=True))


class ProgramSummaryLog(SummaryLogBase):
    """
    Logs a singular addition to the ProgramSummary table
    """
    __tablename__ = "program_logs"

    exe_path_as_id: Mapped[str] = mapped_column(String)  # unique identifier
    process_name: Mapped[str] = mapped_column(String)
    program_name: Mapped[str] = mapped_column(String)

    def get_name(self):
        return self.process_name

    def __str__(self):
        return f"ProgramSummaryLog(id={self.id}, program_name={self.program_name}, hours_spent={self.hours_spent}, " \
            f"start_time={self.start_time}, end_time={self.end_time}, " \
            f"gathering_date={self.gathering_date}, created_at={self.created_at})"


class DomainSummaryLog(SummaryLogBase):
    __tablename__ = "domain_logs"

    domain_name: Mapped[str] = mapped_column(String)

    def get_name(self):
        return self.domain_name

    def __str__(self):
        return f"DomainSummaryLog(domain_name={self.domain_name}, hours_spent={self.hours_spent}, " \
            f"start_time={self.start_time}, end_time={self.end_time}, " \
            f"gathering_date={self.gathering_date}, created_at={self.created_at})"


class TypingSession(Base):
    __tablename__ = "typing_sessions"
    # It is unclear if this model needs a start_time_local, end_time_local, so I'm leaving it
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"TypingSession(id={self.id}, start_time={self.start_time}, end_time={self.end_time})"


class MouseMove(Base):
    __tablename__ = "mouse_moves"
    # It is unclear if this model needs a start_time_local, end_time_local, so I'm leaving it
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"MouseMove(id={self.id}, start_time={self.start_time})"


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

    clientFacingId = Column(
        String,
        # "Sqlalchemy db-agnostic language" - Claude
        Computed(
            "CASE WHEN \"group\" = 'MOUSE' THEN 'mouse-' || id ELSE 'keyboard-' || id END", persisted=True)
    )

    group = Column(SQLAlchemyEnum(ChartEventType))

    content = Column(
        String,
        # "Sqlalchemy db-agnostic language" - Claude
        Computed(
            "CASE WHEN \"group\" = 'MOUSE' THEN 'Mouse Event ' || id ELSE 'Typing Session ' || id END", persisted=True)
    )
    # It is unclear if this model needs a start_time_local, end_time_local, so I'm leaving it
    start = Column(DateTime(timezone=True))
    end = Column(DateTime(timezone=True))

    def __str__(self):
        """
        Returns a human-readable string representation of the TimelineEntry.
        """
        return (
            f"TimelineEntryObj(id={self.id}, "
            f"clientFacingId='{self.clientFacingId}', "
            # f"group='{self.group.value if self.group else None}', "  # says AttributeError: 'str' object has no attribute 'value'
            f"group='{self.group if self.group is not None else None}', "
            f"content='{self.content}', "
            f"start='{self.start.isoformat() if self.start is not None else None}', "
            f"end='{self.end.isoformat() if self.end is not None else None}')"
        )


class PrecomputedTimelineEntry(Base):
    """
    Problem: The program was sending 7.2 mb of timeline data, to be aggregated each refresh, over and over.

    Solution: Precompute the timeline data here on the server, since 
    it only needs to be done one time supposing the result is stored and demanded effectively.

    Note: This table uses camelCase column names (rather than snake_case)
    to avoid expensive case conversion of thousands of records before sending
    to the client. This is an intentional performance optimization.
    """
    __tablename__ = "precomputed_timelines"

    id = Column(Integer, primary_key=True, index=True)

    clientFacingId: Union[str, SQLAlchemyColumn[str]] = Column(String)

    group = Column(SQLAlchemyEnum(ChartEventType))

    content = Column(String)

    start = Column(DateTime(timezone=True))
    end = Column(DateTime(timezone=True))

    eventCount = Column(Integer)

    def __str__(self):
        """
        Returns a human-readable string representation of the TimelineEntry.
        """
        return (
            f"PrecomputedTimelineEntry(id={self.id}, "
            f"clientFacingId='{self.clientFacingId}', "
            # f"group='{self.group.value if self.group else None}', "  # says AttributeError: 'str' object has no attribute 'value'
            f"group='{self.group if self.group is not None else None}', "
            f"content='{self.content}', "
            f"start='{self.start.isoformat() if self.start is not None else None}', "
            f"end='{self.end.isoformat() if self.end is not None else None}', "
            f"eventCount='{self.eventCount}')"
        )

    # count = Column(Integer)  # could be nice to know how many events went into an entry.


class SystemStatus(Base):
    """
    Made to help track when the user is using their machine.

    If the machine is powered off at time t, after, there should be no open program/Chrome sessions.

    If the machine powers on at time t, surely no sessions should be open before t.
    """
    __tablename__ = "system_change_log"

    id = Column(Integer, primary_key=True, index=True)
    status: Mapped[SystemStatusType] = mapped_column(
        SQLAlchemyEnum(SystemStatusType))
    created_at = Column(DateTime(timezone=True))


class Video(Base):
    """
    The Created At field is given BY THE RECORDER, not when the db row is written.

    A Video connects to a Frames table. One to Many.
    """
    __tablename__ = "video_files"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    created_at = Column(DateTime, default=None)

    # This establishes the one-to-many relationship
    frames = relationship("Frame", back_populates="video")


class Frame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)
    # This creates the foreign key column
    video_id = Column(Integer, ForeignKey('video_files.id'))
    created_at = Column(DateTime, default=None)
    frame_number = Column(Integer)

    # This creates the reference back to the Video
    video = relationship("Video", back_populates="frames")
