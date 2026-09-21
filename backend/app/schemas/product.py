from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ProductBase(BaseModel):
    product_name: str
    brand_name: Optional[str] = None
    category: str = "Packaged Food"
    manufacturer_name: Optional[str] = None
    declared_net_quantity: Optional[str] = None
    declared_mrp: Optional[str] = None
    barcode: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    latest_compliance_status: str
    inspection_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductHistoryItem(BaseModel):
    scan_id: str
    created_at: datetime
    status: str
    compliance_score: float
    overall_compliance_verdict: str
    inspector_name: Optional[str] = None
    violations_count: int
    image_url: str

class ProductHistoryResponse(BaseModel):
    product: ProductResponse
    inspections: List[ProductHistoryItem]
