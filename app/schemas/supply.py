from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Import enums from the model
from app.models.supply import SupplyCategory, UnitType, TransactionStatus

# Supply Schemas

class SupplyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Supply name")
    description: Optional[str] = Field(None, description="Supply description")
    category: SupplyCategory = Field(..., description="Supply category")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    model_number: Optional[str] = Field(None, max_length=100, description="Model number")
    
    # Units and Packaging
    unit_type: UnitType = Field(..., description="Unit of measurement")
    package_size: Optional[float] = Field(None, gt=0, description="Package size")
    package_unit: Optional[str] = Field(None, max_length=20, description="Package unit")
    
    # Inventory Management
    current_stock: Optional[float] = Field(0.0, ge=0, description="Current stock level")
    min_stock_level: Optional[float] = Field(None, ge=0, description="Minimum stock level")
    max_stock_level: Optional[float] = Field(None, ge=0, description="Maximum stock level")
    reorder_point: Optional[float] = Field(None, ge=0, description="Reorder point")
    
    # Cost Information
    last_cost_per_unit: Optional[float] = Field(None, ge=0, description="Last cost per unit")
    average_cost_per_unit: Optional[float] = Field(None, ge=0, description="Average cost per unit")
    estimated_monthly_usage: Optional[float] = Field(None, ge=0, description="Estimated monthly usage")
    
    # Supplier Information
    preferred_supplier_id: Optional[int] = Field(None, description="Preferred supplier ID")
    supplier_product_code: Optional[str] = Field(None, max_length=100, description="Supplier product code")
    
    # Storage Information
    storage_location: Optional[str] = Field(None, max_length=200, description="Storage location")
    storage_requirements: Optional[str] = Field(None, description="Storage requirements")
    
    # Product Details
    expiration_tracking: Optional[bool] = Field(False, description="Track expiration dates")
    typical_shelf_life_days: Optional[int] = Field(None, ge=1, description="Typical shelf life in days")
    
    # Status
    is_active: Optional[bool] = Field(True, description="Whether supply is active")
    is_discontinued: Optional[bool] = Field(False, description="Whether supply is discontinued")

    @validator('max_stock_level')
    def validate_max_stock(cls, v, values):
        if v is not None and 'min_stock_level' in values and values['min_stock_level'] is not None:
            if v <= values['min_stock_level']:
                raise ValueError('Max stock level must be greater than min stock level')
        return v

class SupplyCreate(SupplyBase):
    pass

class SupplyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[SupplyCategory] = None
    brand: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    unit_type: Optional[UnitType] = None
    package_size: Optional[float] = Field(None, gt=0)
    package_unit: Optional[str] = Field(None, max_length=20)
    current_stock: Optional[float] = Field(None, ge=0)
    min_stock_level: Optional[float] = Field(None, ge=0)
    max_stock_level: Optional[float] = Field(None, ge=0)
    reorder_point: Optional[float] = Field(None, ge=0)
    last_cost_per_unit: Optional[float] = Field(None, ge=0)
    average_cost_per_unit: Optional[float] = Field(None, ge=0)
    estimated_monthly_usage: Optional[float] = Field(None, ge=0)
    preferred_supplier_id: Optional[int] = None
    supplier_product_code: Optional[str] = Field(None, max_length=100)
    storage_location: Optional[str] = Field(None, max_length=200)
    storage_requirements: Optional[str] = None
    expiration_tracking: Optional[bool] = None
    typical_shelf_life_days: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    is_discontinued: Optional[bool] = None

class SupplyResponse(SupplyBase):
    id: int
    uuid: str
    is_low_stock: bool
    estimated_days_remaining: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Supplier Schemas

class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    business_name: Optional[str] = Field(None, max_length=200, description="Business name")
    description: Optional[str] = Field(None, description="Supplier description")
    
    # Contact Information
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=200, description="Email address")
    website: Optional[str] = Field(None, max_length=200, description="Website URL")
    
    # Address Information
    address_line1: Optional[str] = Field(None, max_length=200, description="Address line 1")
    address_line2: Optional[str] = Field(None, max_length=200, description="Address line 2")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP code")
    country: Optional[str] = Field("USA", max_length=100, description="Country")
    
    # Business Information
    payment_terms: Optional[str] = Field(None, max_length=100, description="Payment terms")
    shipping_policy: Optional[str] = Field(None, description="Shipping policy")
    minimum_order: Optional[float] = Field(None, ge=0, description="Minimum order amount")
    
    # Preferences
    is_preferred: Optional[bool] = Field(False, description="Whether supplier is preferred")
    is_active: Optional[bool] = Field(True, description="Whether supplier is active")
    credit_limit: Optional[float] = Field(None, ge=0, description="Credit limit")
    rating: Optional[float] = Field(None, ge=1, le=5, description="Rating (1-5 stars)")

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    business_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    website: Optional[str] = Field(None, max_length=200)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    payment_terms: Optional[str] = Field(None, max_length=100)
    shipping_policy: Optional[str] = None
    minimum_order: Optional[float] = Field(None, ge=0)
    is_preferred: Optional[bool] = None
    is_active: Optional[bool] = None
    credit_limit: Optional[float] = Field(None, ge=0)
    rating: Optional[float] = Field(None, ge=1, le=5)

class SupplierResponse(SupplierBase):
    id: int
    uuid: str
    total_orders: int
    total_spent: float
    average_delivery_days: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Transaction Schemas

