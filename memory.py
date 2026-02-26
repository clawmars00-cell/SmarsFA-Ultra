"""
Memory - Working Memory 管理
"""
from typing import Dict, Any, Optional
from schemas import AgentContext


class WorkingMemory:
    """
    Working Memory - 结构化共享内存
    每个SubAgent只能操作自己的namespace
    """
    
    def __init__(self):
        self.context: Optional[AgentContext] = None
    
    def init(self, stock: str, quarter: str, raw_text: str = "") -> AgentContext:
        """初始化上下文"""
        self.context = AgentContext(
            stock=stock,
            quarter=quarter,
            raw_text=raw_text
        )
        return self.context
    
    def get(self) -> AgentContext:
        """获取当前上下文"""
        return self.context
    
    def update_financial(self, data: Dict[str, Any]):
        """更新财务数据"""
        if self.context:
            self.context.financial_metrics.update(data)
    
    def update_trend(self, data: Dict[str, Any]):
        """更新趋势数据"""
        if self.context:
            self.context.trend_signals.update(data)
    
    def update_sentiment(self, data: Dict[str, Any]):
        """更新情绪数据"""
        if self.context:
            self.context.sentiment_data.update(data)
    
    def update_whale(self, data: Dict[str, Any]):
        """更新资金流数据"""
        if self.context:
            self.context.whale_activity.update(data)
    
    def add_risk_flag(self, flag: str):
        """添加风险标记"""
        if self.context and flag not in self.context.risk_flags:
            self.context.risk_flags.append(flag)
    
    def add_error(self, error: str):
        """添加错误"""
        if self.context:
            self.context.errors.append(error)
    
    def get_financial(self) -> Dict[str, Any]:
        """获取财务数据"""
        return self.context.financial_metrics if self.context else {}
    
    def get_trend(self) -> Dict[str, Any]:
        """获取趋势数据"""
        return self.context.trend_signals if self.context else {}
    
    def get_sentiment(self) -> Dict[str, Any]:
        """获取情绪数据"""
        return self.context.sentiment_data if self.context else {}
    
    def get_whale(self) -> Dict[str, Any]:
        """获取资金流数据"""
        return self.context.whale_activity if self.context else {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转为dict"""
        if self.context:
            return self.context.model_dump()
        return {}
