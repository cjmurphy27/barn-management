from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional
from datetime import datetime, date, timedelta
import logging
import os
import uuid
import base64

from app.database import get_db
from app.models.supply import (
    Supply, Supplier, Transaction, TransactionItem, StockMovement,
    SupplyCategory, UnitType, TransactionStatus
)
from app.schemas.supply import (
    SupplyCreate, SupplyUpdate, SupplyResponse,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionItemCreate, TransactionItemUpdate, TransactionItemResponse,
    StockMovementCreate, StockMovementResponse,
    ReceiptProcessingRequest, ReceiptProcessingResponse,
    InventoryDashboard, SupplyFilterParams, TransactionFilterParams
)
from app.services.receipt_processor import receipt_processor

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/supplies", tags=["supplies"])

# Supply CRUD Operations

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_supply(
    supply: SupplyCreate,
    db: Session = Depends(get_db)
):
    """Create a new supply item"""
    try:
        # Check for duplicate name in same category
        existing = db.query(Supply).filter(
            and_(
                Supply.name == supply.name,
                Supply.category == supply.category,
                Supply.is_active == True
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supply '{supply.name}' already exists in category '{supply.category.value}'"
            )
        
        # Create new supply
        db_supply = Supply(**supply.dict())
        
        db.add(db_supply)
        db.commit()
        db.refresh(db_supply)
        
        logger.info(f"Created supply: {db_supply.name}")
        return db_supply.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating supply: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create supply"
        )

@router.get("/")
async def get_supplies(
    db: Session = Depends(get_db),
    category: Optional[SupplyCategory] = Query(None, description="Filter by category"),
    low_stock_only: Optional[bool] = Query(False, description="Show only low stock items"),
    active_only: Optional[bool] = Query(True, description="Show only active items"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    limit: Optional[int] = Query(100, le=1000, description="Limit results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    """Get supplies with optional filtering"""
    try:
        query = db.query(Supply)
        
        # Apply filters
        if category:
            query = query.filter(Supply.category == category)
        if active_only:
            query = query.filter(Supply.is_active == True)
        if supplier_id:
            query = query.filter(Supply.preferred_supplier_id == supplier_id)
        if search:
            query = query.filter(
                or_(
                    Supply.name.ilike(f"%{search}%"),
                    Supply.description.ilike(f"%{search}%"),
                    Supply.brand.ilike(f"%{search}%")
                )
            )
        
        # Order by name
        query = query.order_by(asc(Supply.name))
        
        # Apply pagination
        supplies = query.offset(offset).limit(limit).all()
        
        # Convert to dict and filter low stock if requested
        result = []
        for supply in supplies:
            supply_dict = supply.to_dict()
            if low_stock_only and not supply.is_low_stock:
                continue
            result.append(supply_dict)
        
        logger.info(f"Retrieved {len(result)} supplies with filters applied")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving supplies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supplies"
        )

@router.get("/dashboard")
async def get_supply_dashboard(db: Session = Depends(get_db)):
    """Get supply dashboard analytics"""
    try:
        # Basic counts
        total_supplies = db.query(Supply).filter(Supply.is_active == True).count()
        
        # Low stock items
        low_stock_items = []
        supplies = db.query(Supply).filter(Supply.is_active == True).all()
        low_stock_count = 0
        out_of_stock_count = 0
        total_value = 0.0
        
        for supply in supplies:
            if supply.current_stock <= 0:
                out_of_stock_count += 1
            elif supply.is_low_stock:
                low_stock_count += 1
                low_stock_items.append({
                    "id": supply.id,
                    "name": supply.name,
                    "current_stock": supply.current_stock,
                    "reorder_point": supply.reorder_point,
                    "estimated_days_remaining": supply.estimated_days_remaining
                })
            
            # Calculate inventory value
            if supply.current_stock and supply.average_cost_per_unit:
                total_value += supply.current_stock * supply.average_cost_per_unit
        
        # Monthly spending (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        monthly_spending = db.query(func.sum(Transaction.total_amount)).filter(
            Transaction.purchase_date >= thirty_days_ago
        ).scalar() or 0.0
        
        # Top categories by spending
        category_spending = db.query(
            Supply.category,
            func.sum(TransactionItem.total_cost).label('total_spent')
        ).join(
            TransactionItem, Supply.id == TransactionItem.supply_id
        ).join(
            Transaction, TransactionItem.transaction_id == Transaction.id
        ).filter(
            Transaction.purchase_date >= thirty_days_ago
        ).group_by(Supply.category).order_by(desc('total_spent')).limit(5).all()
        
        top_categories = [
            {"category": cat.value, "amount": float(amount)} 
            for cat, amount in category_spending
        ]
        
        # Recent transactions
        recent_transactions = db.query(Transaction).order_by(
            desc(Transaction.purchase_date)
        ).limit(5).all()
        
        recent_list = [
            {
                "id": t.id,
                "vendor_name": t.vendor_name,
                "total_amount": t.total_amount,
                "purchase_date": t.purchase_date.isoformat(),
                "status": t.status.value
            }
            for t in recent_transactions
        ]
        
        return {
            "total_supplies": total_supplies,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_inventory_value": total_value,
            "monthly_spending": monthly_spending,
            "top_categories": top_categories,
            "recent_transactions": recent_list,
            "low_stock_items": low_stock_items[:10]  # Limit to top 10
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dashboard"
        )

@router.get("/{supply_id}")
async def get_supply(supply_id: int, db: Session = Depends(get_db)):
    """Get a specific supply by ID"""
    supply = db.query(Supply).filter(Supply.id == supply_id).first()
    
    if not supply:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supply with ID {supply_id} not found"
        )
    
    return supply.to_dict()

@router.put("/{supply_id}")
async def update_supply(
    supply_id: int,
    supply_update: SupplyUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing supply"""
    try:
        db_supply = db.query(Supply).filter(Supply.id == supply_id).first()
        if not db_supply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supply with ID {supply_id} not found"
            )
        
        # Update fields
        update_data = supply_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_supply, field, value)
        
        db.commit()
        db.refresh(db_supply)
        
        logger.info(f"Updated supply: {db_supply.name}")
        return db_supply.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating supply {supply_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update supply"
        )

@router.delete("/{supply_id}")
async def delete_supply(supply_id: int, db: Session = Depends(get_db)):
    """Delete a supply (soft delete by marking as inactive)"""
    try:
        db_supply = db.query(Supply).filter(Supply.id == supply_id).first()
        if not db_supply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supply with ID {supply_id} not found"
            )
        
        # Soft delete
        db_supply.is_active = False
        db.commit()
        
        logger.info(f"Deleted supply: {db_supply.name}")
        return {"message": f"Supply '{db_supply.name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting supply {supply_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete supply"
        )

