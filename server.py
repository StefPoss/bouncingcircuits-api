import os
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Définition du répertoire de stockage des fichiers
TMP_DIR = "/opt/render/tmp/"
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

# Dossier accessible via /static/
app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    """Vérifie si un module est valide en fonction de la liste chargée."""
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv"
    filepath = os.path.join(TMP_DIR, filename)

    # Sélectionner quelques modules valides pour générer un patch
    selected_modules = [
        {"plugin": "Fundamental", "model": "VCO", "id": 0, "pos": [0, 0]},
        {"plugin": "Fundamental", "model": "VCF", "id": 1, "pos": [9, 0]},
        {"plugin": "Fundamental", "model": "Mixer", "id": 2, "pos": [16, 0]},
        {"plugin": "Core", "model": "AudioInterface", "id": 3, "pos": [19, 0]}
    ]

    # Vérifier que les modules sont bien valides
    valid_modules = [m for m in selected_modules if is_valid_module(m["plugin"], m["model"])]

    # Ajouter des connexions entre les modules
    cables = [
        {"id": 0, "outputModuleId": 0, "outputId": 0, "inputModuleId": 1, "inputId": 3, "color": "#f3374b"},  # ✅ VCO → VCF (entrée correcte)
        {"id": 1, "outputModuleId": 1, "outputId": 0, "inputModuleId": 2, "inputId": 0, "color": "#ffb437"},  # ✅ VCF → Mixer
        {"id": 2, "outputModuleId": 2, "outputId": 0, "inputModuleId": 3, "inputId": 0, "color": "#00b56e"},  # ✅ Mixer → AudioInterface (L)
        {"id": 3, "outputModuleId": 2, "outputId": 0, "inputModuleId": 3, "inputId": 1, "color": "#3695ef"}   # ✅ Mixer → AudioInterface (R)
    ]

    # Construire le patch JSON
    patch_data = {
        "version": "2.5.2",
        "modules": valid_modules,
        "cables": cables,
        "masterModuleId": 3  # ✅ Ajout du masterModuleId pour correspondre à la sauvegarde VCV
    }

    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    print(f"Patch enregistré sous : {filepath}")  # 🔹 Ajout pour voir où le fichier est créé

    # Retourner un lien cliquable pour le téléchargement
    return {"file_url": f"https://bouncingcircuits-api.onrender.com/static/{filename}"}

@app.get("/list_files")
def list_files():
    try:
        files = os.listdir(TMP_DIR)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/list_files_debug")
def list_files_debug():
    files = os.listdir(os.path.abspath(TMP_DIR))
    return {"all_files": files}

@app.get("/list_valid_modules")
def list_valid_modules():
    with open("valid_modules.json", "r") as f:
        valid_modules = json.load(f)
    return valid_modules
