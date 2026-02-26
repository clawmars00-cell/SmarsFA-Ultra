# FinancialParsingSubAgent - 财报解析专家

## 任务
解析财报文本，提取关键财务数据。

## 输入
```json
{
  "stock": "TSLA",
  "quarter": "Q4 2025",
  "raw_text": "财报全文...",
  "context": {},
  "previous_outputs": {}
}
```

## 输出协议
```json
{
  "module": "financial_parsing",
  "version": "1.0",
  "confidence": 0.0-1.0,
  "key_findings": [],
  "structured_data": {
    "revenue": 0,
    "revenue_growth_yoy": 0.0,
    "eps": 0.0,
    "eps_beat_percent": 0.0,
    "gross_margin": 0.0,
    "operating_margin": 0.0,
    "guidance": "positive|negative|neutral"
  },
  "risk_flags": []
}
```
