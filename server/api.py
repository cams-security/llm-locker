from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# .env lives at the repo root (one level above server/), shared with the
# Node MCP client — not next to this file, so cwd-based discovery won't
# find it once this runs from within server/.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, select

from auth import require_api_key
from db import create_db_and_tables, get_session
from models import Memory, MemoryCreate, MemoryRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Locker Memory API", lifespan=lifespan)


@app.get("/")
def health() -> dict:
    return {"status": "ok"}


@app.post("/memories", response_model=MemoryRead, dependencies=[Depends(require_api_key)])
def write_memory(memory: MemoryCreate, session: Session = Depends(get_session)) -> Memory:
    db_memory = Memory.model_validate(memory)
    session.add(db_memory)
    session.commit()
    session.refresh(db_memory)
    return db_memory


@app.get("/memories", response_model=List[MemoryRead], dependencies=[Depends(require_api_key)])
def list_memories(
    type: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> List[Memory]:
    statement = select(Memory).order_by(Memory.created_at.desc())
    if type:
        statement = statement.where(Memory.type == type)
    results = session.exec(statement).all()
    if tag:
        # Exact membership check in Python: SQLite has no reliable JSON-array
        # containment operator (unlike Postgres's `@>`), and this is cheap at
        # personal-use scale. Revisit once on Postgres (see BACKLOG.md).
        results = [memory for memory in results if tag in memory.tags]
    return results


@app.get("/memories/{memory_id}", response_model=MemoryRead, dependencies=[Depends(require_api_key)])
def get_memory(memory_id: int, session: Session = Depends(get_session)) -> Memory:
    memory = session.get(Memory, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory
