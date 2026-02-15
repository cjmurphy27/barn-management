import anthropic
from typing import Dict, Any, List, Optional
import json
import logging
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.horse import Horse
from app.models.horse_document import HorseDocument, HorseDocumentAssociation
from app.services.document_processor import document_processor

logger = logging.getLogger(__name__)

class BarnLadyAI:
    """AI service for horse management assistance using Claude"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.api_key_available = bool(self.settings.ANTHROPIC_API_KEY)
        
        if self.api_key_available:
            try:
                self.client = anthropic.Anthropic(
                    api_key=self.settings.ANTHROPIC_API_KEY
                )
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.api_key_available = False
        else:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables")
    
    def analyze_horse(self, horse_data: Dict[str, Any], question: str = None, image_data: str = None, image_type: str = None, db: Session = None, conversation_history: List[Dict[str, str]] = None) -> str:
        """Analyze a specific horse and provide insights, optionally with image analysis"""
        
        if not self.api_key_available or not self.client:
            return "AI analysis is currently unavailable. Please check that the ANTHROPIC_API_KEY environment variable is properly configured."
        
        # Create a comprehensive horse profile for the AI
        horse_profile = self._format_horse_for_ai(horse_data, db)

        # Check if we have visual documents (PDFs and images) that might benefit from vision analysis
        visual_documents = []
        if db and horse_data.get('id'):
            logger.info(f"Looking for visual documents (PDFs and images) for horse ID {horse_data['id']}")
            from app.models.horse_document import HorseDocument, HorseDocumentAssociation

            # Get both PDF and image documents
            visual_file_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/tiff']
            docs = db.query(HorseDocument).join(
                HorseDocumentAssociation,
                HorseDocument.id == HorseDocumentAssociation.document_id
            ).filter(
                HorseDocumentAssociation.horse_id == horse_data['id'],
                HorseDocument.is_active == True,
                HorseDocument.file_type.in_(visual_file_types)
            ).limit(3).all()  # Limit to 3 to avoid rate limits

            logger.info(f"Found {len(docs)} visual documents for vision analysis")
            for doc in docs:
                logger.info(f"Processing document: {doc.original_filename} ({doc.file_type}) at {doc.file_path}")

                # For PDFs, use first-page-only optimization; for images, process normally
                first_page_only = doc.file_type == 'application/pdf'
                vision_data = document_processor.get_document_for_vision_analysis(
                    doc.file_path,
                    doc.file_type,
                    first_page_only=first_page_only
                )

                if vision_data:
                    logger.info(f"Successfully prepared {doc.original_filename} for vision analysis ({len(vision_data)} chars)")
                    visual_documents.append({
                        'filename': doc.original_filename,
                        'data': vision_data,
                        'description': doc.description or f'{doc.file_type} document'
                    })
                else:
                    logger.warning(f"Failed to prepare {doc.original_filename} for vision analysis")

        # Build system prompt with horse context
        additional_context = ""
        if visual_documents:
            additional_context = " Documents and images with additional information (including handwritten details) may be provided."

        system_prompt = f"""You are a knowledgeable equine specialist and barn manager. You are helping a user manage their horse. Be specific and actionable in your recommendations.{additional_context}

Here is the horse's information:

{horse_profile}"""

        # Build the user message content for the current turn
        message_content = []

        if question:
            if image_data or visual_documents:
                user_text = f"""{question}

Please analyze all provided information (including any documents or images) in context of this question. Pay special attention to:
- Any handwritten information in documents (like age, notes, measurements)
- Details that may not be in printed text but are visible in the documents
- Cross-reference information between different sources"""
            else:
                user_text = question
        else:
            if image_data:
                user_text = """Please analyze this horse's information and the provided photo. Provide:
1. Health assessment based on the available information and visual observations
2. Care recommendations
3. Any concerns or things to monitor based on the image
4. Suggestions for improvement"""
            else:
                user_text = """Please analyze this horse's information and provide insights about their care, health, and management. Provide:
