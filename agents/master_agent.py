"""
MasterAgent - 认知协调器
"""
import time
from typing import Dict, Any, List
from memory import WorkingMemory
from validator import OutputValidator
from schemas import SubAgentOutput, SynthesisOutput
from agents.subagents import (
    FinancialParsingAgent,
    TrendAnalysisAgent,
    SentimentAgent,
    WhaleBehaviorAgent,
    RiskAssessmentAgent,
    SynthesisAgent
)


class MasterAgent:
    """
    EarningsMasterAgent - 协调多个SubAgent
    - 固定执行顺序
    - 固定执行图
    - 不让LLM决定顺序
    """
    
    # 固定执行顺序
    EXECUTION_ORDER = [
        "parsing",
        "trend", 
        "sentiment",
        "whale",
        "risk",
        "synthesis"
    ]
    
    def __init__(self, llm=None):
        self.llm = llm
        self.memory = WorkingMemory()
        self.validator = OutputValidator()
        
        # 初始化SubAgents
        self.subagents = {
            "parsing": FinancialParsingAgent(llm),
            "trend": TrendAnalysisAgent(llm),
            "sentiment": SentimentAgent(llm),
            "whale": WhaleBehaviorAgent(llm),
            "risk": RiskAssessmentAgent(llm),
            "synthesis": SynthesisAgent(llm)
        }
    
    def analyze(self, stock: str, quarter: str = "Q4 2025", raw_text: str = "") -> Dict[str, Any]:
        """
        执行完整分析
        固定顺序: parsing → trend → sentiment → whale → risk → synthesis
        """
        start_time = time.time()
        
        # 1. 初始化上下文
        context = self.memory.init(stock, quarter, raw_text)
        context.execution_order = self.EXECUTION_ORDER.copy()
        
        print(f"\n{'='*60}")
        print(f"MasterAgent - Analyzing {stock} {quarter}")
        print(f"{'='*60}")
        
        # 2. 依次执行SubAgents
        for step_name in self.EXECUTION_ORDER:
            print(f"\n[{self.EXECUTION_ORDER.index(step_name)+1}/6] {step_name.capitalize()}...")
            
            # 获取对应SubAgent
            agent = self.subagents.get(step_name)
            if not agent:
                continue
            
            # 执行
            result = agent.run(self.memory.to_dict())
            
            # 校验
            try:
                validated = self.validator.validate(result)
                warnings = self.validator.get_warnings(result)
                
                if warnings:
                    for w in warnings:
                        print(f"  ⚠️ {w}")
                        
            except Exception as e:
                print(f"  ❌ Validation error: {e}")
                self.memory.add_error(str(e))
                continue
            
            # 更新Memory
            self._update_memory(step_name, validated)
            
            # 检查置信度
            if validated.confidence < 0.6:
                print(f"  ⚠️ Low confidence: {validated.confidence}")
        
        # 3. 获取最终结果
        synthesis_result = self.subagents["synthesis"].run(self.memory.to_dict())
        
        execution_time = int((time.time() - start_time) * 1000)
        
        print(f"\n{'='*60}")
        print(f"Complete! Time: {execution_time}ms")
        print(f"Recommendation: {synthesis_result.get('structured_data', {}).get('recommendation', 'N/A')}")
        print(f"Confidence: {synthesis_result.get('confidence', 0)}")
        print(f"{'='*60}")
        
        return {
            "stock": stock,
            "quarter": quarter,
            "result": synthesis_result,
            "execution_time_ms": execution_time,
            "memory": self.memory.to_dict()
        }
    
    def _update_memory(self, step_name: str, result: SubAgentOutput):
        """根据步骤更新Memory"""
        data = result.structured_data
        
        if step_name == "parsing":
            self.memory.update_financial(data)
        elif step_name == "trend":
            self.memory.update_trend(data)
        elif step_name == "sentiment":
            self.memory.update_sentiment(data)
        elif step_name == "whale":
            self.memory.update_whale(data)
        
        # 风险标记
        for flag in result.risk_flags:
            self.memory.add_risk_flag(flag)
