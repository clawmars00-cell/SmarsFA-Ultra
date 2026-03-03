# SmarsFA-Ultra 5维分析 Agents
# 基于 earnings 提取结果进行多维度分析

import asyncio
import json
from typing import Optional
from dataclasses import dataclass

try:
    from models.earnings import (
        EarningsReport, AnalysisResult, SynthesisResult,
        DataQuality
    )
except ImportError:
    from models.earnings import (
        EarningsReport, AnalysisResult, SynthesisResult,
        DataQuality
    )


# ============================================
# Agent 基类
# ============================================

class BaseAgent:
    """Agent 基类"""
    
    def __init__(self, name: str):
        self.name = name
        
    async def run(self, context: dict) -> dict:
        """执行分析"""
        raise NotImplementedError


# ============================================
# Valuation Agent (估值分析)
# ============================================

@dataclass
class ValuationResult:
    """估值分析结果"""
    score: int  # 0-100
    conclusion: str  # 低估/合理/高估
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    ps_ratio: Optional[float]
    ev_ebitda: Optional[float]
    discount_margin: Optional[float]  # 安全边际
    reason: str


class ValuationAgent(BaseAgent):
    """
    估值分析师 Agent
    
    分析维度:
    - PE / PB / PS 估值
    - EV/EBITDA
    - 安全边际
    - 行业对比
    """
    
    def __init__(self):
        super().__init__("Valuation Agent")
        
    async def run(self, earnings_report: EarningsReport) -> ValuationResult:
        """执行估值分析"""
        print(f"[{self.name}] 分析 {earnings_report.ticker}...")
        
        await asyncio.sleep(0.5)  # 模拟分析时间
        
        # 获取财务数据
        financials = earnings_report.financials
        eps = financials.eps.actual or 0
        revenue = financials.revenue.actual or 0
        net_income = financials.net_income.actual or 0
        
        # 计算估值指标
        # 简化版：基于 EPS 和 Revenue 估算
        pe_ratio = financials.pe_ratio or (35000 / net_income if net_income else None)
        ps_ratio = financials.ps_ratio or (35000 / revenue if revenue else None)
        
        # 计算安全边际 (简化)
        # 假设合理 PE = 20
        fair_pe = 20
        if pe_ratio and eps:
            fair_value = eps * fair_pe
            current_price = eps * pe_ratio
            discount_margin = (fair_value - current_price) / fair_value * 100
        else:
            discount_margin = None
        
        # 计算评分
        score = self._calculate_score(pe_ratio, discount_margin, financials)
        conclusion = self._get_conclusion(score)
        
        return ValuationResult(
            score=score,
            conclusion=conclusion,
            pe_ratio=pe_ratio,
            pb_ratio=financials.pb_ratio,
            ps_ratio=ps_ratio,
            ev_ebitda=None,
            discount_margin=discount_margin,
            reason=self._generate_reason(earnings_report, score, conclusion)
        )
    
    def _calculate_score(self, pe_ratio: float, discount_margin: float, financials) -> int:
        """计算估值评分 (0-100)"""
        score = 50  # 基准分
        
        # PE 评分
        if pe_ratio:
            if pe_ratio < 15:
                score += 20  # 低估
            elif pe_ratio < 25:
                score += 10  # 合理
            elif pe_ratio < 40:
                score -= 10  # 略高
            else:
                score -= 20  # 高估
        
        # 安全边际评分
        if discount_margin:
            if discount_margin > 30:
                score += 20
            elif discount_margin > 10:
                score += 10
            elif discount_margin < 0:
                score -= 15
        
        # 盈利增长加分
        if financials.eps.growth_yoy and financials.eps.growth_yoy > 15:
            score += 10
        elif financials.eps.growth_yoy and financials.eps.growth_yoy < 0:
            score -= 10
        
        return max(0, min(100, score))
    
    def _get_conclusion(self, score: int) -> str:
        if score >= 70:
            return "低估"
        elif score >= 40:
            return "合理"
        else:
            return "高估"
    
    def _generate_reason(self, report: EarningsReport, score: int, conclusion: str) -> str:
        """生成分析理由"""
        ticker = report.ticker
        growth = report.financials.eps.growth_yoy or 0
        
        if conclusion == "低估":
            return f"{ticker} PE估值偏低，安全边际充足，EPS增长 {growth:.1f}%，具备投资价值。"
        elif conclusion == "合理":
            return f"{ticker} 估值处于合理区间，EPS增长 {growth:.1f}%，建议持有。"
        else:
            return f"{ticker} 估值偏高，PE压力较大，需谨慎评估。"


