"""
Schemas - 数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========== Input Schema ==========
class AnalyzeInput(BaseModel):
    """分析输入"""
    stock: str = Field(..., description="股票代码")
    quarter: str = Field(default="Q4 2025", description="财报季度")
    raw_text: Optional[str] = Field(default="", description="财报全文(可选)")


# ========== Output Schema ==========
class SubAgentOutput(BaseModel):
    """SubAgent标准输出"""
    module: str
    version: str = "1.0"
    confidence: float = Field(..., ge=0.0, le=1.0)
    key_findings: List[str] = Field(default_factory=list)
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    risk_flags: List[str] = Field(default_factory=list)
    
    # 可观测性
    latency_ms: int = 0
    tokens_used: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SynthesisOutput(SubAgentOutput):
    """Synthesis模块专用输出"""
    reasoning_chain: List[str] = Field(default_factory=list)
    recommendation: str = ""  # BUY/SELL/HOLD
    overall_score: float = 0.0


# ========== Protocol Schema ==========
class AgentContext(BaseModel):
    """工作上下文"""
    stock: str
    quarter: str
    raw_text: str = ""
    
    # 共享内存 (结构化dict)
    financial_metrics: Dict[str, Any] = Field(default_factory=dict)
    trend_signals: Dict[str, Any] = Field(default_factory=dict)
    sentiment_data: Dict[str, Any] = Field(default_factory=dict)
    whale_activity: Dict[str, Any] = Field(default_factory=dict)
    risk_flags: List[str] = Field(default_factory=list)
    
    # 元数据
    execution_order: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TaskResult(BaseModel):
    """任务结果"""
    task_id: str
    stock: str
    quarter: str
    status: str  # success, failed, partial
    result: Optional[SynthesisOutput] = None
    execution_time_ms: int = 0
    total_tokens: int = 0
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
