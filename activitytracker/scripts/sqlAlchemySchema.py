import os

from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


SIMULATION_CAPTURE_DB_URL = os.getenv("SIMULATION_CAPTURE_DB_URL")


if SIMULATION_CAPTURE_DB_URL is None:
    raise ValueError("Simulation db url failed to load")

# Define schema name
SCHEMA_NAME = "gptSchema"

# Create engine
engine = create_engine(SIMULATION_CAPTURE_DB_URL, echo=True)

# Create schema if not exists
with engine.connect() as conn:
    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_NAME}"'))
    conn.commit()

# Base model with explicit schema
Base = declarative_base()


# Example model with schema specified
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)


class TypingSession(Base):
    __tablename__ = "typing_sessions"
    __table_args__ = {"schema": SCHEMA_NAME}

    id = Column(Integer, primary_key=True)
    letters = Column(String, nullable=False)


# Create all tables in the schema
Base.metadata.create_all(engine)

# Verify tables exist in the schema
inspector = inspect(engine)
tables_in_schema = inspector.get_table_names(schema=SCHEMA_NAME)
print(f"Tables in schema '{SCHEMA_NAME}': {tables_in_schema}")
