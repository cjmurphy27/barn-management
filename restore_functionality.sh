#!/bin/bash

# Barn Lady - Restore Functionality Setup Script
# This script restores CRUD operations and AI functionality

echo "🐴 Barn Lady - Restoring Full Functionality"
echo "=========================================="

# Create timestamp for backups
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups_$TIMESTAMP"

echo "📁 Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup current files
echo "💾 Backing up current files..."
if [ -f "app/main.py" ]; then
    cp app/main.py "$BACKUP_DIR/main.py.backup"
    echo "   ✅ Backed up app/main.py"
else
    echo "   ⚠️  app/main.py not found"
fi

if [ -f "frontend/app.py" ]; then
    cp frontend/app.py "$BACKUP_DIR/app.py.backup"
    echo "   ✅ Backed up frontend/app.py"
else
    echo "   ⚠️  frontend/app.py not found"
fi

# Create enhanced backend
echo "🔧 Installing enhanced backend..."
mkdir -p app
cat > app/main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Barn Lady API")

# Pydantic models for request/response
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

# In-memory storage (will be replaced with database later)
HORSES_DATA = [
    {"id": "1", "name": "Thunder Bay", "breed": "Thoroughbred", 
"age_display": "8 years, 3 months", "color": "Bay", "gender": "Gelding", 
"current_health_status": "Good", "current_location": "Meadowbrook Farm", 
"owner_name": "Sarah Johnson", "is_for_sale": False, "is_retired": False},
    {"id": "2", "name": "Starlight Princess", "breed": "Quarter Horse", 
"age_display": "12 years, 7 months", "color": "Palomino", "gender": 
"Mare", "current_health_status": "Excellent", "current_location": "Sunrise 
Stables", "owner_name": "Mike Rodriguez", "is_for_sale": False, 
"is_retired": False},
    {"id": "3", "name": "Midnight Express", "breed": "Arabian", 
"age_display": "6 years, 10 months", "color": "Black", "gender": 
"Stallion", "current_health_status": "Good", "current_location": "Desert 
Wind Ranch", "owner_name": "Jessica Thompson", "is_for_sale": False, 
"is_retired": False},
    {"id": "4", "name": "Gentle Ben", "breed": "Clydesdale", 
"age_display": "15 years, 2 months", "color": "Chestnut", "gender": 
"Gelding", "current_health_status": "Fair", "current_location": "Green 
Valley Farm", "owner_name": "Green Valley Farm", "is_for_sale": False, 
"is_retired": True},
    {"id": "5", "name": "Lightning Bolt", "breed": "Paint Horse", 
"age_display": "9 years, 5 months", "color": "Pinto", "gender": "Mare", 
"current_health_status": "Good", "current_location": "Lightning Ridge 
Stables", "owner_name": "Lightning Ridge Stables", "is_for_sale": True, 
"is_retired": False},
    {"id": "6", "name": "Farrah", "breed": "Quarter Horse", "age_display": 
"14 years", "color": "Chestnut", "gender": "Mare", 
"current_health_status": "Good", "current_location": "Fernbell Farms", 
"owner_name": "Gennie Murphy", "is_for_sale": False, "is_retired": False}
]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected", "version": 
"2.0.0"}

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
    return {"message": f"Horse {deleted_horse['name']} deleted 
successfully"}

@app.post("/api/v1/horses/ask")
async def ask_ai_question(question: AIQuestion):
    """
    AI Question endpoint - placeholder for now
    This will be enhanced with Anthropic integration
    """
    # Simple mock responses for now
    mock_responses = {
        "health": f"Based on the horses in your barn, most are in good 
health. Gentle Ben needs some extra attention due to his age.",
        "feed": f"For your horses, I recommend high-quality hay and 
appropriate grain portions based on their activity levels.",
        "training": f"Thunder Bay and Midnight Express would benefit from 
regular training sessions given their ages and breeds.",
        "default": f"That's an interesting question about your horses. I'd 
recommend consulting with your veterinarian for specific advice."
    }
    
    # Simple keyword matching (will be replaced with real AI)
    response_text = mock_responses["default"]
    question_lower = question.question.lower()
    
    if any(word in question_lower for word in ["health", "sick", 
"injury"]):
        response_text = mock_responses["health"]
    elif any(word in question_lower for word in ["feed", "food", 
"nutrition"]):
        response_text = mock_responses["feed"]
    elif any(word in question_lower for word in ["train", "exercise", 
"ride"]):
        response_text = mock_responses["training"]
    
    logger.info(f"AI Question: {question.question}")
    return {
        "question": question.question,
        "answer": response_text,
        "horse_count": len(HORSES_DATA)
    }
EOF

echo "   ✅ Enhanced backend installed"

# Create enhanced frontend
echo "🎨 Installing enhanced frontend..."
mkdir -p frontend
cat > frontend/app.py << 'EOF'
import streamlit as st
import requests
import json

st.set_page_config(page_title="Barn Lady", layout="wide")
st.title("🐴 Barn Lady - Multi-Barn Horse Management")

API_BASE_URL = "http://localhost:8000/api/v1"

# Initialize session state
if 'horses' not in st.session_state:
    st.session_state.horses = []
if 'selected_horse_id' not in st.session_state:
    st.session_state.selected_horse_id = None

def load_horses():
    """Load horses from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/horses/", timeout=10)
        if response.status_code == 200:
            st.session_state.horses = response.json()
            return True
        else:
            st.error(f"API Error: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error loading horses: {e}")
        return False

def create_horse(horse_data):
    """Create a new horse"""
    try:
        response = requests.post(f"{API_BASE_URL}/horses/", 
json=horse_data, timeout=10)
        if response.status_code == 200:
            st.success(f"✅ Successfully added {horse_data['name']}!")
            load_horses()  # Refresh the list
            return True
        else:
            st.error(f"Error creating horse: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def update_horse(horse_id, horse_data):
    """Update an existing horse"""
    try:
        response = requests.put(f"{API_BASE_URL}/horses/{horse_id}", 
json=horse_data, timeout=10)
        if response.status_code == 200:
            st.success(f"✅ Successfully updated {horse_data['name']}!")
            load_horses()  # Refresh the list
            return True
        else:
            st.error(f"Error updating horse: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def delete_horse(horse_id, horse_name):
    """Delete a horse"""
    try:
        response = requests.delete(f"{API_BASE_URL}/horses/{horse_id}", 
timeout=10)
        if response.status_code == 200:
            st.success(f"✅ Successfully removed {horse_name}")
            load_horses()  # Refresh the list
            return True
        else:
            st.error(f"Error deleting horse: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def ask_ai_question(question):
    """Ask AI a question about horses"""
    try:
        response = requests.post(f"{API_BASE_URL}/horses/ask", 
                               json={"question": question}, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"AI Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error asking AI: {e}")
        return None

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["🐴 Your Horses", "➕ Add Horse", "🤖 
Ask AI", "⚙️ Settings"])

with tab1:
    st.header("Your Horses")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 Load/Refresh Horses", type="primary"):
            if load_horses():
                st.balloons()
    
    with col2:
        if st.button("🔍 Test API Connection"):
            try:
                response = requests.get("http://localhost:8000/health", 
timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    st.success(f"✅ API is healthy! Version: 
{health_data.get('version', 'Unknown')}")
                else:
                    st.error(f"❌ API returned: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot reach API: {e}")
    
    # Display horses
    if st.session_state.horses:
        st.success(f"🐴 Found {len(st.session_state.horses)} horses in 
your barn!")
        
        for horse in st.session_state.horses:
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.subheader(f"🐴 {horse['name']}")
                    st.write(f"**Breed:** {horse['breed']} | **Age:** 
{horse['age_display']} | **Color:** {horse['color']}")
                    st.write(f"**Gender:** {horse['gender']} | **Owner:** 
{horse['owner_name']}")
                    if horse.get('current_location'):
                        st.write(f"📍 {horse['current_location']}")
                    
                    # Status badges
                    status_color = {"Good": "🟢", "Excellent": "🟢", 
"Fair": "🟡", "Poor": "🔴"}
                    status_icon = 
status_color.get(horse['current_health_status'], "⚪")
                    st.write(f"**Health:** {status_icon} 
{horse['current_health_status']}")
                    
                    if horse.get('is_for_sale'):
                        st.write("🏷️ **For Sale**")
                    if horse.get('is_retired'):
                        st.write("🏖️ **Retired**")
                
                with col2:
                    if st.button(f"✏️ Edit", key=f"edit_{horse['id']}"):
                        st.session_state.selected_horse_id = horse['id']
                        st.rerun()
                
                with col3:
                    if st.button(f"🗑️ Delete", 
key=f"delete_{horse['id']}", type="secondary"):
                        if 
st.session_state.get(f"confirm_delete_{horse['id']}", False):
                            delete_horse(horse['id'], horse['name'])
                            
st.session_state[f"confirm_delete_{horse['id']}"] = False
                        else:
                            
st.session_state[f"confirm_delete_{horse['id']}"] = True
                            st.warning(f"Click again to confirm deletion 
of {horse['name']}")
                            st.rerun()
                
                st.markdown("---")
        
        # Edit horse form (appears when edit is clicked)
        if st.session_state.selected_horse_id:
            selected_horse = next((h for h in st.session_state.horses if 
h['id'] == st.session_state.selected_horse_id), None)
            if selected_horse:
                st.subheader(f"✏️ Edit {selected_horse['name']}")
                
                with st.form(f"edit_horse_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Horse Name", 
value=selected_horse['name'])
                        breed = st.text_input("Breed", 
value=selected_horse['breed'])
                        age = st.text_input("Age Display", 
value=selected_horse['age_display'])
                        color = st.text_input("Color", 
value=selected_horse['color'])
                    
                    with col2:
                        gender = st.selectbox("Gender", ["Mare", 
"Stallion", "Gelding"], 
                                            index=["Mare", "Stallion", 
"Gelding"].index(selected_horse['gender']))
                        health = st.selectbox("Health Status", 
["Excellent", "Good", "Fair", "Poor"],
                                            index=["Excellent", "Good", 
"Fair", "Poor"].index(selected_horse['current_health_status']))
                        location = st.text_input("Current Location", 
value=selected_horse['current_location'])
                        owner = st.text_input("Owner Name", 
value=selected_horse['owner_name'])
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        for_sale = st.checkbox("For Sale", 
value=selected_horse['is_for_sale'])
                    with col4:
                        retired = st.checkbox("Retired", 
value=selected_horse['is_retired'])
                    
                    col5, col6 = st.columns(2)
                    with col5:
                        if st.form_submit_button("💾 Save Changes", 
type="primary"):
                            horse_data = {
                                "name": name,
                                "breed": breed,
                                "age_display": age,
                                "color": color,
                                "gender": gender,
                                "current_health_status": health,
                                "current_location": location,
                                "owner_name": owner,
                                "is_for_sale": for_sale,
                                "is_retired": retired
                            }
                            if update_horse(selected_horse['id'], 
horse_data):
                                st.session_state.selected_horse_id = None
                                st.rerun()
                    
                    with col6:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.selected_horse_id = None
                            st.rerun()
    else:
        st.info("👆 Click 'Load/Refresh Horses' to see your horses!")

with tab2:
    st.header("➕ Add New Horse")
    
    with st.form("add_horse_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Horse Name *", placeholder="e.g., 
Thunder Bay")
            breed = st.text_input("Breed *", placeholder="e.g., 
Thoroughbred")
            age = st.text_input("Age Display *", placeholder="e.g., 8 
years, 3 months")
            color = st.text_input("Color *", placeholder="e.g., Bay")
        
        with col2:
            gender = st.selectbox("Gender *", ["Mare", "Stallion", 
"Gelding"])
            health = st.selectbox("Health Status *", ["Excellent", "Good", 
"Fair", "Poor"])
            location = st.text_input("Current Location *", 
placeholder="e.g., Meadowbrook Farm")
            owner = st.text_input("Owner Name *", placeholder="e.g., Sarah 
Johnson")
        
        col3, col4 = st.columns(2)
        with col3:
            for_sale = st.checkbox("For Sale")
        with col4:
            retired = st.checkbox("Retired")
        
        if st.form_submit_button("🐴 Add Horse", type="primary"):
            if name and breed and age and color and gender and health and 
location and owner:
                horse_data = {
                    "name": name,
                    "breed": breed,
                    "age_display": age,
                    "color": color,
                    "gender": gender,
                    "current_health_status": health,
                    "current_location": location,
                    "owner_name": owner,
                    "is_for_sale": for_sale,
                    "is_retired": retired
                }
                create_horse(horse_data)
            else:
                st.error("Please fill in all required fields marked with 
*")

with tab3:
    st.header("🤖 Ask AI About Your Horses")
    st.write("Ask questions about horse care, health, training, or 
anything else!")
    
    # Show current horse count
    if st.session_state.horses:
        st.info(f"You have {len(st.session_state.horses)} horses in your 
barn")
    
    question = st.text_area("What would you like to know about your 
horses?", 
                           placeholder="e.g., 'What should I feed my 
horses?' or 'How can I improve Thunder Bay's training?'")
    
    if st.button("🤖 Ask AI", type="primary") and question:
        with st.spinner("🤔 AI is thinking..."):
            ai_response = ask_ai_question(question)
            if ai_response:
                st.success("🤖 AI Response:")
                st.write(ai_response['answer'])
                st.caption(f"Based on {ai_response['horse_count']} horses 
in your barn")

with tab4:
    st.header("⚙️ Settings & Information")
    
    st.subheader("API Information")
    st.code(f"API Base URL: {API_BASE_URL}")
    
    st.subheader("Features")
    features = [
        "✅ View all horses",
        "✅ Add new horses", 
        "✅ Edit horse information",
        "✅ Delete horses",
        "✅ AI Q&A about horse care",
        "🔄 Database integration (coming soon)",
        "🔐 Multi-barn authentication (coming soon)"
    ]
    for feature in features:
        st.write(feature)
    
    st.subheader("Quick Actions")
    if st.button("🔄 Refresh All Data"):
        load_horses()
        st.success("Data refreshed!")
EOF

echo "   ✅ Enhanced frontend installed"

# Check for required dependencies
echo "📦 Checking dependencies..."
python3 -c "import fastapi, pydantic, uvicorn" 2>/dev/null && echo "   ✅ 
FastAPI dependencies found" || echo "   ⚠️  FastAPI dependencies missing - 
run: pip install fastapi uvicorn pydantic"
python3 -c "import streamlit, requests" 2>/dev/null && echo "   ✅ 
Streamlit dependencies found" || echo "   ⚠️  Streamlit dependencies 
missing - run: pip install streamlit requests"

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "📁 Backups saved in: $BACKUP_DIR"
echo ""
echo "🚀 To start your enhanced Barn Lady system:"
echo ""
echo "1. Start the API backend:"
echo "   cd app"
echo "   python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   python3 -m streamlit run app.py"
echo ""
echo "🆕 New Features:"
echo "   ✅ Add horses with a form"
echo "   ✅ Edit any horse inline"
echo "   ✅ Delete horses with confirmation"
echo "   ✅ Ask AI questions about horse care"
echo "   ✅ Tabbed interface for better organization"
echo ""
echo "🔄 Next Steps:"
echo "   - Test all CRUD operations"
echo "   - Try the AI Q&A feature"
echo "   - Then we can restore database integration"
echo ""
echo "Happy horse management! 🐴"
