"""
SentimentSubAgent - 情绪分析专家
"""
from .base import BaseSubAgent


class SentimentAgent(BaseSubAgent):
    """情绪分析 - 市场情绪"""
    
    def __init__(self, llm=None):
        super().__init__("sentiment", llm)
    
    def build_prompt(self, context: dict) -> str:
        return f"""你是情绪分析专家。分析市场情绪:

上下文: {context.get('stock')}

请返回JSON格式:
{{
    "confidence": 0.78,
    "key_findings": ["发现"],
    "structured_data": {{
        "analyst_sentiment": 0.65,
        "social_sentiment": 0.58,
        "sentiment_velocity": "INCREASING|DECREASING|STABLE"
    }},
    "risk_flags": []
}}"""
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.78,
    "key_findings": ["分析师整体偏多", "社交媒体情绪正面"],
    "structured_data": {
        "analyst_sentiment": 0.65,
        "social_sentiment": 0.58,
        "sentiment_velocity": "INCREASING"
    },
    "risk_flags": []
}"""
