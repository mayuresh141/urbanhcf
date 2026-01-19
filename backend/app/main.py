from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp_use import MCPAgent, MCPClient
import json
import os
import numpy as np
import shutil
import pickle
import uuid
from app.redis_client import redis_client
from mcp_agent.mcp_service import UrbanHCFMCPService
from app.geojson_utils import ndarrays_to_geojson, format_backend_response

app = FastAPI()
mcp_service = UrbanHCFMCPService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://urbanhcf.netlify.app"],
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
       agent_result = await mcp_service.run_query("what are lat lon irvine?", "")
       return {"result": agent_result}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/analyze")
async def analyze(request: QueryRequest):
    """
    Frontend → MCP → GeoJSON
    """
    run_id = str(uuid.uuid4())
    agent_result = await mcp_service.run_query(request.query, run_id)
    
    return {"run_id": run_id, "analysis": agent_result}

@app.get("/results/{run_id}")
def get_results(run_id: str):
    try:
        payload_str = redis_client.get(f"uhi:{run_id}")
        payload = json.loads(payload_str)
        print(payload.keys())
        lst = payload['lst']
        uhi = payload['uhi']
        counterfactual_uhi = payload['counterfactual_uhi']
        delta = payload['delta_uhi']
        bbox = payload['bbox']
        
        geojson_result = ndarrays_to_geojson({
            "lst": lst,
            "uhi": uhi,
            "counterfactual_uhi": counterfactual_uhi,
            "delta_uhi": delta,
            "bbox": bbox 
        })
        response = format_backend_response(geojson_result)
        return response
    except Exception as e:
        # Log the error for debugging
        print(f"Error in /results/{run_id}: {e}")
        # Return a safe error to frontend
        return {"status": "error", "message": str(e)}

@app.on_event("shutdown")
async def shutdown_event():
    await mcp_service.shutdown()
