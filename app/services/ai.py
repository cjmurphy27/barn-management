import anthropic
from typing import Dict, Any, List, Optional
import json
import logging
from app.core.config import get_settings
from app.models.horse import Horse

logger = logging.getLogger(__name__)

class BarnLadyAI:
    """AI service for horse management assistance using Claude"""
    
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = anthropic.Anthropic(
            api_key=self.settings.ANTHROPIC_API_KEY
        )
    
    def analyze_horse(self, horse_data: Dict[str, Any], question: str = None, image_data: str = None, image_type: str = None) -> str:
        """Analyze a specific horse and provide insights, optionally with image analysis"""
        
        # Create a comprehensive horse profile for the AI
        horse_profile = self._format_horse_for_ai(horse_data)
        
        # Build message content
        message_content = []
        
        if question:
            if image_data:
                prompt = f"""You are a knowledgeable equine specialist and barn manager. A user is asking about their horse and has provided a photo for analysis. Here's the horse's information:

{horse_profile}

User Question: {question}

Please analyze the provided photo in context of this question and the horse's information. Look for:
- Any visible health issues, injuries, or concerns
- Physical conformation and condition
- Environmental factors that might affect the horse
- Any observations that relate to the user's question

Provide helpful, practical advice based on both the horse's data and what you can observe in the image. Be specific and actionable in your recommendations."""
            else:
                prompt = f"""You are a knowledgeable equine specialist and barn manager. A user is asking about their horse. Here's the horse's information:

{horse_profile}

User Question: {question}

Please provide helpful, practical advice based on this horse's specific details. Be specific and actionable in your recommendations."""
        else:
            if image_data:
                prompt = f"""You are a knowledgeable equine specialist and barn manager. Please analyze this horse's information and the provided photo:

{horse_profile}

Please provide:
1. Health assessment based on the available information and visual observations
2. Care recommendations 
3. Any concerns or things to monitor based on the image
4. Suggestions for improvement

Be specific and practical in your advice, incorporating both the data and visual observations."""
            else:
                prompt = f"""You are a knowledgeable equine specialist and barn manager. Please analyze this horse's information and provide insights about their care, health, and management:

{horse_profile}

Please provide:
1. Health assessment based on the available information
2. Care recommendations 
3. Any concerns or things to monitor
4. Suggestions for improvement

Be specific and practical in your advice."""

        # Add text content
        message_content.append({
            "type": "text",
            "text": prompt
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

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1200,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return f"Sorry, I encountered an error while analyzing the horse information: {str(e)}"
    
    def general_horse_question(self, question: str, barn_context: List[Dict[str, Any]] = None) -> str:
        """Answer general horse management questions with barn context"""
        
        context = ""
        if barn_context:
            context = "\n\nFor context, here are the horses currently in the barn:\n"
            for horse in barn_context[:5]:  # Limit to first 5 horses for context
                context += f"- {horse.get('name')} ({horse.get('breed', 'Unknown breed')}, {horse.get('age_display', 'Unknown age')}, {horse.get('current_health_status', 'Unknown health')})\n"
        
        prompt = f"""You are a knowledgeable equine specialist and barn manager. Please answer this question about horse management:

Question: {question}
{context}

Provide practical, actionable advice based on current best practices in horse care and management."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
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
                model="claude-3-5-sonnet-20241022",
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
    
    def _format_horse_for_ai(self, horse_data: Dict[str, Any]) -> str:
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
        
        return info

# Global AI service instance
ai_service = BarnLadyAI()
