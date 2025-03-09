import os
import json
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Définition du dossier de stockage temporaire sur Render
TMP_DIR = "/opt/render/tmp"
os.makedirs(TMP_DIR, exist_ok=True)

# Charger la liste des modules valides depuis un fichier externe
VALID_MODULES_FILE = "valid_modules.json"
if os.path.exists(VALID_MODULES_FILE):
    with open(VALID_MODULES_FILE, "r") as f:
        VALID_MODULES = json.load(f)
else:
    VALID_MODULES = {}

app = FastAPI()

# Rendre les fichiers accessibles via /static
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

    # Sélection de modules avancés
    selected_modules = [
        {"plugin": "Fundamental", "model": "VCO", "id": 0, "pos": [0, 0]},
        {"plugin": "Fundamental", "model": "VCF", "id": 1, "pos": [9, 0]},
        {"plugin": "Bogaudio", "model": "S&H", "id": 2, "pos": [18, 0]},
        {"plugin": "Bogaudio", "model": "Noise", "id": 3, "pos": [27, 0]},
        {"plugin": "Fundamental", "model": "Delay", "id": 4, "pos": [36, 0]},
        {"plugin": "Core", "model": "AudioInterface", "id": 5, "pos": [45, 0]}
    ]

    valid_modules = [m for m in selected_modules if is_valid_module(m["plugin"], m["model"])]

    # Câblage correct (valeurs numériques, plus d'erreur SIN → CUT)
    cables = [
        {"id": 0, "outputModuleId": 0, "outputId": 0, "inputModuleId": 1, "inputId": 0, "color": "#f3374b"},  # ✅ VCO → VCF (entrée correcte)
        {"id": 1, "outputModuleId": 1, "outputId": 0, "inputModuleId": 2, "inputId": 0, "color": "#ffb437"},  # ✅ VCF → S&H
        {"id": 2, "outputModuleId": 2, "outputId": 0, "inputModuleId": 3, "inputId": 0, "color": "#00b56e"},  # ✅ S&H → Noise
        {"id": 3, "outputModuleId": 3, "outputId": 0, "inputModuleId": 4, "inputId": 0, "color": "#3695ef"},  # ✅ Noise → Delay
        {"id": 4, "outputModuleId": 4, "outputId": 0, "inputModuleId": 5, "inputId": 0, "color": "#8844ff"},  # ✅ Delay → AudioInterface (L)
        {"id": 5, "outputModuleId": 4, "outputId": 0, "inputModuleId": 5, "inputId": 1, "color": "#ff44cc"}   # ✅ Delay → AudioInterface (R)
    ]

    patch_data = {
        "version": "2.5.2",
        "modules": valid_modules,
        "cables": cables,
        "masterModuleId": 5
    }

    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    print(f"Patch enregistré sous : {filepath}")

    return {"file_url": f"https://bouncingcircuits-api.onrender.com/static/{filename}"}

@app.get("/list_files")
def list_files():
    try:
        files = os.listdir(TMP_DIR)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

@app.get("/download/{filename}")
def download_patch(filename: str):
    filepath = os.path.join(TMP_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            content = f.read()
        return Response(content, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={filename}"})
    return {"error": "File not found"}

@app.get("/list_valid_modules")
def list_valid_modules():
    with open("valid_modules.json", "r") as f:
        valid_modules = json.load(f)
    return valid_modules
