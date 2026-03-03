# SmarsFA-Ultra Dashboard 指挥中心
# 管理视角的实时监控面板

import streamlit as st
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List

# 导入项目模块
try:
    from models.earnings import EarningsReport, DataQuality
    from pipelines.earnings_calendar import EarningsCalendarCrawler
    from extractors.metrics import EarningsExtractor
    from agents.analysis_agents import run_full_analysis
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models.earnings import EarningsReport, DataQuality
    from pipelines.earnings_calendar import EarningsCalendarCrawler
    from extractors.metrics import EarningsExtractor
    from agents.analysis_agents import run_full_analysis


# ====================
# 页面配置
# ====================

st.set_page_config(
    page_title="SmarsFA-Ultra 指挥中心",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ====================
# 样式定制
# ====================

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .status-running {
        color: #ff9800;
    }
    .status-completed {
        color: #4caf50;
    }
    .status-failed {
        color: #f44336;
    }
    .agent-log {
        font-family: monospace;
        font-size: 0.9rem;
        background-color: #1e1e1e;
        color: #00ff00;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


# ====================
# 状态管理
# ====================

class DashboardState:
    """Dashboard 状态管理"""
    
    def __init__(self):
        self.init_state()
        
    def init_state(self):
        """初始化状态"""
        if 'analysis_history' not in st.session_state:
            st.session_state.analysis_history = []
        if 'current_task' not in st.session_state:
            st.session_state.current_task = None
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        if 'calendar' not in st.session_state:
            st.session_state.calendar = None
    
    def add_log(self, message: str, level: str = "info"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.logs.append({
            "time": timestamp,
            "message": message,
            "level": level
        })
    
    def add_analysis(self, result: dict):
        """添加分析结果"""
        st.session_state.analysis_history.append({
            "timestamp": datetime.now(),
            "ticker": result.get("ticker"),
            "score": result.get("score"),
            "rating": result.get("rating"),
            "status": result.get("status", "completed")
        })


# ====================
# 侧边栏
# ====================

def render_sidebar(state: DashboardState):
    """渲染侧边栏"""
    with st.sidebar:
        st.header("🎛️ 控制面板")
        
        # 股票输入
        ticker = st.text_input("输入美股代码", value="NVDA").upper()
        
        # 分析选项
        st.subheader("⚙️ 分析选项")
        use_fallback = st.checkbox("启用自动Fallback", value=True)
        
        # 运行按钮
        run_button = st.button("🚀 开始分析", type="primary", use_container_width=True)
        
        st.divider()
        
        # 统计
        st.subheader("📊 统计")
        total = len(st.session_state.analysis_history)
        completed = len([x for x in st.session_state.analysis_history if x.get("status") == "completed"])
        st.metric("总任务", total)
        st.metric("已完成", completed)
        
        st.divider()
        
        # 快速操作
        st.subheader("⚡ 快速操作")
        if st.button("📅 刷新日历"):
            state.add_log("刷新财报日历...")
        
        if st.button("🗑️ 清除日志"):
            st.session_state.logs = []
            state.add_log("日志已清除")
        
        return ticker, run_button


# ====================
# Agent 协作链路显示
# ====================

def render_agent_chain(ticker: str, state: DashboardState):
    """渲染 Agent 协作链路"""
    st.subheader(f"🤖 Agent 协作链路: {ticker}")
    
    # 使用 status 容器显示日志
    if st.session_state.logs:
        log_text = "\n".join([
            f"[{log['time']}] {log['message']}"
            for log in st.session_state.logs[-10:]
        ])
        st.markdown(f"```\n{log_text}\n```")
    else:
        st.info("等待任务启动...")


# ====================
# 主展示区
# ====================

def render_main(ticker: str, state: DashboardState):
    """渲染主展示区"""
    
    # 第一行: 核心指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 今日财报", "3", "+1")
    with col2:
        st.metric("🤖 运行中", "0")
    with col3:
        st.metric("✅ 今日完成", "5")
    with col4:
        st.metric("💰 Token消耗", "1.2M")
    
    st.divider()
    
    # 第二行: Agent 链路 + 结果
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        render_agent_chain(ticker, state)
    
    with col_right:
        # 最近分析结果
        st.subheader("📊 最近分析")
        
        if st.session_state.analysis_history:
            for item in reversed(st.session_state.analysis_history[-5:]):
                with st.expander(f"{item['ticker']} - {item['rating']}"):
                    st.write(f"**评分**: {item['score']}")
                    st.write(f"**评级**: {item['rating']}")
                    st.write(f"**时间**: {item['timestamp'].strftime('%H:%M:%S')}")
        else:
            st.info("暂无分析记录")


# ====================
# 质量监控
# ====================

def render_quality_metrics():
    """渲染质量监控指标"""
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📈 数据完整率", "85%", "+5%")
    with col2:
        st.metric("🎯 置信度 > 0.8", "72%")
    with col3:
        st.metric("⚠️ Fallback触发", "15%", "-3%")


# ====================
# 日历显示
# ====================

def render_calendar():
    """渲染财报日历"""
    st.subheader("📅 财报日历")
    
    # 尝试加载日历
    try:
        calendar_file = "./storage/cache/earnings_calendar.json"
        if os.path.exists(calendar_file):
            with open(calendar_file, 'r') as f:
                data = json.load(f)
                items = data.get("items", [])
                
            if items:
                calendar_data = []
                for item in items:
                    calendar_data.append({
                        "日期": item.get("report_date", ""),
                        "股票": item.get("ticker", ""),
                        "季度": item.get("fiscal_quarter", ""),
                        "状态": item.get("status", "")
                    })
                st.table(calendar_data)
            else:
                st.info("暂无财报日历数据")
        else:
            st.info("点击侧边栏刷新日历")
    except Exception as e:
        st.error(f"加载日历失败: {e}")


# ====================
# 人工干预
# ====================

def render_human_intervention():
    """渲染人工干预面板"""
    st.divider()
    
    with st.expander("🎛️ 人工干预 (Human-in-the-loop)"):
        st.write("当数据冲突或质量不足时，可以手动干预")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.button("🔄 重新提取")
        with col2:
            st.button("🔍 触发搜索")
        with col3:
            st.button("✅ 确认结果")


# ====================
# 主函数
# ====================

def main():
    """主函数"""
    # 初始化
    state = DashboardState()
    
    # 标题
    st.markdown('<p class="main-header">🚀 SmarsFA-Ultra 指挥中心</p>', unsafe_allow_html=True)
    st.caption("Powered by Qwen 3.5-plus & OpenClaw Workflow Engine")
    
    # 侧边栏
    ticker, run_button = render_sidebar(state)
    
    # 主展示区
    render_main(ticker, state)
    
    # 质量监控
    render_quality_metrics()
    
    # 日历
    render_calendar()
    
    # 人工干预
    render_human_intervention()


# ====================
# 入口
# ====================

if __name__ == "__main__":
    main()
