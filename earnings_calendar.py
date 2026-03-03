"""
Earnings Calendar - 财报日历

数据来源 (按优先级):
1. Yahoo Finance API (需要解决 JS 渲染问题)
2. MCP web_search (当前超时)
3. 预设主要公司列表 (当前使用)

未来优化:
- 使用 browser 工具自动抓取
- 接入 Finnhub/Alpha Vantage API
- 订阅 RSS feed
"""
from datetime import datetime
from typing import List, Dict


# 预设财报列表 (2026-02-27自动更新)
# 结构: 包含"上次已发布"和"下次预期"两个部分
MAJOR_EARNINGS = [
    # AAPL: 上次02-27已发布, 下次预计5月
    {"stock": "AAPL", "date": "2026-02-27", "expected_eps": 2.84, "expected_revenue": 143.8, "market_cap": 3500e9, 
     "reported_eps": 2.84, "reported_quarter": "2025-12", "reported_revenue": 143.8, "status": "reported"},
    {"stock": "AAPL", "date": "2026-05-01", "expected_eps": 3.0, "expected_revenue": 150.0, "market_cap": 3500e9, 
     "status": "upcoming", "note": "Q2 FY2026 预期"},
    
    # CRM: 上次02-28, 下次预计5月
    {"stock": "CRM", "date": "2026-02-28", "expected_eps": 2.60, "expected_revenue": 9.5, "market_cap": 320e9,
     "reported_eps": 2.19, "reported_quarter": "2025-10", "reported_revenue": 10.3, "status": "reported"},
    
    # NVDA: 上次02-25已发布(Q4 FY2026), 下次预计5月
    {"stock": "NVDA", "date": "2026-02-25", "expected_eps": 0.95, "expected_revenue": 72.0, "market_cap": 3000e9, 
     "reported_eps": 1.30, "reported_quarter": "2026-01", "reported_revenue": 68.1, 
     "note": "Q4 FY2026, 2月25日发布, 超预期", "status": "reported"},
    {"stock": "NVDA", "date": "2026-05-20", "expected_eps": 10.5, "expected_revenue": 80.0, "market_cap": 3000e9, 
     "status": "upcoming", "note": "Q1 FY2027 预期"},
    
    # SE: 下次03-03即将发布
    {"stock": "SE", "date": "2026-03-03", "expected_eps": -0.08, "expected_revenue": 0.35, "market_cap": 15e9,
     "status": "upcoming"},
    {"stock": "SE", "date": "2025-09-30", "expected_eps": 0.50, "expected_revenue": 5.5, 
     "reported_eps": 0.59, "reported_quarter": "2025-09", "reported_revenue": 6.0, "status": "reported"},
    
    # AVGO: 下次03-05
    {"stock": "AVGO", "date": "2026-03-05", "expected_eps": 1.45, "expected_revenue": 14.0, "market_cap": 800e9,
     "status": "upcoming"},
    {"stock": "AVGO", "date": "2025-10-31", "expected_eps": 1.45, "expected_revenue": 14.0,
     "reported_eps": 1.74, "reported_quarter": "2025-10", "reported_revenue": 18.0, "status": "reported"},
    
    # COST: 下次03-05
    {"stock": "COST", "date": "2026-03-05", "expected_eps": 3.80, "expected_revenue": 72.0, "market_cap": 400e9,
     "status": "upcoming"},
    {"stock": "COST", "date": "2025-11-30", "expected_eps": 3.80, "expected_revenue": 72.0,
     "reported_eps": 4.50, "reported_quarter": "2025-11", "reported_revenue": 67.3, "status": "reported"},
    
    # WMT: 下次03-06
    {"stock": "WMT", "date": "2026-03-06", "expected_eps": 0.65, "expected_revenue": 180.0, "market_cap": 650e9,
     "status": "upcoming"},
    {"stock": "WMT", "date": "2026-01-31", "expected_eps": 0.65, "expected_revenue": 180.0,
     "reported_eps": 0.53, "reported_quarter": "2026-01", "reported_revenue": 169.0, "status": "reported"},
    
    # TGT: 下次03-06
    {"stock": "TGT", "date": "2026-03-06", "expected_eps": 1.95, "expected_revenue": 31.0, "market_cap": 50e9,
     "status": "upcoming"},
    {"stock": "TGT", "date": "2025-10-31", "expected_eps": 1.95, "expected_revenue": 31.0,
     "reported_eps": 1.51, "reported_quarter": "2025-10", "reported_revenue": 25.3, "status": "reported"},
    
    # ORCL: 下次03-10
    {"stock": "ORCL", "date": "2026-03-10", "expected_eps": 1.40, "expected_revenue": 14.0, "market_cap": 450e9,
     "status": "upcoming"},
    {"stock": "ORCL", "date": "2025-11-30", "expected_eps": 1.40, "expected_revenue": 14.0,
     "reported_eps": 2.10, "reported_quarter": "2025-11", "reported_revenue": 16.1, "status": "reported"},
    
    # ADBE: 下次03-11
    {"stock": "ADBE", "date": "2026-03-11", "expected_eps": 4.50, "expected_revenue": 5.8, "market_cap": 250e9,
     "status": "upcoming"},
    {"stock": "ADBE", "date": "2025-11-30", "expected_eps": 4.50, "expected_revenue": 5.8,
     "reported_eps": 4.45, "reported_quarter": "2025-11", "reported_revenue": 6.2, "status": "reported"},
    
    # AMD: 下次03-11
    {"stock": "AMD", "date": "2026-03-11", "expected_eps": 0.85, "expected_revenue": 7.8, "market_cap": 180e9,
     "status": "upcoming"},
    {"stock": "AMD", "date": "2025-12-31", "expected_eps": 0.75, "expected_revenue": 7.8,
     "reported_eps": 0.70, "reported_quarter": "2025-12", "reported_revenue": 10.3, "status": "reported"},
    
    # MRVL: 下次03-11
    {"stock": "MRVL", "date": "2026-03-11", "expected_eps": 0.42, "expected_revenue": 1.8, "market_cap": 90e9,
     "status": "upcoming"},
    {"stock": "MRVL", "date": "2025-10-31", "expected_eps": 0.42, "expected_revenue": 1.8,
     "reported_eps": 2.20, "reported_quarter": "2025-10", "reported_revenue": 2.1, "status": "reported"},
    
    # CSCO: 下次03-12
    {"stock": "CSCO", "date": "2026-03-12", "expected_eps": 0.95, "expected_revenue": 14.0, "market_cap": 220e9,
     "status": "upcoming"},
    {"stock": "CSCO", "date": "2026-01-31", "expected_eps": 0.95, "expected_revenue": 14.0,
     "reported_eps": 0.80, "reported_quarter": "2026-01", "reported_revenue": 14.0, "status": "reported"},
    
    # PANW: 下次03-13
    {"stock": "PANW", "date": "2026-03-13", "expected_eps": 0.35, "expected_revenue": 2.1, "market_cap": 120e9,
     "status": "upcoming"},
    {"stock": "PANW", "date": "2025-10-31", "expected_eps": 0.35, "expected_revenue": 2.1,
     "reported_eps": 0.47, "reported_quarter": "2025-10", "reported_revenue": 2.5, "status": "reported"},
]


def get_upcoming_earnings(days: int = 14) -> List[Dict]:
    today = datetime.now()
    result = []
    for e in MAJOR_EARNINGS:
        date = datetime.strptime(e['date'], "%Y-%m-%d")
        days_ahead = (date - today).days
        if 0 <= days_ahead <= days:
            result.append(e)
    return sorted(result, key=lambda x: x['date'])
