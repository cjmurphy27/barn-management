with open("app/main.py","w") as f: f.write("from fastapi import FastAPI
app = FastAPI()
HORSES_DATA = [{\"id\":\"1\",\"name\":\"Thunder Bay\"},{\"id\":\"2\",\"name\":\"Starlight Princess\"}]
@app.get(\"/health\")
def health(): return {\"status\":\"ok\"}
@app.get(\"/api/v1/horses/\")
def get_horses(): return HORSES_DATA")
