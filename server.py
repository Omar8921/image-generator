from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
import os, base64, uuid
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

class ImageReq(BaseModel):
    prompt: str
    size: str = "1024x1024"

@app.post("/generate_image")
def gen(req: ImageReq, request: Request):
    try:
        res = client.images.generate(model="gpt-image-1", prompt=req.prompt, size=req.size)
        data = res.data[0]
        b64 = getattr(data, "b64_json", None)
        url = getattr(data, "url", None)

        if b64:
            name = f"{uuid.uuid4().hex}.png"
            os.makedirs("images", exist_ok=True)
            path = os.path.join("images", name)
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))

            base_url = str(request.base_url).rstrip("/")
            url = f"{base_url}/images/{name}"

        return {"image_url": url, "prompt": req.prompt}
    except Exception as e:
        return {"error": str(e)}