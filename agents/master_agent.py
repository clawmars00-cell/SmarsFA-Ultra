"""
MasterAgent - 认知协调器 (消息总线版)
基于 Message Bus 的 SubAgent 协作
"""
import time
from typing import Dict, Any, List
from memory import WorkingMemory
from validator import OutputValidator
from schemas import SubAgentOutput, SynthesisOutput
from message_bus import MessageBus, Message, MessageType
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
    EarningsMasterAgent - 基于消息总线的协调器
    - SubAgent 通过 Message Bus 通信
    - 支持异步执行
    - 支持外部 Controller 集成
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
    
    def __init__(self, llm=None, message_bus: MessageBus = None):
        self.llm = llm
        self.memory = WorkingMemory()
        self.validator = OutputValidator()
        self.message_bus = message_bus or MessageBus()
        
        # 初始化SubAgents
        self.subagents = {
            "parsing": FinancialParsingAgent(llm),
            "trend": TrendAnalysisAgent(llm),
            "sentiment": SentimentAgent(llm),
            "whale": WhaleBehaviorAgent(llm),
            "risk": RiskAssessmentAgent(llm),
            "synthesis": SynthesisAgent(llm)
        }
        
        # 订阅自己的消息
        self.message_bus.subscribe("MasterAgent", self._handle_message)
    
    async def _handle_message(self, message: Message):
        """处理收到的消息"""
        print(f"[MasterAgent] Received: {message.msg_type.value} from {message.from_agent}")
    
    async def analyze_async(self, stock: str, quarter: str = "Q4 2025", 
                          raw_text: str = "", actual_data: Dict = None) -> Dict[str, Any]:
        """异步执行完整分析"""
        start_time = time.time()
        
        # 1. 初始化上下文
        context = self.memory.init(stock, quarter, raw_text)
        context.execution_order = self.EXECUTION_ORDER.copy()
        
        if actual_data:
            context.financial_metrics["actual_data"] = actual_data
        
        print(f"\n{'='*60}")
        print(f"MasterAgent (MessageBus) - Analyzing {stock} {quarter}")
        print(f"{'='*60}")
        
        # 2. 通过消息总线依次调度 SubAgents
        for step_name in self.EXECUTION_ORDER:
            print(f"\n[{self.EXECUTION_ORDER.index(step_name)+1}/6] {step_name.capitalize()}...")
            
            # 通过消息总线发送请求
            request_msg = Message(
                msg_type=MessageType.AGENT_REQUEST,
                from_agent="MasterAgent",
                to_agent=step_name,
                payload=self.memory.to_dict()
            )
            await self.message_bus.publish(request_msg)
            
            # 获取 SubAgent 响应
            agent = self.subagents.get(step_name)
            if agent:
                # 直接调用执行 (也可以改为等待消息)
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
                
                # 更新 Memory
                self._update_memory(step_name, validated)
                
                # 通过消息总线发送响应
                response_msg = Message(
                    msg_type=MessageType.AGENT_RESPONSE,
                    from_agent=step_name,
                    to_agent="MasterAgent",
                    payload=result,
                    correlation_id=request_msg.id
                )
                await self.message_bus.publish(response_msg)
        
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
    
    def analyze(self, stock: str, quarter: str = "Q4 2025", 
                raw_text: str = "", actual_data: Dict = None) -> Dict[str, Any]:
        """同步版本 (兼容现有 API)"""
        return {
            "stock": stock,
            "quarter": quarter,
            "result": self._analyze_sync(stock, quarter, raw_text, actual_data),
            "execution_time_ms": 0,
            "memory": {}
        }
    
    def _analyze_sync(self, stock: str, quarter: str, raw_text: str, actual_data: Dict) -> Dict:
        """同步分析 (保持原有逻辑)"""
        start_time = time.time()
        
        context = self.memory.init(stock, quarter, raw_text)
        context.execution_order = self.EXECUTION_ORDER.copy()
        
        if actual_data:
            context.financial_metrics["actual_data"] = actual_data
        
        print(f"\n{'='*60}")
        print(f"MasterAgent - Analyzing {stock} {quarter}")
        print(f"{'='*60}")
        
        for step_name in self.EXECUTION_ORDER:
            print(f"\n[{self.EXECUTION_ORDER.index(step_name)+1}/6] {step_name.capitalize()}...")
            
            agent = self.subagents.get(step_name)
            if not agent:
                continue
            
            result = agent.run(self.memory.to_dict())
            
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
            
            self._update_memory(step_name, validated)
            
            if validated.get("confidence", 0) < 0.6:
                print(f"  ⚠️ Low confidence: {validated.get("confidence", 0)}")
        
        synthesis_result = self.subagents["synthesis"].run(self.memory.to_dict())
        
        execution_time = int((time.time() - start_time) * 1000)
        
        print(f"\n{'='*60}")
        print(f"Complete! Time: {execution_time}ms")
        print(f"Recommendation: {synthesis_result.get('structured_data', {}).get('recommendation', 'N/A')}")
        print(f"{'='*60}")
        
        return synthesis_result
    
    def _update_memory(self, step_name: str, result: Dict):
        """根据步骤更新Memory"""
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
