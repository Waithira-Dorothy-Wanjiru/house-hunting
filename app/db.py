from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Base class for models
Base = declarative_base()

# SQLite database URL
DATABASE_URL = "sqlite:///house_hunting.db"  # ensure this matches Alembic

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite
    echo=True  # logs SQL statements (optional)
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
