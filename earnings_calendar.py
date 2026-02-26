"""
Earnings Calendar - 财报日历
主要公司 + MCP 补充搜索
"""
import subprocess
import re
from datetime import datetime, timedelta
from typing import List, Dict


# 主要公司财报日期 (预设)
MAJOR_EARNINGS = [
    {"stock": "NVDA", "date": "2026-02-26", "expected_eps": 0.89, "expected_revenue": 68.1, "market_cap": 3000e9},
    {"stock": "AAPL", "date": "2026-02-27", "expected_eps": 2.84, "expected_revenue": 143.8, "market_cap": 3500e9},
    {"stock": "MSFT", "date": "2026-01-30", "expected_eps": 3.20, "expected_revenue": 69.0, "market_cap": 3200e9},
    {"stock": "GOOGL", "date": "2026-02-05", "expected_eps": 2.10, "expected_revenue": 96.5, "market_cap": 2100e9},
    {"stock": "AMZN", "date": "2026-02-07", "expected_eps": 1.45, "expected_revenue": 170.0, "market_cap": 2400e9},
    {"stock": "META", "date": "2026-01-30", "expected_eps": 6.70, "expected_revenue": 40.0, "market_cap": 1400e9},
    {"stock": "TSLA", "date": "2026-01-30", "expected_eps": 0.81, "expected_revenue": 23.5, "market_cap": 1200e9},
    {"stock": "AMD", "date": "2026-01-29", "expected_eps": 0.80, "expected_revenue": 7.2, "market_cap": 180e9},
    {"stock": "INTC", "date": "2026-01-30", "expected_eps": 0.35, "expected_revenue": 14.0, "market_cap": 120e9},
    {"stock": "AVGO", "date": "2026-03-06", "expected_eps": 1.45, "expected_revenue": 14.0, "market_cap": 800e9},
    {"stock": "NFLX", "date": "2026-01-28", "expected_eps": 5.80, "expected_revenue": 10.0, "market_cap": 350e9},
    {"stock": "CRM", "date": "2026-02-28", "expected_eps": 2.60, "expected_revenue": 9.5, "market_cap": 320e9},
    {"stock": "ORCL", "date": "2026-03-10", "expected_eps": 1.40, "expected_revenue": 14.0, "market_cap": 450e9},
    {"stock": "UBER", "date": "2026-02-13", "expected_eps": 0.45, "expected_revenue": 10.0, "market_cap": 150e9},
    {"stock": "PYPL", "date": "2026-02-07", "expected_eps": 1.20, "expected_revenue": 8.0, "market_cap": 80e9},
]


def get_major_earnings() -> List[Dict]:
    """获取主要公司财报"""
    today = datetime.now()
    result = []
    for e in MAJOR_EARNINGS:
        date = datetime.strptime(e['date'], "%Y-%m-%d")
        if date >= today - timedelta(days=7):
            result.append(e)
    return sorted(result, key=lambda x: x['date'])


def search_with_mcp() -> List[Dict]:
    """用 MCP 搜索补充"""
    print("🔍 MCP searching for more earnings...")
    
    cmd = ["/home/mars/.opencode/bin/opencode", "run", 
           "列出2026年2月-3月发布财报的美股大公司，格式: 股票代码:日期:预期EPS"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
        
        # 解析结果
        earnings = []
        for line in output.split('\n'):
            # 格式: AAPL:2026-02-27:2.84
            match = re.search(r'([A-Z]{3,5})[📅:\s]+(\d{1,2})/(\d{1,2})[📅:\s]+EPS[:\s]+(\d+\.?\d*)', line)
            if match:
                stock = match.group(1)
                month = int(match.group(2))
                day = int(match.group(3))
                eps = float(match.group(4))
                
                earnings.append({
                    "stock": stock,
                    "date": f"2026-{month:02d}-{day:02d}",
                    "expected_eps": eps,
                    "market_cap": 100e9,  # 默认假设 >$100B
                    "source": "mcp"
                })
        
        print(f"🔍 MCP found: {len(earnings)}")
        return earnings
        
    except Exception as e:
        print(f"❌ MCP error: {e}")
        return []


def get_all_upcoming_earnings() -> List[Dict]:
    """获取所有即将发布的财报"""
    # 主要公司
    earnings = get_major_earnings()
    
    # MCP 补充 (暂时跳过，避免超时)
    # additional = search_with_mcp()
    
    # 合并
    # all_earnings = earnings + additional
    
    # 去重
    seen = set()
    unique = []
    for e in earnings:
        if e['stock'] not in seen:
            seen.add(e['stock'])
            unique.append(e)
    
    return sorted(unique, key=lambda x: x['date'])


if __name__ == "__main__":
    earnings = get_all_upcoming_earnings()
    print(f"Upcoming earnings: {len(earnings)}")
    for e in earnings:
        cap = e.get('market_cap', 0) / 1e9
        print(f"  {e['stock']}: {e['date']}, EPS: {e.get('expected_eps')}, Cap: ${cap:.0f}B")
