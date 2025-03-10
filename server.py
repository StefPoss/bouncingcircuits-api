import os
import json
import random
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
        try:
            VALID_MODULES = json.load(f)
        except json.JSONDecodeError:
            VALID_MODULES = {}

app = FastAPI()

# Rendre le dossier temporaire accessible via "/static"
app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    if not VALID_MODULES:
        raise HTTPException(status_code=500, detail="valid_modules.json non chargé ou vide")
    
    filename = f"{request.style}_{request.complexity}.vcv".replace(" ", "_")
    filepath = os.path.join(TMP_DIR, filename)
    
    module_pool = {
        "ambient": ["ConfusingSimpler", "Plateau", "LFO", "Reverb"],
        "breakcore": ["DrumSequencer", "ClockMultiplier", "Random", "Kickall"],
        "acid": ["VCO", "VCF", "Env", "Delay"],
        "experimental": ["JunoV", "Noise", "VCA", "Wavefolder"]
    }
    
    num_modules = {"simple": 3, "intermediate": 5, "advanced": 7}.get(request.complexity, 4)
    selected_models = module_pool.get(request.style, module_pool["experimental"])
    num_modules = min(num_modules, len(selected_models))  # Évite erreur si trop de modules demandés
    selected_models = random.sample(selected_models, num_modules)
    
    selected_modules = []
    for i, model in enumerate(selected_models):
        for plugin in VALID_MODULES:
            if model in VALID_MODULES[plugin]:
                selected_modules.append({"plugin": plugin, "model": model, "id": i, "pos": [i * 8, 0]})
                break
    
    selected_modules.append({"plugin": "Core", "model": "AudioInterface", "id": len(selected_modules), "pos": [len(selected_modules) * 8, 0]})
    
    cables = []
    for i in range(len(selected_modules) - 1):
        cables.append({"id": i, "outputModuleId": i, "outputId": 0, "inputModuleId": i + 1, "inputId": 0})
    
    patch_data = {
        "version": "2.5.2",
        "modules": selected_modules,
        "cables": cables,
        "masterModuleId": len(selected_modules) - 1,
    }
    
    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)
    
    return {"file_url": f"https://bouncingcircuits-api.onrender.com/static/{filename}"}

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
        return FileResponse(filepath, media_type="application/octet-stream", filename=filename, headers={"Content-Disposition": f"attachment; filename={filename}"}, as_attachment=True)
    return {"error": "File not found"}

@app.get("/list_valid_modules")
def list_valid_modules():
    return VALID_MODULES
