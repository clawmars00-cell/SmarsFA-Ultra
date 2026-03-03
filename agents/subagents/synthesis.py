"""
SynthesisSubAgent - 综合合成专家 (增强版)
- 添加未来展望
- 更丰富的财务数据
- 深度分析
"""
from .base import BaseSubAgent


class SynthesisAgent(BaseSubAgent):
    """
    综合合成 - 最终决策
    增强版: 添加未来展望、深度分析
    """
    
    def __init__(self, llm=None):
        super().__init__("synthesis", llm)
    
    def build_prompt(self, context: dict) -> str:
        financial = context.get("financial_metrics", {})
        trend = context.get("trend_signals", {})
        sentiment = context.get("sentiment_data", {})
        whale = context.get("whale_activity", {})
        
        # 提取关键财务指标
        revenue = financial.get('revenue', 0) / 1e9
        eps = financial.get('eps', 0)
        net_income = financial.get('net_income', 0) / 1e9
        profit_margin = financial.get('profit_margin', 0)
        
        return f"""你是综合合成专家。基于以下所有分析生成最终决策:

## 财务数据
- 营收: ${revenue:.1f}B
- EPS: ${eps}
- 净利润: ${net_income:.1f}B
- 利润率: {profit_margin*100:.1f}%

财务: {financial}
趋势: {trend}
情绪: {sentiment}
资金: {whale}

请返回JSON格式 (必须包含future_outlook):
{{
    "confidence": 0.78,
    "key_findings": ["关键发现"],
    "structured_data": {{
        "overall_score": 0.72,
        "recommendation": "BUY|SELL|HOLD",
        "target_price": 250,
        "upside": 0.15,
        "time_horizon": "3M",
        
        "financial_metrics": {{
            "revenue": {revenue*1e9},
            "eps": {eps},
            "net_income": {net_income*1e9},
            "profit_margin": {profit_margin},
            "growth_rate": 0.15,
            "guidance": "positive|negative|neutral"
        }},
        
        "future_outlook": {{
            "next_quarter_outlook": "Positive|Neutral|Negative",
            "catalyst": "催化剂描述",
            "risk_factors": ["风险因素"],
            "price_target_12m": 300,
            "upside_12m": 0.25
        }},
        
        "deep_analysis": {{
            "strengths": ["优势"],
            "weaknesses": ["劣势"],
            "opportunities": ["机会"],
            "threats": ["威胁"]
        }}
    }},
    "reasoning_chain": ["推理步骤"],
    "risk_flags": []
}}"""
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.78,
    "key_findings": [
        "营收超预期5%，显示强劲需求",
        "EPS同比增长12%，盈利能力提升",
        "技术面呈现上升趋势",
        "机构资金净流入",
        "估值合理偏低"
    ],
    "structured_data": {
        "overall_score": 0.72,
        "recommendation": "BUY",
        "target_price": 250,
        "upside": 0.15,
        "time_horizon": "3M",
        
        "financial_metrics": {
            "revenue": 125000000000,
            "eps": 2.10,
            "net_income": 35000000000,
            "profit_margin": 0.28,
            "growth_rate": 0.15,
            "guidance": "positive"
        },
        
        "future_outlook": {
            "next_quarter_outlook": "Positive",
            "catalyst": "新产品发布、季节性需求增长、AI产品线扩张",
            "risk_factors": ["宏观经济不确定性", "竞争加剧", "供应链风险"],
            "price_target_12m": 300,
            "upside_12m": 0.25
        },
        
        "deep_analysis": {
            "strengths": [
                "强大的品牌影响力",
                "稳健的现金流",
                "高利润率",
                "研发投入持续增加"
            ],
            "weaknesses": [
                "对中国市场依赖度较高",
                "成本压力上升"
            ],
            "opportunities": [
                "AI产品线扩张",
                "新兴市场增长",
                "服务业务持续增长"
            ],
            "threats": [
                "监管风险",
                "竞争对手追赶",
                "汇率波动"
            ]
        }
    },
    "reasoning_chain": [
        "1. 财务数据超预期 (+5%)，显示业务韧性",
        "2. 盈利能力提升，EPS同比增长12%",
        "3. 上升趋势确认，技术面有利",
        "4. 资金呈流入，机构看多",
        "5. 估值合理偏低，有上行空间",
        "结论: 建议买入"
    ],
    "risk_flags": [
        "估值略高 (PE 28x)",
        "中国市场政策风险"
    ]
}"""
