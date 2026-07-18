#!/usr/bin/env python3
"""AgentJW API Server - Minimal working version"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import json
from pathlib import Path

sys.path.insert(0, '/home/dibs/agentjw')

app = FastAPI(title="AgentJW API", version="1.0.1")

@app.get("/")
async def root():
    return {"message": "AgentJW API Server", "version": "1.0.1"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Force reload metrics
        import sys
        sys.path.insert(0, '/home/dibs/agentjw')
        
        from sicuan.core.production_metrics import get_production_metrics
        from sicuan.core.ceo_agent import get_ceo_agent
        
        # Get fresh instance
        metrics = get_production_metrics()
        ceo = get_ceo_agent()
        
        data = metrics._data
        health_score = ceo.get_health_score()
        automation_rate = ceo.get_automation_rate()
        
        recovery_rate = (data["recovery"]["recovered"] / max(data["recovery"]["total_crashes"], 1)) * 100
        
        return {
            "status": "healthy",
            "version": "1.0.1",
            "timestamp": "2026-07-17T12:00:00",
            "metrics": {
                "health_score": health_score,
                "automation_rate": automation_rate,
                "workflow_total": data["workflow"]["total"],
                "workflow_success": data["workflow"]["success_rate"],
                "recovery_rate": recovery_rate,
                "mttr": data["recovery"]["mttr"],
                "mtbf": data["recovery"]["mtbf"]
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18791, log_level="info")
