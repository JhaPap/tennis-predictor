from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

# Sports data DB (committed to git, read-mostly)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# User DB (persistent disk in production, separate from sports data)
_user_db_path = os.environ.get("USER_DB_PATH", str(DB_PATH.parent / "users.db"))
Path(_user_db_path).parent.mkdir(parents=True, exist_ok=True)
USER_DATABASE_URL = f"sqlite:///{_user_db_path}"

user_engine = create_engine(
    USER_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
UserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)
UserBase = declarative_base()
