"""
SmarsFA-Ultra - Master Agent
认知协调器 - SubAgent架构
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class AgentContext:
    """工作上下文"""
    stock: str
    quarter: str
    raw_text: str = ""
    financial_data: Dict = None
    trend_analysis: Dict = None
    sentiment: Dict = None
    whale_signals: Dict = None
    risk_assessment: Dict = None
    
    def __post_init__(self):
        if self.financial_data is None:
            self.financial_data = {}
        if self.trend_analysis is None:
            self.trend_analysis = {}
        if self.sentiment is None:
            self.sentiment = {}
        if self.whale_signals is None:
            self.whale_signals = {}
        if self.risk_assessment is None:
            self.risk_assessment = {}


class MasterAgent:
    """
    EarningsMasterAgent
    协调多个SubAgent完成财报分析
    """
    
    def __init__(self):
        self.name = "EarningsMasterAgent"
        self.version = "1.0"
        self.subagents = [
            "FinancialParsingSubAgent",
            "TrendAnalysisSubAgent", 
            "SentimentSubAgent",
            "WhaleBehaviorSubAgent",
            "RiskAssessmentSubAgent",
            "SynthesisSubAgent"
        ]
    
    async def analyze(self, stock: str, quarter: str = "Q4 2025", raw_text: str = "") -> Dict:
        """执行完整分析"""
        print(f"\n{'='*60}")
        print(f"EarningsMasterAgent - Analyzing {stock} {quarter}")
        print(f"{'='*60}")
        
        # 初始化上下文
        context = AgentContext(
            stock=stock,
            quarter=quarter,
            raw_text=raw_text
        )
        
        # Step 1: FinancialParsing
        print("\n[1/6] FinancialParsingSubAgent...")
        result = await self._call_subagent("FinancialParsingSubAgent", context)
        context.financial_data = result.get("structured_data", {})
        self._validate(result)
        
        # Step 2: TrendAnalysis
        print("[2/6] TrendAnalysisSubAgent...")
        result = await self._call_subagent("TrendAnalysisSubAgent", context)
        context.trend_analysis = result.get("structured_data", {})
        self._validate(result)
        
        # Step 3: Sentiment
        print("[3/6] SentimentSubAgent...")
        result = await self._call_subagent("SentimentSubAgent", context)
        context.sentiment = result.get("structured_data", {})
        self._validate(result)
        
        # Step 4: WhaleBehavior
        print("[4/6] WhaleBehaviorSubAgent...")
        result = await self._call_subagent("WhaleBehaviorSubAgent", context)
        context.whale_signals = result.get("structured_data", {})
        self._validate(result)
        
        # Step 5: RiskAssessment
        print("[5/6] RiskAssessmentSubAgent...")
        result = await self._call_subagent("RiskAssessmentSubAgent", context)
        context.risk_assessment = result.get("structured_data", {})
        self._validate(result)
        
        # Step 6: Synthesis
        print("[6/6] SynthesisSubAgent...")
        final_result = await self._call_subagent("SynthesisSubAgent", context)
        
        # 添加元数据
        final_result["stock"] = stock
        final_result["quarter"] = quarter
        final_result["subagents_executed"] = len(self.subagents)
        
        print(f"\n{'='*60}")
        print(f"Analysis Complete!")
        print(f"Recommendation: {final_result.get('structured_data', {}).get('recommendation')}")
        print(f"Confidence: {final_result.get('confidence')}")
        print(f"{'='*60}")
        
        return final_result
    
    async def _call_subagent(self, agent_name: str, context: AgentContext) -> Dict:
        """调用SubAgent"""
        
        if agent_name == "FinancialParsingSubAgent":
            return self._mock_financial_parsing(context)
        elif agent_name == "TrendAnalysisSubAgent":
            return self._mock_trend_analysis(context)
        elif agent_name == "SentimentSubAgent":
            return self._mock_sentiment(context)
        elif agent_name == "WhaleBehaviorSubAgent":
            return self._mock_whale_behavior(context)
        elif agent_name == "RiskAssessmentSubAgent":
            return self._mock_risk_assessment(context)
        elif agent_name == "SynthesisSubAgent":
            return self._mock_synthesis(context)
        
        return {"error": "Unknown agent"}
    
    def _validate(self, result: Dict):
        """验证输出"""
        confidence = result.get("confidence", 0)
        if confidence < 0.6:
            print(f"  ⚠️ Low confidence: {confidence}")
        
        if result.get("risk_flags"):
            print(f"  ⚠️ Risk flags: {result['risk_flags']}")
    
    # Mock Implementations
    def _mock_financial_parsing(self, context: AgentContext) -> Dict:
        return {
            "module": "financial_parsing",
            "version": "1.0",
            "confidence": 0.85,
            "key_findings": [f"{context.stock} Revenue beat expectations"],
            "structured_data": {
                "revenue": 25000000000,
                "revenue_growth_yoy": 0.12,
                "eps": 0.85,
                "eps_beat_percent": 0.05,
                "gross_margin": 0.25,
                "guidance": "positive"
            },
            "risk_flags": []
        }
    
    def _mock_trend_analysis(self, context: AgentContext) -> Dict:
        return {
            "module": "trend_analysis",
            "version": "1.0", 
            "confidence": 0.82,
            "key_findings": ["Revenue连续增长"],
            "structured_data": {
                "revenue_trend": "UPWARD",
                "eps_trend": "UPWARD",
                "momentum_score": 0.75
            },
            "risk_flags": []
        }
    
    def _mock_sentiment(self, context: AgentContext) -> Dict:
        return {
            "module": "sentiment",
            "version": "1.0",
            "confidence": 0.78,
            "key_findings": ["分析师看多"],
            "structured_data": {
                "analyst_sentiment": 0.65,
                "social_sentiment": 0.58,
                "sentiment_velocity": "INCREASING"
            },
            "risk_flags": []
        }
    
    def _mock_whale_behavior(self, context: AgentContext) -> Dict:
        return {
            "module": "whale_behavior",
            "version": "1.0",
            "confidence": 0.80,
            "key_findings": ["资金呈流入"],
            "structured_data": {
                "options_flow": "CALLS_HEAVY",
                "call_put_ratio": 1.5,
                "whale_signal": "ACCUMULATING"
            },
            "risk_flags": []
        }
    
    def _mock_risk_assessment(self, context: AgentContext) -> Dict:
        return {
            "module": "risk_assessment",
            "version": "1.0",
            "confidence": 0.85,
            "key_findings": ["风险中等"],
            "structured_data": {
                "overall_risk": 0.55,
                "risk_level": "MEDIUM",
                "volatility_risk": 0.60,
                "valuation_risk": 0.50
            },
            "risk_flags": []
        }
    
    def _mock_synthesis(self, context: AgentContext) -> Dict:
        return {
            "module": "synthesis",
            "version": "1.0",
            "confidence": 0.78,
            "key_findings": ["综合看多"],
            "structured_data": {
                "overall_score": 0.72,
                "recommendation": "BUY",
                "target_price": 250,
                "upside": 0.15,
                "time_horizon": "3M"
            },
            "reasoning_chain": [
                "1. 财务数据超预期",
                "2. 上升趋势确认",
                "3. 资金呈流入",
                "4. 风险中等可控",
                "结论: 建议买入"
            ],
            "risk_flags": ["估值略高"]
        }


async def analyze(stock: str, quarter: str = "Q4 2025", raw_text: str = "") -> Dict:
    """便捷函数"""
    agent = MasterAgent()
    return await agent.analyze(stock, quarter, raw_text)
