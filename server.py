from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class ImageReq(BaseModel):
    prompt: str
    size: str = "1024x1024"

@app.post("/generate_image")
def gen(req: ImageReq):
    try:
        res = client.images.generate(model="gpt-image-1", prompt=req.prompt, size=req.size)
        url = res.data[0].url
        return {"image_url": url, "prompt": req.prompt}
    except Exception as e:
        return {"error": str(e)}
