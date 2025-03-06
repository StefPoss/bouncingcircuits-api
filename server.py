from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

app = FastAPI()

# Dossier /tmp accessible sur Render
app.mount("/static", StaticFiles(directory="/tmp"), name="static")

class PatchRequest(BaseModel):
    style: str
    complexity: str

@app.post("/generate_vcv_patch")
def generate_patch(request: PatchRequest):
    filename = f"{request.style}_{request.complexity}.vcv"
    filepath = os.path.join("/tmp", filename)

    with open(filepath, "w") as f:
        f.write("Patch VCV Rack - Contenu fictif pour test\n")

    return {"file_url": f"https://bouncingcircuits-api.onrender.com/static/{filename}"}

@app.get("/list_files")
def list_files():
    try:
        files = os.listdir("/tmp")
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}
