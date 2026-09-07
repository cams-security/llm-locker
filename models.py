from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class MemoryBase(SQLModel):
    type: str = Field(
        index=True, description="One of: 'memory' (facts to recall), 'tool' (reference info about an external tool/API), 'note' (anything else)"
    )
    content: str
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON), description="list of keywords, e.g. ['preferences', 'denver']")


class Memory(MemoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryCreate(MemoryBase):
    pass


class MemoryRead(MemoryBase):
    id: int
    created_at: datetime
