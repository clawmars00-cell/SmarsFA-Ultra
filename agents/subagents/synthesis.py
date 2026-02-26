"""
SynthesisSubAgent - 综合合成专家
"""
from .base import BaseSubAgent


class SynthesisAgent(BaseSubAgent):
    """综合合成 - 最终决策"""
    
    def __init__(self, llm=None):
        super().__init__("synthesis", llm)
    
    def build_prompt(self, context: dict) -> str:
        financial = context.get("financial_metrics", {})
        trend = context.get("trend_signals", {})
        sentiment = context.get("sentiment_data", {})
        whale = context.get("whale_activity", {})
        
        return f"""你是综合合成专家。基于以下所有分析生成最终决策:

财务: {financial}
趋势: {trend}
情绪: {sentiment}
资金: {whale}

请返回JSON格式:
{{
    "confidence": 0.78,
    "key_findings": ["关键发现"],
    "structured_data": {{
        "overall_score": 0.72,
        "recommendation": "BUY|SELL|HOLD",
        "target_price": 250,
        "upside": 0.15,
        "time_horizon": "3M"
    }},
    "reasoning_chain": ["推理步骤"],
    "risk_flags": []
}}"""
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.78,
    "key_findings": ["综合看多", "财务超预期"],
    "structured_data": {
        "overall_score": 0.72,
        "recommendation": "BUY",
        "target_price": 250,
        "upside": 0.15,
        "time_horizon": "3M"
    },
    "reasoning_chain": [
        "1. 财务数据超预期 (+5%)",
        "2. 上升趋势确认",
        "3. 资金呈流入",
        "4. 风险中等可控",
        "结论: 建议买入"
    ],
    "risk_flags": ["估值略高"]
}"""
