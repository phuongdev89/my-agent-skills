from pydantic import BaseModel
from typing import List, Optional

class ProductPrice(BaseModel):
    current_price: float
    original_price: Optional[float] = None
    currency: str
    discount_rate: Optional[float] = None

class ImageItem(BaseModel):
    url: str
    alt: Optional[str] = None
    is_cover: bool = False

class ShoppingProduct(BaseModel):
    title: str
    images: List[str]
    description: Optional[str] = None
    price: ProductPrice
    platform: Optional[str] = None
    source_url: str
