# SmarsFA-Ultra PRD

## 产品名称
**SmarsFA-Ultra – SubAgent Cognitive Architecture**

## 产品目标
构建一个基于 OpenClaw SubAgent 架构的：
> 财报智能分析多专家认知系统

核心能力：
1. 自动解析财报文本
2. 多维度结构化分析
3. 生成投资判断逻辑链
4. 输出结构化决策报告
5. 支持可扩展专家模块

## 架构

```
External Controller Loop
↓
EarningsMasterAgent
↓
├── FinancialParsingSubAgent
├── TrendAnalysisSubAgent
├── SentimentSubAgent
├── WhaleBehaviorSubAgent
├── RiskAssessmentSubAgent
└── SynthesisSubAgent
```

## 用户场景

### 场景 1：单次财报分析
输入：股票代码 + 季度
输出：结构化报告 + 风险评估 + 投资建议

### 场景 2：批量监控
Controller遍历watchlist，调用Master Agent，存储结果

## SubAgents

1. **FinancialParsingSubAgent** - 财报解析
2. **TrendAnalysisSubAgent** - 趋势分析
3. **SentimentSubAgent** - 情绪分析
4. **WhaleBehaviorSubAgent** - 资金流分析
5. **RiskAssessmentSubAgent** - 风险评估
6. **SynthesisSubAgent** - 综合合成

## 非功能性要求

- 推理链可追踪
- 输出结构化JSON
- 支持模块热插拔
- 成本可控
- 延迟 < 20秒
