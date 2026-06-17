import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATA_DIR = os.getenv("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{DATA_DIR}/data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

SERVER_PORT = int(os.getenv("PORT", os.getenv("SERVER_PORT", "9002")))
SECRET_KEY = os.getenv("SECRET_KEY", "happy-run-secret-key-2026")
