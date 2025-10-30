from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import os, base64, uuid
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PUBLIC_URL = os.getenv("EXTERNAL_BASE_URL", "https://image-generator-bpo3.onrender.com")

# --- Initialize MCP ---
mcp = FastMCP("image_generator")

# ✅ Correct: use the built-in MCP tool registration method
@mcp.tool()
def generate_image(prompt: str, size: str = "1024x1024") -> dict:
    """Generate a photorealistic image and return its live URL."""
    res = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
    data = res.data[0]
    b64 = getattr(data, "b64_json", None)
    url = getattr(data, "url", None)

    if b64:
        name = f"{uuid.uuid4().hex}.png"
        os.makedirs("images", exist_ok=True)
        path = os.path.join("images", name)
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        url = f"{PUBLIC_URL.rstrip('/')}/images/{name}"

    return {"image_url": url, "prompt": prompt}


# ✅ FastAPI setup
app = FastAPI(title="Image Generator MCP Server")

# ✅ Add CORS so Agent Builder can call /mcp/tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Mount the MCP app
app.mount("/mcp", mcp.streamable_http_app())


# ✅ (Optional sanity check route)
@app.get("/")
def root():
    return {"status": "ok", "message": "MCP server running"}
