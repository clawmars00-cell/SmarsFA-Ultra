"""
High-Performance Report Generator - 高性能报告生成器
- 并行数据获取
- 缓存优化 (持久化)
- 异步处理
"""
import asyncio
import time
import concurrent.futures
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

from whatsapp_formatter import WhatsAppFormatter, CommandParser
from watchlist_manager import WatchlistManager
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'SmarsCho'))

try:
    from agents.master_agent import MasterAgent
    master_agent = MasterAgent()
except Exception as e:
    master_agent = None
    print(f"Warning: SmarsCho MasterAgent not loaded: {e}")


# 缓存配置 - TTL定义
# 注意: 缓存永不过期，只标记可信度

CACHE_DIR = "./storage/cache/"

CACHE_TTL_HOURS = {
    'price': 1,        # 价格: 1小时内高可信
    'financial': 730,  # 财报: 约1个月(静态，财报发布后不更新)
    'analysis': 24,   # 分析: 24小时内可信
    'macro': 730,     # 宏观: 约1个月(按月发布)
    'news': 6,        # 新闻: 6小时内可信
}

# 宏观数据发布日期追踪
# 完整的经济数据发布日程
MACRO_RELEASE_DATES = {
    # 月度数据
    'cpi': {'day': 15, 'description': 'CPI 消费者物价指数', 'frequency': 'monthly'},
    'ppi': {'day': 13, 'description': 'PPI 生产者物价指数', 'frequency': 'monthly'},
    'jobs': {'day': 1, 'description': '非农就业数据', 'frequency': 'monthly'},
    'retail': {'day': 15, 'description': '零售销售数据', 'frequency': 'monthly'},
    'housing': {'day': 17, 'description': '新屋开工数据', 'frequency': 'monthly'},
    'consumer_sentiment': {'day': 15, 'description': '密歇根消费者信心指数', 'frequency': 'monthly'},
    
    # 季度数据
    'gdp_advance': {'day': 28, 'description': 'GDP 预估值', 'frequency': 'quarterly'},
    'gdp_final': {'day': 28, 'description': 'GDP 终值', 'frequency': 'quarterly'},
    
    # 利率/央行数据
    'fed_rate': {'day': 99, 'description': '美联储利率决议', 'frequency': '8times_year', 'note': '约每6周一次'},
    'fomc_minutes': {'day': 99, 'description': 'FOMC会议纪要', 'frequency': '8times_year'},
    
    # 其他
    ' ISM_manufacturing': {'day': 1, 'description': 'ISM制造业指数', 'frequency': 'monthly'},
    ' ISM_services': {'day': 3, 'description': 'ISM非制造业指数', 'frequency': 'monthly'},
}

# 常用利率数据
INTEREST_RATES = {
    'fed_funds': {'name': '联邦基金利率', 'source': 'FOMC'},
    'prime_rate': {'name': '优惠利率', 'source': 'Banks'},
    'libor': {'name': 'Libor', 'source': 'ICE'},
    'sofr': {'name': 'SOFR', 'source': 'Federal Reserve'},
    'treasury_2y': {'name': '2年期国债收益率', 'source': 'Treasury'},
    'treasury_10y': {'name': '10年期国债收益率', 'source': 'Treasury'},
    'treasury_30y': {'name': '30年期国债收益率', 'source': 'Treasury'},
}


