import os

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get("LOCKER_DB_URL", "sqlite:///./memories.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
