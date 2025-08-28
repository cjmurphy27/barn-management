from fastapi import FastAPI

app = FastAPI(
    title="Barn Lady API",
    version="1.0.0",
    description="AI-Powered Multi-Tenant Horse Management System"
)

@app.get("/")
async def root():
    return {"message": "Welcome to Barn Lady API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}