1. Health assessment based on the available information
2. Care recommendations
3. Any concerns or things to monitor
4. Suggestions for improvement"""

        # Add text content
        message_content.append({
            "type": "text",
            "text": user_text
        })

        # Add image if provided
        if image_data:
            message_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_type,
                    "data": image_data
                }
            })

        # Add visual documents (PDFs and images) if available
        logger.info(f"Adding {len(visual_documents)} visual documents to AI message for vision analysis")
        for visual_doc in visual_documents:
            logger.info(f"Attaching document: {visual_doc['filename']} ({len(visual_doc['data'])} chars)")

            # Determine the correct message type based on file type
            if visual_doc['filename'].lower().endswith('.pdf'):
                doc_type = "document"
                media_type = "application/pdf"
            else:
                doc_type = "image"
                # Determine image media type from filename
                if visual_doc['filename'].lower().endswith('.png'):
                    media_type = "image/png"
                elif visual_doc['filename'].lower().endswith('.jpg') or visual_doc['filename'].lower().endswith('.jpeg'):
                    media_type = "image/jpeg"
                elif visual_doc['filename'].lower().endswith('.tiff'):
                    media_type = "image/tiff"
                else:
                    media_type = "image/jpeg"  # Default fallback

            message_content.append({
                "type": doc_type,
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": visual_doc['data']
                }
            })

        try:
            # Build messages array with conversation history
            messages = []
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({
                "role": "user",
                "content": message_content
            })

            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1200,
                temperature=0.3,
                system=system_prompt,
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return f"Sorry, I encountered an error while analyzing the horse information: {str(e)}"

    def general_horse_question(self, question: str, barn_context: List[Dict[str, Any]] = None, conversation_history: List[Dict[str, str]] = None, supply_context: List[Dict[str, Any]] = None) -> str:
        """Answer general horse management questions with barn and inventory context"""

        context = ""
        if barn_context:
            context += "\n\n--- HORSES IN THE BARN ---\n"
            for horse in barn_context:
                entry = f"- {horse.get('name', 'Unknown')}"
                details = []
                if horse.get('breed'):
                    details.append(horse['breed'])
                if horse.get('age_display'):
                    details.append(horse['age_display'])
                if horse.get('gender'):
                    details.append(horse['gender'])
                if horse.get('current_health_status'):
                    details.append(f"Health: {horse['current_health_status']}")
                if horse.get('allergies'):
                    details.append(f"Allergies: {horse['allergies']}")
                if horse.get('medications'):
                    details.append(f"Medications: {horse['medications']}")
                if horse.get('special_needs'):
                    details.append(f"Special needs: {horse['special_needs']}")
                if horse.get('stall_number'):
                    details.append(f"Stall: {horse['stall_number']}")
                if horse.get('feeding_schedule'):
                    details.append(f"Feeding: {horse['feeding_schedule']}")
                if horse.get('notes'):
                    details.append(f"Notes: {horse['notes']}")
                if details:
                    entry += f" ({', '.join(details)})"
                context += entry + "\n"

        if supply_context:
            context += "\n--- INVENTORY / SUPPLIES ---\n"
            for supply in supply_context:
                entry = f"- {supply.get('name', 'Unknown')}"
                details = []
                if supply.get('category'):
                    details.append(supply['category'].replace('_', ' '))
                if supply.get('brand'):
                    details.append(supply['brand'])
                stock = supply.get('current_stock', 0)
                unit = supply.get('unit_type', '')
                details.append(f"Stock: {stock} {unit}")
                if supply.get('is_low_stock'):
                    details.append("LOW STOCK")
                if supply.get('estimated_days_remaining') is not None:
                    details.append(f"~{supply['estimated_days_remaining']} days remaining")
                if supply.get('last_cost_per_unit'):
                    details.append(f"${supply['last_cost_per_unit']:.2f}/unit")
                if details:
                    entry += f" ({', '.join(details)})"
                context += entry + "\n"

        system_prompt = f"""You are a knowledgeable equine specialist and barn manager. You have access to the full barn roster and inventory. Provide practical, actionable advice based on current best practices in horse care and management.{context}"""

        try:
            # Build messages array with conversation history
            messages = []
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({
                "role": "user",
                "content": question
            })

            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1000,
                temperature=0.3,
                system=system_prompt,
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
    
    def compare_horses(self, horses_data: List[Dict[str, Any]], comparison_question: str = None) -> str:
        """Compare multiple horses and provide insights"""
        
        if len(horses_data) < 2:
            return "I need at least 2 horses to make a comparison."
        
        horses_info = ""
        for i, horse in enumerate(horses_data, 1):
            horses_info += f"\nHorse {i}: {self._format_horse_for_ai(horse)}\n"
        
        if comparison_question:
            prompt = f"""You are a knowledgeable equine specialist. Please compare these horses based on the user's specific question:

{horses_info}

User Question: {comparison_question}

