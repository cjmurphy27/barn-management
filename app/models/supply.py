from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional
import uuid
import enum

from app.database import Base

class SupplyCategory(str, enum.Enum):
    FEED_NUTRITION = "feed_nutrition"
    BEDDING = "bedding"
    HEALTH_MEDICAL = "health_medical"
    FACILITY_MAINTENANCE = "facility_maintenance"
    TACK_EQUIPMENT = "tack_equipment"
    GROOMING = "grooming"
    OTHER = "other"

class UnitType(str, enum.Enum):
    BAGS = "bags"
    BALES = "bales"
    POUNDS = "pounds"
    GALLONS = "gallons"
    BOTTLES = "bottles"
    BOXES = "boxes"
    EACH = "each"
    YARDS = "yards"
    ROLLS = "rolls"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    VERIFIED = "verified"
    ERROR = "error"

class Supply(Base):
    """Inventory items and supply catalog"""
    __tablename__ = "supplies"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic Information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(Enum(SupplyCategory), nullable=False, index=True)
    brand = Column(String(100), nullable=True)
    model_number = Column(String(100), nullable=True)
    
    # Units and Packaging
    unit_type = Column(Enum(UnitType), nullable=False)
    package_size = Column(Float, nullable=True)  # e.g., 50 for "50 lb bag"
    package_unit = Column(String(20), nullable=True)  # e.g., "lbs", "oz"
    
    # Inventory Management
    current_stock = Column(Float, default=0.0, nullable=False)
    min_stock_level = Column(Float, nullable=True)
    max_stock_level = Column(Float, nullable=True)
    reorder_point = Column(Float, nullable=True)
    
    # Cost Information
    last_cost_per_unit = Column(Float, nullable=True)
    average_cost_per_unit = Column(Float, nullable=True)
    estimated_monthly_usage = Column(Float, nullable=True)
    
    # Supplier Information
    preferred_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier_product_code = Column(String(100), nullable=True)
    
    # Storage Information
    storage_location = Column(String(200), nullable=True)
    storage_requirements = Column(Text, nullable=True)  # e.g., "Keep dry", "Refrigerate"
    
    # Product Details
    expiration_tracking = Column(Boolean, default=False)
    typical_shelf_life_days = Column(Integer, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_discontinued = Column(Boolean, default=False)
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    preferred_supplier = relationship("Supplier", back_populates="supplies")
    transaction_items = relationship("TransactionItem", back_populates="supply", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovement", back_populates="supply", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Supply(name='{self.name}', category='{self.category}')>"
    
    @property
    def is_low_stock(self) -> bool:
        """Check if item is below reorder point or min stock level"""
        if self.reorder_point and self.current_stock <= self.reorder_point:
            return True
        if self.min_stock_level and self.current_stock <= self.min_stock_level:
            return True
        return False
    
    @property
    def estimated_days_remaining(self) -> Optional[int]:
        """Estimate days until stock runs out based on usage"""
        if not self.estimated_monthly_usage or self.estimated_monthly_usage <= 0:
            return None
        if self.current_stock <= 0:
            return 0
        
        daily_usage = self.estimated_monthly_usage / 30
        return int(self.current_stock / daily_usage)
    
    def to_dict(self) -> dict:
        """Convert supply object to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if self.category else None,
            "brand": self.brand,
            "model_number": self.model_number,
            "unit_type": self.unit_type.value if self.unit_type else None,
            "package_size": self.package_size,
            "package_unit": self.package_unit,
            "current_stock": self.current_stock,
            "min_stock_level": self.min_stock_level,
            "max_stock_level": self.max_stock_level,
            "reorder_point": self.reorder_point,
            "last_cost_per_unit": self.last_cost_per_unit,
            "average_cost_per_unit": self.average_cost_per_unit,
            "estimated_monthly_usage": self.estimated_monthly_usage,
            "preferred_supplier_id": self.preferred_supplier_id,
            "supplier_product_code": self.supplier_product_code,
            "storage_location": self.storage_location,
            "storage_requirements": self.storage_requirements,
            "expiration_tracking": self.expiration_tracking,
            "typical_shelf_life_days": self.typical_shelf_life_days,
            "is_active": self.is_active,
            "is_discontinued": self.is_discontinued,
            "is_low_stock": self.is_low_stock,
            "estimated_days_remaining": self.estimated_days_remaining,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Supplier(Base):
    """Vendors and suppliers for supplies"""
    __tablename__ = "suppliers"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic Information
    name = Column(String(200), nullable=False, index=True)
    business_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Contact Information
    contact_person = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    website = Column(String(200), nullable=True)
    
    # Address Information
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), default="USA")
    
    # Business Information
    tax_id = Column(String(50), nullable=True)
    payment_terms = Column(String(100), nullable=True)  # e.g., "Net 30", "COD"
    shipping_policy = Column(Text, nullable=True)
    minimum_order = Column(Float, nullable=True)
    
    # Preferences and Status
    is_preferred = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    credit_limit = Column(Float, nullable=True)
    
    # Performance Tracking
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    average_delivery_days = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)  # 1-5 star rating
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplies = relationship("Supply", back_populates="preferred_supplier")
    transactions = relationship("Transaction", back_populates="supplier")
    
    def __repr__(self):
        return f"<Supplier(name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """Convert supplier object to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "business_name": self.business_name,
            "description": self.description,
            "contact_person": self.contact_person,
            "phone_number": self.phone_number,
            "email": self.email,
            "website": self.website,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "payment_terms": self.payment_terms,
            "shipping_policy": self.shipping_policy,
            "minimum_order": self.minimum_order,
            "is_preferred": self.is_preferred,
            "is_active": self.is_active,
            "credit_limit": self.credit_limit,
            "total_orders": self.total_orders,
            "total_spent": self.total_spent,
            "average_delivery_days": self.average_delivery_days,
            "rating": self.rating,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Transaction(Base):
    """Purchase transactions from suppliers"""
    __tablename__ = "transactions"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Transaction Information
    transaction_number = Column(String(100), nullable=True, index=True)  # Invoice/Receipt number
    purchase_date = Column(Date, nullable=False, index=True)
    delivered_date = Column(Date, nullable=True)
    
    # Supplier Information
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    vendor_name = Column(String(200), nullable=False)  # From receipt OCR, may not match supplier
    
    # Financial Information
    subtotal = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    shipping_cost = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    
    # Payment Information
    payment_method = Column(String(50), nullable=True)  # Cash, Credit Card, Check, etc.
    
    # Receipt Processing
    receipt_image_path = Column(String(500), nullable=True)
    ai_processed = Column(Boolean, default=False)
    ai_confidence_score = Column(Float, nullable=True)
    ai_processing_notes = Column(Text, nullable=True)
    manual_review_required = Column(Boolean, default=False)
    
    # Status
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Additional Information
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")
    
    def __repr__(self):
        total_str = f"${self.total_amount:.2f}" if self.total_amount is not None else "No total"
        return f"<Transaction(vendor='{self.vendor_name}', total={total_str})>"
    
    @property
    def item_count(self) -> int:
        """Count of line items in transaction"""
        return len(self.items) if self.items else 0
    
    def to_dict(self) -> dict:
        """Convert transaction object to dictionary for API responses"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "transaction_number": self.transaction_number,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "delivered_date": self.delivered_date.isoformat() if self.delivered_date else None,
            "supplier_id": self.supplier_id,
            "vendor_name": self.vendor_name,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "shipping_cost": self.shipping_cost,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "payment_method": self.payment_method,
            "receipt_image_path": self.receipt_image_path,
            "ai_processed": self.ai_processed,
            "ai_confidence_score": self.ai_confidence_score,
            "ai_processing_notes": self.ai_processing_notes,
            "manual_review_required": self.manual_review_required,
            "status": self.status.value if self.status else None,
            "verified": self.verified,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "notes": self.notes,
            "tags": self.tags,
            "item_count": self.item_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class TransactionItem(Base):
    """Individual line items within a transaction"""
    __tablename__ = "transaction_items"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    supply_id = Column(Integer, ForeignKey("supplies.id"), nullable=True, index=True)  # May be null for unrecognized items
    
    # Item Information (from receipt OCR)
    item_description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    
    # Additional Details
    unit_type = Column(String(50), nullable=True)  # From receipt
    brand = Column(String(100), nullable=True)
    product_code = Column(String(100), nullable=True)
    
    # Expiration and Storage
    expiry_date = Column(Date, nullable=True)
    lot_number = Column(String(100), nullable=True)
    
    # AI Processing
    ai_matched = Column(Boolean, default=False)  # Whether AI matched to existing supply
    ai_confidence = Column(Float, nullable=True)
    manual_review_required = Column(Boolean, default=False)
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transaction = relationship("Transaction", back_populates="items")
    supply = relationship("Supply", back_populates="transaction_items")
    
    def __repr__(self):
        return f"<TransactionItem(description='{self.item_description}', qty={self.quantity})>"
    
    def to_dict(self) -> dict:
        """Convert transaction item to dictionary for API responses"""
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "supply_id": self.supply_id,
            "item_description": self.item_description,
            "quantity": self.quantity,
            "unit_cost": self.unit_cost,
            "total_cost": self.total_cost,
            "unit_type": self.unit_type,
            "brand": self.brand,
            "product_code": self.product_code,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "lot_number": self.lot_number,
            "ai_matched": self.ai_matched,
            "ai_confidence": self.ai_confidence,
            "manual_review_required": self.manual_review_required,
            "supply_name": self.supply.name if self.supply else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class StockMovement(Base):
    """Track all stock level changes for inventory management"""
    __tablename__ = "stock_movements"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    supply_id = Column(Integer, ForeignKey("supplies.id"), nullable=False, index=True)
    transaction_item_id = Column(Integer, ForeignKey("transaction_items.id"), nullable=True)
    
    # Movement Information
    movement_type = Column(String(50), nullable=False, index=True)  # "purchase", "usage", "adjustment", "waste"
    quantity_change = Column(Float, nullable=False)  # Positive for increase, negative for decrease
    previous_stock = Column(Float, nullable=False)
    new_stock = Column(Float, nullable=False)
    
    # Additional Information
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    reason = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Multi-tenant support
    organization_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    movement_date = Column(Date, nullable=False, default=lambda: date.today(), index=True)
    
    # Relationships
    supply = relationship("Supply", back_populates="stock_movements")
    transaction_item = relationship("TransactionItem")
    
    def __repr__(self):
        return f"<StockMovement(supply_id={self.supply_id}, change={self.quantity_change})>"
    
    def to_dict(self) -> dict:
        """Convert stock movement to dictionary for API responses"""
        return {
            "id": self.id,
            "supply_id": self.supply_id,
            "transaction_item_id": self.transaction_item_id,
            "movement_type": self.movement_type,
            "quantity_change": self.quantity_change,
            "previous_stock": self.previous_stock,
            "new_stock": self.new_stock,
            "unit_cost": self.unit_cost,
            "total_cost": self.total_cost,
            "reason": self.reason,
            "notes": self.notes,
            "movement_date": self.movement_date.isoformat() if self.movement_date else None,
            "supply_name": self.supply.name if self.supply else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }