# SmarsFA-Ultra 财报数据模型 v2
# 增强版：支持 Actual + Estimate + 容错机制

from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum


# =======================
# 数据质量枚举
# =======================

class DataQuality(str, Enum):
    """数据质量等级"""
    HIGH = "high"           # 完整准确
    MEDIUM = "medium"       # 部分缺失但可靠
    LOW = "low"             # 需要人工复核
    MISSING = "missing"     # 完全缺失


# =======================
# 情绪分析模型
# =======================

class SentimentScore(BaseModel):
    """财报情绪评分"""
    label: Literal["Bullish", "Bearish", "Neutral"] = Field(
        description="情绪标签"
    )
    confidence: Annotated[float, Field(ge=0, le=1)] = Field(
        description="置信度 0-1"
    )
    reasoning: str = Field(
        description="提取该情绪的关键财务指标或管理层表态"
    )
    
    # 附加信号
    positive_signals: list[str] = Field(
        default_factory=list,
        description="积极信号列表"
    )
    negative_signals: list[str] = Field(
        default_factory=list,
        description="消极信号列表"
    )


# =======================
# 单项财务指标 (带估计值)
# =======================

class FinancialMetric(BaseModel):
    """单项财务指标 - 支持 Actual + Estimate"""
    actual: float | None = Field(default=None, description="实际值")
    estimate: float | None = Field(default=None, description="分析师预期")
    growth_yoy: float | None = Field(default=None, description="同比增长 %")
    
    @property
    def surprise(self) -> float | None:
        """超预期 = 实际 - 预期"""
        if self.actual is not None and self.estimate is not None:
            return self.actual - self.estimate
        return None
    
    @property
    def surprise_percent(self) -> float | None | Literal["N/A"]:
        """超预期百分比"""
        if self.actual is not None and self.estimate and self.estimate != 0:
            return (self.actual - self.estimate) / self.estimate * 100
        return "N/A"


# =======================
# 核心财务指标 (增强版)
# =======================

class FinancialMetrics(BaseModel):
    """核心财务指标 - 完整版 (单位: 百万美元)"""
    
    # =====
    # 营收 (有 Estimate)
    # =====
    revenue: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="营收"
    )
    
    # =====
    # 每股收益 (有 Estimate)
    # =====
    eps: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="每股收益"
    )
    
    # =====
    # 净利润 (无 Estimate，通常不提前预测)
    # =====
    net_income: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="净利润"
    )
    
    # =====
    # 营业利润 / EBIT (可能有 Estimate)
    # =====
    operating_income: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="营业利润 (Operating Income / EBIT)"
    )
    
    # =====
    # EBITDA (可能有 Estimate)
    # =====
    ebitda: FinancialMetric = Field(
        default_factory=FinancialMetric,
        description="EBITDA"
    )
    
    # =====
    # 利润率 (派生指标，无 Estimate)
    # =====
    gross_margin: float | None = Field(default=None, description="毛利率 %")
    net_margin: float | None = Field(default=None, description="净利率 %")
    operating_margin: float | None = Field(default=None, description="营业利润率 %")
    
    # =====
    # 估值指标
    # =====
    pe_ratio: float | None = Field(default=None, description="市盈率 P/E")
    pb_ratio: float | None = Field(default=None, description="市净率 P/B")
    ps_ratio: float | None = Field(default=None, description="市销率 P/S")
    
    # =====
    # 现金流
    # =====
    operating_cash_flow: float | None = Field(default=None, description="经营活动现金流")
    free_cash_flow: float | None = Field(default=None, description="自由现金流")
    capital_expenditure: float | None = Field(default=None, description="资本支出")
    
    # =====
    # 资产负债表
    # =====
    total_assets: float | None = Field(default=None, description="总资产")
    total_liabilities: float | None = Field(default=None, description="总负债")
    shareholders_equity: float | None = Field(default=None, description="股东权益")
    debt_to_equity: float | None = Field(default=None, description="负债/权益比率")
    
    # =====
    # 每股指标
    # =====
    book_value_per_share: float | None = Field(default=None, description="每股净资产")
    operating_cash_flow_per_share: float | None = Field(default=None, description="每股经营现金流")
    free_cash_flow_per_share: float | None = Field(default=None, description="每股自由现金流")


# =======================
# 财报主模型 (容错增强版)
# =======================

