# SmarsFA-Ultra PRD (v2.1)

**项目**: SmarsFA-Ultra 多智能体股票分析系统  
**版本**: 2.1  
**更新日期**: 2026-03-03  
**状态**: 开发中

---

## 1. 项目概述

SmarsFA-Ultra 是一个基于多智能体 (Multi-Agent) 的美股财报情绪提取与股票分析系统。采用 OpenClaw 框架，支持自动化财报爬取、多维度分析、容错机制和人工复核。

### 核心特性
- 🤖 **多智能体协作**: 5个专业分析师 + 1个综合决策师
- 📊 **财报自动提取**: 从 SEC 10-Q/10-K 提取财务指标
- 🛡️ **生产级容错**: 多轮寻回、冲突解决、优雅退化
- 📈 **主动监控**: 财报日历自动爬取，临近发布自动分析
- 🎯 **管理指挥中心**: 实时监控 Agent 工作状态

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户 (Mars)                           │
│                 (WhatsApp / Dashboard)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │ WhatsApp │      │Dashboard │      │  Scheduler│
   │  交互    │      │  指挥中心 │      │  定时任务 │
   └────┬─────┘      └────┬─────┘      └────┬─────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
              ┌───────────────────────────┐
              │    工作流引擎 (DAG)       │
              │  primary_extraction       │
              │  validate_data            │
              │  spawn_searcher (可选)    │
              │  merge_results           │
              │  finalize_report         │
              └───────────────┬───────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │   Coder  │        │ Searcher │        │ Reviewer │
   │  (提取)  │        │  (搜索)  │        │  (校验)  │
   └────┬─────┘        └────┬─────┘        └────┬─────┘
        │                    │                  │
        └────────────────────┴──────────────────┘
                             │
                             ▼
              ┌───────────────────────────────┐
              │   5 维度分析 Agents          │
              │  Valuation / Quality /       │
              │  Analyst / Momentum /        │
              │  Sentiment                  │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      Synthesis Agent          │
              │      (综合决策)               │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │    输出 (WhatsApp / DB)       │
              └───────────────────────────────┘
```

### 2.2 模块结构

```
SmarsFA-Ultra/
├── models/
│   └── earnings.py           # Pydantic 数据模型 v2
├── prompts/
│   ├── earnings_v1.yaml       # 基础版
│   ├── earnings_v2.yaml       # 容错版
│   └── earnings_v3.yaml       # 完整版 (推荐)
├── workflows/
│   └── earnings_extraction.yaml  # DAG 工作流
├── pipelines/
│   ├── earnings_calendar.py   # 财报日历爬虫
│   └── scheduler.py          # 定时调度
├── extractors/
│   ├── metrics.py            # 指标提取
│   └── sentiment.py          # 情绪分析
├── agents/                   # 5+1 分析 Agent
├── dashboard/
│   └── dashboard.py          # 管理指挥中心 ⭐
└── main.py                  # 入口
```

---

## 3. 数据模型

### 3.1 核心字段 (FinancialMetrics)

| 字段 | Actual | Estimate | Growth YoY | 说明 |
|------|--------|----------|-------------|------|
| **revenue** | ✅ | ✅ | ✅ | 营收 (百万美元) |
| **eps** | ✅ | ✅ | ✅ | 每股收益 |
| **net_income** | ✅ | ❌ | ✅ | 净利润 |
| **operating_income** | ✅ | ❌ | ✅ | 营业利润 (EBIT) |
| **ebitda** | ✅ | ❌ | ✅ | EBITDA |
| **gross_margin** | - | - | - | 毛利率 % |
| **net_margin** | - | - | - | 净利率 % |
| **pe_ratio** | - | - | - | 市盈率 |
| **operating_cash_flow** | - | - | - | 经营现金流 |

### 3.2 容错机制

```python
is_data_complete: bool       # 数据完整标记
data_quality: DataQuality    # HIGH / MEDIUM / LOW / MISSING
confidence_score: float      # 0-1 置信度
missing_fields: list[str]   # 缺失字段
extraction_notes: str        # 提取备注
```

---

## 4. 工作流 (DAG)

### 4.1 节点定义

| Stage | 节点 | 类型 | 说明 |
|-------|------|------|------|
| 1 | primary_extraction | Agent | 初次提取 (SEC Filing) |
| 2 | validate_data | Decision | 质量校验 |
| 3 | spawn_searcher | Agent | 补偿搜索 (Fallback) |
| 4 | merge_results | Agent | 冲突解决 |
| 5 | finalize_report | Action | 归档 |

### 4.2 触发条件

```yaml
fallback_trigger:
  - confidence_score < 0.8
  - guidance == null
  - missing_fields.length > 2
