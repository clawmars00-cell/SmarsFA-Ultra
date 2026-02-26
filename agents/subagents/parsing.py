"""
FinancialParsingSubAgent - 支持手动输入实际财报数据
"""
from .base import BaseSubAgent
from tools import get_financial_data


class FinancialParsingAgent(BaseSubAgent):
    """财报解析 - 支持实际数据输入"""
    
    def __init__(self, llm=None):
        super().__init__("financial_parsing", llm)
    
    def run(self, context: dict) -> dict:
        """执行分析"""
        import time
        start = time.time()
        
        try:
            stock = context.get("stock", "NVDA")
            
            # 检查是否有手动输入的实际数据
            actual_data = context.get("financial_metrics", {}).get("actual_data")
            
            if actual_data:
                # 使用手动输入的实际数据
                data = actual_data
                data["source"] = "manual"
                data["revenue_b"] = actual_data.get("revenue", 0) / 1e9
                data["net_income_b"] = actual_data.get("net_income", 0) / 1e9
            else:
                # 使用yfinance数据
                data = get_financial_data(stock)
                data["source"] = "yfinance"
            
            # 计算beat百分比 (假设预期EPS=0.85)
            expected_eps = 0.85
            actual_eps = data.get("eps", 0)
            beat_percent = ((actual_eps - expected_eps) / expected_eps) * 100 if expected_eps else 0
            
            return {
                "module": "financial_parsing",
                "confidence": 0.90,
                "key_findings": [
                    f"营收: ${data.get('revenue_b', 0):.2f}B",
                    f"净利润: ${data.get('net_income_b', 0):.2f}B",
                    f"EPS: ${actual_eps:.2f} (beat: {beat_percent:+.1f}%)"
                ],
                "structured_data": data,
                "beat_percent": beat_percent,
                "risk_flags": [],
                "latency_ms": int((time.time() - start) * 1000),
                "tokens_used": 0
            }
        except Exception as e:
            return {
                "module": "financial_parsing",
                "confidence": 0.0,
                "error": str(e),
                "structured_data": {},
                "risk_flags": []
            }