class TransactionBase(BaseModel):
    transaction_number: Optional[str] = Field(None, max_length=100, description="Transaction number")
    purchase_date: date = Field(..., description="Purchase date")
    delivered_date: Optional[date] = Field(None, description="Delivered date")
    
    supplier_id: Optional[int] = Field(None, description="Supplier ID")
    vendor_name: str = Field(..., min_length=1, max_length=200, description="Vendor name")
    
    # Financial Information
    subtotal: Optional[float] = Field(None, ge=0, description="Subtotal amount")
    tax_amount: Optional[float] = Field(None, ge=0, description="Tax amount")
    shipping_cost: Optional[float] = Field(None, ge=0, description="Shipping cost")
    discount_amount: Optional[float] = Field(None, ge=0, description="Discount amount")
    total_amount: float = Field(..., ge=0, description="Total amount")
    
    payment_method: Optional[str] = Field(None, max_length=50, description="Payment method")
    
    # Status and Processing
    status: Optional[TransactionStatus] = Field(TransactionStatus.PENDING, description="Transaction status")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[str] = Field(None, max_length=500, description="Tags (comma-separated)")

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    transaction_number: Optional[str] = Field(None, max_length=100)
    purchase_date: Optional[date] = None
    delivered_date: Optional[date] = None
    supplier_id: Optional[int] = None
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    subtotal: Optional[float] = Field(None, ge=0)
    tax_amount: Optional[float] = Field(None, ge=0)
    shipping_cost: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    total_amount: Optional[float] = Field(None, ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    status: Optional[TransactionStatus] = None
    notes: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=500)

class TransactionResponse(TransactionBase):
    id: int
    uuid: str
    receipt_image_path: Optional[str]
    ai_processed: bool
    ai_confidence_score: Optional[float]
    ai_processing_notes: Optional[str]
    manual_review_required: bool
    verified: bool
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    item_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Transaction Item Schemas

class TransactionItemBase(BaseModel):
    item_description: str = Field(..., min_length=1, max_length=500, description="Item description")
    quantity: float = Field(..., gt=0, description="Quantity")
    unit_cost: Optional[float] = Field(None, ge=0, description="Unit cost")
    total_cost: float = Field(..., ge=0, description="Total cost")
    
    unit_type: Optional[str] = Field(None, max_length=50, description="Unit type")
    brand: Optional[str] = Field(None, max_length=100, description="Brand")
    product_code: Optional[str] = Field(None, max_length=100, description="Product code")
    
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    lot_number: Optional[str] = Field(None, max_length=100, description="Lot number")
    
    supply_id: Optional[int] = Field(None, description="Linked supply ID")

class TransactionItemCreate(TransactionItemBase):
    transaction_id: int = Field(..., description="Transaction ID")

class TransactionItemUpdate(BaseModel):
    item_description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[float] = Field(None, gt=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    total_cost: Optional[float] = Field(None, ge=0)
    unit_type: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    product_code: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None
    lot_number: Optional[str] = Field(None, max_length=100)
    supply_id: Optional[int] = None

class TransactionItemResponse(TransactionItemBase):
    id: int
    transaction_id: int
    ai_matched: bool
    ai_confidence: Optional[float]
    manual_review_required: bool
    supply_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Stock Movement Schemas

class StockMovementBase(BaseModel):
    supply_id: int = Field(..., description="Supply ID")
    movement_type: str = Field(..., description="Movement type")
    quantity_change: float = Field(..., description="Quantity change")
    unit_cost: Optional[float] = Field(None, ge=0, description="Unit cost")
    total_cost: Optional[float] = Field(None, ge=0, description="Total cost")
    reason: Optional[str] = Field(None, max_length=200, description="Reason for movement")
    notes: Optional[str] = Field(None, description="Additional notes")
    movement_date: Optional[date] = Field(None, description="Movement date")

class StockMovementCreate(StockMovementBase):
    pass

class StockMovementResponse(StockMovementBase):
    id: int
    previous_stock: float
    new_stock: float
    supply_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# AI Receipt Processing Schemas

class ReceiptProcessingRequest(BaseModel):
    receipt_image: str = Field(..., description="Base64 encoded receipt image")
    image_type: str = Field(..., description="Image MIME type")
    vendor_name_hint: Optional[str] = Field(None, description="Vendor name hint")
    expected_total: Optional[float] = Field(None, ge=0, description="Expected total amount")

class ReceiptProcessingResponse(BaseModel):
    transaction_id: int
    vendor_name: str
    purchase_date: Optional[date]
    total_amount: float
    line_items: List[dict]
    confidence_score: float
    processing_notes: str
    manual_review_required: bool

# Dashboard and Analytics Schemas

class InventoryDashboard(BaseModel):
    total_supplies: int
    low_stock_count: int
    out_of_stock_count: int
    total_inventory_value: float
    monthly_spending: float
    top_categories: List[dict]
    recent_transactions: List[dict]
    low_stock_items: List[dict]

class SupplyAnalytics(BaseModel):
    supply_id: int
    supply_name: str
    category: str
    usage_trend: List[dict]  # Monthly usage data
    cost_trend: List[dict]   # Cost over time
    stock_alerts: List[str]  # Current alerts
    supplier_performance: Optional[dict]

# Filtering Schemas

class SupplyFilterParams(BaseModel):
    category: Optional[SupplyCategory] = None
    low_stock_only: Optional[bool] = False
    active_only: Optional[bool] = True
    supplier_id: Optional[int] = None
    search: Optional[str] = None

class TransactionFilterParams(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    supplier_id: Optional[int] = None
    vendor_name: Optional[str] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    status: Optional[TransactionStatus] = None
    unverified_only: Optional[bool] = False