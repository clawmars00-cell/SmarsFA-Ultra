"""
RiskAssessmentSubAgent - 风险评估专家
"""
from .base import BaseSubAgent


class RiskAssessmentAgent(BaseSubAgent):
    """风险评估 - 综合风险"""
    
    def __init__(self, llm=None):
        super().__init__("risk_assessment", llm)
    
    def build_prompt(self, context: dict) -> str:
        financial = context.get("financial_metrics", {})
        
        return f"""你是风险评估专家。评估投资风险:

财务数据: {financial}

请返回JSON格式:
{{
    "confidence": 0.85,
    "key_findings": ["发现"],
    "structured_data": {{
        "overall_risk": 0.55,
        "risk_level": "LOW|MEDIUM|HIGH",
        "volatility_risk": 0.60,
        "valuation_risk": 0.50
    }},
    "risk_flags": []
}}"""
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.85,
    "key_findings": ["风险中等"],
    "structured_data": {
        "overall_risk": 0.55,
        "risk_level": "MEDIUM",
        "volatility_risk": 0.60,
        "valuation_risk": 0.50
    },
    "risk_flags": []
}"""
