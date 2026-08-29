from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class CategoryCreate(CategoryBase):
    """Yangi category yaratishda ishlatiladi (POST /api/categories)"""
    pass


class CategoryUpdate(BaseModel):
    """Category yangilashda ishlatiladi (PATCH/PUT) — optional"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)


class CategoryOut(BaseModel):
    """Clientga qaytariladigan shakl (GET javoblari)"""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)