from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
import os, base64, uuid
from dotenv import load_dotenv

# --- Load env ---
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PUBLIC_URL = os.getenv("EXTERNAL_BASE_URL", "https://image-generator-bpo3.onrender.com")

mcp = FastMCP("image_generator")

REGISTERED_TOOLS = {}

def register_tool(func):
    REGISTERED_TOOLS[func.__name__] = func
    return mcp.tool()(func)

@register_tool
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


# --- App setup ---
app = FastAPI(title="Image Generator MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "MCP server running"}

router = APIRouter()

@router.get("/tools")
def list_tools():
    """Return tools in the official MCP schema format."""
    return {
        "tools": [
            {
                "name": name,
                "description": func.__doc__ or "",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "size": {"type": "string", "default": "1024x1024"}
                    },
                    "required": ["prompt"]
                }
            }
            for name, func in REGISTERED_TOOLS.items()
        ]
    }

@router.post("/call/{tool_name}")
async def call_tool(tool_name: str, body: dict):
    tool = REGISTERED_TOOLS.get(tool_name)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found"}
    return await tool(**body) if callable(tool) else {"error": "Invalid tool"}

app.include_router(router, prefix="/mcp")

print("✅ Routes:", [r.path for r in app.router.routes])
