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

# Dossier /tmp accessible sur Render pour stocker les fichiers générés
STATIC_DIR = "/tmp"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    """Vérifie si un module est valide en fonction de la liste chargée."""
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv"
    filepath = os.path.join(STATIC_DIR, filename)

    # Sélectionner des modules valides
    selected_modules = [
        {"plugin": "Fundamental", "model": "VCO", "id": 0},
        {"plugin": "Fundamental", "model": "VCF", "id": 1},
        {"plugin": "Fundamental", "model": "Mixer", "id": 2},
        {"plugin": "Core", "model": "AudioInterface", "id": 3}  # Module de sortie
    ]

    print("Modules valides chargés :", VALID_MODULES)
    print("Modules sélectionnés avant filtrage :", selected_modules)

    # Filtrer uniquement les modules valides
    valid_modules = [m for m in selected_modules if is_valid_module(m["plugin"], m["model"])]

    print("Modules après filtrage :", valid_modules)

    # Ajouter des connexions entre les modules
    wires = []
    if len(valid_modules) >= 3:
        wires.extend([
            {"outputModuleId": 0, "outputId": "sin", "inputModuleId": 1, "inputId": "in"},  # VCO → VCF
            {"outputModuleId": 1, "outputId": "lowpass", "inputModuleId": 2, "inputId": "in"},  # VCF → Mixer
        ])

    if len(valid_modules) >= 4:
        wires.extend([
            {"outputModuleId": 2, "outputId": "mix", "inputModuleId": 3, "inputId": "1"},  # Mixer → Audio Interface (Left)
            {"outputModuleId": 2, "outputId": "mix", "inputModuleId": 3, "inputId": "2"}   # Mixer → Audio Interface (Right)
        ])

    # Construire le patch JSON
    patch_data = {
        "version": "2.5.2",
        "modules": valid_modules,
        "wires": wires
    }

    # Écrire le fichier JSON
    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    return {"file_url": f"/static/{filename}"}

@app.get("/list_files")
def list_files():
    """Liste les fichiers générés dans le dossier temporaire."""
    try:
        files = os.listdir(STATIC_DIR)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

@app.get("/list_valid_modules")
def list_valid_modules():
    """Retourne la liste des modules valides à partir du fichier JSON."""
    with open(VALID_MODULES_FILE, "r") as f:
        valid_modules = json.load(f)
    return valid_modules

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)
