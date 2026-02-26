"""
Earnings Calendar - 预设财报列表 + MCP 补充
"""
from datetime import datetime
from typing import List, Dict


# 预设财报列表 (主要来源)
MAJOR_EARNINGS = [
    {"stock": "AAPL", "date": "2026-02-27", "expected_eps": 2.84, "expected_revenue": 143.8, "market_cap": 3500e9},
    {"stock": "CRM", "date": "2026-02-28", "expected_eps": 2.60, "expected_revenue": 9.5, "market_cap": 320e9},
    {"stock": "SE", "date": "2026-03-03", "expected_eps": -0.08, "expected_revenue": 0.35, "market_cap": 15e9},
    {"stock": "AVGO", "date": "2026-03-05", "expected_eps": 1.45, "expected_revenue": 14.0, "market_cap": 800e9},
    {"stock": "COST", "date": "2026-03-05", "expected_eps": 3.80, "expected_revenue": 72.0, "market_cap": 400e9},
    {"stock": "WMT", "date": "2026-03-06", "expected_eps": 0.65, "expected_revenue": 180.0, "market_cap": 650e9},
    {"stock": "TGT", "date": "2026-03-06", "expected_eps": 1.95, "expected_revenue": 31.0, "market_cap": 50e9},
    {"stock": "NVDA", "date": "2026-03-06", "expected_eps": 0.95, "expected_revenue": 72.0, "market_cap": 3000e9},
    {"stock": "ORCL", "date": "2026-03-10", "expected_eps": 1.40, "expected_revenue": 14.0, "market_cap": 450e9},
    {"stock": "ADBE", "date": "2026-03-11", "expected_eps": 4.50, "expected_revenue": 5.8, "market_cap": 250e9},
    {"stock": "AMD", "date": "2026-03-11", "expected_eps": 0.85, "expected_revenue": 7.8, "market_cap": 180e9},
    {"stock": "MRVL", "date": "2026-03-11", "expected_eps": 0.42, "expected_revenue": 1.8, "market_cap": 90e9},
    {"stock": "CSCO", "date": "2026-03-12", "expected_eps": 0.95, "expected_revenue": 14.0, "market_cap": 220e9},
    {"stock": "PANW", "date": "2026-03-13", "expected_eps": 0.35, "expected_revenue": 2.1, "market_cap": 120e9},
]


def get_upcoming_earnings(days: int = 14) -> List[Dict]:
    """获取未来N天财报"""
    today = datetime.now()
    
    result = []
    for e in MAJOR_EARNINGS:
        date = datetime.strptime(e['date'], "%Y-%m-%d")
        days_ahead = (date - today).days
        
        if 0 <= days_ahead <= days:
            result.append(e)
    
    return sorted(result, key=lambda x: x['date'])


if __name__ == "__main__":
    earnings = get_upcoming_earnings(14)
    print(f"未来2周财报 ({len(earnings)}家):\n")
    
    for e in earnings:
        cap = e['market_cap'] / 1e9
        print(f"{e['date']} | {e['stock']:5} | EPS: {e['expected_eps']:+.2f} | Rev: {e['expected_revenue']:.1f}B | Cap: ${cap:.0f}B")
