"""
MasterAgent - 完全并行版
"""
import time
import concurrent.futures
from typing import Dict, Any, List
from memory import WorkingMemory
from validator import OutputValidator
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
    完全并行版 MasterAgent
    - Phase 1: Parsing (串行，必须)
    - Phase 2: 所有分析并行 (trend/sentiment/whale/risk)
    - Phase 3: Synthesis (串行)
    """
    
    EXECUTION_ORDER = ["parsing", "trend", "sentiment", "whale", "risk", "synthesis"]
    
    def __init__(self, llm=None):
        self.llm = llm
        self.memory = WorkingMemory()
        self.validator = OutputValidator()
        
        self.subagents = {
            "parsing": FinancialParsingAgent(llm),
            "trend": TrendAnalysisAgent(llm),
            "sentiment": SentimentAgent(llm),
            "whale": WhaleBehaviorAgent(llm),
            "risk": RiskAssessmentAgent(llm),
            "synthesis": SynthesisAgent(llm)
        }
    
    def analyze(self, stock: str, quarter: str = "Q4 2025", 
                raw_text: str = "", actual_data: Dict = None) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. 初始化
        context = self.memory.init(stock, quarter, raw_text)
        context.execution_order = self.EXECUTION_ORDER.copy()
        
        if actual_data:
            context.financial_metrics["actual_data"] = actual_data
        
        print(f"\n{'='*60}")
        print(f"MasterAgent (Parallel) - {stock} {quarter}")
        print(f"{'='*60}")
        
        # 2. Phase 1: Parsing (必须先获取数据)
        print(f"\n[Phase 1] Parsing...")
        self._run_agent("parsing")
        
        # 3. Phase 2: 完全并行 (trend/sentiment/whale/risk)
        print(f"\n[Phase 2] Parallel: trend, sentiment, whale, risk...")
        self._run_parallel(["trend", "sentiment", "whale", "risk"])
        
        # 4. Phase 3: Synthesis
        print(f"\n[Phase 3] Synthesis...")
        synthesis_result = self.subagents["synthesis"].run(self.memory.to_dict())
        
        execution_time = int((time.time() - start_time) * 1000)
        
        print(f"\n{'='*60}")
        print(f"Complete! Time: {execution_time}ms")
        print(f"Recommendation: {synthesis_result.get('structured_data', {}).get('recommendation', 'N/A')}")
        print(f"{'='*60}")
        
        return {
            "stock": stock,
            "quarter": quarter,
            "result": synthesis_result,
            "execution_time_ms": execution_time,
            "memory": self.memory.to_dict()
        }
    
    def _run_agent(self, name: str):
        agent = self.subagents.get(name)
        if not agent:
            return
        
        result = agent.run(self.memory.to_dict())
        
        try:
            validated = self.validator.validate(result)
            warnings = self.validator.get_warnings(validated)
            if warnings:
                for w in warnings:
                    print(f"  ⚠️ {w}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            validated = result
        
        self._update_memory(name, validated)
    
    def _run_parallel(self, names: List[str]):
        def run_and_update(name):
            agent = self.subagents.get(name)
            if not agent:
                return name, None
            result = agent.run(self.memory.to_dict())
            return name, result
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(run_and_update, name): name for name in names}
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    name, result = future.result()
                    if result:
                        validated = self.validator.validate(result)
                        self._update_memory(name, validated)
                        print(f"  ✓ {name} done")
                except Exception as e:
                    print(f"  ❌ {futures[future]}: {e}")
    
    def _update_memory(self, step_name: str, result: Dict):
        data = result.get("structured_data", {})
        
        if step_name == "parsing":
            self.memory.update_financial(data)
        elif step_name == "trend":
            self.memory.update_trend(data)
        elif step_name == "sentiment":
            self.memory.update_sentiment(data)
        elif step_name == "whale":
            self.memory.update_whale(data)
        
        for flag in result.get("risk_flags", []):
            self.memory.add_risk_flag(flag)
