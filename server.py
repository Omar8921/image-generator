from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
import os, base64, uuid
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PUBLIC_URL = os.getenv("EXTERNAL_BASE_URL")

app = FastAPI()

os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

class ImageReq(BaseModel):
    prompt: str
    size: str = "1024x1024"

@app.get("/")
def home():
    return {"status": "OK", "message": "Image generator is live."}

@app.post("/generate_image")
def gen(req: ImageReq, request: Request):
    try:
        res = client.images.generate(model="gpt-image-1", prompt=req.prompt, size=req.size)
        data = res.data[0]
        b64 = getattr(data, "b64_json", None)
        url = getattr(data, "url", None)

        if b64:
            name = f"{uuid.uuid4().hex}.png"
            path = os.path.join("images", name)
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))

            base_url = (PUBLIC_URL or str(request.base_url)).rstrip("/")
            url = f"{base_url}/images/{name}"

        return {"image_url": url, "prompt": req.prompt}
    except Exception as e:
        return {"error": str(e)}

@app.get("/.well-known/ai-plugin.json")
def plugin_manifest():
    """
    Simple MCP manifest so Agent Builder can discover /generate_image.
    """
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "Image Generator",
        "name_for_model": "image_generator",
        "description_for_model": "Generate images from text prompts.",
        "api": {
            "type": "openapi",
            "url": f"{os.getenv('EXTERNAL_BASE_URL', 'https://image-generator-bpo3.onrender.com')}/openapi.json"
        },
        "auth": { "type": "none" },
        "contact_email": "you@example.com",
        "legal_info_url": "https://example.com"
    })