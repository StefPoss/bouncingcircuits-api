from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

class PatchRequest(BaseModel):
    style: str
    complexity: str

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    # Générer un fichier .vcv fictif pour le test
    filename = f"{request.style}_{request.complexity}.vcv"
    filepath = f"static/{filename}"

    # Créer un fichier vide (à remplacer par une vraie génération)
    os.makedirs("static", exist_ok=True)
    with open(filepath, "w") as f:
        f.write("Patch VCV Rack - Contenu fictif pour test\n")

    file_url = f"https://bouncingcircuits-api.onrender.com/static/{filename}"
    return {"file_url": file_url}
