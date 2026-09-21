import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
# Handle postgresql:// vs postgresql+psycopg2:// if needed
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if "sqlite" in db_url:
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    try:
        connect_args = {}
        if "postgresql" in db_url:
            connect_args["connect_timeout"] = 3

        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=3,
            connect_args=connect_args
        )
        # Test connection
        with engine.connect() as conn:
            pass
    except Exception as e:
        logger.warning(f"Could not connect to configured DB ({db_url}): {e}. Falling back to local SQLite database.")
        sqlite_path = os.path.join(os.path.dirname(__file__), "..", "legalmetro.db")
        db_url = f"sqlite:///{os.path.abspath(sqlite_path)}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
