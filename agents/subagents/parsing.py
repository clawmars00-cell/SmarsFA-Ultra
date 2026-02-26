"""
FinancialParsingSubAgent - 财报解析专家 (真实数据版)
"""
from .base import BaseSubAgent
from tools import get_stock_data, get_earnings_data


class FinancialParsingAgent(BaseSubAgent):
    """财报解析 - 提取关键财务数据"""
    
    def __init__(self, llm=None):
        super().__init__("financial_parsing", llm)
    
    def build_prompt(self, context: dict) -> str:
        stock = context.get("stock", "")
        raw_text = context.get("raw_text", "")[:5000]
        
        # 获取真实数据
        stock_data = get_stock_data(stock)
        earnings_data = get_earnings_data(stock)
        
        return f"""你是财务解析专家。从以下{stock}的财报数据中提取关键指标:

股票数据:
{stock_data}

财报历史:
{earnings_data}

原始财报文本:
{raw_text or '无原文'}

请返回JSON格式:
{{
    "confidence": 0.85,
    "key_findings": ["发现1", "发现2"],
    "structured_data": {{
        "revenue": 金额,
        "revenue_growth_yoy": 0.0,
        "eps": 0.0,
        "eps_beat_percent": 0.0,
        "gross_margin": 0.0,
        "guidance": "positive|negative|neutral"
    }},
    "risk_flags": []
}}"""
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.85,
    "key_findings": ["Revenue beat expectations", "EPS above consensus"],
    "structured_data": {
        "revenue": 25000000000,
        "revenue_growth_yoy": 0.12,
        "eps": 0.85,
        "eps_beat_percent": 0.05,
        "gross_margin": 0.25,
        "guidance": "positive"
    },
    "risk_flags": []
}"""
