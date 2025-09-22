# Import all models to ensure they're registered with SQLAlchemy
from .horse import Horse
from .event import Event, EventType_Config
from .supply import Supply, Supplier, Transaction, TransactionItem, StockMovement
from .health import HealthRecord, FeedingRecord
from .horse_document import HorseDocument, HorseDocumentAssociation
from .whiteboard import WhiteboardPost, WhiteboardComment, WhiteboardAttachment

__all__ = [
    "Horse",
    "Event",
    "EventType_Config",
    "Supply",
    "Supplier",
    "Transaction",
    "TransactionItem",
    "StockMovement",
    "HealthRecord",
    "FeedingRecord",
    "HorseDocument",
    "HorseDocumentAssociation",
    "WhiteboardPost",
    "WhiteboardComment",
    "WhiteboardAttachment"
]