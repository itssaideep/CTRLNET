import asyncio
import logging
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ctrlnet.server.event_bus import event_bus
from ctrlnet.config import config
from ctrlnet.scanner.network_scanner import NetworkScanner
from ctrlnet.database.database import db_manager
from ctrlnet.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

app = FastAPI(title="CTRLNET Profiler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static dashboard files
dashboard_path = Path(__file__).parent.parent / "dashboard"
app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")

@app.on_event("startup")
async def startup_event():
    await db_manager.initialize_schema()
    logger.info("CTRLNET Server started.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    event_bus.subscribe(queue)
    
    try:
        while True:
            # Wait for messages from the event bus
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        event_bus.unsubscribe(queue)
        logger.info("WebSocket client disconnected")

@app.post("/api/scan")
async def start_scan(target: str, model: str = None):
    """Trigger a network scan and hybrid analysis."""
    
    async def event_callback(event_name: str, payload: Dict[str, Any]):
        await event_bus.emit(event_name, payload)
        
    scanner = NetworkScanner(event_callback=event_callback)
    
    # Run scan in background task
    asyncio.create_task(scanner.scan_target(target))
    
    return {"status": "Scan initiated", "target": target}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/api/runs")
async def get_runs():
    """List experiment runs."""
    return await db_manager.get_runs()

@app.get("/api/runs/{run_id}")
async def get_run_details(run_id: str):
    """Get run details."""
    run = await db_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.get("/api/results/{run_id}")
async def get_run_results(run_id: str):
    """Get all service results for a run."""
    run = await db_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    results = await db_manager.get_run_results(run_id)
    return {"run": run, "results": results}

@app.get("/api/models")
async def list_models():
    """List available Ollama models."""
    client = OllamaClient()
    models = await client.list_models()
    return {"models": models}