class PersistentCache:
    """持久化缓存 - 不过期，只标记可信度"""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """获取缓存文件路径"""
        safe_key = key.replace('/', '_').replace(' ', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.json")
    
    def get(self, key: str) -> Optional[Dict]:
        """获取缓存 (不过期)"""
        path = self._get_cache_path(key)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def set(self, key: str, value: Any, data_type: str = 'general'):
        """设置缓存"""
        path = self._get_cache_path(key)
        
        # 判断可信度
        ttl_hours = CACHE_TTL_HOURS.get(data_type, 12)
        
        cache_data = {
            'value': value,
            'data_type': data_type,
            'last_updated': datetime.now().isoformat(),
            'cached_at': time.time()
        }
        
        with open(path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def get_with_trust(self, key: str) -> Dict:
        """获取缓存 + 可信度信息"""
        path = self._get_cache_path(key)
        
        if not os.path.exists(path):
            return {
                'value': None,
                'cached': False,
                'last_updated': None,
                'trust_level': 'no_data'
            }
        
        try:
            with open(path, 'r') as f:
                cache_data = json.load(f)
            
            last_updated = datetime.fromisoformat(cache_data['last_updated'])
            age_hours = (datetime.now() - last_updated).total_seconds() / 3600
            data_type = cache_data.get('data_type', 'general')
            ttl = CACHE_TTL_HOURS.get(data_type, 12)
            
            # 计算可信度
            if age_hours < ttl * 0.5:
                trust = 'high'  # 50% TTL内，高可信
            elif age_hours < ttl:
                trust = 'medium'  # TTL内，中可信
            else:
                trust = 'low'  # 超过TTL，低可信（但仍可用）
            
            return {
                'value': cache_data['value'],
                'cached': True,
                'last_updated': cache_data['last_updated'],
                'age_hours': round(age_hours, 1),
                'trust_level': trust,
                'data_type': data_type
            }
        except:
            return {
                'value': None,
                'cached': False,
                'last_updated': None,
                'trust_level': 'error'
            }
    
    def format_trust_emoji(self, trust: str) -> str:
        """可信度emoji"""
        return {'high': '🟢', 'medium': '🟡', 'low': '🔴', 'no_data': '⚪', 'error': '❌'}.get(trust, '⚪')


class PerformanceCache:
    """内存缓存 (兼容旧代码)"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()


class ReportGenerator:
    """
    高性能报告生成器
    - 并行数据获取
    - 持久化缓存
    - WhatsApp消息集成
    """
    
    def __init__(self):
        self.formatter = WhatsAppFormatter()
        self.parser = CommandParser()
        self.watchlist = WatchlistManager()
        self.cache = PersistentCache()  # 持久化缓存
        self.results_storage = "./storage/analysis_results.json"
        
        # 预加载常青股票
        self.evergreen_stocks = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META']
    
    def _format_trust_info(self, data_type: str) -> str:
        """格式化可信度信息"""
        # 获取各数据可信度
        trust_info = []
        
        type_labels = {
            'price': '价格',
            'financial': '财报', 
            'analysis': '分析',
            'macro': '宏观',
            'news': '新闻'
        }
        
        for dt, label in type_labels.items():
            result = self.cache.get_with_trust(dt)
            if result['cached']:
                emoji = self.cache.format_trust_emoji(result['trust_level'])
                # 转换为更易读的格式
                age = result['age_hours']
                if age < 1:
                    age_str = f"{age*60:.0f}分钟"
                elif age < 24:
                    age_str = f"{age:.1f}小时"
                else:
                    age_str = f"{age/24:.1f}天"
                trust_info.append(f"{emoji}{label}:{age_str}")
        
        if trust_info:
            return " | ".join(trust_info)
        return "⚪数据未缓存"
    
    def get_macro_data(self) -> Dict:
        """获取宏观数据 (带缓存)"""
        cache_key = "macro_data"
        cached = self.cache.get_with_trust(cache_key)
        
        if cached and cached.get('value'):
            return cached['value']
        
        # 抓取宏观数据
        macro_data = {}
        
        try:
            import yfinance as yf
            
            # 国债收益率
            for tenor in ['^TNX', '^IRX', '^FVX']:
                ticker = yf.Ticker(tenor)
                hist = ticker.history(period='5d')
                if not hist.empty:
                    key = 'treasury_10y' if tenor == '^TNX' else 'treasury_2y' if tenor == '^FVX' else 'treasury_3m'
                    macro_data[key] = round(hist['Close'].iloc[-1], 2)
        except:
            pass
        
        # 缓存
        self.cache.set(cache_key, macro_data, data_type='macro')
        
        return macro_data
    
    def format_macro_summary(self) -> str:
        """格式化宏观数据摘要"""
        macro = self.get_macro_data()
        
        lines = []
        lines.append("🌍 *宏观数据*")
        
        rates = []
        if macro.get('treasury_10y'):
            rates.append(f"10年: {macro['treasury_10y']}%")
        if macro.get('treasury_2y'):
            rates.append(f"2年: {macro['treasury_2y']}%")
        
        if rates:
            lines.append(" ".join(rates))
        
        return "\n".join(lines)
    
    def process_command(self, message: str) -> str:
        """处理WhatsApp消息指令"""
        parsed = self.parser.parse(message)
        action = parsed.get('action')
        stocks = parsed.get('stocks', [])
        
        if action == 'unknown':
            return self._get_help_message()
        
        if action == 'help':
            return self._get_help_message()
        
        if action == 'list':
            return self._format_watchlist()
        
        if action == 'add':
            return self._add_stocks(stocks, message)
        
        if action == 'remove':
            return self._remove_stocks(stocks)
        
        if action == 'calendar':
            return self._get_earnings_calendar()
        
        if action == 'analyze':
            return self._analyze_stocks(stocks)
        
        return "未知指令，请输入帮助查看可用命令"
    
    def _get_help_message(self) -> str:
        """帮助信息"""
        return """
⭐ *SmarsFA 指令帮助*

📝 *添加自选:*
• "添加 AAPL MSFT GOOGL"
• "watch NVDA META"

📝 *删除自选:*
• "删除 AAPL"
• "remove MSFT"

📝 *查看自选:*
• "自选列表"
• "list"

📝 *分析财报:*
• "分析 AAPL"
• "分析我的自选"

📝 *财报日历:*
• "财报日历"
• "calendar"
"""
    
    def _add_stocks(self, stocks: List[str], message: str) -> str:
        """添加自选股"""
        if not stocks:
            # 尝试从消息中提取
            import re
            stocks = re.findall(r'\b[A-Z]{2,5}\b', message.upper())
            stocks = [s for s in stocks if s not in ['ADD', 'WATCH', '添加', '加入']]
        
        if not stocks:
            return "❌ 请指定要添加的股票代码\n例如: 添加 AAPL MSFT"
        
        added = []
        exists = []
        for stock in stocks:
            if self.watchlist.add(stock):
                added.append(stock)
            else:
                exists.append(stock)
        
        result = []
        if added:
            result.append(f"✅ 已添加: {', '.join(added)}")
        if exists:
            result.append(f"⚠️ 已存在: {', '.join(exists)}")
        
        return "\n".join(result)
    
    def _remove_stocks(self, stocks: List[str]) -> str:
        """删除自选股"""
        if not stocks:
            return "❌ 请指定要删除的股票代码"
        
        removed = []
        not_found = []
        for stock in stocks:
            if self.watchlist.remove(stock):
                removed.append(stock)
            else:
                not_found.append(stock)
        
        result = []
        if removed:
            result.append(f"✅ 已删除: {', '.join(removed)}")
        if not_found:
            result.append(f"⚠️ 不在列表中: {', '.join(not_found)}")
        
        return "\n".join(result)
    
    def _format_watchlist(self) -> str:
        """格式化自选股列表"""
        watchlist = self.watchlist.get_all()
        
        if not watchlist:
            return "⭐ 自选股列表为空\n输入'添加 AAPL'来添加"
        
        lines = []
        lines.append(f"⭐ *自选股 ({len(watchlist)}只)*")
        lines.append("")
        
        for w in watchlist:
            stock = w['stock']
            note = w.get('note', '')
            last = w.get('last_analyzed')
            
            # 获取缓存的价格
            price_data = self._get_price_cached(stock)
            price_str = f"${price_data['price']}" if price_data else "N/A"
            
            lines.append(f"• {stock} {price_str}")
            if note:
                lines.append(f"  📝 {note}")
            if last:
                lines.append(f"  🕐 上次分析: {last[:10]}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_earnings_calendar(self) -> str:
        """获取财报日历"""
        from earnings_calendar import get_all_upcoming_earnings
        
        earnings = get_all_upcoming_earnings()
        return self.formatter.format_earnings_calendar(earnings)
    
    def _analyze_stocks(self, stocks: List[str]) -> str:
        """分析股票"""
        # 如果没有指定，分析所有自选
        if not stocks:
            stocks = self.watchlist.list_stocks()
        
        if not stocks:
            return "❌ 没有可分析的股票\n请先添加自选股"
        
        # 并行分析
        results = self._parallel_analyze(stocks)
        
        # 格式化输出
        return self._format_analysis_results(results)
    
    def _parallel_analyze(self, stocks: List[str], max_workers: int = 4) -> Dict[str, Dict]:
        """顺序分析多只股票 (避免多线程问题)"""
        results = {}
        
        # 逐个分析，避免多线程signal问题
        for stock in stocks:
            print(f"分析 {stock}...")
            result, trust = self._analyze_single_stock(stock)
            results[stock] = {'data': result, 'trust': trust}
        
        return results
    
    def _analyze_single_stock(self, stock: str) -> tuple:
        """单只股票分析"""
        try:
            # 尝试缓存
            cache_key = f"analysis_{stock}"
            cached = self.cache.get_with_trust(cache_key)
            if cached and cached['value']:
                return cached['value'], cached['trust_level']
            
            if not master_agent:
                return {'error': 'MasterAgent not loaded'}, 'error'
            
            # 直接调用
            result = master_agent.analyze(
                stock=stock,
                quarter="Q4 2025"
            )
            
            # 持久化缓存
            self.cache.set(cache_key, result, data_type='analysis')
            
            return result, 'new'
        except Exception as e:
            return {'error': str(e)}, 'error'
    
    def _format_analysis_results(self, results: Dict[str, Dict]) -> str:
        """格式化分析结果"""
        lines = []
        
        # 标题
        lines.append("📊 *财报分析报告*")
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        # 数据可信度
        trust_summary = self._format_trust_info('analysis')
        lines.append(f"📡 可信度: {trust_summary}")
        lines.append("")
        
        # 统计
        buy = sell = hold = 0
        for stock, result in results.items():
            data = result.get('data', {})
            if 'error' in data:
                continue
            rec = data.get('result', {}).get('structured_data', {}).get('recommendation', 'N/A')
            if rec == 'BUY':
                buy += 1
            elif rec == 'SELL':
                sell += 1
            elif rec == 'HOLD':
                hold += 1
        
        lines.append(f"🟢 BUY: {buy} | 🔴 SELL: {sell} | 🟡 HOLD: {hold}")
        lines.append("")
        
        # 详细结果
        for stock, result in results.items():
            data = result.get('data', {})
            trust = result.get('trust', 'unknown')
            trust_emoji = {'high': '🟢', 'medium': '🟡', 'low': '🔴', 'new': '✨', 'no_data': '⚪', 'error': '❌'}.get(trust, '⚪')
            
            if 'error' in data:
                lines.append(f"❌ {stock}: {data['error']}")
                continue
            
            data_result = data.get('result', {}).get('structured_data', {})
            rec = data_result.get('recommendation', 'N/A')
            score = data_result.get('overall_score', 0) * 100
            
            rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(rec, "⚪")
            
            # 价格
            price_data = self._get_price_cached(stock)
            price_str = f"${price_data['price']}" if price_data else "N/A"
            
            lines.append(f"{trust_emoji} {rec_emoji} *{stock}* {price_str}")
            lines.append(f"   建议: {rec} ({score:.0f}%)")
            
            # 关键财务数据
            fin = data_result.get('financial_metrics', {})
            if fin.get('revenue'):
                rev = fin.get('revenue', 0) / 1e9
                lines.append(f"   营收: ${rev:.1f}B")
            if fin.get('eps'):
                eps = fin.get('eps')
                lines.append(f"   EPS: ${eps:.2f}")
            
            # 风险
            risks = data.get('risk_flags', [])
            if risks:
                lines.append(f"   ⚠️ {risks[0][:30]}")
            
            # 未来展望
            outlook = data.get('future_outlook', {})
            if outlook:
                next_q = outlook.get('next_quarter_outlook', 'N/A')
                lines.append(f"   🔮 下季度: {next_q}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_price_cached(self, symbol: str) -> Optional[Dict]:
        """获取缓存的价格"""
        cache_key = f"price_{symbol}"
        cached = self.cache.get_with_trust(cache_key)
        
        if cached and cached.get('value'):
            # 返回value部分
            return cached['value']
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            change = info.get('regularMarketChangePercent', 0)
            
            data = {'price': price, 'change': change}
            self.cache.set(cache_key, data, data_type='price')
            return data
        except:
            return None
    
    def generate_market_brief(self) -> str:
        """生成市场简报"""
        lines = []
        lines.append("🌎 *市场概况*")
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
        lines.append("")
        
        # 快速获取大盘数据
        for symbol in ['SPY', 'QQQ']:
            data = self._get_price_cached(symbol)
            if data:
                name = 'S&P 500' if symbol == 'SPY' else 'NASDAQ'
                change = data['change']
                emoji = "🟢" if change >= 0 else "🔴"
                lines.append(f"{emoji} {name}: ${data['price']} ({change:+.2f}%)")
        
        return "\n".join(lines)


# 全局实例
report_generator = ReportGenerator()


if __name__ == "__main__":
    # 测试
    rg = report_generator
    
    # 测试命令
    print(rg.process_command("添加 AAPL MSFT"))
    print("\n" + "="*30 + "\n")
    print(rg.process_command("分析 AAPL"))
    print("\n" + "="*30 + "\n")
    print(rg.process_command("自选列表"))