Provide a detailed comparison addressing the user's specific question."""
        else:
            prompt = f"""You are a knowledgeable equine specialist. Please compare these horses:

{horses_info}

Please provide:
1. Key similarities and differences
2. Individual care recommendations for each horse
3. Management considerations for keeping them together
4. Any special attention needed for each horse"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1200,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return f"Sorry, I encountered an error while comparing the horses: {str(e)}"
    
    def _format_horse_for_ai(self, horse_data: Dict[str, Any], db: Session = None) -> str:
        """Format horse data for AI consumption"""

        info = f"Horse: {horse_data.get('name', 'Unknown')}"

        if horse_data.get('barn_name'):
            info += f" (Barn name: {horse_data['barn_name']})"

        info += "\n"

        # Basic info
        if horse_data.get('breed'):
            info += f"Breed: {horse_data['breed']}\n"
        if horse_data.get('age_display'):
            info += f"Age: {horse_data['age_display']}\n"
        if horse_data.get('gender'):
            info += f"Gender: {horse_data['gender']}\n"
        if horse_data.get('color'):
            info += f"Color: {horse_data['color']}\n"

        # Physical characteristics
        if horse_data.get('height_hands'):
            info += f"Height: {horse_data['height_hands']} hands\n"
        if horse_data.get('weight_lbs'):
            info += f"Weight: {horse_data['weight_lbs']} lbs\n"
        if horse_data.get('body_condition_score'):
            info += f"Body Condition Score: {horse_data['body_condition_score']}/9\n"

        # Health and care
        if horse_data.get('current_health_status'):
            info += f"Current Health Status: {horse_data['current_health_status']}\n"
        if horse_data.get('allergies'):
            info += f"Allergies: {horse_data['allergies']}\n"
        if horse_data.get('medications'):
            info += f"Current Medications: {horse_data['medications']}\n"
        if horse_data.get('special_needs'):
            info += f"Special Needs: {horse_data['special_needs']}\n"

        # Management
        if horse_data.get('current_location'):
            info += f"Location: {horse_data['current_location']}\n"
        if horse_data.get('stall_number'):
            info += f"Stall: {horse_data['stall_number']}\n"
        if horse_data.get('boarding_type'):
            info += f"Boarding Type: {horse_data['boarding_type']}\n"
        if horse_data.get('training_level'):
            info += f"Training Level: {horse_data['training_level']}\n"
        if horse_data.get('disciplines'):
            info += f"Disciplines: {horse_data['disciplines']}\n"

        # Additional info
        if horse_data.get('notes'):
            info += f"Notes: {horse_data['notes']}\n"

        # Status
        status_items = []
        if horse_data.get('is_retired'):
            status_items.append("Retired")
        if horse_data.get('is_for_sale'):
            status_items.append("For Sale")
        if status_items:
            info += f"Status: {', '.join(status_items)}\n"

        # Include document information if database session is provided
        if db and horse_data.get('id'):
            document_info = self._get_horse_documents_info(horse_data['id'], db)
            if document_info:
                info += f"\n--- DOCUMENTS & RECORDS ---\n{document_info}\n"

        return info

    def _get_horse_documents_info(self, horse_id: int, db: Session) -> str:
        """Fetch and format horse document information for AI context"""
        try:
            # Get all documents for this horse
            documents = db.query(HorseDocument).join(
                HorseDocumentAssociation,
                HorseDocument.id == HorseDocumentAssociation.document_id
            ).filter(
                HorseDocumentAssociation.horse_id == horse_id,
                HorseDocument.is_active == True
            ).order_by(HorseDocument.upload_date.desc()).all()

            if not documents:
                return ""

            document_sections = []

            for doc in documents:
                doc_info = f"Document: {doc.original_filename} ({doc.document_category.value})"

                if doc.title and doc.title != doc.original_filename:
                    doc_info += f" - {doc.title}"

                if doc.description:
                    doc_info += f"\nDescription: {doc.description}"

                # Process document content if not already extracted
                if not doc.extracted_text and doc.file_path:
                    logger.info(f"Extracting text from {doc.original_filename}")
                    extracted_text = document_processor.extract_text(doc.file_path, doc.file_type)
                    if extracted_text:
                        # Update the database with extracted text
                        doc.extracted_text = extracted_text
                        doc.processing_status = 'processed'
                        db.commit()
                        logger.info(f"Saved extracted text for document {doc.id}")

                # Include extracted text content
                if doc.extracted_text:
                    doc_info += f"\nContent:\n{doc.extracted_text}"

                    # For PDFs, also try vision analysis to catch handwritten content
                    if doc.file_type == 'application/pdf':
                        vision_data = document_processor.get_document_for_vision_analysis(doc.file_path, doc.file_type)
                        if vision_data:
                            doc_info += f"\n\n[Note: This document also contains visual elements that may include handwritten content - analyzing with AI vision]"
                            # The vision analysis will be handled by the main AI analysis

                elif doc.ai_summary:
                    doc_info += f"\nSummary: {doc.ai_summary}"
                else:
                    doc_info += "\n(No text content available)"

                document_sections.append(doc_info)

            return "\n\n".join(document_sections)

        except Exception as e:
            logger.error(f"Error fetching documents for horse {horse_id}: {str(e)}")
            return ""


# Global AI service instance
ai_service = BarnLadyAI()
