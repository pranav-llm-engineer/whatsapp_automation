from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from backend.config import SQLITE_DB_PATH, DATABASE_URL

def get_engine():
    if DATABASE_URL:
        db_url = DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        try:
            eng = create_engine(db_url)
            # Test connection
            with eng.connect() as conn:
                pass
            print("Successfully connected to Supabase PostgreSQL.")
            return eng
        except Exception as e:
            print(f"Warning: Failed to connect to Supabase PostgreSQL ({e}). Falling back to local SQLite.")
            
    # Ensure directory exists for local sqlite
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
    print("Using local SQLite database.")
    return create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
