# SmarsFA-Ultra PRD

## 产品名称
**SmarsFA-Ultra – SubAgent Cognitive Architecture**

---

## 一、产品目标

构建一个基于 OpenClaw SubAgent 架构的：
> 财报智能分析多专家认知系统

核心能力：
1. 自动解析财报文本
2. 多维度结构化分析
3. 生成投资判断逻辑链
4. 输出结构化决策报告
5. 支持可扩展专家模块

---

## 二、核心问题

传统单 LLM 分析问题：
- 推理不稳定
- 结构混乱
- 信息丢失
- 无法模块化扩展

---

## 三、产品定位

SmarsFA-Ultra 是：
> 一个"单脑多专家"的认知系统

不是多个独立 Agent 互聊。

---

## 四、用户场景

### 场景 1：单次财报分析
输入：
- 财报全文
- 上季度数据
- 行业信息

输出：
- 多维结构化报告
- 风险评估
- 情绪判断
- 资金流向分析
- 综合评分

### 场景 2：批量股票监控（由外部 Controller 驱动）
Controller：
- 遍历股票列表
- 调用 Master Agent
- 存储结果

---

## 五、功能模块

Master Agent 下挂 SubAgents：
1. **FinancialParsingSubAgent** - 财报解析
2. **TrendAnalysisSubAgent** - 趋势分析
3. **SentimentSubAgent** - 情绪分析
4. **WhaleBehaviorSubAgent** - 资金流分析
5. **RiskAssessmentSubAgent** - 风险评估
6. **SynthesisSubAgent** - 综合合成

---

## 六、技术架构

```
External Controller Loop
        ↓
EarningsMasterAgent
        ↓
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ P   │ T   │ S   │ W   │ R   │ Sy  │
│ arsing│ rend│ nt   │ hale│ isk │ nthesis│
└─────┴─────┴─────┴─────┴─────┴─────┘
```

---

## 七、执行流程

### Step 1 Controller 触发
```
analyze(stock="TSLA", quarter="Q4 2025")
```

### Step 2 Master Agent 创建 Session

### Step 3 依次调度 SubAgents
1. FinancialParsing
2. TrendAnalysis
3. Sentiment
4. WhaleBehavior
5. RiskAssessment
6. Synthesis

---

## 八、内存模型

### Working Memory（共享）
单次调用内共享：
- context.financial_data
- context.metrics
- context.sentiment_score
- context.whale_signals

### Long-term Memory（可选）
由 Controller 存 DB：
- 历史财报结果
- 趋势时间序列

---

## 九、数据流

每个 SubAgent 输出：
```json
{
  "module": "trend_analysis",
  "version": "1.0",
  "confidence": 0.82,
  "key_findings": [],
  "structured_data": {},
  "risk_flags": []
}
```

Master 读取后写入共享 context。

---

## 十、SubAgent 协作协议

### 标准输入协议
```json
{
  "stock": "",
  "quarter": "",
  "raw_text": "",
  "context": {},
  "previous_outputs": {}
}
```

### 协作规则
1. 禁止修改其他模块输出
2. 只能读取 context
3. 必须声明数据来源
4. 置信度 < 0.6 必须标记

### 内部状态机
```
INIT → CALL_SUBAGENT → VALIDATE → STORE_CONTEXT → NEXT_SUBAGENT → SYNTHESIS → DONE
```

---

## 十一、错误处理

- 子模块输出缺失 → 重试
- 置信度低 → 标记风险
- JSON 不合法 → 强制修正

---

## 十二、非功能性要求

- 推理链可追踪
- 输出结构化 JSON
- 支持模块热插拔
- 成本可控
- 延迟 < 20 秒

---

## 十三、成本模型

### Token 成本
- 每个 SubAgent ~3k tokens
- 6 个 SubAgent
- 总计 ≈ 18k tokens

| 架构 | Token 消耗 |
|------|-----------|
| 单 LLM | 10k |
| SubAgent | 18k |
| 多独立 Agent | 25k+ |

### 延迟
- 串行：12~18秒
- 优化并行：8~12秒

---

## 十四、与外部 Controller 关系

Controller 负责：
- 批量调度
- 存储
- 重试
- 历史对比
- 异步队列

Master 负责：
- 单股票认知

---

## 十五、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-26 | 初始版本 |