# ============================================
# Quality Agent (质量分析)
# ============================================

class QualityAgent(BaseAgent):
    """
    质量分析师 Agent
    
    分析维度:
    - ROE / ROIC
    - 毛利率 / 净利率
    - 资产负债表健康度
    - 护城河
    """
    
    def __init__(self):
        super().__init__("Quality Agent")
        
    async def run(self, earnings_report: EarningsReport) -> AnalysisResult:
        """执行质量分析"""
        print(f"[{self.name}] 分析 {earnings_report.ticker}...")
        
        await asyncio.sleep(0.5)
        
        financials = earnings_report.financials
        
        # 计算评分
        score = self._calculate_score(financials)
        conclusion = self._get_conclusion(score)
        
        return AnalysisResult(
            score=score,
            conclusion=conclusion,
            key_metrics={
                "gross_margin": financials.gross_margin,
                "net_margin": financials.net_margin,
                "operating_margin": financials.operating_margin,
                "revenue_growth": financials.revenue.growth_yoy,
                "eps_growth": financials.eps.growth_yoy
            },
            reason=self._generate_reason(earnings_report, score, conclusion)
        )
    
    def _calculate_score(self, financials) -> int:
        score = 50
        
        # 毛利率
        if financials.gross_margin:
            if financials.gross_margin > 50:
                score += 20
            elif financials.gross_margin > 30:
                score += 10
            elif financials.gross_margin < 20:
                score -= 15
        
        # 净利率
        if financials.net_margin:
            if financials.net_margin > 20:
                score += 15
            elif financials.net_margin > 10:
                score += 5
            elif financials.net_margin < 0:
                score -= 20
        
        # 增长率
        if financials.eps.growth_yoy:
            if financials.eps.growth_yoy > 15:
                score += 15
            elif financials.eps.growth_yoy > 0:
                score += 5
            else:
                score -= 10
        
        return max(0, min(100, score))
    
    def _get_conclusion(self, score: int) -> str:
        if score >= 80:
            return "优秀"
        elif score >= 60:
            return "良好"
        elif score >= 40:
            return "一般"
        else:
            return "差"
    
    def _generate_reason(self, report: EarningsReport, score: int, conclusion: str) -> str:
        ticker = report.ticker
        gm = report.financials.gross_margin or 0
        nm = report.financials.net_margin or 0
        
        return f"{ticker} 毛利率 {gm:.1f}%，净利率 {nm:.1f}%，整体质量 {conclusion}。"


# ============================================
# Analyst Agent (金融分析)
# ============================================

class AnalystAgent(BaseAgent):
    """
    金融分析师 Agent
    
    分析维度:
    - 商业模式
    - 行业地位
    - 管理层评估
    - 宏观影响
    """
    
    def __init__(self):
        super().__init__("Analyst Agent")
        
    async def run(self, earnings_report: EarningsReport) -> AnalysisResult:
        """执行金融分析"""
        print(f"[{self.name}] 分析 {earnings_report.ticker}...")
        
        await asyncio.sleep(0.5)
        
        # 基于财报情绪评估
        sentiment = earnings_report.sentiment
        if sentiment:
            score = int(sentiment.confidence * 80)
        else:
            score = 50
        
        conclusion = self._get_conclusion(score)
        
        return AnalysisResult(
            score=score,
            conclusion=conclusion,
            key_metrics={
                "sentiment": sentiment.label if sentiment else "Neutral",
                "confidence": sentiment.confidence if sentiment else 0.5,
                "guidance": earnings_report.guidance,
                "guidance_direction": earnings_report.guidance_direction
            },
            reason=self._generate_reason(earnings_report, score, conclusion)
        )
    
    def _get_conclusion(self, score: int) -> str:
        if score >= 80:
            return "顶级"
        elif score >= 60:
            return "优秀"
        elif score >= 40:
            return "良好"
        else:
            return "一般"
    
    def _generate_reason(self, report: EarningsReport, score: int, conclusion: str) -> str:
        ticker = report.ticker
        sentiment = report.sentiment
        
        if sentiment:
            return f"{ticker} 管理层信心 {sentiment.confidence:.0%}，情绪 {sentiment.label}。"
        
        return f"{ticker} 商业模式分析 {conclusion}。"


