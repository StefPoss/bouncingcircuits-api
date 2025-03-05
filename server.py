from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Modèle pour recevoir les paramètres
class PatchRequest(BaseModel):
    style: str
    complexity: str

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    # Simulation : Génération d'un patch fictif
    file_url = f"https://example.com/patches/{request.style}_{request.complexity}.vcv"
    return {"file_url": file_url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
