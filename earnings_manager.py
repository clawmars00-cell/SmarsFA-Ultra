"""
Earnings Manager - 财报生命周期管理 (重构版)
逻辑:
1. 上一次财报: 日期 + 实际数据 + vs 预期 → 分析
2. 下一次财报: 日期 + 市场预期 → 更新日历
3. 发布日: 刷新获取实际数据 → 分析报告
4. 一周后: 标记历史，开始下一轮

重构特性:
- 重试机制 (装饰器) - tenacity + asyncio
- 断路保护 - CircuitBreaker 类
- 异步下载器 - aiohttp 并发抓取
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypeAlias
import asyncio
import logging
from functools import wraps

# 第三方库 (需要安装: pip install aiohttp tenacity)
try:
    import aiohttp
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )
    HAS_ASYNC_DEPS = True
except ImportError:
    HAS_ASYNC_DEPS = False

import yfinance as yf


# ============================================================
# PEP 695 类型别名
# ============================================================

EarningsEntry: TypeAlias = Dict[str, str | float | int | None]
CalendarEntries: TypeAlias = List[EarningsEntry]
RefreshResult: TypeAlias = Dict[str, str | float | None]
LifecycleStatus: TypeAlias = Dict[str, str | RefreshResult | EarningsEntry | None]


# ============================================================
# 日志配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# 断路保护 (Circuit Breaker)
# ============================================================

class CircuitBreaker:
    """
    断路器实现
    
    状态:
    - CLOSED: 正常, 允许请求
    - OPEN: 失败次数过多, 拒绝请求
    - HALF_OPEN: 尝试恢复, 允许少量请求
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._half_open_calls = 0
    
    @property
    def state(self) -> str:
        """获取当前状态 (自动状态转换)"""
        if self._state == "OPEN":
            # 检查是否需要转换到 HALF_OPEN
            if self._last_failure_time:
                elapsed = asyncio.get_event_loop().time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = "HALF_OPEN"
                    self._half_open_calls = 0
                    logger.info("CircuitBreaker: OPEN -> HALF_OPEN")
        return self._state
    
    def record_success(self):
        """记录成功, 复位断路器"""
        self._failure_count = 0
        if self._state != "CLOSED":
            self._state = "CLOSED"
            logger.info("CircuitBreaker: 复位为 CLOSED")
    
    def record_failure(self):
        """记录失败, 可能打开断路器"""
        self._failure_count += 1
        self._last_failure_time = asyncio.get_event_loop().time()
        
        if self._state == "HALF_OPEN":
            # HALF_OPEN 状态下失败, 重新打开
            self._state = "OPEN"
            logger.warning("CircuitBreaker: HALF_OPEN 失败, 重新打开")
        elif self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            logger.warning(f"CircuitBreaker: 失败次数 {self._failure_count} >= {self.failure_threshold}, 打开")
    
    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        state = self.state
        if state == "CLOSED":
            return True
        elif state == "HALF_OPEN":
            return self._half_open_calls < self.half_open_max_calls
        return False
    
    def __enter__(self):
        if not self.can_execute():
            raise CircuitBreakerOpenError(f"CircuitBreaker 当前状态: {self.state}")
        if self._state == "HALF_OPEN":
            self._half_open_calls += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
        return False


class CircuitBreakerOpenError(Exception):
    """断路器打开异常"""
    pass


# ============================================================
# 重试装饰器 (异步版本)
# ============================================================

