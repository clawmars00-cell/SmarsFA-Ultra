# Phase 3 测试: Dashboard

import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_dashboard_imports():
    """测试 Dashboard 导入"""
    print("\n" + "="*60)
    print("🧪 测试 1: Dashboard 导入")
    print("="*60)
    
    try:
        # 尝试导入 (不实际运行 streamlit)
        import dashboard
        print("✅ Dashboard 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_streamlit_available():
    """测试 Streamlit 是否可用"""
    print("\n" + "="*60)
    print("🧪 测试 2: Streamlit 可用性")
    print("="*60)
    
    try:
        import streamlit as st
        print(f"✅ Streamlit 已安装: {st.__version__}")
        return True
    except ImportError:
        print("⚠️ Streamlit 未安装")
        print("安装命令: pip install streamlit")
        return False


def test_modules():
    """测试各个模块"""
    print("\n" + "="*60)
    print("🧪 测试 3: 依赖模块")
    print("="*60)
    
    modules = [
        ("models.earnings", "EarningsReport"),
        ("pipelines.earnings_calendar", "EarningsCalendarCrawler"),
        ("extractors.metrics", "EarningsExtractor"),
        ("agents.analysis_agents", "run_full_analysis"),
    ]
    
    all_ok = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")
            all_ok = False
    
    return all_ok


def test_data_models():
    """测试数据模型"""
    print("\n" + "="*60)
    print("🧪 测试 4: 数据模型")
    print("="*60)
    
    try:
        from models.earnings import (
            EarningsReport, FinancialMetrics, FinancialMetric,
            SentimentScore, DataQuality
        )
        
        # 创建测试数据
        report = EarningsReport(
            ticker="TEST",
            fiscal_quarter="2026 Q1",
            fiscal_year=2026,
            financials=FinancialMetrics(
                revenue=FinancialMetric(actual=1000, estimate=900),
                eps=FinancialMetric(actual=1.0, estimate=0.9)
            ),
            source="10-Q"
        )
        
        print(f"✅ EarningsReport: {report.ticker}")
        print(f"✅ FinancialMetrics: {report.financials.revenue.actual}")
        
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False


def main():
    """主测试"""
    print("\n" + "="*60)
    print("🚀 SmarsFA-Ultra Phase 3 测试 (Dashboard)")
    print("="*60)
    
    results = []
    
    # 测试导入
    results.append(("模块导入", test_dashboard_imports()))
    
    # 测试 Streamlit
    results.append(("Streamlit", test_streamlit_available()))
    
    # 测试依赖模块
    results.append(("依赖模块", test_modules()))
    
    # 测试数据模型
    results.append(("数据模型", test_data_models()))
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 Phase 3 测试通过!")
        print("\n启动 Dashboard:")
        print("  cd SmarsFA")
        print("  streamlit run dashboard/dashboard.py")
    else:
        print("❌ 部分测试失败")
    print("="*60)


if __name__ == "__main__":
    main()