# ============================================
# Momentum Agent (动量分析)
# ============================================

class MomentumAgent(BaseAgent):
    """
    动量分析师 Agent
    
    分析维度:
    - 价格趋势
    - RSI / MACD
    - 支撑/阻力位
    """
    
    def __init__(self):
        super().__init__("Momentum Agent")
        
    async def run(self, earnings_report: EarningsReport) -> AnalysisResult:
        """执行动量分析"""
        print(f"[{self.name}] 分析 {earnings_report.ticker}...")
        
        await asyncio.sleep(0.5)
        
        # 基于业绩趋势评估动量
        growth = earnings_report.financials.revenue.growth_yoy or 0
        
        if growth > 20:
            score = 85
            conclusion = "强势"
        elif growth > 10:
            score = 70
            conclusion = "强势"
        elif growth > 0:
            score = 55
            conclusion = "震荡"
        else:
            score = 40
            conclusion = "弱势"
        
        return AnalysisResult(
            score=score,
            conclusion=conclusion,
            key_metrics={
                "revenue_growth": growth,
                "eps_growth": earnings_report.financials.eps.growth_yoy,
                "guidance_direction": earnings_report.guidance_direction
            },
            reason=f"{earnings_report.ticker} 营收增长 {growth:.1f}%，动量 {conclusion}。"
        )


# ============================================
# Sentiment Agent (舆情分析)
# ============================================

class SentimentAgent(BaseAgent):
    """
    舆情分析师 Agent
    
    分析维度:
    - 新闻情绪
    - 分析师评级
    - 社交媒体
    - 风险/催化剂
    """
    
    def __init__(self):
        super().__init__("Sentiment Agent")
        
    async def run(self, earnings_report: EarningsReport) -> AnalysisResult:
        """执行舆情分析"""
        print(f"[{self.name}] 分析 {earnings_report.ticker}...")
        
        await asyncio.sleep(0.5)
        
        # 基于财报情绪
        sentiment = earnings_report.sentiment
        if sentiment:
            if sentiment.label == "Bullish":
                score = 85
                conclusion = "正面"
            elif sentiment.label == "Bearish":
                score = 35
                conclusion = "负面"
            else:
                score = 55
                conclusion = "中性"
        else:
            score = 50
            conclusion = "中性"
        
        return AnalysisResult(
            score=score,
            conclusion=conclusion,
            key_metrics={
                "sentiment_label": sentiment.label if sentiment else "Neutral",
                "confidence": sentiment.confidence if sentiment else 0.5,
                "positive_signals": sentiment.positive_signals if sentiment else [],
                "negative_signals": sentiment.negative_signals if sentiment else []
            },
            reason=f"{earnings_report.ticker} 舆情 {conclusion}。"
        )


# ============================================
# Synthesis Agent (综合决策)
# ============================================

