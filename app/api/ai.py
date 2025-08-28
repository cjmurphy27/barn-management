from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models.horse import Horse
from app.services.ai import ai_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

# Pydantic models for requests
class HorseAnalysisRequest(BaseModel):
    horse_id: int
    question: Optional[str] = None
    image: Optional[str] = None  # Base64 encoded image
    image_type: Optional[str] = None  # MIME type

class GeneralQuestionRequest(BaseModel):
    question: str
    include_barn_context: bool = True

class CompareHorsesRequest(BaseModel):
    horse_ids: List[int]
    comparison_question: Optional[str] = None

class AIResponse(BaseModel):
    response: str
    horses_analyzed: Optional[List[str]] = None

# AI Endpoints

@router.post("/analyze-horse", response_model=AIResponse)
async def analyze_horse(
    request: HorseAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI analysis and recommendations for a specific horse
    """
    try:
        # Get horse data
        horse = db.query(Horse).filter(Horse.id == request.horse_id).first()
        
        if not horse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Horse with ID {request.horse_id} not found"
            )
        
        # Convert horse to dict for AI service
        horse_data = horse.to_dict()
        
        # Get AI analysis (with optional image)
        ai_response = ai_service.analyze_horse(
            horse_data, 
            request.question, 
            request.image, 
            request.image_type
        )
        
        logger.info(f"Generated AI analysis for horse {horse.name}")
        
        return AIResponse(
            response=ai_response,
            horses_analyzed=[horse.name]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI horse analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze horse with AI"
        )

@router.post("/general-question", response_model=AIResponse)
async def ask_general_question(
    request: GeneralQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a general horse management question with optional barn context
    """
    try:
        barn_context = None
        
        if request.include_barn_context:
            # Get all active horses for context
            horses = db.query(Horse).filter(Horse.is_active == True).limit(10).all()
            barn_context = [horse.to_dict() for horse in horses]
        
        # Get AI response
        ai_response = ai_service.general_horse_question(request.question, barn_context)
        
        logger.info(f"Generated AI response for general question")
        
        return AIResponse(response=ai_response)
        
    except Exception as e:
        logger.error(f"Error in AI general question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question with AI"
        )

@router.post("/compare-horses", response_model=AIResponse)
async def compare_horses(
    request: CompareHorsesRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple horses using AI analysis
    """
    try:
        if len(request.horse_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 horses are required for comparison"
            )
        
        # Get horse data
        horses = db.query(Horse).filter(Horse.id.in_(request.horse_ids)).all()
        
        if len(horses) != len(request.horse_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more horses not found"
            )
        
        # Convert horses to dict for AI service
        horses_data = [horse.to_dict() for horse in horses]
        horse_names = [horse.name for horse in horses]
        
        # Get AI comparison
        ai_response = ai_service.compare_horses(horses_data, request.comparison_question)
        
        logger.info(f"Generated AI comparison for horses: {', '.join(horse_names)}")
        
        return AIResponse(
            response=ai_response,
            horses_analyzed=horse_names
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI horse comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare horses with AI"
        )

@router.get("/health")
async def ai_health_check():
    """
    Check if AI service is working
    """
    try:
        # Test if we can create the AI service
        test_response = ai_service.general_horse_question("What is the most important thing in horse care?")
        
        return {
            "status": "healthy",
            "ai_service": "connected",
            "test_response_length": len(test_response)
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service unavailable: {str(e)}"
        )

# Horse-specific AI shortcuts
@router.get("/horse/{horse_id}/quick-analysis", response_model=AIResponse)
async def quick_horse_analysis(horse_id: int, db: Session = Depends(get_db)):
    """
    Get a quick AI analysis of a horse without a specific question
    """
    request = HorseAnalysisRequest(horse_id=horse_id)
    return await analyze_horse(request, db)

@router.post("/horse/{horse_id}/ask", response_model=AIResponse)
async def ask_about_horse(
    horse_id: int,
    question: str,
    db: Session = Depends(get_db)
):
    """
    Ask a specific question about a horse
    """
    request = HorseAnalysisRequest(horse_id=horse_id, question=question)
    return await analyze_horse(request, db)