# Supplier CRUD Operations

@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db)
):
    """Create a new supplier"""
    try:
        # Check for duplicate name
        existing = db.query(Supplier).filter(
            Supplier.name == supplier.name,
            Supplier.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supplier '{supplier.name}' already exists"
            )
        
        db_supplier = Supplier(**supplier.dict())
        
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        
        logger.info(f"Created supplier: {db_supplier.name}")
        return db_supplier.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating supplier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create supplier"
        )

@router.get("/suppliers")
async def get_suppliers(
    db: Session = Depends(get_db),
    active_only: Optional[bool] = Query(True, description="Show only active suppliers"),
    preferred_only: Optional[bool] = Query(False, description="Show only preferred suppliers"),
    limit: Optional[int] = Query(100, le=1000, description="Limit results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    """Get suppliers with optional filtering"""
    try:
        query = db.query(Supplier)
        
        if active_only:
            query = query.filter(Supplier.is_active == True)
        if preferred_only:
            query = query.filter(Supplier.is_preferred == True)
        
        # Order by preferred first, then by name
        query = query.order_by(desc(Supplier.is_preferred), asc(Supplier.name))
        
        suppliers = query.offset(offset).limit(limit).all()
        
        result = [supplier.to_dict() for supplier in suppliers]
        
        logger.info(f"Retrieved {len(result)} suppliers")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving suppliers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve suppliers"
        )

# Transaction and Receipt Processing

@router.post("/transactions/process-receipt", status_code=status.HTTP_201_CREATED)
async def process_receipt(
    receipt_image: UploadFile = File(...),
    vendor_hint: Optional[str] = Form(None),
    expected_total: Optional[float] = Form(None)
):
    """Process a receipt image using AI"""
    try:
        # Validate file type
        if not receipt_image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read and encode image
        image_data = await receipt_image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Process with AI
        result = receipt_processor.process_receipt(
            image_base64,
            receipt_image.content_type,
            vendor_hint,
            expected_total
        )
        
        if not result.get("success", False):
            return {
                "success": False,
                "error": result.get("error", "Processing failed"),
                "manual_review_required": True
            }
        
        # Save receipt image
        receipt_path = await save_receipt_image(receipt_image, image_data)
        
        # Create transaction record
        db = next(get_db())
        try:
            # Create transaction
            transaction_data = {
                "vendor_name": result["vendor_name"],
                "purchase_date": result["purchase_date"] or date.today(),
                "total_amount": result["total_amount"],
                "subtotal": result.get("subtotal"),
                "tax_amount": result.get("tax_amount"),
                "receipt_image_path": receipt_path,
                "ai_processed": True,
                "ai_confidence_score": result["confidence_score"],
                "ai_processing_notes": result.get("notes", ""),
                "manual_review_required": result["manual_review_required"],
                "status": TransactionStatus.PROCESSED if not result["manual_review_required"] else TransactionStatus.PENDING
            }
            
            db_transaction = Transaction(**transaction_data)
            db.add(db_transaction)
            db.flush()  # Get the ID without committing
            
            # Create transaction items
            line_items = []
            for item in result.get("line_items", []):
                item_data = {
                    "transaction_id": db_transaction.id,
                    "item_description": item["description"],
                    "quantity": item["quantity"],
                    "unit_cost": item.get("unit_price"),
                    "total_cost": item["total_price"],
                    "product_code": item.get("product_code"),
                    "brand": item.get("brand"),
                    "ai_confidence": item.get("confidence", 0.5)
                }
                
                db_item = TransactionItem(**item_data)
                db.add(db_item)
                line_items.append(item)
            
            db.commit()
            db.refresh(db_transaction)
            
            logger.info(f"Successfully processed receipt for {result['vendor_name']}")
            
            return {
                "success": True,
                "transaction_id": db_transaction.id,
                "vendor_name": result["vendor_name"],
                "total_amount": result["total_amount"],
                "line_items": line_items,
                "confidence_score": result["confidence_score"],
                "manual_review_required": result["manual_review_required"]
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process receipt"
        )

@router.get("/transactions")
async def get_transactions(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    vendor_name: Optional[str] = Query(None, description="Filter by vendor name"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    status: Optional[TransactionStatus] = Query(None, description="Filter by status"),
    unverified_only: Optional[bool] = Query(False, description="Show only unverified transactions"),
    limit: Optional[int] = Query(100, le=1000, description="Limit results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
):
    """Get transactions with optional filtering"""
    try:
        query = db.query(Transaction)
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.purchase_date >= start_date)
        if end_date:
            query = query.filter(Transaction.purchase_date <= end_date)
        if supplier_id:
            query = query.filter(Transaction.supplier_id == supplier_id)
        if vendor_name:
            query = query.filter(Transaction.vendor_name.ilike(f"%{vendor_name}%"))
        if min_amount:
            query = query.filter(Transaction.total_amount >= min_amount)
        if max_amount:
            query = query.filter(Transaction.total_amount <= max_amount)
        if status:
            query = query.filter(Transaction.status == status)
        if unverified_only:
            query = query.filter(Transaction.verified == False)
        
        # Order by purchase date (newest first)
        query = query.order_by(desc(Transaction.purchase_date))
        
        # Apply pagination
        transactions = query.offset(offset).limit(limit).all()
        
        result = [transaction.to_dict() for transaction in transactions]
        
        logger.info(f"Retrieved {len(result)} transactions")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions"
        )

@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a specific transaction with line items"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Get transaction items
    items = db.query(TransactionItem).filter(
        TransactionItem.transaction_id == transaction_id
    ).all()
    
    result = transaction.to_dict()
    result["items"] = [item.to_dict() for item in items]
    
    return result


# Stock Management

@router.post("/stock-movements", status_code=status.HTTP_201_CREATED)
async def create_stock_movement(
    movement: StockMovementCreate,
    db: Session = Depends(get_db)
):
    """Create a stock movement (manual adjustment)"""
    try:
        # Get current supply
        supply = db.query(Supply).filter(Supply.id == movement.supply_id).first()
        if not supply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supply with ID {movement.supply_id} not found"
            )
        
        # Create stock movement record
        movement_data = movement.dict()
        movement_data["previous_stock"] = supply.current_stock
        movement_data["new_stock"] = supply.current_stock + movement.quantity_change
        
        db_movement = StockMovement(**movement_data)
        db.add(db_movement)
        
        # Update supply stock level
        supply.current_stock = movement_data["new_stock"]
        
        # Update cost information if provided
        if movement.unit_cost:
            supply.last_cost_per_unit = movement.unit_cost
            
            # Recalculate average cost (simple moving average)
            if supply.average_cost_per_unit:
                supply.average_cost_per_unit = (supply.average_cost_per_unit + movement.unit_cost) / 2
            else:
                supply.average_cost_per_unit = movement.unit_cost
        
        db.commit()
        db.refresh(db_movement)
        
        logger.info(f"Created stock movement for {supply.name}")
        return db_movement.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating stock movement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create stock movement"
        )

async def save_receipt_image(receipt_file: UploadFile, image_data: bytes) -> str:
    """Save receipt image to storage directory"""
    
    # Create storage directory
    storage_dir = "storage/receipts"
    os.makedirs(storage_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = receipt_file.filename.split('.')[-1] if '.' in receipt_file.filename else 'jpg'
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(storage_dir, filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(image_data)
    
    return file_path