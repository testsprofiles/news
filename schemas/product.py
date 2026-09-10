from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category_id: int = Field(..., gt=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = Field(None, gt=0)


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)