import os
import json
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Définition du dossier temporaire
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

# Dossier temporaire accessible en statique
app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    """Vérifie si un module est valide."""
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv".replace(" ", "_")  # Supprimer les espaces
    filepath = os.path.join(TMP_DIR, filename)

    # Définition des modules valides avec correction du câblage
    selected_modules = [
        {"plugin": "Fundamental", "model": "VCO", "id": 0, "pos": [0, 0]},
        {"plugin": "Fundamental", "model": "VCF", "id": 1, "pos": [9, 0]},
        {"plugin": "Fundamental", "model": "Mixer", "id": 2, "pos": [16, 0]},
        {"plugin": "Core", "model": "AudioInterface", "id": 3, "pos": [19, 0]}
    ]

    valid_modules = [m for m in selected_modules if is_valid_module(m["plugin"], m["model"])]

    # Correction du câblage : VCO → IN du VCF
    cables = [
        {"id": 0, "outputModuleId": 0, "outputId": "sin", "inputModuleId": 1, "inputId": "in", "color": "#f3374b"},  # ✅ Correct VCO → VCF
        {"id": 1, "outputModuleId": 1, "outputId": "lowpass", "inputModuleId": 2, "inputId": "in", "color": "#ffb437"},  # ✅ VCF → Mixer
        {"id": 2, "outputModuleId": 2, "outputId": "mix", "inputModuleId": 3, "inputId": "1", "color": "#00b56e"},  # ✅ Mixer → AudioInterface (L)
        {"id": 3, "outputModuleId": 2, "outputId": "mix", "inputModuleId": 3, "inputId": "2", "color": "#3695ef"}   # ✅ Mixer → AudioInterface (R)
    ]

    patch_data = {"version": "2.5.2", "modules": valid_modules, "cables": cables, "masterModuleId": 3}

    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    print(f"Patch enregistré sous : {filepath}")
    return {"file_url": f"https://bouncingcircuits-api.onrender.com/download/{filename}"}

@app.get("/download/{filename}")
def download_file(filename: str):
    filepath = os.path.join(TMP_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, headers={"Content-Disposition": f"attachment; filename={filename}"})
    return Response(status_code=404, content="Fichier non trouvé")

@app.get("/list_files")
def list_files():
    try:
        files = os.listdir(TMP_DIR)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

@app.get("/list_valid_modules")
def list_valid_modules():
    with open("valid_modules.json", "r") as f:
        valid_modules = json.load(f)
    return valid_modules