```

### 4.3 源可信度权重

| 来源 | 权重 | 说明 |
|------|------|------|
| 10-Q / 10-K | 1.0 | SEC 官方 |
| 8-K | 0.9 | SEC 临时 |
| Earnings Call | 0.8 | 电话会议 |
| Press Release | 0.7 | 新闻稿 |
| Yahoo Finance | 0.6 | 第三方 |

---

## 5. Dashboard 指挥中心

### 5.1 核心功能

| 模块 | 功能 |
|------|------|
| **Agent 协作链路** | 实时显示每个 Agent 的执行状态 |
| **财报日历** | 今日/本周财报发布列表 |
| **分析看板** | 股票评分、关键指标 |
| **质量监控** | 缺失率、置信度分布 |
| **成本分析** | Token 消耗、API 费用 |
| **人工干预** | 数据冲突时的手动仲裁 |

### 5.2 UI 布局

```
┌─────────────────────────────────────────────────────────────┐
│  SmarsFA-Ultra 指挥中心                        [刷新] [设置] │
├─────────────────────────────────────────────────────────────┤
│  📅 财报日历  │  🤖 Agent 状态  │  📊 分析看板           │
│  ───────────  │  ──────────────  │  ─────────────         │
│  Today: 3    │  Running: 2      │  MSFT: 78 ⬆          │
│  Tomorrow: 5 │  Idle: 4         │  AAPL: 65 ⬇          │
│              │  Failed: 0        │  NVDA: 82 ⬆          │
├─────────────────────────────────────────────────────────────┤
│  🤖 Agent 协作链路 (实时日志)                              │
│  ───────────────────────────────────────────────────────   │
│  ✅ [15:02] primary_extraction 完成 (置信度 0.85)         │
│  ⚠️ [15:03] guidance 缺失，触发 spawn_searcher            │
│  🔍 [15:04] 搜索 Earnings Call Transcript...              │
│  ⚖️ [15:05] merge_results: 冲突解决完成                   │
│  📊 [15:06] 触发 5 维度分析 Agents                        │
│  🎯 [15:08] Synthesis 完成，最终评分 82                    │
├─────────────────────────────────────────────────────────────┤
│  📈 质量监控          │  💰 成本分析                      │
│  完整率: 85%          │  今日: $12.50                     │
│  置信度 > 0.8: 72%    │  本周: $89.20                    │
│  触发 Fallback: 15%    │  Token: 1.2M                      │
├─────────────────────────────────────────────────────────────┤
│  🎛️ 人工干预 (Human-in-the-loop)                          │
│  ───────────────────────────────────────────────────────   │
│  ⚠️ TSLA 数据冲突: SEC (EPS=0.92) vs Yahoo (EPS=0.88)    │
│  [选择 SEC 来源] [选择 Yahoo 来源] [自行输入]               │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Agent 定义

### 6.1 SmarsFA-Ultra Agents

| Agent ID | 职责 | 权重 |
|----------|------|------|
| ultra-valuation | 估值分析 | 25% |
| ultra-quality | 质量分析 | 25% |
| ultra-analyst | 金融分析 | 20% |
| ultra-momentum | 动量分析 | 15% |
| ultra-sentiment | 舆情分析 | 15% |
| ultra-synthesis | 综合决策 | - |

### 6.2 Engineering Agents

| Agent ID | 职责 |
|----------|------|
| smars-coder | 核心开发 + 指标提取 |
| smars-tester | 测试验证 |
| smars-reviewer | 代码评审 + 冲突解决 |
| smars-searcher | 补充搜索 (Fallback) |

---

## 7. 使用方式

### 7.1 快速分析
```
用户: "MSFT"
    ↓
SmarsFA-Ultra
    ↓
并行: Valuation + Quality + Analyst + Momentum + Sentiment
    ↓
Synthesis → 最终报告
```

### 7.2 Dashboard 指挥中心
```
打开 Dashboard
    ↓
查看 Agent 实时状态
    ↓
如有异常 → 人工干预
    ↓
查看分析结果
```

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-01 | 初始智能体架构 |
| v2.0 | 2026-03-03 | 增加财报提取、容错机制、DAG工作流 |
| v2.1 | 2026-03-03 | 增加 Dashboard 指挥中心 |

---

## 9. 未来规划

- [ ] Dashboard MVP 上线
- [ ] 财报日历自动爬取
- [ ] 定时调度系统
- [ ] IB 实盘对接
- [ ] SmarsCho 深度分析系统
