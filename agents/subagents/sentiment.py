"""
SentimentSubAgent - 简化版 (跳过 MCP)
"""
from .base import BaseSubAgent


class SentimentAgent(BaseSubAgent):
    """情绪分析 - LLM 分析"""
    
    def __init__(self, llm=None):
        super().__init__("sentiment", llm)
        self.timeout = 15  # 缩短超时
    
    def build_prompt(self, context: dict) -> str:
        financial = context.get("financial_metrics", {})
        stock = context.get("stock", "NVDA")
        
        return f"""你是情绪分析专家。分析 {stock} 的投资者情绪:

财务数据: {financial}

请返回JSON:
{{
    "confidence": 0.75,
    "key_findings": ["发现1", "发现2"],
    "structured_data": {{
        "analyst_sentiment": 0.65,
        "social_sentiment": 0.58,
        "sentiment_velocity": "STABLE"
    }},
    "risk_flags": []
}}"""
    
    def run(self, context: dict) -> dict:
        return super().run(context)
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.75,
    "key_findings": ["情绪偏正面"],
    "structured_data": {
        "analyst_sentiment": 0.65,
        "social_sentiment": 0.58,
        "sentiment_velocity": "STABLE"
    },
    "risk_flags": []
}"""
