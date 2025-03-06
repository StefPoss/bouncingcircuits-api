import os
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Charger la liste des modules valides depuis un fichier externe
VALID_MODULES_FILE = "valid_modules.json"

if os.path.exists(VALID_MODULES_FILE):
    with open(VALID_MODULES_FILE, "r") as f:
        VALID_MODULES = json.load(f)
else:
    VALID_MODULES = {}

app = FastAPI()

# Dossier /tmp accessible sur Render
app.mount("/static", StaticFiles(directory="/tmp"), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    """Vérifie si un module est valide en fonction de la liste chargée."""
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv"
    filepath = os.path.join("/tmp", filename)

    # Sélectionner quelques modules valides pour générer un patch
    selected_modules = [
        {"id": 0, "plugin": "Fundamental", "model": "VCO"},
        {"id": 1, "plugin": "Fundamental", "model": "VCF"},
        {"id": 2, "plugin": "Fundamental", "model": "Mixer"},
        {"id": 3, "plugin": "Core", "model": "AudioInterface"}  # Module de sortie
    ]

    print("Modules valides chargés :", VALID_MODULES)
    print("Modules sélectionnés avant filtrage :", selected_modules)

    # Filtrer uniquement les modules valides
    valid_modules = [m for m in selected_modules if is_valid_module(m["plugin"], m["model"])]

    print("Modules après filtrage :", valid_modules)

    # Ajouter des connexions entre les modules
    wires = []
    if len(valid_modules) >= 3:
        wires = [
            {"outputModuleId": 0, "outputId": "saw", "inputModuleId": 1, "inputId": "in"},  # VCO → VCF
            {"outputModuleId": 1, "outputId": "lowpass", "inputModuleId": 2, "inputId": "in"},  # VCF → Mixer
        ]

    # Connexion du Mixer à l'Audio Interface
    if len(valid_modules) >= 4:
        wires.append({
            "outputModuleId": 2,  # Mixer -> Audio Interface
            "outputId": "mix",
            "inputModuleId": 3,  # Audio Interface
            "inputId": "left"
        })
        wires.append({
            "outputModuleId": 2,
            "outputId": "mix",
            "inputModuleId": 3,
            "inputId": "right"
        })

    # Construire le patch JSON
    patch_data = {
        "version": "2.5.2",
        "modules": valid_modules,
        "wires": wires
    }

    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    return {"file_url": f"https://bouncingcircuits-api.onrender.com/static/{filename}"}

@app.get("/list_files")
def list_files():
    try:
        files = os.listdir("/tmp")
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/list_valid_modules")
def list_valid_modules():
    with open("valid_modules.json", "r") as f:
        valid_modules = json.load(f)
    return valid_modules
