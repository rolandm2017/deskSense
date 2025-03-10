# models.py
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Interval, Computed, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, relationship

from sqlalchemy import Column as SQLAlchemyColumn

from typing import Union, Any, Optional
from datetime import datetime
from .database import Base
from ..object.enums import ChartEventType
from ..config.definitions import max_content_len


class TypingSession(Base):
    __tablename__ = "typing_sessions"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"TypingSession(id={self.id}, start_time={self.start_time}, end_time={self.end_time})"


class MouseMove(Base):
    __tablename__ = "mouse_moves"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"MouseMove(id={self.id}, start_time={self.start_time})"


class Program(Base):
    __tablename__ = "program_changes"

    id = Column(Integer, primary_key=True, index=True)
    window = Column(String(max_content_len), unique=False, index=True)
    # As of Jan 19, I am unsure that I need this column. Could take it out.
    detail = Column(String(max_content_len))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    duration = Column(Interval)
    productive = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now)

    def __eq__(self, other):
        if not isinstance(other, Program):
            return False
        return (
            self.id == other.id and
            self.window == other.window and
            self.detail == other.detail and
            self.start_time == other.start_time and
            self.end_time == other.end_time and
            self.productive == other.productive
        )

    def __repr__(self):
        return f"Program(\n\tid={self.id}, window='{self.window}', \n\tstart_time={self.start_time},\n\tend_time={self.end_time},\n\tproductive={self.productive})"


class ChromeTab(Base):
    __tablename__ = "chrome_tabs"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(max_content_len))
    # _ (underscore) because the @property and @tab_title.setter use "tab_title"
    _tab_title = Column("tab_title", String(max_content_len), index=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    productive = Column(Boolean)
    # TODO: Remove "tab_change_time"
    tab_change_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime, default=datetime.now)

    @property
    def tab_title(self):
        return self._tab_title

    @tab_title.setter
    def tab_title(self, value):
        if value:
            self._tab_title = value[:max_content_len]  # truncates to 80 chars
        else:
            self._tab_title = value

    def __repr__(self):
        return f"Chrome(id={self.id}, tab_title='{self.tab_title}', productive={self.productive})"

# ###
# ###


class DailyProgramSummary(Base):
    __tablename__ = "daily_program_summaries"

    id = Column(Integer, primary_key=True, index=True)
    program_name = Column(String)
    hours_spent = Column(Float)
    # The date on which the program data was gathered, without hh:mm:ss
    gathering_date = Column(DateTime(timezone=True))

    def __str__(self):
        formatted_date = self.gathering_date.strftime(
            "%Y-%m-%d") if self.gathering_date is not None else "No date"
        return f"Program: {self.program_name}, Hours: {self.hours_spent:.2f}, Date: {formatted_date}"


class DailyDomainSummary(Base):
    __tablename__ = "daily_chrome_summaries"

    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String)
    hours_spent = Column(Float)
    # The date on which the program data was gathered
    gathering_date = Column(DateTime(timezone=True))

    def __str__(self):
        formatted_date = self.gathering_date.strftime(
            "%Y-%m-%d") if self.gathering_date is not None else "No date"
        return f"Domain: {self.domain_name}, Hours: {self.hours_spent:.2f}, Date: {formatted_date}"


class ProgramSummaryLog(Base):
    __tablename__ = "program_summary_logs"

    id = Column(Integer, primary_key=True, index=True)
    program_name = Column(String)
    hours_spent = Column(Float)
    # The date on which the program data was gathered
    gathering_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))


class DomainSummaryLog(Base):
    __tablename__ = "domain_summary_logs"

    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String)
    hours_spent = Column(Float)
    # The date on which the program data was gathered
    gathering_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))


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
        Computed(
            "CASE WHEN \"group\" = 'MOUSE' THEN 'mouse-' || id::TEXT ELSE 'keyboard-' || id::TEXT END",
            # postgresql_persisted=True  # Add this back
            persisted=True
        )
    )

    group = Column(SQLAlchemyEnum(ChartEventType))

    content = Column(
        String,
        Computed(
            "CASE WHEN \"group\" = 'MOUSE' THEN 'Mouse Event ' || id::TEXT ELSE 'Typing Session ' || id::TEXT END",
            # postgresql_persisted=True,  # Add this back
            persisted=True

        )
    )

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
    # clientFacingId = Column(
    #     String,
    #     Computed(
    #         "CASE WHEN \"group\" = 'MOUSE' THEN 'mouse-' || id::TEXT ELSE 'keyboard-' || id::TEXT END",
    #         # postgresql_persisted=True  # Add this back
    #         persisted=True
    #     )
    # )

    group = Column(SQLAlchemyEnum(ChartEventType))

    content = Column(String)
    # content = Column(
    #     String,
    #     Computed(
    #         "CASE WHEN \"group\" = 'MOUSE' THEN 'Mouse Event ' || id::TEXT ELSE 'Typing Session ' || id::TEXT END",
    #         # postgresql_persisted=True,  # Add this back
    #         persisted=True

    #     )
    # )

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
