from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class PostBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=1)
    category_id: int = Field(..., gt=0)


class PostCreate(PostBase):
    """Yangi post yaratishda ishlatiladi (POST /api/posts)"""
    pass


class PostUpdate(BaseModel):
    """Postni yangilashda ishlatiladi (PATCH/PUT /api/posts/{id}) — hammasi optional"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = Field(None, gt=0)


class PostOut(BaseModel):
    """Clientga qaytariladigan shakl (GET javoblari)"""
    id: int
    title: str
    content: str
    category_id: int
    image_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)