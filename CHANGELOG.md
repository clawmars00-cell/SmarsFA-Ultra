# SmarsFA v1.1.0 更新日志

## 2026-02-27 重大更新

### ✨ 新增功能

#### 1. WhatsApp消息命令支持
通过WhatsApp消息添加自选股和获取分析：
- `添加 AAPL MSFT` - 添加自选股
- `删除 TSLA` - 删除自选股
- `列表` - 查看自选股列表（含实时价格）
- `分析 AAPL` - 分析单只股票
- `分析自选` - 分析所有自选股
- `日历` - 查看即将发布的财报
- `大盘` - 查看市场概况

#### 2. WhatsApp友好汇报格式
- 优化的IM消息格式
- 实时价格显示
- 多消息卡片输出
- 简洁的emoji标识

#### 3. 丰富的财报数据 + 深度分析
- 营收、EPS、净利润数据
- 利润率、增长率指标
- 未来展望（next_quarter_outlook）
- 催化剂（catalyst）
- 风险因素（risk_factors）
- SWOT深度分析（优势/劣势/机会/威胁）
- 12个月目标价

#### 4. 性能大幅提升
- 并行数据获取（AsyncDataFetcher）
- 缓存机制（PerformanceCache）
- 批量价格/财务/期权数据获取
- 线程池并发处理

### 📁 新增文件
- `whatsapp_formatter.py` - WhatsApp格式器
- `whatsapp_handler.py` - WhatsApp消息处理器
- `watchlist_manager.py` - 自选股管理
- `report_generator.py` - 报告生成器
- `data_fetcher.py` - 高性能数据获取器

### 🔧 API端点
```
POST /api/whatsapp          - 处理WhatsApp消息
GET  /api/watchlist         - 获取自选股列表
POST /api/watchlist/add     - 添加自选股
DELETE /api/watchlist/{stock} - 删除自选股
POST /api/watchlist/analyze - 分析所有自选股
GET  /api/report/formatted  - 获取格式化报告
```

### 🚀 性能指标
- 并行分析: ~40秒完成单只股票完整分析
- 批量价格获取: ~1秒获取8只股票
- 缓存机制: 5分钟TTL避免重复请求

### 📝 使用示例
```
# WhatsApp消息
添加 AAPL TSLA NVDA

# 响应
✅ 已添加: AAPL, TSLA, NVDA

# 获取列表（带实时价格）
列表

# 响应
⭐ *自选股 (3只)*
🔴 AAPL $272.95 (-0.47%)
🔴 TSLA $185.00 (-2.30%)
🔴 NVDA $184.89 (-5.49%)

# 分析自选
分析自选

# 响应
📊 分析完成 (3只)
🟢 BUY: 2 | 🟡 HOLD: 1
🟢 AAPL $272.95
   BUY · 置信度 75%
   营收: $50.0B
   🔮 下季度: Positive
```
