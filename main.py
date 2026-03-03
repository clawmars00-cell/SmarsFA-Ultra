"""
SmarsFA-Ultra - Main API Server
工程可落地版本 - 支持WhatsApp消息处理
"""
import os
import sys

# 添加当前目录到path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# 导入模块
from agents.master_agent import MasterAgent
from controller import Scheduler, ResultStorage
from watchlist_manager import WatchlistManager

# 全局实例
watchlist_manager = WatchlistManager()

app = FastAPI(title="SmarsFA-Ultra", version="1.1.0")

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

# WhatsApp handler lazy import
WhatsAppHandler = None

def get_whatsapp_handler():
    global WhatsAppHandler
    if WhatsAppHandler is None:
        from whatsapp_handler import WhatsAppHandler as _WH
        WhatsAppHandler = _WH
    return WhatsAppHandler()
    stock: str
    quarter: Optional[str] = "Q4 2025"
    raw_text: Optional[str] = ""
    actual_revenue: Optional[float] = None  # 实际营收(手动输入)
    actual_eps: Optional[float] = None      # 实际EPS(手动输入)
    actual_net_income: Optional[float] = None  # 实际净利润


class WhatsAppMessage(BaseModel):
    message: str
    sender: Optional[str] = "unknown"


@app.get("/")
def root():
    return {
        "message": "SmarsFA-Ultra - Engineering Version",
        "architecture": "SubAgent Cognitive",
        "whatsapp": "enabled"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "1.1.0",
        "architecture": "SubAgent",
        "execution_order": MasterAgent.EXECUTION_ORDER,
        "whatsapp_commands": ["添加", "删除", "列表", "分析", "日历", "大盘", "帮助"]
    }


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """分析股票"""
    try:
        # 构建实际数据
        actual_data = None
        if request.actual_revenue or request.actual_eps:
            actual_data = {
                "revenue": request.actual_revenue * 1e9 if request.actual_revenue else 0,
                "eps": request.actual_eps,
                "net_income": request.actual_net_income * 1e9 if request.actual_net_income else 0,
            }
        
        result = master_agent.analyze(
            request.stock.upper(),
            request.quarter,
            request.raw_text,
            actual_data
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


# ========== WhatsApp API ==========

@app.post("/api/whatsapp")
async def whatsapp_message(msg: WhatsAppMessage):
    """处理WhatsApp消息"""
    try:
        handler = get_whatsapp_handler()
        responses = handler.handle_message(msg.message, msg.sender or "unknown")
        
        return {
            "status": "success",
            "responses": responses,
            "count": len(responses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/watchlist")
def get_watchlist():
    """获取自选股列表"""
    watchlist = watchlist_manager.get_all()
    return {
        "count": len(watchlist),
        "watchlist": watchlist
    }


@app.post("/api/watchlist/add")
def add_to_watchlist(stock: str, note: str = ""):
    """添加自选股"""
    success = watchlist_manager.add(stock, note)
    return {
        "status": "success" if success else "exists",
        "stock": stock.upper()
    }


@app.delete("/api/watchlist/{stock}")
def remove_from_watchlist(stock: str):
    """删除自选股"""
    success = watchlist_manager.remove(stock)
    return {
        "status": "success" if success else "not_found",
        "stock": stock.upper()
    }


@app.post("/api/watchlist/analyze")
def analyze_watchlist():
    """分析所有自选股"""
    stocks = watchlist_manager.list_stocks()
    if not stocks:
        return {"status": "empty", "message": "自选股列表为空"}
    
    # 并行分析
    results = {}
    for stock in stocks:
        try:
            result = master_agent.analyze(
                stock=stock,
                quarter="Q4 2025",
                actual_data={"revenue": 50e9, "eps": 1.0}
            )
            results[stock] = result
            watchlist_manager.update_analysis(stock)
        except Exception as e:
            results[stock] = {"error": str(e)}
    
    return {
        "status": "success",
        "analyzed": len(results),
        "results": results
    }


@app.get("/api/report/formatted")
def get_formatted_report(stock: str = None):
    """获取格式化报告"""
    from whatsapp_formatter import WhatsAppFormatter
    from main import master_agent
    
    formatter = WhatsAppFormatter()
    
    if stock:
        # 单只股票
        result = master_agent.analyze(stock, "Q4 2025")
        report = formatter.format_single_stock(result)
        return {"stock": stock, "report": report}
    else:
        # 自选股汇总
        watchlist = watchlist_manager.list_stocks()
        # 分析自选
        results = {}
        for s in watchlist:
            try:
                results[s] = master_agent.analyze(s, "Q4 2025")
            except:
                pass
        
        return formatter.format_watchlist_report(watchlist, results)


if __name__ == "__main__":
    print("=" * 60)
    print("SmarsFA-Ultra - Engineering Version v1.1.0")
    print("Architecture: SubAgent Cognitive")
    print("WhatsApp Commands: 添加/删除/列表/分析/日历/大盘")
    print("Execution Order:", MasterAgent.EXECUTION_ORDER)
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=9000)
