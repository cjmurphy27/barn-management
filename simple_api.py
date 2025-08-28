from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="Barn Lady Simple API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "🐴 Barn Lady Simple API is working!",
        "status": "healthy",
        "time": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "healthy", "api": "working"}

@app.get("/test")
def test():
    return {"test": "success", "message": "API is responding correctly"}
