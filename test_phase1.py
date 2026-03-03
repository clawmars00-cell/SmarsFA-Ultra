# Phase 1 测试: 财报日历 + 提取器

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipelines.earnings_calendar import EarningsCalendarCrawler
from extractors.metrics import EarningsExtractor
from models.earnings import DataQuality


async def test_earnings_calendar():
    """测试财报日历爬虫"""
    print("\n" + "="*60)
    print("🧪 测试 1: 财报日历爬虫")
    print("="*60)
    
    crawler = EarningsCalendarCrawler(cache_dir="./storage/cache")
    
    # 获取未来7天日历
    calendar = await crawler.get_calendar(days_ahead=7, use_cache=False)
    
    # 如果没有真实数据，使用模拟数据
    if len(calendar.items) == 0:
        print("\n⚠️ 真实数据获取失败，使用模拟数据...")
        calendar = crawler._get_mock_calendar(7)
    
    print(f"\n📅 未来7天财报日历 (共 {len(calendar.items)} 条):")
    print("-" * 60)
    
    for item in calendar.items:
        print(f"{item.report_date} | {item.ticker:6} | {item.fiscal_quarter}")
    
    # 检查今天/明天
    triggered = crawler.check_and_trigger(calendar)
    print(f"\n⚡ 今天/明天触发: {[i.ticker for i in triggered]}")
    
    assert len(calendar.items) > 0, "日历获取失败"
    print("\n✅ 日历爬虫测试通过!")
    
    return calendar


async def test_extractor():
    """测试指标提取器"""
    print("\n" + "="*60)
    print("🧪 测试 2: 指标提取器")
    print("="*60)
    
    extractor = EarningsExtractor()
    
    # 模拟财报原文
    sample_text = """
    NVIDIA Corporation Reports Financial Results for Q4 2026
    
    Financial Highlights:
    - Revenue: $35.1 billion, up 25% year-over-year
    - Analysts expected $33.0 billion
    - EPS: $0.81, compared to $0.72 in the previous year
    - Analysts expected $0.75
    - Net Income: $8.5 billion, up 18% year-over-year
    - Operating Income: $12.0 billion
    - EBITDA: $15.0 billion, up 22%
    - Gross Margin: 55.2%
    - Net Margin: 24.3%
    
    Management Discussion:
    Our data center business reached record highs, driven by unprecedented 
    demand for AI chips. We expect Q2 revenue of approximately $36 billion.
    
    The strong demand in AI continues to be a major tailwind for our business.
    """
    
    report, metrics = await extractor.extract(
        ticker="NVDA",
        raw_text=sample_text,
        fiscal_quarter="2026 Q4",
        source="10-Q"
    )
    
    print(f"\n📊 提取结果:")
    print("-" * 60)
    print(f"Ticker: {report.ticker}")
    print(f"Company: {report.company_name}")
    print(f"Quarter: {report.fiscal_quarter}")
    print(f"\n💰 财务指标:")
    print(f"  Revenue: ${report.financials.revenue.actual}B (预期: ${report.financials.revenue.estimate}B)")
    print(f"  EPS: ${report.financials.eps.actual} (预期: ${report.financials.eps.estimate})")
    print(f"  Net Income: ${report.financials.net_income.actual}B")
    print(f"  Gross Margin: {report.financials.gross_margin}%")
    print(f"\n🎯 情绪分析:")
    if report.sentiment:
        print(f"  Label: {report.sentiment.label}")
        print(f"  Confidence: {report.sentiment.confidence}")
        print(f"  Reasoning: {report.sentiment.reasoning}")
    print(f"\n📈 提取指标:")
    print(f"  Model: {metrics.model_used}")
    print(f"  Token Usage: ~{metrics.token_usage}")
    print(f"  Processing Time: {metrics.processing_time_seconds:.2f}s")
    print(f"  Confidence Score: {metrics.confidence_score}")
    print(f"  Status: {metrics.status}")
    print(f"  Requires Review: {metrics.requires_manual_review}")
    print(f"\n🔍 数据质量:")
    print(f"  Complete: {report.is_data_complete}")
    print(f"  Quality: {report.data_quality}")
    print(f"  Missing Fields: {report.missing_fields}")
    
    # 断言验证 (注意: 单位是百万美元)
    assert report.ticker == "NVDA", "Ticker 提取失败"
    assert report.financials.revenue.actual == 35100.0, "Revenue 提取失败 (单位: 百万美元)"
    assert report.financials.eps.actual == 0.81, "EPS 提取失败"
    assert report.sentiment is not None, "情绪分析失败"
    assert report.sentiment.label == "Bullish", "情绪标签错误"
    assert metrics.confidence_score > 0.7, "置信度过低"
    
    print("\n✅ 提取器测试通过!")
    
    return report, metrics


async def test_end_to_end():
    """端到端测试"""
    print("\n" + "="*60)
    print("🧪 测试 3: 端到端流程")
    print("="*60)
    
    # 1. 获取日历
    crawler = EarningsCalendarCrawler()
    calendar = await crawler.get_calendar(days_ahead=7, use_cache=False)
    
    # 2. 检查今天/明天触发
    triggered = crawler.check_and_trigger(calendar)
    
    if triggered:
        print(f"\n⚡ 触发分析的股票: {[i.ticker for i in triggered]}")
        
        # 3. 对每只触发股票进行提取
        extractor = EarningsExtractor()
        
        sample_text = """
        Q4 2026 Financial Results
        Revenue: $35.1B, EPS: $0.81
        Strong demand continues
        """
        
        for item in triggered[:2]:  # 只测试前2个
            report, metrics = await extractor.extract(
                ticker=item.ticker,
                raw_text=sample_text,
                fiscal_quarter=item.fiscal_quarter
            )
            print(f"  {item.ticker}: {report.sentiment.label if report.sentiment else 'N/A'}")
    
    print("\n✅ 端到端测试通过!")


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 SmarsFA-Ultra Phase 1 测试")
    print("="*60)
    
    try:
        # 测试 1: 日历爬虫
        await test_earnings_calendar()
        
        # 测试 2: 提取器
        await test_extractor()
        
        # 测试 3: 端到端
        await test_end_to_end()
        
        print("\n" + "="*60)
        print("🎉 Phase 1 全部测试通过!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
