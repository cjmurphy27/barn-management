import anthropic
from typing import Dict, Any, List, Optional, Tuple
import json
import logging
import re
from datetime import datetime, date
from app.core.config import get_settings
from app.models.supply import SupplyCategory

logger = logging.getLogger(__name__)

class ReceiptProcessor:
    """AI-powered receipt processing using Claude Vision"""
    
    def __init__(self):
        self.settings = get_settings()
        if not self.settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = anthropic.Anthropic(
            api_key=self.settings.ANTHROPIC_API_KEY
        )
        
        # Common barn supply keywords for category detection
        self.category_keywords = {
            SupplyCategory.FEED_NUTRITION: [
                "hay", "grain", "feed", "oats", "pellets", "supplement", "molasses",
                "bran", "alfalfa", "timothy", "sweet feed", "corn", "barley",
                "protein", "vitamin", "mineral", "salt", "nutrition"
            ],
            SupplyCategory.BEDDING: [
                "bedding", "shavings", "straw", "sawdust", "pellets bedding",
                "wood shavings", "pine", "cedar", "hemp bedding", "paper bedding"
            ],
            SupplyCategory.HEALTH_MEDICAL: [
                "medical", "medicine", "antibiotic", "vaccine", "syringe", "bandage",
                "ointment", "paste", "dewormer", "ivermectin", "bute", "phenylbutazone",
                "thermometer", "wound", "spray", "liniment", "poultice"
            ],
            SupplyCategory.TACK_EQUIPMENT: [
                "halter", "lead rope", "bridle", "saddle", "blanket", "boots",
                "brush", "curry", "hoof pick", "bucket", "waterer", "feeder",
                "gate", "latch", "rope", "chain"
            ],
            SupplyCategory.FACILITY_MAINTENANCE: [
                "fence", "post", "wire", "gate", "hardware", "bolt", "screw",
                "paint", "lumber", "concrete", "gravel", "tools", "repair"
            ],
            SupplyCategory.GROOMING: [
                "brush", "curry comb", "shampoo", "conditioner", "hoof oil",
                "grooming", "mane", "tail", "detangler", "fly spray", "polish"
            ]
        }
    
    def process_receipt(
        self, 
        image_data: str, 
        image_type: str,
        vendor_hint: Optional[str] = None,
        expected_total: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process a receipt image using Claude Vision API
        
        Args:
            image_data: Base64 encoded image data
            image_type: Image MIME type (e.g., 'image/jpeg')
            vendor_hint: Optional vendor name hint
            expected_total: Optional expected total amount for validation
            
        Returns:
            Dictionary containing extracted receipt data
        """
        
        try:
            # Build the prompt for receipt analysis
            prompt = self._build_receipt_prompt(vendor_hint, expected_total)
            
            # Create message with image
            message_content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_type,
                        "data": image_data
                    }
                }
            ]
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.1,  # Low temperature for accuracy
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            )
            
            # Parse the response
            result = self._parse_receipt_response(response.content[0].text)
            
            # Add processing metadata
            result["ai_processed"] = True
            result["processing_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"Successfully processed receipt for vendor: {result.get('vendor_name', 'Unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ai_processed": False,
                "confidence_score": 0.0,
                "manual_review_required": True
            }
    
    def _build_receipt_prompt(self, vendor_hint: Optional[str], expected_total: Optional[float]) -> str:
        """Build the prompt for receipt analysis"""
        
        base_prompt = """You are an expert at analyzing receipts for barn and horse supply purchases. 
Please analyze this receipt image and extract the following information in a structured JSON format:

REQUIRED INFORMATION:
1. Vendor/Store Name
2. Purchase Date (YYYY-MM-DD format)
3. Receipt/Invoice Number (if visible)
4. Total Amount
5. Subtotal (if shown)
6. Tax Amount (if shown)
7. All line items with:
   - Item description/name
   - Quantity (if shown, default to 1)
   - Unit price (if shown)
   - Total price for the item
   - Any product codes/SKUs

ADDITIONAL ANALYSIS:
For each line item, categorize it into one of these barn supply categories:
- feed_nutrition: Feed, hay, grain, supplements, salt, vitamins
- bedding: Shavings, straw, bedding materials
- health_medical: Medications, vaccines, medical supplies, dewormers
- tack_equipment: Halters, ropes, blankets, buckets, gates
- facility_maintenance: Fence materials, tools, hardware, paint
- grooming: Brushes, shampoos, fly spray, hoof care
- other: Items that don't fit the above categories

CONFIDENCE SCORING:
Provide a confidence score (0.0-1.0) for:
- Overall extraction accuracy
- Each line item match
- Category assignments

OUTPUT FORMAT:
Return a JSON object with this structure:
{
  "vendor_name": "Store Name",
  "purchase_date": "YYYY-MM-DD",
  "receipt_number": "12345",
  "subtotal": 45.67,
  "tax_amount": 3.65,
  "total_amount": 49.32,
  "line_items": [
    {
      "description": "Item name",
      "quantity": 1,
      "unit_price": 12.50,
      "total_price": 12.50,
      "product_code": "ABC123",
      "category": "feed_nutrition",
      "confidence": 0.95
    }
  ],
  "confidence_score": 0.92,
  "notes": "Any issues or observations",
  "manual_review_required": false
}

IMPORTANT RULES:
- If text is unclear, use your best judgment but lower the confidence score
- Always try to extract at least vendor name and total amount
- If amounts don't add up correctly, note this in manual_review_required
- Be conservative with confidence scores - accuracy is more important than confidence
- For barn supplies, be specific about the category - horses need very specific items
"""

        # Add context if provided
        if vendor_hint:
            base_prompt += f"\n\nHINT: This receipt is likely from '{vendor_hint}'"
        
        if expected_total:
            base_prompt += f"\n\nEXPECTED TOTAL: Around ${expected_total:.2f} (use this to validate your extraction)"
        
        return base_prompt
    
    def _parse_receipt_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response and extract structured data"""
        
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # Fallback: try to parse the entire response as JSON
                result = json.loads(response_text)
            
            # Validate and clean the result
            result = self._validate_extracted_data(result)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            return {
                "success": False,
                "error": "Failed to parse AI response",
                "confidence_score": 0.0,
                "manual_review_required": True,
                "raw_response": response_text
            }
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        
        # Set defaults for required fields
        validated = {
            "success": True,
            "vendor_name": data.get("vendor_name", "Unknown Vendor"),
            "purchase_date": self._parse_date(data.get("purchase_date")),
            "receipt_number": data.get("receipt_number"),
            "subtotal": self._parse_float(data.get("subtotal")),
            "tax_amount": self._parse_float(data.get("tax_amount")),
            "total_amount": self._parse_float(data.get("total_amount", 0)),
            "line_items": [],
            "confidence_score": float(data.get("confidence_score", 0.5)),
            "notes": data.get("notes", ""),
            "manual_review_required": bool(data.get("manual_review_required", False))
        }
        
        # Validate line items
        raw_items = data.get("line_items", [])
        for item in raw_items:
            validated_item = self._validate_line_item(item)
            if validated_item:
                validated["line_items"].append(validated_item)
        
        # Calculate totals if missing
        if not validated["subtotal"] and validated["line_items"]:
            validated["subtotal"] = sum(item["total_price"] for item in validated["line_items"])
        
        # Validation checks
        if validated["total_amount"] <= 0:
            validated["manual_review_required"] = True
            validated["notes"] += " Missing or invalid total amount."
        
        if not validated["line_items"]:
            validated["manual_review_required"] = True
            validated["notes"] += " No line items detected."
        
        # Check if math adds up
        if (validated["subtotal"] and validated["tax_amount"] and 
            abs(validated["subtotal"] + validated["tax_amount"] - validated["total_amount"]) > 0.02):
            validated["manual_review_required"] = True
            validated["notes"] += " Amounts don't add up correctly."
        
        return validated
    
    def _validate_line_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and clean a single line item"""
        
        description = item.get("description", "").strip()
        if not description:
            return None
        
        return {
            "description": description,
            "quantity": max(float(item.get("quantity", 1)), 1),
            "unit_price": self._parse_float(item.get("unit_price")),
            "total_price": self._parse_float(item.get("total_price", 0)),
            "product_code": item.get("product_code"),
            "category": self._validate_category(item.get("category", "other")),
            "confidence": min(max(float(item.get("confidence", 0.5)), 0), 1),
            "brand": item.get("brand"),
            "unit_type": item.get("unit_type")
        }
    
    def _validate_category(self, category: str) -> str:
        """Validate supply category"""
        try:
            # Check if it's a valid category
            SupplyCategory(category)
            return category
        except ValueError:
            # Default to other if invalid
            return "other"
    
    def _parse_date(self, date_str: Any) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, str):
                # Try different date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue
            return None
        except:
            return None
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse float value safely"""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                value = re.sub(r'[$,]', '', value)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def auto_match_supplies(
        self, 
        line_items: List[Dict[str, Any]], 
        existing_supplies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Automatically match receipt line items to existing supplies
        
        Args:
            line_items: List of line items from receipt
            existing_supplies: List of existing supplies in database
            
        Returns:
            Line items with supply_id matches and confidence scores
        """
        
        matched_items = []
        
        for item in line_items:
            best_match = None
            best_score = 0.0
            
            item_desc = item["description"].lower()
            item_category = item.get("category", "other")
            
            for supply in existing_supplies:
                score = self._calculate_match_score(item_desc, item_category, supply)
                
                if score > best_score and score > 0.7:  # Threshold for auto-matching
                    best_match = supply
                    best_score = score
            
            # Add match information to item
            matched_item = item.copy()
            if best_match:
                matched_item["supply_id"] = best_match["id"]
                matched_item["matched_supply_name"] = best_match["name"]
                matched_item["match_confidence"] = best_score
                matched_item["ai_matched"] = True
            else:
                matched_item["supply_id"] = None
                matched_item["ai_matched"] = False
                matched_item["manual_review_required"] = True
            
            matched_items.append(matched_item)
        
        return matched_items
    
    def _calculate_match_score(
        self, 
        item_description: str, 
        item_category: str, 
        supply: Dict[str, Any]
    ) -> float:
        """Calculate match score between receipt item and supply"""
        
        score = 0.0
        
        supply_name = supply.get("name", "").lower()
        supply_desc = supply.get("description", "").lower()
        supply_category = supply.get("category", "")
        
        # Category match (high weight)
        if item_category == supply_category:
            score += 0.4
        
        # Name/description similarity
        desc_words = set(item_description.split())
        supply_words = set(supply_name.split() + supply_desc.split())
        
        if desc_words and supply_words:
            common_words = desc_words.intersection(supply_words)
            if common_words:
                similarity = len(common_words) / len(desc_words.union(supply_words))
                score += similarity * 0.4
        
        # Brand match
        if supply.get("brand"):
            brand_lower = supply["brand"].lower()
            if brand_lower in item_description:
                score += 0.2
        
        return min(score, 1.0)
    
    def suggest_new_supply(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest creating a new supply item based on receipt line item"""
        
        category = item.get("category", "other")
        description = item.get("description", "")
        
        # Extract potential brand from description
        brand = self._extract_brand(description)
        
        # Suggest unit type based on category and description
        unit_type = self._suggest_unit_type(category, description)
        
        return {
            "name": description.title(),
            "description": f"Auto-suggested from receipt: {description}",
            "category": category,
            "brand": brand,
            "unit_type": unit_type,
            "current_stock": item.get("quantity", 1),
            "last_cost_per_unit": item.get("unit_price"),
            "is_active": True,
            "expiration_tracking": category in ["health_medical", "feed_nutrition"]
        }
    
    def _extract_brand(self, description: str) -> Optional[str]:
        """Extract potential brand name from item description"""
        
        # Common barn supply brands
        brands = [
            "purina", "nutrena", "blue seal", "tribute", "buckeye", "southern states",
            "tractor supply", "smartpak", "farnam", "absorbine", "vetericyn", "durvet"
        ]
        
        desc_lower = description.lower()
        for brand in brands:
            if brand in desc_lower:
                return brand.title()
        
        return None
    
    def _suggest_unit_type(self, category: str, description: str) -> str:
        """Suggest appropriate unit type based on category and description"""
        
        desc_lower = description.lower()
        
        if category == "feed_nutrition":
            if any(word in desc_lower for word in ["bale", "hay"]):
                return "bales"
            elif any(word in desc_lower for word in ["bag", "feed", "grain"]):
                return "bags"
            else:
                return "pounds"
        
        elif category == "bedding":
            if "bale" in desc_lower:
                return "bales"
            else:
                return "bags"
        
        elif category == "health_medical":
            if any(word in desc_lower for word in ["bottle", "liquid"]):
                return "bottles"
            elif any(word in desc_lower for word in ["tube", "paste"]):
                return "each"
            else:
                return "each"
        
        else:
            return "each"

# Global receipt processor instance
receipt_processor = ReceiptProcessor()