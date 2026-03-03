# Phase 2 测试: DAG 工作流 + 5维分析 Agents

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.engine import WorkflowEngine, get_earnings_extraction_workflow
from agents.analysis_agents import (
    ValuationAgent, QualityAgent, AnalystAgent, 
    MomentumAgent, SentimentAgent, SynthesisAgent,
    run_full_analysis
)
from models.earnings import (
    EarningsReport, FinancialMetrics, FinancialMetric, 
    SentimentScore, DataQuality
)


async def test_workflow_engine():
    """测试 DAG 工作流引擎"""
    print("\n" + "="*60)
    print("🧪 测试 1: DAG 工作流引擎")
    print("="*60)
    
    # 创建工作流
    workflow_config = get_earnings_extraction_workflow()
    engine = WorkflowEngine(workflow_config)
    
    # 测试正常流程
    result = await engine.run(
        input_data={
            "ticker": "NVDA",
            "input_file": "./data/NVDA_10Q.pdf",
            "confidence_score": 0.85,
            "guidance": "We expect Q2 revenue to be $36 billion"
        }
    )
    
    status = engine.get_status()
    print(f"\n📊 工作流状态:")
    print(json.dumps(status, indent=2, default=str))
    
    # 工作流已完成 (运行完毕)
    assert status["status"] in ["completed", "running"], "工作流执行失败"
    print("\n✅ DAG 工作流测试通过!")
    
    return status


async def test_workflow_with_fallback():
    """测试 Fallback 触发"""
    print("\n" + "="*60)
    print("🧪 测试 2: Fallback 触发")
    print("="*60)
    
    workflow_config = get_earnings_extraction_workflow()
    engine = WorkflowEngine(workflow_config)
    
    # 测试低置信度触发 Fallback
    result = await engine.run(
        input_data={
            "ticker": "TEST",
            "input_file": "./data/TEST_10Q.pdf",
            "confidence_score": 0.65,  # 低置信度
            "guidance": None  # 缺失
        }
    )
    
    status = engine.get_status()
    print(f"\n📊 Fallback 工作流状态:")
    print(json.dumps(status, indent=2, default=str))
    
    print("\n✅ Fallback 工作流测试通过!")
    
    return status


async def test_analysis_agents():
    """测试 5 维分析 Agents"""
    print("\n" + "="*60)
    print("🧪 测试 3: 5维分析 Agents")
    print("="*60)
    
    # 创建模拟财报数据
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
            net_margin=24.3,
            operating_margin=34.3,
            pe_ratio=35.2,
            pb_ratio=12.5
        ),
        sentiment=SentimentScore(
            label="Bullish",
            confidence=0.92,
            reasoning="Revenue beat estimates by 6%, guidance raised on strong AI chip demand.",
            positive_signals=["Data center record high", "AI chip demand unprecedented"],
            negative_signals=["Supply chain constraints"]
        ),
        guidance="We expect Q2 revenue to be approximately $36 billion, driven by strong data center demand.",
        guidance_direction="up",
        source="10-Q"
    )
    
    # 测试各个 Agent
    print("\n📊 单个 Agent 测试:")
    
    # 1. Valuation Agent
    valuation = await ValuationAgent().run(mock_report)
    print(f"  估值: score={valuation.score}, conclusion={valuation.conclusion}")
    
    # 2. Quality Agent
    quality = await QualityAgent().run(mock_report)
    print(f"  质量: score={quality.score}, conclusion={quality.conclusion}")
    
    # 3. Analyst Agent
    analyst = await AnalystAgent().run(mock_report)
    print(f"  金融: score={analyst.score}, conclusion={analyst.conclusion}")
    
    # 4. Momentum Agent
    momentum = await MomentumAgent().run(mock_report)
    print(f"  动量: score={momentum.score}, conclusion={momentum.conclusion}")
    
    # 5. Sentiment Agent
    sentiment = await SentimentAgent().run(mock_report)
    print(f"  舆情: score={sentiment.score}, conclusion={sentiment.conclusion}")
    
    # 6. Synthesis Agent
    print("\n📊 Synthesis Agent:")
    synthesis = await SynthesisAgent().run(valuation, quality, analyst, momentum, sentiment)
    print(f"  综合评分: {synthesis.score}")
    print(f"  投资评级: {synthesis.rating}")
    print(f"  摘要: {synthesis.summary}")
    print(f"  风险: {synthesis.risk_alert}")
    
    # 断言验证
    assert valuation.score > 0, "估值评分错误"
    assert quality.score > 0, "质量评分错误"
    assert analyst.score > 0, "金融评分错误"
    assert momentum.score > 0, "动量评分错误"
    assert sentiment.score > 0, "舆情评分错误"
    assert synthesis.score > 0, "综合评分错误"
    assert synthesis.rating in ["强烈推荐", "推荐", "持有", "回避"], "评级错误"
    
    print("\n✅ 5维分析 Agents 测试通过!")
    
    return synthesis


async def test_full_pipeline():
    """测试完整流程"""
    print("\n" + "="*60)
    print("🧪 测试 4: 完整流程 (财报 -> 提取 -> 5维分析)")
    print("="*60)
    
    from extractors.metrics import EarningsExtractor
    
    # 1. 提取
    extractor = EarningsExtractor()
    sample_text = """
    NVIDIA Corporation Reports Financial Results for Q4 2026
    
    Financial Highlights:
    - Revenue: $35.1 billion, up 25% year-over-year
    - EPS: $0.81
    - Net Income: $8.5 billion
    - Gross Margin: 55.2%
    
    Management: Strong demand continues.
    """
    
    report, metrics = await extractor.extract(
        ticker="NVDA",
        raw_text=sample_text,
        fiscal_quarter="2026 Q4"
    )
    
    print(f"\n📊 提取结果:")
    print(f"  Ticker: {report.ticker}")
    print(f"  Revenue: {report.financials.revenue.actual}")
    print(f"  Confidence: {metrics.confidence_score}")
    
    # 2. 5维分析
    synthesis = await run_full_analysis(report)
    
    print(f"\n📊 最终分析:")
    print(f"  综合评分: {synthesis.score}")
    print(f"  投资评级: {synthesis.rating}")
    
    print("\n✅ 完整流程测试通过!")
    
    return synthesis


async def main():
    """主测试"""
    print("\n" + "="*60)
    print("🚀 SmarsFA-Ultra Phase 2 测试")
    print("="*60)
    
    try:
        # 测试 1: DAG 工作流
        await test_workflow_engine()
        
        # 测试 2: Fallback
        await test_workflow_with_fallback()
        
        # 测试 3: 5维 Agents
        await test_analysis_agents()
        
        # 测试 4: 完整流程
        await test_full_pipeline()
        
        print("\n" + "="*60)
        print("🎉 Phase 2 全部测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
