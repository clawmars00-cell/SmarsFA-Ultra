# SmarsFA-Ultra

SubAgent Cognitive Architecture for Earnings Analysis

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
cd SmarsFA-Ultra
python3.12 api.py
```

## API

- `GET /api/health` - 健康检查
- `POST /api/analyze` - 分析股票
- `GET /api/agents/status` - Agent状态

## GitHub

https://github.com/clawmars00-cell/SmarsFA-Ultra

## 版本

v1.0 - 2026-02-26
