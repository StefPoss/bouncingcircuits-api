from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import random

app = FastAPI()

TMP_DIR = "/tmp"
os.makedirs(TMP_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

# Modules disponibles selon les styles
MODULES = {
    "ambient": [
        {"plugin": "VCV", "model": "VCO"},
        {"plugin": "VCV", "model": "VCF"},
        {"plugin": "Valley", "model": "Plateau"},
        {"plugin": "VCV", "model": "LFO"}
    ],
    "breakcore": [
        {"plugin": "VCV", "model": "Drums"},
        {"plugin": "VCV", "model": "Delay"},
        {"plugin": "VCV", "model": "Filter"}
    ],
    "granular": [
        {"plugin": "NYSTHI", "model": "Confusing Simpler"},
        {"plugin": "VCV", "model": "Reverb"}
    ]
}

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv"
    filepath = os.path.join(TMP_DIR, filename)

    selected_modules = MODULES.get(request.style, MODULES["ambient"])
    
    # Générer dynamiquement les modules
    modules = [
        {
            "plugin": mod["plugin"],
            "model": mod["model"],
            "pos": [random.randint(100, 400), random.randint(100, 300)],
            "params": {},
            "inputs": {},
            "outputs": {}
        } for mod in selected_modules
    ]

    patch_data = {
        "version": "2.5.2",
        "modules": modules,
        "wires": []
    }

    with open(filepath, "w") as f:
        json.dump(patch_data, f, indent=4)

    return {"file_url": f"https://bouncingcircuits-api.onrender.com/static/{filename}"}
