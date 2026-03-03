"""
High-Performance Data Fetcher - 高性能数据获取
- 异步并行获取
- 批量处理
- 错误恢复
"""
import asyncio
import time
import concurrent.futures
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import yfinance as yf
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncDataFetcher:
    """
    异步数据获取器
    - 支持批量异步获取
    - 自动重试
    - 错误隔离
    """
    
    def __init__(self, max_workers: int = 8, timeout: int = 10):
        self.max_workers = max_workers
        self.timeout = timeout
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    async def fetch_multiple(self, symbols: List[str], fetch_func: Callable) -> Dict[str, Any]:
        """异步批量获取"""
        loop = asyncio.get_event_loop()
        
        # 提交所有任务
        futures = {
            loop.run_in_executor(self.executor, fetch_func, symbol): symbol
            for symbol in symbols
        }
        
        results = {}
        for future in concurrent.futures.as_completed(futures, timeout=self.timeout):
            symbol = futures[future]
            try:
                result = await future
                results[symbol] = result
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    def fetch_price_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取价格数据"""
        def fetch_one(symbol):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return {
                    'symbol': symbol,
                    'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                    'change': info.get('regularMarketChangePercent', 0),
                    'volume': info.get('regularMarketVolume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                return {'symbol': symbol, 'error': str(e)}
    
    def _get_full_financials(self, ticker, calendar_entry=None) -> Dict:
        """
        获取完整财务数据
        包含: 损益表、资产负债表、现金流量表、历史季度数据
        """
        financials = {}
        
        # 1. Info基础数据
        info = ticker.info
        financials['info'] = {
            'company_name': info.get('longName', info.get('shortName', '')),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'beta': info.get('beta', 0),
            'vol_avg': info.get('averageVolume', 0),
            'vol': info.get('volume', 0),
            '52w_high': info.get('fiftyTwoWeekHigh', 0),
            '52w_low': info.get('fiftyTwoWeekLow', 0),
        }
        
        # 2. 季度损益表
        quarterly = ticker.quarterly_financials
        if quarterly is not None and not quarterly.empty:
            financials['quarterly_income'] = self._extract_quarterly_data(quarterly)
        
        # 3. 季度资产负债表
        balance = ticker.quarterly_balance_sheet
        if balance is not None and not balance.empty:
            financials['quarterly_balance'] = self._extract_quarterly_data(balance)
        
        # 4. 季度现金流量表
        cashflow = ticker.quarterly_cashflow
        if cashflow is not None and not cashflow.empty:
            financials['quarterly_cashflow'] = self._extract_quarterly_data(cashflow)
        
        # 5. 年度财务数据
        annual = ticker.financials
        if annual is not None and not annual.empty:
            financials['annual_income'] = self._extract_quarterly_data(annual)
        
        # 6. 分析师预期
        financials['analyst_targets'] = {
            'target_mean': info.get('targetMeanPrice', 0),
            'target_high': info.get('targetHighPrice', 0),
            'target_low': info.get('targetLowPrice', 0),
            'recommendations': info.get('numberOfAnalystOpinions', 0),
            'rating': info.get('recommendationKey', 'N/A'),
        }
        
        # 7. 股息数据
        financials['dividends'] = {
            'yield': info.get('dividendYield', 0),
            'rate': info.get('dividendRate', 0),
            'ex_date': info.get('exDividendDate', 0),
            'payout_ratio': info.get('payoutRatio', 0),
        }
        
        # 8. 完整估值
        financials['valuation'] = {
            'market_cap': info.get('marketCap', 0),
            'enterprise_value': info.get('enterpriseValue', 0),
            'pe_trailing': info.get('trailingPE', 0),
            'pe_forward': info.get('forwardPE', 0),
            'peg': info.get('pegRatio', 0),
            'pb': info.get('priceToBook', 0),
            'ps': info.get('priceToSalesTrailing12Months', 0),
            'enterprise_ev': info.get('enterpriseToRevenue', 0),
            'enterprise_ebitda': info.get('enterpriseToEbitda', 0),
        }
        
        # 9. 盈利能力
        financials['profitability'] = {
            'profit_margin': info.get('profitMargins', 0),
            'gross_margin': info.get('grossMargins', 0),
            'operating_margin': info.get('operatingMargins', 0),
            'ebitda_margin': info.get('ebitdaMargins', 0),
            'roe': info.get('returnOnEquity', 0),
            'roa': info.get('returnOnAssets', 0),
            'roic': info.get('returnOnCapital', 0),
        }
        
        # 10. 增长指标
        financials['growth'] = {
            'revenue_growth': info.get('revenueGrowth', 0),
            'earnings_growth': info.get('earningsGrowth', 0),
            'revenue_q_growth': info.get('revenueQuarterlyGrowth', 0),
            'earnings_q_growth': info.get('earningsQuarterlyGrowth', 0),
            'eps_growth': info.get('epsGrowth', 0),
        }
        
        # 11. 财务健康
        financials['health'] = {
            'total_cash': info.get('totalCash', 0),
            'total_debt': info.get('totalDebt', 0),
            'net_cash': info.get('netDebtToEnterpriseValue', 0),
            'current_ratio': info.get('currentRatio', 0),
            'quick_ratio': info.get('quickRatio', 0),
            'debt_equity': info.get('debtToEquity', 0),
        }
        
        # 12. 运营效率
        financials['efficiency'] = {
            'asset_turnover': info.get('assetTurnover', 0),
            'inventory_turnover': info.get('inventoryTurnover', 0),
            'receivables_turnover': info.get('receivablesTurnover', 0),
        }
        
        # 13. 管理层持股
        financials['insider'] = {
            'shares_owned': info.get('sharesOwnedByInsiders', 0),
            'shares_held_pct': info.get('heldByInsiders', 0),
            'institutional_pct': info.get('heldByInstitutions', 0),
        }
        
        # 14. 日历数据
        if calendar_entry:
            financials['earnings_calendar'] = {
                'last_date': calendar_entry.get('date'),
                'last_eps': calendar_entry.get('reported_eps'),
                'last_revenue': calendar_entry.get('reported_revenue'),
                'expected_eps': calendar_entry.get('expected_eps'),
                'expected_revenue': calendar_entry.get('expected_revenue'),
                'status': calendar_entry.get('status'),
            }
        
        return financials
    
    def _extract_quarterly_data(self, df) -> List[Dict]:
        """提取季度数据为列表"""
        result = []
        
        if df is None or df.empty:
            return result
        
        # 取最近8个季度
        for col in df.columns[:8]:
            row_data = {'date': str(col)}
            
            for idx in df.index:
                value = df.loc[idx, col]
                # 简化key名
                key = idx.replace(' ', '_').lower()
                if value and not pd.isna(value):
                    row_data[key] = float(value)
            
            result.append(row_data)
        
        return result
        
        # 使用线程池同步获取
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_one, s): s for s in symbols}
            
            for future in concurrent.futures.as_completed(futures):
                symbol = futures[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    results[symbol] = {'error': str(e)}
        
        return results
    
    def fetch_financials_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取财务数据 - 完整财务指标"""
        # 读取本地财报日历
        from earnings_calendar import MAJOR_EARNINGS
        # calendar是list，每个股票可能有多条
        
        def fetch_one(symbol):
            try:
                from datetime import datetime
                ticker = yf.Ticker(symbol)
                
                # 获取该股票的所有日历条目
                calendar_entries = [e for e in MAJOR_EARNINGS if e.get('stock', '').upper() == symbol.upper()]
                
                # 先检查本地日历 - 取已发布的
                calendar_entry = None
                for e in calendar_entries:
                    if e.get('status') == 'reported':
                        calendar_entry = e
                        break
                
                # 获取完整财务数据
                financials = self._get_full_financials(ticker, calendar_entry)
                
                return {
                    'symbol': symbol,
                    'financials': financials,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                return {'symbol': symbol, 'error': str(e)}
                
                # 获取季度财务数据
                quarterly = ticker.quarterly_financials
                financials = {}
                
                # 获取info中的估值和现金流数据
                info = ticker.info
                
                if quarterly is not None and not quarterly.empty:
                    # 最新季度 (第一列)
                    col = quarterly.columns[0]
                    quarter_date = col
                    financials['quarter_date'] = str(col)
                    
                    # === 季度损益表数据 ===
                    # 季度营收
                    if 'Total Revenue' in quarterly.index:
                        financials['revenue'] = quarterly.loc['Total Revenue', col]
                    # 季度净利润
                    if 'Net Income' in quarterly.index:
                        financials['net_income'] = quarterly.loc['Net Income', col]
                    # 季度EPS
                    if 'Diluted EPS' in quarterly.index:
                        financials['eps'] = quarterly.loc['Diluted EPS', col]
                    # 营业利润 (Operating Income)
                    if 'Operating Income' in quarterly.index:
                        financials['operating_income'] = quarterly.loc['Operating Income', col]
                    # 毛利 (Gross Profit)
                    if 'Gross Profit' in quarterly.index:
                        financials['gross_profit'] = quarterly.loc['Gross Profit', col]
                    # EBITDA
                    if 'EBITDA' in quarterly.index:
                        financials['ebitda'] = quarterly.loc['EBITDA', col]
                    # 税前利润 (Pretax Income)
                    if 'Pretax Income' in quarterly.index:
                        financials['pretax_income'] = quarterly.loc['Pretax Income', col]
                    # 研发费用 (R&D)
                    if 'Research And Development' in quarterly.index:
                        financials['rd_expense'] = quarterly.loc['Research And Development', col]
                    # 销售及管理费用 (SG&A)
                    if 'Selling General And Administration' in quarterly.index:
                        financials['sga_expense'] = quarterly.loc['Selling General And Administration', col]
                    # 利息收入/支出
                    if 'Interest Income' in quarterly.index:
                        financials['interest_income'] = quarterly.loc['Interest Income', col]
                    if 'Interest Expense' in quarterly.index:
                        financials['interest_expense'] = quarterly.loc['Interest Expense', col]
                
                # === 估值指标 (从info) ===
                financials['pe_ratio'] = info.get('trailingPE', 0) or info.get('peRatio', 0)
                financials['forward_pe'] = info.get('forwardPE', 0)
                financials['peg_ratio'] = info.get('pegRatio', 0)
                financials['price_to_book'] = info.get('priceToBook', 0)
                financials['price_to_sales'] = info.get('priceToSalesTrailing12Months', 0)
                financials['enterprise_value'] = info.get('enterpriseValue', 0)
                financials['market_cap'] = info.get('marketCap', 0)
                
                # === 市场预期对比 (从calendar - 取上次财报的预期) ===
                # calendar_entry已经在前面获取了
                if calendar_entry and calendar_entry.get('reported_eps'):
                    exp_eps = calendar_entry.get('expected_eps')
                    exp_rev = calendar_entry.get('expected_revenue')
                    
                    if exp_eps and financials.get('eps'):
                        financials['expected_eps'] = exp_eps
                        financials['eps_beat'] = (financials.get('eps') - exp_eps) / exp_eps * 100
                    
                    if exp_rev and financials.get('revenue'):
                        financials['expected_revenue'] = exp_rev
                        financials['revenue_beat'] = (financials.get('revenue')/1e9 - exp_rev) / exp_rev * 100
                
                # === 现金流 (从info) ===
                financials['free_cash_flow'] = info.get('freeCashflow', 0)
                financials['operating_cashflow'] = info.get('operatingCashflow', 0)
                financials['total_cash'] = info.get('totalCash', 0)
                financials['total_debt'] = info.get('totalDebt', 0)
                financials['cash_per_share'] = info.get('cashPerShare', 0)
                
                # === 盈利能力 (从info) ===
                financials['profit_margin'] = info.get('profitMargins', 0)
                financials['operating_margin'] = info.get('operatingMargins', 0)
                financials['gross_margin'] = info.get('grossMargins', 0)
                financials['ebitda_margin'] = info.get('ebitdaMargins', 0)
                financials['roe'] = info.get('returnOnEquity', 0)
                financials['roa'] = info.get('returnOnAssets', 0)
                
                # === 增长指标 ===
                financials['revenue_growth'] = info.get('revenueGrowth', 0)
                financials['earnings_growth'] = info.get('earningsGrowth', 0)
                financials['revenue_quarterly_growth'] = info.get('revenueQuarterlyGrowth', 0)
                financials['earnings_quarterly_growth'] = info.get('earningsQuarterlyGrowth', 0)
                
                # === 每股指标 ===
                financials['book_value_per_share'] = info.get('bookValue', 0)
                financials['dividend_yield'] = info.get('dividendYield', 0)
                financials['dividend_rate'] = info.get('dividendRate', 0)
                financials['payout_ratio'] = info.get('payoutRatio', 0)
                
                # === 交易指标 ===
                financials['volume'] = info.get('volume', 0)
                financials['avg_volume'] = info.get('averageVolume', 0)
                financials['beta'] = info.get('beta', 0)
                financials['fifty_two_week_high'] = info.get('fiftyTwoWeekHigh', 0)
                financials['fifty_two_week_low'] = info.get('fiftyTwoWeekLow', 0)
                
                # 判断财报状态 - 简化处理
                # 如果calendar有已发布数据，优先使用
                if calendar_entry:
                    if calendar_entry.get('status') == 'reported':
                        financials['earnings_status'] = 'reported'
                        if calendar_entry.get('reported_revenue'):
                            financials['revenue'] = calendar_entry.get('reported_revenue') * 1e9
                        if calendar_entry.get('reported_eps'):
                            financials['eps'] = calendar_entry.get('reported_eps')
                        financials['reported_quarter'] = calendar_entry.get('reported_quarter', '')
                    else:
                        financials['earnings_status'] = 'upcoming'
                else:
                    financials['earnings_status'] = 'reported'
                
                # 原来从info获取next_earnings的逻辑保留作为备用
                info = ticker.info
                next_earnings = info.get('nextEarningsDate', None)
                
                if next_earnings:
                    # 尝试解析下次财报日期
                    if isinstance(next_earnings, str):
                        try:
                            next_date = datetime.strptime(next_earnings, '%Y-%m-%d')
                            today = datetime.now()
                            if next_date > today:
                                financials['earnings_status'] = 'upcoming'
                                financials['next_earnings_date'] = next_earnings
                                # 获取预期EPS
                                financials['expected_eps'] = info.get('forwardEps', 0) or info.get('epsForward', 0)
                        except:
                            pass
                
                # 市值和估值
                financials['market_cap'] = info.get('marketCap', 0)
                financials['pe_ratio'] = info.get('trailingPE', 0)
                financials['forward_pe'] = info.get('forwardPE', 0)
                
                # 增长 (TTM)
                financials['revenue_growth'] = info.get('revenueGrowth', 0)
                financials['earnings_growth'] = info.get('earningsGrowth', 0)
                
                # 计算利润率
                if financials.get('revenue') and financials.get('net_income'):
                    financials['profit_margin'] = financials['net_income'] / financials['revenue']
                
                # 股息
                financials['dividend_yield'] = info.get('dividendYield', 0)
                financials['dividend_rate'] = info.get('dividendRate', 0)
                
                return {
                    'symbol': symbol,
                    'financials': financials,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                return {'symbol': symbol, 'error': str(e)}
        
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_one, s): s for s in symbols}
            
            for future in concurrent.futures.as_completed(futures):
                symbol = futures[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    results[symbol] = {'error': str(e)}
        
        return results
    
    def fetch_options_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取期权数据"""
        def fetch_one(symbol):
            try:
                ticker = yf.Ticker(symbol)
                options = ticker.options
                
                return {
                    'symbol': symbol,
                    'options_available': len(options) > 0,
                    'next_expiry': options[0] if options else None,
                    'expiry_list': options[:5],
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                return {'symbol': symbol, 'error': str(e)}
        
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_one, s): s for s in symbols}
            
            for future in concurrent.futures.as_completed(futures):
                symbol = futures[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    results[symbol] = {'error': str(e)}
        
        return results
    
    def fetch_all_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """一次性获取所有数据（价格+财务+期权）"""
        logger.info(f"Fetching all data for {len(symbols)} symbols...")
        start = time.time()
        
        price_data = self.fetch_price_batch(symbols)
        financial_data = self.fetch_financials_batch(symbols)
        options_data = self.fetch_options_batch(symbols)
        
        # 合并结果
        combined = {}
        for symbol in symbols:
            combined[symbol] = {
                'price': price_data.get(symbol, {}),
                'financials': financial_data.get(symbol, {}).get('financials', {}),
                'options': options_data.get(symbol, {}),
                'timestamp': datetime.now().isoformat()
            }
        
        elapsed = time.time() - start
        logger.info(f"Fetched all data in {elapsed:.2f}s")
        
        return combined
    
    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)


# 全局实例
data_fetcher = AsyncDataFetcher(max_workers=8)


if __name__ == "__main__":
    # 测试
    fetcher = AsyncDataFetcher()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'SPY']
    
    print("Testing batch fetch...")
    results = fetcher.fetch_all_batch(symbols)
    
    for symbol, data in results.items():
        price = data.get('price', {})
        fin = data.get('financials', {})
        print(f"{symbol}: ${price.get('price', 'N/A')} | PE: {fin.get('pe_ratio', 'N/A')} | Rev Growth: {fin.get('revenue_growth', 'N/A')}")
    
    fetcher.shutdown()
