from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", os.getenv("DATABASE_HOST", "localhost"))
DB_PORT = os.getenv("POSTGRES_PORT", os.getenv("DATABASE_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB")

missing = [
    name for name, value in {
        "POSTGRES_USER": DB_USER,
        "POSTGRES_PASSWORD": DB_PASSWORD,
        "POSTGRES_DB": DB_NAME,
    }.items()
    if not value
]

if missing:
    raise RuntimeError(f"Missing database environment variables: {missing}")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

logging.info("Database engine initialized for host=%s port=%s db=%s", DB_HOST, DB_PORT, DB_NAME)