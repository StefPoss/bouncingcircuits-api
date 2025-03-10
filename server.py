import os
import json
import random
import threading
import time
import requests
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
    try:
        with open(VALID_MODULES_FILE, "r") as f:
            VALID_MODULES = json.load(f)
        if not VALID_MODULES:
            print("⚠️ valid_modules.json est vide ou mal formatté!")
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de chargement de valid_modules.json: {e}")
        VALID_MODULES = {}
else:
    print("⚠️ valid_modules.json introuvable!")

print("📌 Modules chargés depuis valid_modules.json:", list(VALID_MODULES.keys()))

app = FastAPI()

@app.on_event("startup")
def startup_event():
    print("✅ Serveur FastAPI démarré avec succès !")
    print("🚀 FastAPI tourne sur le bon port !")

@app.on_event("shutdown")
def shutdown_event():
    print("⚠️ Serveur FastAPI est en train de s'arrêter !")

@app.get("/")
def root():
    return {"message": "🚀 API VCV Rack est en ligne ! Utilise /generate_vcv_patch pour créer un patch."}

@app.get("/health")
@app.head("/health")
def health_check():
    """Répond aux requêtes HEAD pour éviter l'erreur 405 sur Render."""
    return {"status": "ok"}

app.mount("/static", StaticFiles(directory=TMP_DIR), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

def is_valid_module(plugin, model):
    return plugin in VALID_MODULES and model in VALID_MODULES.get(plugin, [])

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    print(f"📌 Requête reçue: {request.style}, {request.complexity}")
    if not VALID_MODULES:
        raise HTTPException(status_code=500, detail="valid_modules.json non chargé ou vide")
    
    filename = f"{request.style}_{request.complexity}.vcv".replace(" ", "_")
    filepath = os.path.join(TMP_DIR, filename)
    
    module_pool = {
        "ambient": ["VCO", "VCF", "Reverb", "LFO", "Plateau"],
        "breakcore": ["DrumSequencer", "ClockMultiplier", "VCA", "Random", "Kickall"],
        "acid": ["VCO", "VCF", "VCA", "Delay", "Env"],
        "experimental": ["Noise", "Wavefolder", "SampleHold", "LFO", "Random"]
    }
    
    num_modules = {"simple": 3, "intermediate": 5, "advanced": 7}.get(request.complexity, 4)
    selected_models = module_pool.get(request.style, module_pool.get("experimental", []))
    num_modules = min(num_modules, len(selected_models)) if selected_models else 3
    
    if not selected_models:
        print(f"⚠️ Aucun module trouvé pour {request.style}, fallback sur des modules aléatoires")
        all_models = [m for p in VALID_MODULES.values() for m in p]
        selected_models = random.sample(all_models, min(num_modules, len(all_models)))
    else:
        selected_models = random.sample(selected_models, num_modules)
    
    selected_modules = []
    for i, model in enumerate(selected_models):
        for plugin in VALID_MODULES:
            if model in VALID_MODULES[plugin]:
                selected_modules.append({"plugin": plugin, "model": model, "id": i, "pos": [i * 8, 0]})
                break
    
    if not selected_modules:
        raise HTTPException(status_code=500, detail="Aucun module valide sélectionné. Vérifiez valid_modules.json.")
    
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

# Vérification keep-alive avec URL publique
def keep_alive():
    while True:
        try:
            requests.get("https://bouncingcircuits-api.onrender.com/health")
            print("🔄 Keep-alive ping envoyé")
        except Exception as e:
            print(f"⚠️ Erreur keep-alive: {e}")
        time.sleep(30)

threading.Thread(target=keep_alive, daemon=True).start()

# Boucle infinie pour éviter l'arrêt du serveur
while True:
    time.sleep(60)