def async_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exceptions: tuple = (Exception,),
):
    """
    异步重试装饰器
    
    使用 tenacity 库, 支持:
    - 指数退避 (exponential backoff)
    - 指定异常类型
    - 最大重试次数
    """
    if HAS_ASYNC_DEPS:
        decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
            retry=retry_if_exception_type(exceptions),
            reraise=True,
        )
        
        def decorator_func(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await decorator(func)(*args, **kwargs)
            return wrapper
        return decorator_func
    else:
        # 无依赖时的简单实现
        def decorator_func(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            wait_time = min(wait_min * (2 ** attempt), wait_max)
                            logger.warning(
                                f"重试 {attempt + 1}/{max_attempts}, "
                                f"等待 {wait_time}s: {e}"
                            )
                            await asyncio.sleep(wait_time)
                raise last_exception
            return wrapper
        return decorator_func


def sync_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exceptions: tuple = (Exception,),
):
    """
    同步重试装饰器 (用于非 async 函数)
    """
    if HAS_ASYNC_DEPS:
        decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
            retry=retry_if_exception_type(exceptions),
            reraise=True,
        )
        return decorator
    else:
        def decorator_func(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            wait_time = min(wait_min * (2 ** attempt), wait_max)
                            logger.warning(
                                f"重试 {attempt + 1}/{max_attempts}, "
                                f"等待 {wait_time}s: {e}"
                            )
                            import time
                            time.sleep(wait_time)
                raise last_exception
            return wrapper
        return decorator_func


# ============================================================
# 异步下载器
# ============================================================

class AsyncDownloader:
    """
    异步下载器 - 并发抓取多个数据源
    
    特性:
    - 连接池复用
    - 超时控制
    - 并发限制
    - 自动重试 (通过装饰器)
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: aiohttp.ClientSession | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
        )
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=2,
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
        )
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self._session:
            await self._session.close()
        return False
    
    @async_retry(max_attempts=3, wait_min=1.0, wait_max=5.0)
    async def fetch_json(self, url: str) -> Dict:
        """获取 JSON 数据 (带重试)"""
        if not self._session:
            raise RuntimeError("AsyncDownloader not initialized. Use 'async with'.")
        
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpenError(
                f"CircuitBreaker 打开, 跳过请求: {url}"
            )
        
        with self.circuit_breaker:
            async with self._semaphore:
                async with self._session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
    
    @async_retry(max_attempts=3, wait_min=1.0, wait_max=5.0)
    async def fetch_text(self, url: str) -> str:
        """获取文本数据 (带重试)"""
        if not self._session:
            raise RuntimeError("AsyncDownloader not initialized. Use 'async with'.")
        
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpenError(
                f"CircuitBreaker 打开, 跳过请求: {url}"
            )
        
        with self.circuit_breaker:
            async with self._semaphore:
                async with self._session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
    
    async def fetch_multiple(self, urls: List[str], fetch_func=None) -> List[Dict | str]:
        """
        并发获取多个 URL
        
        Args:
            urls: URL 列表
            fetch_func: 自定义获取函数, 默认 fetch_json
            
        Returns:
            结果列表 (顺序与 urls 一致)
        """
        if fetch_func is None:
            fetch_func = self.fetch_json
        
        async def safe_fetch(url: str, idx: int) -> tuple[int, Dict | str | Exception]:
            try:
                result = await fetch_func(url)
                return idx, result
            except Exception as e:
                logger.error(f"获取失败 {url}: {e}")
                return idx, e
        
        # 使用 gather 并发执行
        tasks = [safe_fetch(url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]


# ============================================================
# 财报管理器 (重构版)
# ============================================================

class EarningsManager:
    """
    财报生命周期管理器 (重构版)
    
    新增特性:
    - 异步刷新数据
    - 断路保护
    - 自动重试
    """
    
    def __init__(self, calendar: CalendarEntries = None):
        # 日历: [{"stock": "NVDA", "date": "2026-02-25", "expected_eps": 0.95, ...}]
        self.calendar: CalendarEntries = calendar or []
        self._build_index()
        self._downloader: AsyncDownloader | None = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30.0,
        )
    
    def _build_index(self):
        """构建索引"""
        self._by_stock: Dict[str, EarningsEntry] = {
            e['stock']: e for e in self.calendar
        }
    
    # -------------------- 同步方法 (保留兼容性) --------------------
    
    def get_last_earnings(self, symbol: str) -> EarningsEntry | None:
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
                except ValueError:
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
                'is_beat': self._calc_beat(entry),
            }
        
        return None
    
    def _calc_beat(self, entry: EarningsEntry) -> bool | None:
        """计算是否超预期"""
        exp_eps = entry.get('expected_eps')
        rep_eps = entry.get('reported_eps')
        if exp_eps and rep_eps:
            return rep_eps > exp_eps
        return None
    
    def get_next_earnings(self, symbol: str, yf_ticker=None) -> EarningsEntry | None:
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
                            'days_until': (date - today).days,
                        })
                except ValueError:
                    pass
        
        if upcoming:
            # 返回最近的
            return min(upcoming, key=lambda x: x['days_until'])
        
        return None
    
    @sync_retry(max_attempts=3, wait_min=1.0, wait_max=5.0)
    def refresh_earnings(self, symbol: str) -> RefreshResult:
        """刷新获取最新财报数据 (从Yahoo或搜索) - 同步版本带重试"""
        ticker = yf.Ticker(symbol.upper())
        
        # 1. 获取最新季度财报
        q = ticker.quarterly_financials
        result: RefreshResult = {
            'stock': symbol.upper(),
            'refreshed_at': datetime.now().isoformat(),
            'source': 'yahoo',
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
    
    async def refresh_earnings_async(self, symbol: str) -> RefreshResult:
        """刷新获取最新财报数据 - 异步版本
        
        使用断路保护，如果 Yahoo Finance 失败会自动跳过
        """
        if not self._circuit_breaker.can_execute():
            logger.warning(f"CircuitBreaker 打开, 跳过 {symbol} 的刷新")
            return {
                'stock': symbol.upper(),
                'error': 'circuit_breaker_open',
                'refreshed_at': datetime.now().isoformat(),
            }
        
        with self._circuit_breaker:
            try:
                # 异步获取 (这里仍使用 yfinance 同步调用，但可以在未来替换为异步 API)
                # yfinance 本身是同步的，我们在线程池中运行它
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.refresh_earnings(symbol)
                )
                self._circuit_breaker.record_success()
                return result
            except Exception as e:
                self._circuit_breaker.record_failure()
                logger.error(f"刷新 {symbol} 失败: {e}")
                raise
    
    async def refresh_multiple_async(
        self,
        symbols: List[str],
        max_concurrent: int = 3,
    ) -> Dict[str, RefreshResult]:
        """并发刷新多个股票的财报数据
        
        Args:
            symbols: 股票代码列表
            max_concurrent: 最大并发数
            
        Returns:
            {symbol: result} 字典
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def refresh_one(symbol: str) -> tuple[str, RefreshResult]:
            async with semaphore:
                try:
                    result = await self.refresh_earnings_async(symbol)
                    return symbol, result
                except Exception as e:
                    logger.error(f"刷新 {symbol} 失败: {e}")
                    return symbol, {
                        'stock': symbol,
                        'error': str(e),
                        'refreshed_at': datetime.now().isoformat(),
                    }
        
        # 并发执行
        tasks = [refresh_one(s) for s in symbols]
        results = await asyncio.gather(*tasks)
        
        return dict(results)
    
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
        except ValueError:
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
    
    def get_lifecycle_status(self, symbol: str) -> LifecycleStatus:
        """获取股票当前的生命周期状态"""
        last = self.get_last_earnings(symbol)
        next_e = self.get_next_earnings(symbol)
        
        status: LifecycleStatus = {
            'stock': symbol.upper(),
            'phase': 'unknown',
            'last': last,
            'next': next_e,
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


# ============================================================
# 测试
# ============================================================

async def test_async_features():
    """测试异步功能"""
    from earnings_calendar import MAJOR_EARNINGS
    
    print("=" * 60)
    print("测试: 异步刷新多只股票")
    print("=" * 60)
    
    em = EarningsManager(MAJOR_EARNINGS)
    
    # 测试并发刷新
    symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL']
    print(f"\n并发刷新: {symbols}")
    
    results = await em.refresh_multiple_async(symbols, max_concurrent=2)
    
    for symbol, result in results.items():
        print(f"\n{symbol}:")
        print(f"  EPS: {result.get('eps')}")
        print(f"  Revenue: {result.get('revenue')}")
        print(f"  Source: {result.get('source')}")
        if result.get('error'):
            print(f"  Error: {result.get('error')}")
    
    # 测试断路器
    print("\n" + "=" * 60)
    print("测试: 断路器")
    print("=" * 60)
    
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)
    
    # 模拟失败
    for i in range(5):
        try:
            with cb:
                print(f"尝试 {i + 1}: {cb.state}")
                if i < 2:
                    raise Exception("模拟失败")
        except CircuitBreakerOpenError as e:
            print(f"断路器打开: {e}")
        except Exception as e:
            print(f"记录失败: {e}")
    
    print(f"\n最终状态: {cb.state}")
    
    # 等待恢复
    print("\n等待断路器恢复...")
    await asyncio.sleep(6)
    print(f"恢复后状态: {cb.state}")
    
    print("\n✅ 所有测试完成!")


def test_sync():
    """测试同步功能 (保留兼容性)"""
    from earnings_calendar import MAJOR_EARNINGS
    
    print("=" * 60)
    print("测试: 同步功能")
    print("=" * 60)
    
    em = EarningsManager(MAJOR_EARNINGS)
    
    # 测试 NVDA
    print("\n=== NVDA 生命周期状态 ===")
    status = em.get_lifecycle_status('NVDA')
    print(f"阶段: {status['phase']}")
    print(f"上次: {status['last']}")
    print(f"下次: {status['next']}")
    
    print("\n=== 刷新数据 (同步) ===")
    fresh = em.refresh_earnings('NVDA')
    print(f"数据: {fresh}")


if __name__ == "__main__":
    # 运行同步测试
    test_sync()
    
    # 运行异步测试
    asyncio.run(test_async_features())
