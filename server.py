import os
import json
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import urllib.parse

# Définir le chemin du dossier temporaire en fonction de l'environnement Render
TMP_DIR = "/opt/render/tmp" if os.getenv("RENDER") else "tmp"

# Vérifier si le dossier TMP_DIR existe, sinon le créer
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

# Charger la liste des modules valides depuis un fichier externe
VALID_MODULES_FILE = "valid_modules.json"
if os.path.exists(VALID_MODULES_FILE):
    with open(VALID_MODULES_FILE, "r") as f:
        VALID_MODULES = json.load(f)
else:
    VALID_MODULES = {}

app = FastAPI()

# Rendre le dossier temporaire accessible publiquement
app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    """Vérifie si un module est valide en fonction de la liste chargée."""
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    # Nettoyage du nom de fichier pour éviter les problèmes
    filename = f"{request.style}_{request.complexity}.vcv".replace(" ", "_")
    filepath = os.path.join(TMP_DIR, filename)

    # Sélection de modules valides
    selected_modules = [
        {"plugin": "Fundamental", "model": "VCO", "id": 0, "pos": [0, 0]},
        {"plugin": "Fundamental", "model": "VCF", "id": 1, "pos": [9, 0]},
        {"plugin": "Fundamental", "model": "Mixer", "id": 2, "pos": [16, 0]},
        {"plugin": "Core", "model": "AudioInterface", "id": 3, "pos": [19, 0]}
    ]

    valid_modules = [m for m in selected_modules if is_valid_module(m["plugin"], m["model"])]

    # Câblage correct
    cables = [
        {"id": 0, "outputModuleId": 0, "outputId": 0, "inputModuleId": 1, "inputId": 0, "color": "#f3374b"},
        {"id": 1, "outputModuleId": 1, "outputId": 0, "inputModuleId": 2, "inputId": 0, "color": "#ffb437"},
        {"id": 2, "outputModuleId": 2, "outputId": 0, "inputModuleId": 3, "inputId": 0, "color": "#00b56e"},
        {"id": 3, "outputModuleId": 2, "outputId": 0, "inputModuleId": 3, "inputId": 1, "color": "#3695ef"}
    ]

    patch_data = {
        "version": "2.5.2",
        "modules": valid_modules,
        "cables": cables,
        "masterModuleId": 3
    }

    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    print(f"Patch enregistré sous : {filepath}")

    # URL encodée correctement pour éviter les problèmes d'affichage
    encoded_filename = urllib.parse.quote(filename)
    file_url = f"https://bouncingcircuits-api.onrender.com/static/{encoded_filename}"
    return {"file_url": file_url}

@app.get("/list_files")
def list_files():
    try:
        files = os.listdir(TMP_DIR)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

@app.get("/download/{filename}")
def download_file(filename: str):
    filepath = os.path.join(TMP_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            content = f.read()
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return Response(content, media_type="application/octet-stream", headers=headers)
    return {"detail": "File not found"}

@app.get("/list_valid_modules")
def list_valid_modules():
    with open("valid_modules.json", "r") as f:
        valid_modules = json.load(f)
    return valid_modules
