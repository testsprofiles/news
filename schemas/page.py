from pydantic import BaseModel
from typing import Optional


class PageCreate(BaseModel):
    title: str
    content: str
    slug: str


class PageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    slug: Optional[str] = None