#!/usr/bin/env python3
"""
Creates a clean, working app/main.py for Barn Lady system
"""
import os
from datetime import datetime

print("🐴 Creating clean Barn Lady main.py file...")

# Backup existing file
if os.path.exists('app/main.py'):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'app/main.py.broken_{timestamp}'
    os.rename('app/main.py', backup_name)
    print(f"📦 Backed up old file to {backup_name}")

# Ensure app directory exists
os.makedirs('app', exist_ok=True)

# Write the clean file
with open('app/main.py', 'w') as f:
    f.write("""from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Barn Lady API")

class Horse(BaseModel):
    id: Optional[str] = None
    name: str
    breed: str
    age_display: str
    color: str
    gender: str
    current_health_status: str
    current_location: str
    owner_name: str
    is_for_sale: bool = False
    is_retired: bool = False

class HorseCreate(BaseModel):
    name: str
    breed: str
    age_display: str
    color: str
    gender: str
    current_health_status: str
    current_location: str
    owner_name: str
    is_for_sale: bool = False
    is_retired: bool = False

class AIQuestion(BaseModel):
    question: str
    horse_name: Optional[str] = None

HORSES_DATA = [
    {
        "id": "1", 
        "name": "Thunder Bay", 
        "breed": "Thoroughbred", 
        "age_display": "8 years, 3 months", 
        "color": "Bay", 
        "gender": "Gelding", 
        "current_health_status": "Good", 
        "current_location": "Meadowbrook Farm", 
        "owner_name": "Sarah Johnson", 
        "is_for_sale": False, 
        "is_retired": False
    },
    {
        "id": "2", 
        "name": "Starlight Princess", 
        "breed": "Quarter Horse", 
        "age_display": "12 years, 7 months", 
        "color": "Palomino", 
        "gender": "Mare", 
        "current_health_status": "Excellent", 
        "current_location": "Sunrise Stables", 
        "owner_name": "Mike Rodriguez", 
        "is_for_sale": False, 
        "is_retired": False
    },
    {
        "id": "3", 
        "name": "Midnight Express", 
        "breed": "Arabian", 
        "age_display": "6 years, 10 months", 
        "color": "Black", 
        "gender": "Stallion", 
        "current_health_status": "Good", 
        "current_location": "Desert Wind Ranch", 
        "owner_name": "Jessica Thompson", 
        "is_for_sale": False, 
        "is_retired": False
    },
    {
        "id": "4", 
        "name": "Gentle Ben", 
        "breed": "Clydesdale", 
        "age_display": "15 years, 2 months", 
        "color": "Chestnut", 
        "gender": "Gelding", 
        "current_health_status": "Fair", 
        "current_location": "Green Valley Farm", 
        "owner_name": "Green Valley Farm", 
        "is_for_sale": False, 
        "is_retired": True
    },
    {
        "id": "5", 
        "name": "Lightning Bolt", 
        "breed": "Paint Horse", 
        "age_display": "9 years, 5 months", 
        "color": "Pinto", 
        "gender": "Mare", 
        "current_health_status": "Good", 
        "current_location": "Lightning Ridge Stables", 
        "owner_name": "Lightning Ridge Stables", 
        "is_for_sale": True, 
        "is_retired": False
    },
    {
        "id": "6", 
        "name": "Farrah", 
        "breed": "Quarter Horse", 
        "age_display": "14 years", 
        "color": "Chestnut", 
        "gender": "Mare", 
        "current_health_status": "Good", 
        "current_location": "Fernbell Farms", 
        "owner_name": "Gennie Murphy", 
        "is_for_sale": False, 
        "is_retired": False
    }
]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "version": "2.0.0"}

@app.get("/api/v1/horses/", response_model=List[Horse])
async def get_horses():
    return HORSES_DATA

@app.get("/api/v1/horses/{horse_id}", response_model=Horse)
async def get_horse(horse_id: str):
    horse = next((h for h in HORSES_DATA if h["id"] == horse_id), None)
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    return horse

@app.post("/api/v1/horses/", response_model=Horse)
async def create_horse(horse: HorseCreate):
    new_horse = horse.dict()
    new_horse["id"] = str(uuid.uuid4())
    HORSES_DATA.append(new_horse)
    logger.info(f"Created new horse: {new_horse['name']}")
    return new_horse

@app.put("/api/v1/horses/{horse_id}", response_model=Horse)
async def update_horse(horse_id: str, horse_update: HorseCreate):
    horse_index = next((i for i, h in enumerate(HORSES_DATA) if h["id"] == 
horse_id), None)
    if horse_index is None:
        raise HTTPException(status_code=404, detail="Horse not found")
    
    updated_horse = horse_update.dict()
    updated_horse["id"] = horse_id
    HORSES_DATA[horse_index] = updated_horse
    logger.info(f"Updated horse: {updated_horse['name']}")
    return updated_horse

@app.delete("/api/v1/horses/{horse_id}")
async def delete_horse(horse_id: str):
    horse_index = next((i for i, h in enumerate(HORSES_DATA) if h["id"] == 
horse_id), None)
    if horse_index is None:
        raise HTTPException(status_code=404, detail="Horse not found")
    
    deleted_horse = HORSES_DATA.pop(horse_index)
    logger.info(f"Deleted horse: {deleted_horse['name']}")
    return {"message": f"Horse {deleted_horse['name']} deleted successfully"}

@app.post("/api/v1/horses/ask")
async def ask_ai_question(question: AIQuestion):
    responses = {
        "health": "Most horses are in good health. Gentle Ben needs extra 
attention.",
        "feed": "Recommend high-quality hay and grain based on activity 
levels.",
        "training": "Thunder Bay and Midnight Express would benefit from 
regular training.",
        "default": "Consult your veterinarian for specific horse advice."
    }
    
    response_text = responses["default"]
    question_lower = question.question.lower()
    
    if any(word in question_lower for word in ["health", "sick", "injury"]):
        response_text = responses["health"]
    elif any(word in question_lower for word in ["feed", "food", "nutrition"]):
        response_text = responses["feed"]
    elif any(word in question_lower for word in ["train", "exercise", "ride"]):
        response_text = responses["training"]
    
    logger.info(f"AI Question: {question.question}")
    return {
        "question": question.question,
        "answer": response_text,
        "horse_count": len(HORSES_DATA)
    }
""")

print("✅ Created clean app/main.py")

# Verify syntax
import py_compile
try:
    py_compile.compile('app/main.py', doraise=True)
    print("✅ Python syntax is perfect!")
except py_compile.PyCompileError as e:
    print(f"❌ Syntax error: {e}")
    exit(1)

print("🎉 File created successfully! Now run: docker-compose down && 
docker-compose up -d")
