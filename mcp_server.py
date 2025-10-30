# from fastapi import FastAPI, APIRouter
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from mcp.server.fastmcp import FastMCP
# from openai import OpenAI
# import os, base64, uuid, inspect
# from dotenv import load_dotenv

# # --- Load environment ---
# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# PUBLIC_URL = os.getenv("EXTERNAL_BASE_URL", "https://image-generator-bpo3.onrender.com")

# # --- Initialize MCP server ---
# mcp = FastMCP("image_generator")

# REGISTERED_TOOLS = {}

# def register_tool(func):
#     """Decorator to register tools for MCP discovery."""
#     REGISTERED_TOOLS[func.__name__] = func
#     return mcp.tool()(func)

# # --- Tool definition ---
# @register_tool
# def generate_image(prompt: str, size: str = "1024x1024") -> dict:
#     """Generate a photorealistic image and return its live URL."""
#     res = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
#     data = res.data[0]
#     b64 = getattr(data, "b64_json", None)
#     url = getattr(data, "url", None)

#     # Save locally if only base64 is returned
#     if b64:
#         name = f"{uuid.uuid4().hex}.png"
#         os.makedirs("images", exist_ok=True)
#         path = os.path.join("images", name)
#         with open(path, "wb") as f:
#             f.write(base64.b64decode(b64))
#         url = f"{PUBLIC_URL.rstrip('/')}/images/{name}"

#     return {"image_url": url, "prompt": prompt}


# # --- FastAPI app setup ---
# app = FastAPI(title="Image Generator MCP Server")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def root():
#     return {"status": "ok", "message": "MCP server running"}


# # --- MCP Routes ---
# router = APIRouter()

# @router.get("/tools")
# def list_tools():
#     """Return tools in the official MCP schema format."""
#     return {
#         "tools": [
#             {
#                 "name": name,
#                 "description": func.__doc__ or "",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "prompt": {"type": "string"},
#                         "size": {"type": "string", "default": "1024x1024"},
#                     },
#                     "required": ["prompt"],
#                 },
#             }
#             for name, func in REGISTERED_TOOLS.items()
#         ]
#     }

# @router.post("/call/{tool_name}")
# async def call_tool(tool_name: str, body: dict):
#     """Call a registered MCP tool."""
#     tool = REGISTERED_TOOLS.get(tool_name)
#     if not tool:
#         return {"error": f"Tool '{tool_name}' not found"}

#     if inspect.iscoroutinefunction(tool):
#         return await tool(**body)
#     else:
#         return tool(**body)


# @app.get("/.well-known/mcp.json")
# def mcp_manifest():
#     return JSONResponse({
#         "version": "1.0",
#         "server_url": f"{PUBLIC_URL.rstrip('/')}",
#         "tools": {
#             "endpoint": f"{PUBLIC_URL.rstrip('/')}/mcp/tools"
#         }
#     })

# # --- Register router ---
# app.include_router(router, prefix="/mcp")

# print("✅ Routes:", [r.path for r in app.router.routes])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Image Generator MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- tool definition ---
@app.post("/generate_image")
def generate_image(prompt: str, size: str = "1024x1024"):
    res = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
    return {"image_url": res.data[0].url, "prompt": prompt}

# --- MCP discovery endpoints ---
@app.get("/.well-known/mcp.json")
def mcp_manifest():
    return {
        "mcp_server": {
            "name": "image_generator",
            "version": "1.0.0",
            "tools_endpoint": "/mcp/tools"
        }
    }

@app.get("/mcp/tools")
def mcp_tools():
    return {
        "tools": [
            {
                "name": "generate_image",
                "description": "Generate a photorealistic image using GPT-image-1.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "size": {"type": "string", "default": "1024x1024"}
                    },
                    "required": ["prompt"]
                }
            }
        ]
    }
