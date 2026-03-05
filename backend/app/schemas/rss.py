from pydantic import BaseModel, HttpUrl
from typing import Optional


class GroupIn(BaseModel):
    name: str


class GroupOut(GroupIn):
    id: int

    class Config:
        from_attributes = True


class SourceIn(BaseModel):
    name: str
    url: HttpUrl
    group_id: Optional[int] = None
    enabled: bool = True


class SourceOut(BaseModel):
    id: int
    name: str
    url: str
    group_id: Optional[int]
    enabled: bool

    class Config:
        from_attributes = True


class EntryOut(BaseModel):
    id: int
    source_id: int
    source_name: str
    group_id: Optional[int]
    group_name: str
    title: str
    title_en: str
    title_zh: str
    summary_en: str
    summary_zh: str
    link: str
    published_at: str
    ai_status: str


class ReaderStatsOut(BaseModel):
    source_count: int
    group_count: int
    entry_count: int
