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
    return plugin in VALID_MODULES and model in VALID_MODULES[plugin]

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv"
    filepath = os.path.join("/tmp", filename)
    
    # Exemple de modules générés (doit être amélioré pour la génération dynamique)
    modules = [
        {"plugin": "Fundamental", "model": "VCO"},
        {"plugin": "Fundamental", "model": "VCF"},
        {"plugin": "Fundamental", "model": "VCA"}
    ]
    
    # Filtrer uniquement les modules valides
    valid_modules = [m for m in modules if is_valid_module(m["plugin"], m["model"])]
    
    patch_data = {
        "version": "2.5.2",
        "modules": valid_modules,
        "wires": []
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
