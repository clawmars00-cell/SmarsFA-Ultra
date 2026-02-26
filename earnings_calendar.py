"""
Earnings Calendar - 财报日历
抓取最近半月的财报发布时间表
"""
import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict


def search_earnings_calendar(days: int = 15) -> List[Dict]:
    """
    搜索未来N天的财报发布时间
    
    Returns:
        List of {
            "stock": "AAPL",
            "date": "2026-02-28",
            "time": "after_close",  # after_close, before_open
            "expected_eps": 2.10,
            "expected_revenue": 85.0
        }
    """
    print(f"📅 Searching earnings calendar for next {days} days...")
    
    # 用 MCP 搜索
    cmd = [
        "/home/mars/.opencode/bin/opencode", "run",
        f"搜索未来{days}天即将发布财报的美股公司列表，包括股票代码、发布日期、预期EPS和营收"
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        
        output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        
        # 解析结果
        earnings = parse_earnings_calendar(output)
        
        print(f"📅 Found {len(earnings)} earnings")
        return earnings
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def parse_earnings_calendar(text: str) -> List[Dict]:
    """解析财报日历文本"""
    earnings = []
    
    # 简单的解析 - 提取股票代码和日期
    # 实际需要更复杂的解析
    lines = text.split('\n')
    
    for line in lines:
        # 匹配股票代码 (大写字母，3-5个)
        matches = re.findall(r'\b([A-Z]{3,5})\b', line)
        
        if matches and any(m in line for m in ['财报', 'EPS', 'Q', 'earnings']):
            # 提取日期
            date_match = re.search(r'(\d{1,2})[月/-](\d{1,2})', line)
            
            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                
                # 获取当前年份
                year = datetime.now().year
                
                earnings.append({
                    "stock": matches[0],
                    "date": f"{year}-{month:02d}-{day:02d}",
                    "expected_eps": None,
                    "expected_revenue": None,
                    "source": "search"
                })
    
    # 去重
    seen = set()
    unique = []
    for e in earnings:
        key = (e['stock'], e['date'])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    
    return unique


def get_upcoming_earnings() -> List[Dict]:
    """获取即将发布的财报列表"""
    return search_earnings_calendar(15)


if __name__ == "__main__":
    earnings = get_upcoming_earnings()
    print(json.dumps(earnings, indent=2, ensure_ascii=False))
