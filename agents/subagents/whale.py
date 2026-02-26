"""
WhaleBehaviorSubAgent - 资金流分析专家
"""
from .base import BaseSubAgent


class WhaleBehaviorAgent(BaseSubAgent):
    """资金流分析 - 大资金动向"""
    
    def __init__(self, llm=None):
        super().__init__("whale_behavior", llm)
    
    def build_prompt(self, context: dict) -> str:
        return f"""你是资金流专家。分析大资金动向:

股票: {context.get('stock')}

请返回JSON格式:
{{
    "confidence": 0.80,
    "key_findings": ["发现"],
    "structured_data": {{
        "options_flow": "CALLS_HEAVY|PUTS_HEAVY|BALANCED",
        "call_put_ratio": 1.5,
        "whale_signal": "ACCUMULATING|DISTRIBUTING|NEUTRAL"
    }},
    "risk_flags": []
}}"""
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.80,
    "key_findings": ["期权资金流偏看涨", "大单持续流入"],
    "structured_data": {
        "options_flow": "CALLS_HEAVY",
        "call_put_ratio": 1.5,
        "whale_signal": "ACCUMULATING"
    },
    "risk_flags": []
}"""
