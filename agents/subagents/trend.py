"""
TrendAnalysisSubAgent - 趋势分析专家
"""
from .base import BaseSubAgent


class TrendAnalysisAgent(BaseSubAgent):
    """趋势分析 - 分析历史趋势"""
    
    def __init__(self, llm=None):
        super().__init__("trend_analysis", llm)
    
    def build_prompt(self, context: dict) -> str:
        financial = context.get("financial_metrics", {})
        
        return f"""你是趋势分析专家。基于以下财务数据分析趋势:

财务指标:
{financial}

请返回JSON格式:
{{
    "confidence": 0.82,
    "key_findings": ["发现"],
    "structured_data": {{
        "revenue_trend": "UPWARD|DOWNWARD|STABLE",
        "eps_trend": "UPWARD|DOWNWARD|STABLE",
        "momentum_score": 0.75
    }},
    "risk_flags": []
}}"""
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.82,
    "key_findings": ["Revenue连续增长", "上升趋势确认"],
    "structured_data": {
        "revenue_trend": "UPWARD",
        "eps_trend": "UPWARD",
        "momentum_score": 0.75
    },
    "risk_flags": []
}"""
