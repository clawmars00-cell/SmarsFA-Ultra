"""
Earnings Calendar - 财报日历
抓取所有市值>10亿美金的近期财报发布
"""
import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict


def search_all_earnings(days: int = 15) -> List[Dict]:
    """
    搜索未来N天所有市值>10亿美金的财报
    
    Returns:
        List of {
            "stock": "AAPL",
            "date": "2026-02-28",
            "market_cap": 3000e9,  # 3000B
            "expected_eps": 2.10,
            "expected_revenue": 85.0
        }
    """
    print(f"📅 Searching ALL earnings (>$1B market cap) next {days} days...")
    
    # 用 MCP 搜索
    cmd = [
        "/home/mars/.opencode/bin/opencode", "run",
        f"""搜索未来{days}天即将发布财报的所有美股公司。
        
要求:
1. 股票代码和日期
2. 市值(必须>100亿美元)
3. 预期EPS和营收(如果有)

列出所有符合条件的公司，格式:
- 股票代码: XXX, 日期: X月X日, 市值: XXXB, 预期EPS: X.XX"""
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        
        output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        
        # 解析结果
        earnings = parse_earnings(output)
        
        print(f"📅 Found {len(earnings)} earnings (>$10B)")
        return earnings
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def parse_earnings(text: str) -> List[Dict]:
    """解析财报日历文本"""
    earnings = []
    lines = text.split('\n')
    
    current_stock = None
    
    for line in lines:
        line = line.strip()
        
        # 匹配股票代码
        stock_match = re.search(r'([A-Z]{3,5})', line)
        
        if stock_match:
            current_stock = stock_match.group(1)
        
        # 跳过无关行
        if not any(k in line for k in ['财报', 'Q', ' earnings', 'EPS', '日期', '市值', 'Market']):
            continue
        
        # 提取日期
        date_match = re.search(r'(\d{1,2})[月/-](\d{1,2})', line)
        
        # 提取市值
        cap_match = re.search(r'(\d+\.?\d*)\s*[Bb]', line)
        
        # 提取预期EPS
        eps_match = re.search(r'EPS[:\s]+(\d+\.?\d*)', line, re.I)
        
        # 提取预期营收
        rev_match = re.search(r'[营收Revenue]+[:\s]+(\d+\.?\d*)\s*[Bb]?', line, re.I)
        
        if current_stock and date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            year = datetime.now().year
            
            # 过滤市值>10B
            market_cap = float(cap_match.group(1)) * 1e9 if cap_match else None
            
            earnings.append({
                "stock": current_stock,
                "date": f"{year}-{month:02d}-{day:02d}",
                "market_cap": market_cap,
                "expected_eps": float(eps_match.group(1)) if eps_match else None,
                "expected_revenue": float(rev_match.group(1)) if rev_match else None,
                "source": "mcp_search"
            })
    
    # 过滤市值>10B
    filtered = [e for e in earnings if e.get('market_cap') and e['market_cap'] > 10e9]
    
    # 去重
    seen = set()
    unique = []
    for e in filtered:
        key = e['stock']
        if key not in seen:
            seen.add(key)
            unique.append(e)
    
    return unique


def get_all_upcoming_earnings() -> List[Dict]:
    """获取所有即将发布的财报"""
    return search_all_earnings(15)


if __name__ == "__main__":
    earnings = get_all_upcoming_earnings()
    print(json.dumps(earnings[:20], indent=2, ensure_ascii=False))