class EarningsReport(BaseModel):
    """完整财报数据模型 - 生产级"""
    
    # =====
    # 基础信息
    # =====
    ticker: str = Field(description="股票代码")
    company_name: str | None = Field(default=None, description="公司名称")
    fiscal_quarter: str = Field(description="财报季度，如 2026 Q1")
    fiscal_year: int = Field(description="财年")
    
    # =====
    # 报告日期
    # =====
    report_date: str | None = Field(default=None, description="财报发布日期")
    earnings_call_date: str | None = Field(default=None, description="电话会议日期")
    
    # =====
    # 核心指标
    # =====
    financials: FinancialMetrics = Field(
        default_factory=FinancialMetrics,
        description="财务指标"
    )
    
    # =====
    # 管理层指引 (优雅退化)
    # =====
    guidance: str | None = Field(
        default=None,
        description="管理层业绩展望。若财报未提及，请设为 null 而非捏造。"
    )
    guidance_direction: Literal["up", "down", "neutral"] | None = Field(
        default=None,
        description="指引方向"
    )
    guidance_eps_low: float | None = Field(default=None, description="EPS 指引下限")
    guidance_eps_high: float | None = Field(default=None, description="EPS 指引上限")
    
    # =====
    # 情绪分析
    # =====
    sentiment: SentimentScore | None = Field(default=None, description="财报情绪")
    
    # =====
    # 数据来源
    # =====
    source: Literal["10-Q", "10-K", "8-K", "press_release"] = Field(
        description="数据来源"
    )
    raw_text_length: int | None = Field(default=None, description="原文长度")
    
    # =====
    # 容错机制 (新增)
    # =====
    is_data_complete: bool = Field(
        default=True,
        description="数据是否完整"
    )
    data_quality: DataQuality = Field(
        default=DataQuality.HIGH,
        description="数据质量等级"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="缺失字段列表"
    )
    extraction_notes: str | None = Field(
        default=None,
        description="提取备注 (如数据来源说明)"
    )
    
    # =====
    # 时间戳
    # =====
    extracted_at: datetime = Field(
        default_factory=datetime.now,
        description="提取时间"
    )
    
    # =====
    # 验证器
    # =====
    @field_validator('ticker')
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper()
    
    @field_validator('guidance')
    @classmethod
    def check_guidance_validity(cls, v: str | None) -> str | None:
        """过滤无效的 guidance"""
        if v is None:
            return None
        # 过滤掉 "N/A", "None", "TBD" 等无效字符串
        invalid_values = {"n/a", "none", "tbd", "tbc", "-", ""}
        if v.strip().lower() in invalid_values:
            return None
        if len(v.strip()) < 10:  # 太短可能是无效内容
            return None
        return v
    
    @model_validator(mode='after')
    def assess_data_quality(self) -> 'EarningsReport':
        """自动评估数据质量"""
        missing = []
        
        # 检查关键字段
        if self.financials.revenue.actual is None:
            missing.append("revenue.actual")
        if self.financials.eps.actual is None:
            missing.append("eps.actual")
        if self.sentiment is None:
            missing.append("sentiment")
            
        self.missing_fields = missing
        
        if missing:
            self.is_data_complete = False
            if len(missing) <= 2:
                self.data_quality = DataQuality.MEDIUM
            else:
                self.data_quality = DataQuality.LOW
        else:
            self.data_quality = DataQuality.HIGH
            
        return self


# =======================
# 财报日历模型
# =======================

class EarningsCalendarItem(BaseModel):
    """财报日历条目"""
    ticker: str
    company_name: str | None = None
    fiscal_quarter: str
    report_date: str  # YYYY-MM-DD
    eps_estimate: float | None = None
    revenue_estimate: float | None = None
    status: Literal["upcoming", "confirmed", "released"] = "upcoming"
    
    @field_validator('ticker')
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.upper()


class EarningsCalendar(BaseModel):
    """财报日历"""
    start_date: str
    end_date: str
    items: list[EarningsCalendarItem]
    fetched_at: datetime = Field(default_factory=datetime.now)


# =======================
# 分析结果模型
# =======================

class AnalysisResult(BaseModel):
    """单维度分析结果"""
    score: int = Field(ge=0, le=100)
    conclusion: str
    key_metrics: dict = Field(default_factory=dict)
    reason: str


class SynthesisResult(BaseModel):
    """综合分析结果"""
    score: int = Field(ge=0, le=100)
    rating: Literal["强烈推荐", "推荐", "持有", "回避"]
    summary: str
    risk_alert: str | None = None
    reason: str
    
    # 附加
    target_price: float | None = None
    stop_loss: float | None = None
    confidence: float | None = None


# =======================
# 监控模型
# =======================

class ExtractionMetrics(BaseModel):
    """提取过程监控指标"""
    model_used: str = Field(description="使用的模型")
    token_usage: int = Field(description="Token 消耗")
    processing_time_seconds: float = Field(description="处理时间")
    confidence_score: float = Field(description="置信度")
    status: Literal["success", "partial", "failed"] = "success"
    
    # 触发标记
    requires_manual_review: bool = Field(
        default=False,
        description="是否需要人工复核"
    )
    fallback_triggered: bool = Field(
        default=False,
        description="是否触发了 Fallback"
    )
    
    @model_validator(mode='after')
    def check_review_requirement(self) -> 'ExtractionMetrics':
        """自动标记需要人工复核的情况"""
        if self.confidence_score < 0.7:
            self.requires_manual_review = True
        if self.token_usage > 50000:
            self.status = "partial"
        return self
