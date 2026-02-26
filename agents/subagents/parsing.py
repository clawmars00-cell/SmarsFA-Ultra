"""
FinancialParsingSubAgent - 完整财务数据版
"""
from .base import BaseSubAgent
from tools import get_financial_data


class FinancialParsingAgent(BaseSubAgent):
    """财报解析 - 完整财务指标"""
    
    def __init__(self, llm=None):
        super().__init__("financial_parsing", llm)
    
    def build_prompt(self, context: dict) -> str:
        stock = context.get("stock", "")
        
        # 直接调用真实工具获取数据
        data = get_financial_data(stock)
        
        return f"""分析{stock}财务数据:

营收: ${data.get('revenue_b', 0):.2f}B
净利润: ${data.get('net_income_b', 0):.2f}B
毛利率: {data.get('gross_margin', 0)*100:.1f}%
营业利润率: {data.get('operating_margin', 0)*100:.1f}%
净利率: {data.get('net_margin', 0)*100:.1f}%
EPS历史: {data.get('eps_history', [])}

市值: ${data.get('market_cap_t', 0):.2f}T
PE: {data.get('pe_ratio', 0)}
股价: ${data.get('price', 0)}

返回JSON:
{{
    "confidence": 0.90,
    "key_findings": [],
    "structured_data": {{
        "revenue": {data.get('revenue', 0)},
        "revenue_b": {data.get('revenue_b', 0)},
        "net_income": {data.get('net_income', 0)},
        "net_income_b": {data.get('net_income_b', 0)},
        "gross_margin": {data.get('gross_margin', 0)},
        "operating_margin": {data.get('operating_margin', 0)},
        "net_margin": {data.get('net_margin', 0)},
        "eps": {data.get('eps_history', [{}])[0].get('eps', 0) if data.get('eps_history') else 0},
        "pe_ratio": {data.get('pe_ratio', 0)},
        "guidance": "positive"
    }},
    "risk_flags": []
}}"""
    
    def run(self, context: dict) -> dict:
        """Override to use real data"""
        import time
        start = time.time()
        
        try:
            stock = context.get("stock", "NVDA")
            data = get_financial_data(stock)
            
            return {
                "module": "financial_parsing",
                "confidence": 0.90,
                "key_findings": [
                    f"营收: ${data.get('revenue_b', 0):.2f}B",
                    f"净利润: ${data.get('net_income_b', 0):.2f}B",
                    f"毛利率: {data.get('gross_margin', 0)*100:.1f}%"
                ],
                "structured_data": data,
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
