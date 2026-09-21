from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False, index=True)
    brand_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False, default="Packaged Food", index=True)
    manufacturer_name = Column(String(255), nullable=True)
    declared_net_quantity = Column(String(100), nullable=True)
    declared_mrp = Column(String(100), nullable=True)
    barcode = Column(String(100), nullable=True, index=True)
    latest_compliance_status = Column(String(50), default="PENDING")
    inspection_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scans = relationship("ScanJob", back_populates="product", cascade="all, delete-orphan")