class SynthesisAgent(BaseAgent):
    """
    综合决策 Agent
    
    汇总 5 个维度的分析结果
    """
    
    def __init__(self):
        super().__init__("Synthesis Agent")
        
    async def run(
        self,
        valuation: ValuationResult,
        quality: AnalysisResult,
        analyst: AnalysisResult,
        momentum: AnalysisResult,
        sentiment: AnalysisResult
    ) -> SynthesisResult:
        """执行综合决策"""
        print(f"[{self.name}] 汇总分析结果...")
        
        # 计算综合评分 (加权平均)
        score = int(
            valuation.score * 0.25 +
            quality.score * 0.25 +
            analyst.score * 0.20 +
            momentum.score * 0.15 +
            sentiment.score * 0.15
        )
        
        # 确定评级
        rating = self._get_rating(score)
        
        # 生成摘要
        summary = self._generate_summary(
            valuation, quality, analyst, momentum, sentiment
        )
        
        # 风险提示
        risk_alert = self._generate_risk_alert(sentiment, momentum)
        
        return SynthesisResult(
            score=score,
            rating=rating,
            summary=summary,
            risk_alert=risk_alert,
            reason=self._generate_reason(score, rating),
            confidence=0.85
        )
    
    def _get_rating(self, score: int) -> str:
        if score >= 80:
            return "强烈推荐"
        elif score >= 65:
            return "推荐"
        elif score >= 45:
            return "持有"
        else:
            return "回避"
    
    def _generate_summary(self, v, q, a, m, s) -> str:
        return (
            f"估值 {v.conclusion}，质量 {q.conclusion}，"
            f"金融 {a.conclusion}，动量 {m.conclusion}，"
            f"舆情 {s.conclusion}。"
        )
    
    def _generate_risk_alert(self, sentiment_result, momentum_result) -> str:
        alerts = []
        
        # sentiment_result 是 AnalysisResult，不是 SentimentScore
        if sentiment_result and sentiment_result.conclusion in ["负面", "Bearish"]:
            alerts.append("舆情偏空")
        if momentum_result and momentum_result.conclusion == "弱势":
            alerts.append("动量偏弱")
            
        return "，".join(alerts) if alerts else "无明显风险"
    
    def _generate_reason(self, score: int, rating: str) -> str:
        return f"综合评分 {score} 分，投资评级 {rating}。"


# ============================================
# 便捷函数
# ============================================

async def run_full_analysis(earnings_report: EarningsReport) -> SynthesisResult:
    """
    运行完整的 5 维分析
    
    Args:
        earnings_report: 财报数据
        
    Returns:
        SynthesisResult: 综合分析结果
    """
    # 并行执行 5 个 Agent
    tasks = [
        ValuationAgent().run(earnings_report),
        QualityAgent().run(earnings_report),
        AnalystAgent().run(earnings_report),
        MomentumAgent().run(earnings_report),
        SentimentAgent().run(earnings_report)
    ]
    
    results = await asyncio.gather(*tasks)
    
    valuation, quality, analyst, momentum, sentiment = results
    
    # 执行综合决策
    synthesis = await SynthesisAgent().run(
        valuation, quality, analyst, momentum, sentiment
    )
    
    return synthesis


# ============================================
# 测试
# ============================================

async def main():
    """测试 5 维分析"""
    # 创建模拟财报数据
    from models.earnings import FinancialMetrics, FinancialMetric, SentimentScore
    
    mock_report = EarningsReport(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        fiscal_quarter="2026 Q4",
        fiscal_year=2026,
        financials=FinancialMetrics(
            revenue=FinancialMetric(actual=35100, estimate=33000, growth_yoy=25.5),
            eps=FinancialMetric(actual=0.81, estimate=0.75, growth_yoy=15.2),
            net_income=FinancialMetric(actual=8500, growth_yoy=18.3),
            operating_income=FinancialMetric(actual=12000),
            ebitda=FinancialMetric(actual=15000),
            gross_margin=55.2,
            net_margin=24.3
        ),
        sentiment=SentimentScore(
            label="Bullish",
            confidence=0.92,
            reasoning="Revenue beat estimates"
        ),
        source="10-Q"
    )
    
    # 运行分析
    result = await run_full_analysis(mock_report)
    
    print("\n" + "="*60)
    print("📊 综合分析结果")
    print("="*60)
    print(f"评分: {result.score}")
    print(f"评级: {result.rating}")
    print(f"摘要: {result.summary}")
    print(f"风险: {result.risk_alert}")
    print(f"理由: {result.reason}")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())
