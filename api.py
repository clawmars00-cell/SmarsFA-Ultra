"""
SmarsFA-Ultra API Server
FastAPI - SubAgent Cognitive Architecture
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="SmarsFA-Ultra", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    stock: str
    quarter: Optional[str] = "Q4 2025"
    raw_text: Optional[str] = ""


@app.get("/")
def root():
    return {"message": "SmarsFA-Ultra - SubAgent Cognitive Architecture"}


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0", "architecture": "SubAgent"}


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """分析股票"""
    try:
        from agents.master import MasterAgent
        
        agent = MasterAgent()
        result = await agent.analyze(request.stock, request.quarter, request.raw_text)
        
        return {
            "status": "success",
            "stock": request.stock,
            "quarter": request.quarter,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/status")
def agents_status():
    """Agent状态"""
    from agents.master import MasterAgent
    agent = MasterAgent()
    return {
        "agents": agent.subagents,
        "count": len(agent.subagents)
    }


if __name__ == "__main__":
    print("=" * 50)
    print("SmarsFA-Ultra API Server")
    print("Architecture: SubAgent Cognitive")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=9000)
