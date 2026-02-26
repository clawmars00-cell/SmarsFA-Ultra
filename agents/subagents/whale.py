"""
WhaleBehaviorSubAgent - 资金流分析
"""
from .base import BaseSubAgent
from tools import get_options_data


class WhaleBehaviorAgent(BaseSubAgent):
    """资金流分析"""
    
    def __init__(self, llm=None):
        super().__init__("whale_behavior", llm)
    
    def run(self, context: dict) -> dict:
        """直接使用真实数据"""
        import time
        start = time.time()
        
        try:
            stock = context.get("stock", "NVDA")
            data = get_options_chain(stock)
            
            signal = "ACCUMULATING"
            if data.get("calls_heavy"):
                signal = "ACCUMULATING"
            elif data.get("call_put_ratio", 1) < 1:
                signal = "DISTRIBUTING"
            else:
                signal = "NEUTRAL"
            
            return {
                "module": "whale_behavior",
                "confidence": 0.85,
                "key_findings": [
                    f"Call/Put比率: {data.get('call_put_ratio', 0)}",
                    f"期权流向: {'CALLS_HEAVY' if data.get('calls_heavy') else 'PUTS_HEAVY'}"
                ],
                "structured_data": data,
                "risk_flags": [],
                "latency_ms": int((time.time() - start) * 1000),
                "tokens_used": 0
            }
        except Exception as e:
            return {
                "module": "whale_behavior",
                "confidence": 0.0,
                "error": str(e),
                "structured_data": {},
                "risk_flags": []
            }
