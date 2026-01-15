from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp_use import MCPAgent, MCPClient
import json
import os
import numpy as np
import shutil
from mcp_service import UrbanHCFMCPService
from geojson_utils import ndarrays_to_geojson, format_backend_response

app = FastAPI()
mcp_service = UrbanHCFMCPService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug/mcp")
async def debug_mcp():
    try:
       agent_result = await mcp_service.run_query("what are lat lon irvine?")
       return {"result": agent_result}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/analyze")
async def analyze(request: QueryRequest):
    """
    Frontend → MCP → GeoJSON
    """
    artifact_dir = "runtime/"
    # if os.path.exists(artifact_dir):
    #     shutil.rmtree(artifact_dir)
    # os.makedirs(artifact_dir, exist_ok=True)
    agent_result = await mcp_service.run_query(request.query)
    lst = np.load(f"{artifact_dir}lst.npy")
    uhi = np.load(f"{artifact_dir}uhi.npy")
    counterfactual_uhi = np.load(f"{artifact_dir}counterfactual_uhi.npy")
    delta = np.load(f"{artifact_dir}delta_uhi.npy")

    with open(os.path.join(artifact_dir, "meta.json")) as f:
        meta = json.load(f)
    geojson_result = ndarrays_to_geojson({
        "lst": lst,
        "uhi": uhi,
        "counterfactual_uhi": counterfactual_uhi,
        "delta_uhi": delta,
        "bbox": meta['bbox'] 
    })
    response = format_backend_response(geojson_result, agent_result)
    if os.path.exists(artifact_dir) and os.path.isdir(artifact_dir):
        shutil.rmtree(artifact_dir)
    return response

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_service.shutdown()
