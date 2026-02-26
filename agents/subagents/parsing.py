"""
FinancialParsingSubAgent - 财报解析专家
集成 LLM 分析 + 真实数据获取
"""
from .base import BaseSubAgent
from tools import get_financial_data


class FinancialParsingAgent(BaseSubAgent):
    """财报解析 - LLM 分析 + 真实数据"""
    
    def __init__(self, llm=None):
        super().__init__("financial_parsing", llm)
    
    def build_prompt(self, context: dict) -> str:
        financial = context.get("financial_metrics", {})
        
        return f"""你是财报解析专家。分析以下财务数据，给出结构化评估:

股票: {context.get('stock', 'N/A')}
季度: {context.get('quarter', 'N/A')}

财务指标:
{financial}

请返回JSON格式:
{{
    "confidence": 0.85,
    "key_findings": ["关键发现1", "关键发现2"],
    "structured_data": {{
        "revenue_beat": "BEAT/MISS/INLINE",
        "revenue_beat_percent": 5.2,
        "eps_beat": "BEAT/MISS/INLINE",
        "eps_beat_percent": 8.1,
        "profit_margin": 0.25,
        "yoy_growth": 0.12,
        "source": "yfinance/manual"
    }},
    "risk_flags": []
}}"""
    
    def run(self, context: dict) -> dict:
        """执行分析"""
        import time
        start = time.time()
        
        try:
            stock = context.get("stock", "NVDA")
            
            # 1. 获取真实财务数据
            actual_data = context.get("financial_metrics", {}).get("actual_data")
            
            if actual_data:
                data = actual_data.copy()
                data["source"] = "manual"
                data["revenue_b"] = actual_data.get("revenue", 0) / 1e9
                data["net_income_b"] = actual_data.get("net_income", 0) / 1e9
            else:
                data = get_financial_data(stock)
                data["source"] = "yfinance"
            
            # 2. 构建 LLM prompt
            prompt = self.build_prompt(context)
            
            # 3. 调用 LLM 分析
            llm_result = self.call_llm(prompt)
            analysis = self.parse_response(llm_result)
            
            # 4. 合并结果
            result = {
                "module": "financial_parsing",
                "confidence": analysis.get("confidence", 0.80),
                "key_findings": analysis.get("key_findings", data.get("key_findings", [])),
                "structured_data": {
                    **data,
                    **analysis.get("structured_data", {})
                },
                "risk_flags": analysis.get("risk_flags", []),
                "latency_ms": int((time.time() - start) * 1000),
                "tokens_used": self.estimate_tokens(prompt, llm_result)
            }
            
            return result
            
        except Exception as e:
            return {
                "module": "financial_parsing",
                "confidence": 0.0,
                "error": str(e),
                "structured_data": {},
                "risk_flags": []
            }
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.85,
    "key_findings": ["营收超预期", "EPS beats consensus"],
    "structured_data": {
        "revenue_beat": "BEAT",
        "revenue_beat_percent": 3.2,
        "eps_beat": "BEAT",
        "eps_beat_percent": 5.8,
        "profit_margin": 0.28
    },
    "risk_flags": []
}"""
