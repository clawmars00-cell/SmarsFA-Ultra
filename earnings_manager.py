"""
Earnings Manager - 财报生命周期管理
逻辑:
1. 上一次财报: 日期 + 实际数据 + vs 预期 → 分析
2. 下一次财报: 日期 + 市场预期 → 更新日历
3. 发布日: 刷新获取实际数据 → 分析报告
4. 一周后: 标记历史，开始下一轮
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf


class EarningsManager:
    """
    财报生命周期管理器
    """
    
    def __init__(self, calendar: List[Dict] = None):
        # 日历: [{"stock": "NVDA", "date": "2026-02-25", "expected_eps": 0.95, ...}]
        self.calendar = calendar or []
        self._build_index()
    
    def _build_index(self):
        """构建索引"""
        self._by_stock = {e['stock']: e for e in self.calendar}
    
    def get_last_earnings(self, symbol: str) -> Dict:
        """获取上一次财报 (今天之前的最近一次)"""
        symbol = symbol.upper()
        today = datetime.now()
        
        # 找今天之前的最近一次
        past = []
        for entry in self.calendar:
            if entry.get('stock', '').upper() == symbol:
                date_str = entry.get('date', '')
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    if date <= today:
                        past.append(entry)
                except:
                    pass
        
        if past:
            # 返回最近的
            entry = max(past, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
            return {
                'stock': symbol.upper(),
                'date': entry.get('date'),
                'expected_eps': entry.get('expected_eps'),
                'expected_revenue': entry.get('expected_revenue'),
                'reported_eps': entry.get('reported_eps'),
                'reported_revenue': entry.get('reported_revenue'),
                'quarter': entry.get('reported_quarter'),
                'status': entry.get('status', 'unknown'),
                'is_beat': self._calc_beat(entry)
            }
        
        return None
    
    def _calc_beat(self, entry: Dict) -> Optional[bool]:
        """计算是否超预期"""
        exp_eps = entry.get('expected_eps')
        rep_eps = entry.get('reported_eps')
        if exp_eps and rep_eps:
            return rep_eps > exp_eps
        return None
    
    def get_next_earnings(self, symbol: str, yf_ticker=None) -> Dict:
        """获取下一次财报 (从日历或API)
        
        逻辑: 遍历所有财报，取今天之后的最近一次
        """
        symbol = symbol.upper()
        
        # 找所有该股票的财报，取今天之后的最近一次
        upcoming = []
        for entry in self.calendar:
            if entry.get('stock', '').upper() == symbol:
                date_str = entry.get('date', '')
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    today = datetime.now()
                    
                    # 今天之后 = 下次
                    if date >= today:
                        upcoming.append({
                            'stock': symbol,
                            'date': date_str,
                            'expected_eps': entry.get('expected_eps'),
                            'expected_revenue': entry.get('expected_revenue'),
                            'days_until': (date - today).days
                        })
                except:
                    pass
        
        if upcoming:
            # 返回最近的
            return min(upcoming, key=lambda x: x['days_until'])
        
        return None
    
    def refresh_earnings(self, symbol: str) -> Dict:
        """刷新获取最新财报数据 (从Yahoo或搜索)"""
        ticker = yf.Ticker(symbol.upper())
        
        # 1. 获取最新季度财报
        q = ticker.quarterly_financials
        result = {
            'stock': symbol.upper(),
            'refreshed_at': datetime.now().isoformat(),
            'source': 'yahoo'
        }
        
        if q is not None and not q.empty:
            col = q.columns[0]  # 最新季度
            result['quarter_date'] = str(col)
            result['revenue'] = q.loc['Total Revenue', col] if 'Total Revenue' in q.index else None
            result['eps'] = q.loc['Diluted EPS', col] if 'Diluted EPS' in q.index else None
            result['net_income'] = q.loc['Net Income', col] if 'Net Income' in q.index else None
        
        # 2. 检查是否需要从日历获取最新数据 (如果Yahoo没更新)
        entry = self._by_stock.get(symbol.upper())
        if entry and entry.get('reported_revenue'):
            # 日历有新数据，优先使用
            if not result.get('revenue') or result.get('revenue') != entry.get('reported_revenue') * 1e9:
                result['revenue'] = entry.get('reported_revenue', 0) * 1e9
                result['eps'] = entry.get('reported_eps')
                result['quarter_date'] = entry.get('reported_quarter')
                result['source'] = 'calendar'
        
        return result
    
    def is_earnings_due(self, symbol: str) -> bool:
        """检查是否到了财报发布时间"""
        entry = self._by_stock.get(symbol.upper())
        if not entry:
            return False
        
        date_str = entry.get('date', '')
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now()
            
            # 已发布但未刷新数据
            if date <= today and entry.get('status') == 'upcoming':
                return True
        except:
            pass
        return False
    
    def mark_as_reported(self, symbol: str, actual_data: Dict):
        """标记为已发布并更新数据"""
        entry = self._by_stock.get(symbol.upper())
        if entry:
            entry['status'] = 'reported'
            entry['reported_eps'] = actual_data.get('eps')
            entry['reported_revenue'] = actual_data.get('revenue', 0) / 1e9
            entry['reported_at'] = datetime.now().isoformat()
    
    def get_lifecycle_status(self, symbol: str) -> Dict:
        """获取股票当前的生命周期状态"""
        last = self.get_last_earnings(symbol)
        next_e = self.get_next_earnings(symbol)
        
        status = {
            'stock': symbol.upper(),
            'phase': 'unknown',
            'last': last,
            'next': next_e
        }
        
        # 判断当前阶段
        if last and last.get('status') == 'reported':
            if next_e:
                status['phase'] = 'waiting_next'  # 等下次
            else:
                status['phase'] = 'need_calendar_update'  # 需要更新日历
        elif self.is_earnings_due(symbol):
            status['phase'] = 'publishing'  # 正在发布
        
        return status


# 测试
if __name__ == "__main__":
    from earnings_calendar import MAJOR_EARNINGS
    
    em = EarningsManager(MAJOR_EARNINGS)
    
    # 测试 NVDA
    print("=== NVDA 生命周期状态 ===")
    status = em.get_lifecycle_status('NVDA')
    print(f"阶段: {status['phase']}")
    print(f"上次: {status['last']}")
    print(f"下次: {status['next']}")
    
    print("\n=== 刷新数据 ===")
    fresh = em.refresh_earnings('NVDA')
    print(f"数据: {fresh}")
