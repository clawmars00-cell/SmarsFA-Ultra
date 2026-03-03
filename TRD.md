# SmarsFA-Ultra 技术设计文档 (TRD)

**项目**: SmarsFA-Ultra  
**版本**: 1.0  
**日期**: 2026-03-03  
**作者**: SmarsFA Team

---

## 1. 概述

本文档详细描述 SmarsFA-Ultra 系统的技术架构、设计决策和实现细节。

### 1.1 设计目标

- **数据严谨性**: 所有财务数据必须可验证，禁止编造
- **容错性**: 生产级异常处理机制
- **可观测性**: 实时监控 Agent 协作链路
- **可扩展性**: 模块化设计，支持新增分析维度

---

## 2. 技术架构

### 2.1 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **框架** | OpenClaw 2026 | 多智能体协作平台 |
| **模型** | Qwen 3.5-plus | 核心推理引擎 |
| **数据验证** | Pydantic v2 | 强类型数据模型 |
| **工作流** | DAG Engine | 有向无环图任务编排 |
| **前端** | Streamlit | 管理指挥中心 (MVP) |
| **存储** | JSON 文件 | 轻量级持久化 |

### 2.2 Agent 通信机制

```
┌─────────────┐     sessions_send     ┌─────────────┐
│  Agent A   │ ──────────────────────▶│  Agent B   │
└─────────────┘                       └─────────────┘
       │                                     │
       │ JSON 写入                           │ JSON 读取
       ▼                                     ▼
┌─────────────┐                       ┌─────────────┐
│ state/*.json│                       │ state/*.json│
└─────────────┘                       └─────────────┘
```

---

## 3. 数据模型设计

### 3.1 核心原则

1. **强类型**: 使用 Pydantic + Python 3.12+ 类型注解
2. **可空但明确**: 使用 `Optional` 而非默认空字符串
3. **派生字段**: 计算属性 (如 `surprise = actual - estimate`)

### 3.2 FinancialMetric 结构

```python
class FinancialMetric(BaseModel):
    actual: float | None = Field(default=None, description="实际值")
    estimate: float | None = Field(default=None, description="分析师预期")
    growth_yoy: float | None = Field(default=None, description="同比增长 %")
    
    @property
    def surprise(self) -> float | None:
        """超预期 = 实际 - 预期"""
        if self.actual is not None and self.estimate is not None:
            return self.actual - self.estimate
        return None
```

### 3.3 容错设计

```python
class EarningsReport(BaseModel):
    # 数据质量追踪
    is_data_complete: bool = True
    data_quality: DataQuality = DataQuality.HIGH
    confidence_score: float = 1.0
    missing_fields: list[str] = Field(default_factory=list)
    
    @model_validator
    def assess_data_quality(self):
        """自动评估数据质量"""
        if len(self.missing_fields) > 2:
            self.data_quality = DataQuality.LOW
        elif self.missing_fields:
            self.data_quality = DataQuality.MEDIUM
        return self
```

---

## 4. 黄金 Prompt 设计

### 4.1 CoT + Schema 模式

```
# Chain of Thought (思维链)
1. 指标检索 → 2. 指引捕获 → 3. 情绪判读 → 4. JSON 验证

# Schema 强约束
- 输出必须符合预定义的 JSON 格式
- 字段类型严格匹配 (float, string, null)
- 禁止额外字段
```

### 4.2 NULL VALUE POLICY

> **硬约束**: 如果原文找不到数据，必须设为 `null`，严禁：
> - ❌ 使用 "N/A"、"TBD"、"None" 填充
> - ❌ 根据历史数据推测
> - ❌ 捏造任何数字

### 4.3 动态 Token 路由

当原文超过 50k tokens 时：
1. 先用正则/关键词定位 "Financial Highlights" 章节
2. 只提取相关段落 (~10k tokens)
3. 避免全量喂入，降低成本提高精度

---

## 5. DAG 工作流

### 5.1 节点流转

```
primary_extraction ──▶ validate_data ──┬──▶ finalize_report
                    │                   │
                    │ (confidence < 0.8)│
                    ▼                   │
              spawn_searcher ───────────▶
                    │
                    ▼
              merge_results ───────────▶
```

### 5.2 冲突解决规则

| 源类型 | 权重 | 优先级 |
|--------|------|--------|
| 10-Q / 10-K | 1.0 | 最高 |
| 8-K | 0.9 | |
| Earnings Call | 0.8 | |
| Press Release | 0.7 | |
| Yahoo Finance | 0.6 | 最低 |

**原则**: 高权重来源覆盖低权重来源

---

## 6. Dashboard 指挥中心

### 6.1 设计理念

1. **过程透明**: 实时显示 Agent 协作链路
2. **管理视角**: 关注质量、成本、异常
3. **人工干预**: 数据冲突时可手动仲裁

### 6.2 核心模块

```python
# Agent 协作链路显示
with st.status("工作流执行中...") as status:
    st.write("📡 [Primary] 下载 10-Q...")
    st.write("🧠 [Coder] 提取指标...")
    st.write("⚠️ [Validator] 检测到缺失...")
    st.write("🔍 [Searcher] 搜索补充...")
    st.write("⚖️ [Reviewer] 冲突解决...")
    status.update(state="complete")
```

### 6.3 质量监控指标

| 指标 | 计算方式 | 阈值 |
|------|----------|------|
| 完整率 | (字段总数 - 缺失) / 字段总数 | > 80% |
| 置信度 > 0.8 比例 | 高置信度 / 总数 | > 70% |
| Fallback 触发率 | 触发次数 / 总数 | < 20% |

---

## 7. 安全与合规

### 7.1 数据验证

- 所有目标价必须来自 Yahoo Finance / 官方财报
- 禁止编造数据
- 可追溯: 记录数据来源 URL

### 7.2 API 安全

- 模型调用通过 OpenClaw 代理
- API Key 不暴露在前端
- 请求日志可审计

---

## 8. 性能优化

### 8.1 Token 优化

- Context Pruning: cache-ttl 模式
- 长文档预处理: 提取关键章节
- 缓存: 分析结果本地缓存

### 8.2 并行策略

- 5 个分析 Agent 并行执行
- 依赖链串行 (SmarsCho)

---

## 9. 监控与告警

### 9.1 自动告警

| 条件 | 级别 | 动作 |
|------|------|------|
| confidence < 0.6 | Critical | 人工复核 |
| Fallback > 30% | Warning | 优化策略 |
| Token > 50k/次 | Info | 切换分段 |

### 9.2 周报指标

- 哪些公司最容易缺失 guidance
- smars-searcher 召回率
- Token 消耗趋势
- Agent 响应时间

---

## 10. 附录

### 10.1 文件结构

```
SmarsFA/
├── models/
│   └── earnings.py           # 数据模型
├── prompts/
│   ├── earnings_v1.yaml      # 基础 Prompt
│   ├── earnings_v2.yaml      # 容错 Prompt
│   └── earnings_v3.yaml      # 完整 Prompt (推荐)
├── workflows/
│   └── earnings_extraction.yaml  # DAG 定义
├── dashboard/
│   └── dashboard.py          # Streamlit 看板
└── PRD.md / TRD.md          # 文档
```

### 10.2 参考资料

- OpenClaw 官方文档
- Pydantic v2 最佳实践
- Qwen 3.5-plus 长文本处理

---

**文档版本**: 1.0  
**最后更新**: 2026-03-03
