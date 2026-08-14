from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class MemoryBase(SQLModel):
    type: str = Field(index=True, description="e.g. 'memory', 'tool', 'note'")
    content: str
    tags: Optional[str] = Field(default=None, description="comma-separated tags")


class Memory(MemoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryCreate(MemoryBase):
    pass


class MemoryRead(MemoryBase):
    id: int
    created_at: datetime
