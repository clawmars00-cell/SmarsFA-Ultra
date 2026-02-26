"""
SmarsFA-Ultra - Main API Server
工程可落地版本
"""
import os
import sys

# 添加当前目录到path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# 导入模块
from agents.master_agent import MasterAgent
from controller import Scheduler, ResultStorage

app = FastAPI(title="SmarsFA-Ultra", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局实例
master_agent = MasterAgent()
scheduler = Scheduler()
scheduler.set_agent(master_agent)
scheduler.set_persister(ResultStorage("./storage"))


class AnalyzeRequest(BaseModel):
    stock: str
    quarter: Optional[str] = "Q4 2025"
    raw_text: Optional[str] = ""


@app.get("/")
def root():
    return {
        "message": "SmarsFA-Ultra - Engineering Version",
        "architecture": "SubAgent Cognitive"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "architecture": "SubAgent",
        "execution_order": MasterAgent.EXECUTION_ORDER
    }


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """分析股票"""
    try:
        result = master_agent.analyze(
            request.stock.upper(),
            request.quarter,
            request.raw_text
        )
        
        # 存储
        scheduler.persister.save(request.stock.upper(), request.quarter, result)
        
        return {
            "status": "success",
            "stock": request.stock.upper(),
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
def get_history(stock: Optional[str] = None):
    """获取历史"""
    results = scheduler.persister.get_all(stock)
    return {"count": len(results), "results": results}


@app.get("/api/agents/status")
def agents_status():
    """Agent状态"""
    return {
        "execution_order": MasterAgent.EXECUTION_ORDER,
        "subagents": list(master_agent.subagents.keys())
    }


if __name__ == "__main__":
    print("=" * 60)
    print("SmarsFA-Ultra - Engineering Version")
    print("Architecture: SubAgent Cognitive")
    print("Execution Order:", MasterAgent.EXECUTION_ORDER)
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=9000)
