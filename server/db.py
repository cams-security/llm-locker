import os

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get("LOCKER_DB_URL", "sqlite:///./memories.db")

# check_same_thread is a SQLite-only connect arg; psycopg errors on it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
