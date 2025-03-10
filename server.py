import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Définition du dossier temporaire correct pour Render
TMP_DIR = "/opt/render/tmp"
os.makedirs(TMP_DIR, exist_ok=True)

# Charger la liste des modules valides
VALID_MODULES_FILE = "valid_modules.json"
VALID_MODULES = {}
if os.path.exists(VALID_MODULES_FILE):
    with open(VALID_MODULES_FILE, "r") as f:
        VALID_MODULES = json.load(f)

app = FastAPI()

# Rendre le dossier temporaire accessible via "/static"
app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    """Vérifie si un module est valide en fonction de la liste chargée."""
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv".replace(" ", "_")
    filepath = os.path.join(TMP_DIR, filename)

    # Sélection de modules avec un placement plus compact
    selected_modules = [
        {"plugin": "Fundamental", "model": "VCO", "id": 0, "pos": [0, 0]},
        {"plugin": "Fundamental", "model": "VCF", "id": 1, "pos": [8, 0]},
        {"plugin": "Fundamental", "model": "Mixer", "id": 2, "pos": [16, 0]},
        {"plugin": "Core", "model": "AudioInterface", "id": 3, "pos": [24, 0]},
    ]

    # Vérifier que les modules sont bien valides
    valid_modules = [m for m in selected_modules if is_valid_module(m["plugin"], m["model"])]

    # Connexions corrigées (évite l'erreur sur le CUT)
    cables = [
        {"id": 0, "outputModuleId": 0, "outputId": 0, "inputModuleId": 1, "inputId": 1},
        {"id": 1, "outputModuleId": 1, "outputId": 0, "inputModuleId": 2, "inputId": 0},
        {"id": 2, "outputModuleId": 2, "outputId": 0, "inputModuleId": 3, "inputId": 0},
        {"id": 3, "outputModuleId": 2, "outputId": 0, "inputModuleId": 3, "inputId": 1},
    ]

    # Construction du patch JSON
    patch_data = {
        "version": "2.5.2",
        "modules": valid_modules,
        "cables": cables,
        "masterModuleId": 3,
    }

    # Sauvegarde du fichier VCV
    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    print(f"Patch enregistré sous : {filepath}")

    return {"file_url": f"https://bouncingcircuits-api.onrender.com/static/{filename}"}

@app.get("/list_files")
def list_files():
    """Liste les fichiers disponibles dans /tmp"""
    try:
        files = os.listdir(TMP_DIR)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

@app.get("/download/{filename}")
def download_file(filename: str):
    """Fournit un lien de téléchargement avec Content-Disposition pour éviter l'ouverture directe"""
    filepath = os.path.join(TMP_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="application/octet-stream", filename=filename)
    return {"error": "File not found"}

@app.get("/list_valid_modules")
def list_valid_modules():
    """Renvoie la liste des modules valides"""
    return VALID_MODULES
