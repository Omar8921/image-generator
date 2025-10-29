from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os, base64, uuid

load_dotenv()

app = FastAPI(title="Image Generator API")

# CORS so Agent Builder can access it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # okay for testing; restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure image directory exists and serve it
os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PUBLIC_URL = os.getenv("EXTERNAL_BASE_URL", "https://image-generator-bpo3.onrender.com")

class ImageReq(BaseModel):
    prompt: str
    size: str = "1024x1024"

@app.get("/")
def home():
    return {"status": "OK", "message": "Image generator is live."}

@app.post("/generate_image")
async def generate_image(req: ImageReq, request: Request):
    res = client.images.generate(model="gpt-image-1", prompt=req.prompt, size=req.size)
    data = res.data[0]
    b64 = getattr(data, "b64_json", None)
    url = getattr(data, "url", None)

    if b64:
        name = f"{uuid.uuid4().hex}.png"
        path = os.path.join("images", name)
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        base_url = PUBLIC_URL.rstrip("/")
        url = f"{base_url}/images/{name}"

    return {"image_url": url, "prompt": req.prompt}


# 👇 ADD THIS: AI Plugin Manifest for MCP Discovery
@app.get("/.well-known/ai-plugin.json")
def ai_plugin_manifest():
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "Image Generator",
        "name_for_model": "image_generator",
        "description_for_model": "Generate images from text prompts.",
        "api": {
            "type": "openapi",
            "url": f"{PUBLIC_URL}/openapi.json"
        },
        "auth": { "type": "none" },
        "contact_email": "you@example.com",
        "legal_info_url": "https://example.com"
    })
