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

---

## 十六、增强评分系统 (v2.0 - 2026-03-01)

### 16.1 四维度评分体系

| 维度 | 权重 | 评分项 |
|------|------|--------|
| 财务评分 | 35% | 盈利能力 + 成长性 + 估值 + 现金流 + 资产负债表 |
| 技术评分 | 25% | 趋势 + 动量RSI + 相对强度 + 波动性 |
| 舆情评分 | 20% | 分析师评级 + 法律风险 + 新闻情绪 + 机构持仓 |
| 宏观政治 | 20% | 利率环境 + 通胀 + 经济增长 + 地缘政治 |

### 16.2 改进项 (v2.0 新增)

#### 财务维度增强
- ✅ **ROIC (资本回报率)** - 比ROE更能反映真实盈利能力
- ✅ **盈余质量** - 应计项/经营性现金流
- ✅ **资产周转率** - 运营效率
- ✅ **DCF内在价值** - 市价 vs 内在价值对比

#### 技术维度增强
- ✅ **12个月历史数据** - 从6个月扩展到12个月
- ✅ **趋势持续性验证** - 过去12个月趋势稳定性
- ✅ **相对板块表现** - vs行业ETF (XLK, XLF等)
- ✅ **量价配合分析** - 成交量与价格趋势一致性

#### 舆情维度增强
- ✅ **盈利预期趋势** - 过去4个季度EPS预期上调/下调
- ✅ **内部人士交易** - 内部人买入/卖出监测
- ✅ **目标价时间衰减** - 3个月以上目标价降低权重

#### 宏观维度增强
- ✅ **宏观Regime检测** - 加息/降息/滞胀/衰退周期
- ✅ **行业轮动信号** - 行业相对表现
- ✅ **风险资产vs避险资产** - 股债金相对表现

### 16.3 评分阈值

| 评分 | 建议 | 综合分 |
|------|------|--------|
| 🚀 STRONG_BUY | 强烈买入 | >= 75 |
| 🟢 BUY | 建议买入 | 60-74 |
| 🟡 HOLD | 建议观望 | 45-59 |
| 🔴 SELL | 建议卖出 | 30-44 |
| 💥 STRONG_SELL | 强烈回避 | < 30 |

### 16.4 行业宏观敏感度

| 行业 | 利率 | 通胀 | GDP | 地缘 | 监管 |
|------|------|------|-----|------|------|
| 金融 | 0.4 | 0.2 | 0.3 | - | - |
| 科技 | 0.3 | 0.2 | 0.3 | - | 0.3 |
| 能源 | 0.2 | 0.3 | - | 0.4 | - |
| 医疗 | 0.2 | 0.2 | 0.2 | - | 0.4 |
| 消费 | 0.2 | 0.3 | 0.3 | - | - |
| 工业 | 0.2 | 0.2 | 0.4 | - | - |
| 房地产 | 0.5 | 0.2 | 0.2 | - | 0.1 |

### 16.5 预期效果

| 改进项 | 目标提升 |
|--------|---------|
| ROIC + DCF | 财务准确性 +15% |
| 盈利预期趋势 | 预测方向准确 +20% |
| 动量质量 | 过滤假突破 +15% |
| 宏观Regime | 避免逆风操作 +10% |

**整体目标**: 从当前60-65%胜率 → 70-75%

---

## 十七、SubAgent增强 (v2.0)

### 17.1 新增SubAgents

| Agent | 职责 | 输出 |
|-------|------|------|
| ROICAgent | 计算资本回报率 | ROIC/ROE/ROA评分 |
| MomentumAgent | 动量质量分析 | 趋势持续性/量价配合 |
| MacroRegimeAgent | 宏观周期检测 | 当前Regime/行业建议 |
| EarningsTrendAgent | 盈利预期趋势 | EPS预期上调/下调信号 |

### 17.2 执行流程 (v2.0)

```
Phase 1: DataAgent (串行)
         ↓
Phase 2: ValuationAgent + GrowthAgent + QualityAgent + MomentumAgent (并行)
         ↓
Phase 3: ROICAgent + DCFAgent (串行)
         ↓
Phase 4: EarningsTrendAgent + MacroRegimeAgent (并行)
         ↓
Phase 5: SynthesisAgent (串行)
```

---

## 十八、版本历史 v2.0

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2026-03-01 | 新增ROIC/DCF/动量质量/宏观Regime评分 |
