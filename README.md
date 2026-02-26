# SmarsFA-Ultra - SubAgent Cognitive Architecture

> 财报智能分析多专家认知系统

## 架构

```
External Controller
        ↓
EarningsMasterAgent
        ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ P   │ T   │ S   │ W   │ R   │ Sy  │
│ arsing│ rend│ nt   │ hale│ isk │ nthesis│
└─────┴─────┴─────┴─────┴─────┴─────┘
```

## SubAgents

| SubAgent | 功能 |
|----------|------|
| FinancialParsingSubAgent | 财报解析 |
| TrendAnalysisSubAgent | 趋势分析 |
| SentimentSubAgent | 情绪分析 |
| WhaleBehaviorSubAgent | 资金流分析 |
| RiskAssessmentSubAgent | 风险评估 |
| SynthesisSubAgent | 综合合成 |

## 启动

```bash
cd /home/mars/.openclaw/sandbox/pm/SmarsFA-Ultra
python3.12 api.py
```

## API

- `POST /api/analyze` - 分析单支股票
- `GET /api/watchlist` - 分析watchlist (NVDA, SE)
- `GET /api/history` - 查询历史

## MVP

- Watchlist: NVDA, SE
- SubAgents: 6个
- 延迟目标: < 20秒

## 版本

v1.0 - 2026-02-26
