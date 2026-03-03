# SmarsFA-Ultra 财报日历爬虫
# 自动获取美股财报发布日期

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import aiohttp
from dateutil import parser as date_parser

# 尝试导入，如果失败则使用基础实现
try:
    from .models.earnings import EarningsCalendar, EarningsCalendarItem
except ImportError:
    from models.earnings import EarningsCalendar, EarningsCalendarItem


class EarningsCalendarCrawler:
    """财报日历爬虫 - 从 Yahoo Finance 获取财报发布日期"""
    
    def __init__(self, cache_dir: str = "./storage/cache"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "earnings_calendar.json")
        os.makedirs(cache_dir, exist_ok=True)
        
    async def get_calendar(
        self, 
        days_ahead: int = 7,
        use_cache: bool = True
    ) -> EarningsCalendar:
        """
        获取未来 N 天的财报日历
        
        Args:
            days_ahead: 向前看几天
            use_cache: 是否使用缓存
            
        Returns:
            EarningsCalendar 对象
        """
        # 检查缓存
        if use_cache:
            cached = self._load_cache()
            if cached:
                # 检查缓存是否过期 (4小时内有效)
                if self._is_cache_valid(cached):
                    print(f"[EarningsCalendar] 使用缓存，共 {len(cached.items)} 条")
                    return cached
        
        # 抓取新数据
        print(f"[EarningsCalendar] 正在获取未来 {days_ahead} 天的财报日历...")
        calendar = await self._fetch_from_yahoo(days_ahead)
        
        # 保存缓存
        self._save_cache(calendar)
        
        return calendar
    
    async def _fetch_from_yahoo(self, days_ahead: int) -> EarningsCalendar:
        """从 Yahoo Finance 获取财报日历"""
        
        # Yahoo Finance Earnings Calendar API (模拟)
        # 实际使用 yfinance 库
        try:
            import yfinance as yf
            
            # 获取即将发布财报的热门股票
            # 注意: yfinance 没有直接的日历 API，我们用已知股票列表模拟
            # 实际生产中可以使用第三方 API
            
            today = datetime.now()
            end_date = today + timedelta(days=days_ahead)
            
            # 常用股票列表 (可以从 watchlist 加载)
            tickers = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
                "BRK-B", "JNJ", "V", "PG", "JPM", "UNH", "HD", "MA",
                "DIS", "PYPL", "BAC", "NFLX", "ADBE", "CRM", "INTC",
                "CSCO", "PFE", "TMO", "ABT", "VZ", "MRK", "KO"
            ]
            
            items = []
            
            # 获取每只股票的下次财报日期
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    # 获取财报日期
                    earnings_dates = stock.earnings_dates
                    
                    if earnings_dates is not None and not earnings_dates.empty:
                        # 获取最近一次未来日期
                        for idx, row in earnings_dates.iterrows():
                            if isinstance(idx, datetime) and idx >= today and idx <= end_date:
                                items.append(EarningsCalendarItem(
                                    ticker=ticker,
                                    company_name=stock.info.get('shortName', ticker),
                                    fiscal_quarter=self._guess_quarter(idx),
                                    report_date=idx.strftime("%Y-%m-%d"),
                                    eps_estimate=row.get('EPS Estimate') if 'EPS Estimate' in row else None,
                                    revenue_estimate=row.get('Revenue Estimate') if 'Revenue Estimate' in row else None,
                                    status="upcoming"
                                ))
                                break
                except Exception as e:
                    # 忽略单个股票的错误，继续处理下一个
                    continue
            
            calendar = EarningsCalendar(
                start_date=today.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                items=items
            )
            
            print(f"[EarningsCalendar] 获取到 {len(items)} 条财报日历")
            return calendar
            
        except ImportError as e:
            print(f"[EarningsCalendar] yfinance 未安装: {e}")
            return self._get_mock_calendar(days_ahead)
    
    def _guess_quarter(self, date: datetime) -> str:
        """根据日期猜测财报季度"""
        month = date.month
        year = date.year
        
        if month in [1, 2, 3]:
            return f"{year} Q4"
        elif month in [4, 5, 6]:
            return f"{year} Q1"
        elif month in [7, 8, 9]:
            return f"{year} Q2"
        else:
            return f"{year} Q3"
    
    def _get_mock_calendar(self, days_ahead: int) -> EarningsCalendar:
        """获取模拟数据 (用于测试)"""
        today = datetime.now()
        
        mock_data = [
            {"ticker": "AAPL", "date": 2, "quarter": "2026 Q1"},
            {"ticker": "MSFT", "date": 3, "quarter": "2026 Q2"},
            {"ticker": "NVDA", "date": 5, "quarter": "2026 Q4"},
            {"ticker": "GOOGL", "date": 7, "quarter": "2026 Q1"},
            {"ticker": "AMZN", "date": 8, "quarter": "2026 Q1"},
            {"ticker": "TSLA", "date": 10, "quarter": "2026 Q1"},
            {"ticker": "META", "date": 12, "quarter": "2026 Q1"},
        ]
        
        items = []
        for item in mock_data:
            report_date = today + timedelta(days=item["date"])
            if item["date"] <= days_ahead:
                items.append(EarningsCalendarItem(
                    ticker=item["ticker"],
                    company_name=item["ticker"],
                    fiscal_quarter=item["quarter"],
                    report_date=report_date.strftime("%Y-%m-%d"),
                    eps_estimate=None,
                    revenue_estimate=None,
                    status="upcoming"
                ))
        
        return EarningsCalendar(
            start_date=today.strftime("%Y-%m-%d"),
            end_date=(today + timedelta(days=days_ahead)).strftime("%Y-%m-%d"),
            items=items
        )
    
    def _load_cache(self) -> Optional[EarningsCalendar]:
        """加载缓存"""
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                return EarningsCalendar(**data)
        except Exception as e:
            print(f"[EarningsCalendar] 缓存加载失败: {e}")
            return None
    
    def _save_cache(self, calendar: EarningsCalendar):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(calendar.model_dump(), f, indent=2, default=str)
        except Exception as e:
            print(f"[EarningsCalendar] 缓存保存失败: {e}")
    
    def _is_cache_valid(self, calendar: EarningsCalendar) -> bool:
        """检查缓存是否有效 (4小时)"""
        if not calendar.fetched_at:
            return False
        
        cache_time = calendar.fetched_at
        if isinstance(cache_time, str):
            cache_time = date_parser.parse(cache_time)
            
        age = datetime.now() - cache_time
        return age.total_seconds() < 4 * 3600  # 4小时
    
    def check_and_trigger(self, calendar: EarningsCalendar) -> list[EarningsCalendarItem]:
        """
        检查今天/明天有谁发财报
        
        Returns:
            需要触发分析的股票列表
        """
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        triggered = []
        
        for item in calendar.items:
            if item.status != "upcoming":
                continue
                
            report_date = datetime.strptime(item.report_date, "%Y-%m-%d").date()
            
            if report_date == today or report_date == tomorrow:
                triggered.append(item)
                print(f"[EarningsCalendar] 触发: {item.ticker} {item.report_date}")
        
        return triggered


async def main():
    """测试函数"""
    crawler = EarningsCalendarCrawler()
    
    # 获取未来7天日历
    calendar = await crawler.get_calendar(days_ahead=7)
    
    print(f"\n📅 未来7天财报日历 (共 {len(calendar.items)} 条):")
    print("-" * 60)
    
    for item in calendar.items:
        print(f"{item.report_date} | {item.ticker:6} | {item.fiscal_quarter}")
    
    # 检查今天/明天
    today_trigger = crawler.check_and_trigger(calendar)
    print(f"\n⚡ 今天/明天触发: {[i.ticker for i in today_trigger]}")
    
    return calendar


if __name__ == "__main__":
    asyncio.run(main())
