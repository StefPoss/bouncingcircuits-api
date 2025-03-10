import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Configuration du dossier temporaire sur Render
TMP_DIR = "/opt/render/tmp"
os.makedirs(TMP_DIR, exist_ok=True)

# Chargement des modules valides
VALID_MODULES_FILE = "valid_modules.json"
try:
    with open(VALID_MODULES_FILE, "r") as f:
        VALID_MODULES = json.load(f)
except FileNotFoundError:
    VALID_MODULES = []

# Initialisation de FastAPI
app = FastAPI()

# Fonction pour nettoyer les noms de fichiers
def sanitize_filename(filename: str) -> str:
    return filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

# Endpoint pour télécharger un patch VCV Rack
@app.get("/download/{filename}")
async def download_patch(filename: str):
    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(TMP_DIR, sanitized_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    return FileResponse(file_path, filename=sanitized_filename, media_type='application/octet-stream', headers={
        "Content-Disposition": f"attachment; filename={sanitized_filename}"
    })

# Modèle pour la génération dynamique de patches
class PatchRequest(BaseModel):
    patch_name: str
    modules: list[str]

# Endpoint pour générer dynamiquement un patch VCV Rack
@app.post("/generate_patch")
async def generate_patch(request: PatchRequest):
    sanitized_name = sanitize_filename(request.patch_name) + ".vcv"
    file_path = os.path.join(TMP_DIR, sanitized_name)
    
    # Vérification des modules
    invalid_modules = [m for m in request.modules if m not in VALID_MODULES]
    if invalid_modules:
        raise HTTPException(status_code=400, detail=f"Modules invalides: {', '.join(invalid_modules)}")
    
    # Génération du fichier JSON pour le patch VCV Rack
    patch_data = {
        "modules": [{"name": m} for m in request.modules],
        "connections": []  # À compléter selon tes besoins
    }
    
    with open(file_path, "w") as f:
        json.dump(patch_data, f, indent=4)
    
    return {"message": "Patch généré avec succès", "download_url": f"/download/{sanitized_name}"}

# Montage des fichiers statiques pour tester les téléchargements
app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")
