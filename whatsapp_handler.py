"""
WhatsApp Handler - WhatsApp消息处理器
整合所有功能，提供完整的WhatsApp消息响应
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from report_generator import ReportGenerator, report_generator
from whatsapp_formatter import WhatsAppFormatter, CommandParser
from watchlist_manager import WatchlistManager, watchlist_manager
from data_fetcher import AsyncDataFetcher

# 导入交易追踪
import os
import sys

# 添加SmarsFA-Ultra路径
ultra_path = os.path.join(os.path.dirname(__file__), '..', 'SmarsFA-Ultra')
if ultra_path not in sys.path:
    sys.path.insert(0, ultra_path)

try:
    from smarsfa_ultra import SmarsFAUltra, sf_ultra
    ultra_available = True
except Exception as e:
    print(f"SmarsFA-Ultra not available: {e}")
    ultra_available = False
    sf_ultra = None


class WhatsAppHandler:
    """
    WhatsApp消息处理器
    - 解析消息指令
    - 生成响应
    - 格式化输出
    """
    
    def __init__(self):
        self.report_gen = ReportGenerator()
        self.formatter = WhatsAppFormatter()
        self.watchlist = WatchlistManager()
        self.data_fetcher = AsyncDataFetcher()
        
        # 交易追踪
        self.tracker = None
        self._load_tracker_positions()
    
    def _load_tracker_positions(self):
        """从配置加载追踪持仓"""
        try:
            from trading_tracker import TradingTracker
            
            self.tracker = TradingTracker()
            
            config_path = os.path.join(
                os.path.dirname(__file__), '..', 'SmarsCho', 'tracker_config.json'
            )
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
                for stock in config.get('stocks', []):
                    self.tracker.add_stock(
                        stock['symbol'],
                        stock['shares'],
                        stock.get('avg_cost', 0),
                        stock.get('name', ''),
                        stock.get('currency')  # 传递货币信息
                    )
                for opt in config.get('options', []):
                    self.tracker.add_option(
                        opt['symbol'],
                        opt['expiry'],
                        opt['strike'],
                        opt['type'],
                        opt['contracts'],
                        opt['premium']
                    )
        except Exception as e:
            print(f"加载追踪配置失败: {e}")
            self.tracker = None
    
    def handle_message(self, message: str, sender: str = "unknown") -> List[str]:
        """
        处理收到的WhatsApp消息
        返回多条消息列表 (WhatsApp格式)
        """
        # 解析命令
        parsed = CommandParser.parse(message)
        action = parsed.get('action')
        stocks = parsed.get('stocks', [])
        
        # 路由处理
        if action == 'help':
            return [self._get_help_message()]
        
        elif action == 'list':
            return [self._format_watchlist_enhanced()]
        
        elif action == 'add':
            return [self._add_stocks(stocks)]
        
        elif action == 'remove':
            return [self._remove_stocks(stocks)]
        
        elif action == 'calendar':
            return [self._get_earnings_calendar_enhanced()]
        
        elif action == 'analyze':
            return self._analyze_and_respond(stocks)
        
        elif action == 'brief':
            return [self._get_market_brief_enhanced()]
        
        elif action == 'tracker' or action == '持仓':
            report_type = parsed.get('report_type')
            return self._get_tracker_report(report_type)
        
        elif action == 'ultra' or action == 'llm_analyze' or action == 'value_analyze':
            # LLM直接分析 - 不需要Python处理
            return self._get_ultra_analysis(stocks)
        
        else:
            # 未知命令，显示帮助
            return [
                f"❓ 未知指令: {message}",
                "",
                self._get_help_message()
            ]
    
    def _get_help_message(self) -> str:
        """帮助信息 - WhatsApp优化格式"""
        return """
⭐ *SmarsFA 财报助手*

📝 *指令列表:*

🏷️ *自选管理:*
• 添加 AAPL MSFT → 添加自选
• 删除 AAPL → 删除自选
• 列表 → 查看自选

📊 *分析功能:*
• 分析 AAPL → 分析单只股票
• 分析自选 → 分析全部自选

📅 *日历:*
• 日历 → 即将发布的财报

📈 *市场:*
• 大盘 → 市场概况

💡 *帮助 → 显示此帮助

📊 *持仓追踪:*
• 持仓 → 显示当前持仓
• 持仓 开盘 → 开盘报告
• 持仓 收盘 → 收盘报告

🤖 *AI分析 (SmarsFA-Ultra):*
• 分析 Ultra <股票> → LLM智能体分析
"""
    
    def _get_tracker_report(self, report_type: str = None) -> List[str]:
        """获取持仓追踪报告"""
        if report_type == 'open':
            return self._generate_open_report()
        elif report_type == 'close':
            return self._generate_close_report()
        else:
            return self._generate_tracker_summary()
    
    def _generate_tracker_summary(self) -> List[str]:
        """生成追踪汇总"""
        report = self.tracker.get_daily_report()
        
        messages = []
        
        date = report['report_date']
        total = report['total']
        
        emoji = '📈' if total['total_pnl'] >= 0 else '📉'
        
        # 计算总市值
        total_value = sum(
            info.get('market_value', 0) 
            for info in report.get('stocks', {}).get('positions_detail', {}).values()
            if isinstance(info, dict) and 'error' not in info
        )
        
        # 格式化函数
        def format_value(v):
            if v >= 1e6:
                return f"${v/1e6:.1f}M"
            return f"${v:.2f}"
        
        msg = f"{emoji} *持仓追踪* {date}\n\n"
        msg += f"🎯 总P&L: ${total['total_pnl']:+,.2f} ({total['total_pnl_pct']:+.2f}%)\n"
        msg += f"📊 持仓数: {total['positions']} | 市值: {format_value(total_value)}"
        messages.append(msg)
        
        stocks = report['stocks']
        if stocks.get('positions', 0) > 0:
            msg = "📦 *股票*\n"
            for sym, info in stocks.get('positions_detail', {}).items():
                if isinstance(info, dict) and 'error' not in info:
                    pnl_emoji = '🟢' if info['pnl'] >= 0 else '🔴'
                    # 格式化成交量
                    vol = info.get('volume', 0)
                    if vol >= 1e6:
                        vol_str = f"{vol/1e6:.1f}M"
                    elif vol >= 1e3:
                        vol_str = f"{vol/1e3:.1f}K"
                    else:
                        vol_str = str(vol)
                    
                    msg += f"{pnl_emoji} {sym}: ${info['current_price']:.2f} "
                    msg += f"(今{info['day_change_pct']:+.2f}% | 持{info['pnl_pct']:+.2f}% | V:{vol_str})\n"
            messages.append(msg)
        
        options = report['options']
        if options.get('positions', 0) > 0:
            msg = "🎰 *期权*\n"
            for key, info in options.get('positions_detail', {}).items():
                if isinstance(info, dict) and 'error' not in info:
                    pnl_emoji = '🟢' if info['pnl'] >= 0 else '🔴'
                    msg += f"{pnl_emoji} {info['symbol']} "
                    msg += f"{info['strike']}${info['expiry'][-5:]} "
                    msg += f"{info['type'].upper()} IV:{info['iv']:.0f}% P&L:${info['pnl']:+.2f}\n"
            messages.append(msg)
        
        return messages
    
    def _generate_open_report(self) -> List[str]:
        """生成开盘报告"""
        report = self.tracker.get_daily_report()
        
        messages = ["🌅 *开盘追踪*", f"📅 {report['report_date']}", ""]
        
        total = report.get('total', {})
        pnl_emoji = '🟢' if total.get('total_pnl', 0) >= 0 else '🔴'
        messages.append(f"{pnl_emoji} *隔夜P&L: ${total.get('total_pnl', 0):+,.2f}*")
        messages.append("")
        
        stocks = report.get('stocks', {}).get('positions_detail', {})
        if stocks:
            messages.append("📈 *异动*")
            for sym, info in stocks.items():
                if isinstance(info, dict) and 'error' not in info:
                    day = info.get('day_change_pct', 0)
                    if abs(day) > 2:
                        emoji = '🔺' if day > 0 else '🔻'
                        messages.append(f"{emoji} {sym}: ${info.get('current_price', 0):.2f} ({day:+.2f}%)")
        
        return messages
    
    def _generate_close_report(self) -> List[str]:
        """生成收盘报告"""
        return self._generate_tracker_summary()
    
    def _get_ultra_analysis(self, stocks: List[str]) -> List[str]:
        """SmarsFA-Ultra LLM智能体分析 - 直接返回分析prompt让LLM处理"""
        if not stocks:
            return ["❌ 请指定股票代码，如: MSFT"]
        
        stock = stocks[0].upper()
        
        # 直接返回简洁的LLM prompt
        return [f"""你是一个专业的投资分析师。请用中文分析 {stock} 的投资价值。

请从以下维度进行分析：
1. 估值分析 (PE, PEG, 市值)
2. 质量分析 (ROE, 利润率)
3. 技术动量 (趋势, RSI)
4. 舆情分析 (分析师评级, 新闻)

请给出：
- 综合评分 (0-100)
- 投资评级 (强烈推荐/推荐/持有/回避)
- 一句话理由
- 风险提示"""]
    
    def _add_stocks(self, stocks: List[str]) -> str:
        """添加自选股"""
        if not stocks:
            return "❌ 请指定股票代码\n例如: 添加 AAPL"
        
        added = []
        exists = []
        for stock in stocks:
            if self.watchlist.add(stock, added_by="whatsapp"):
                added.append(stock)
            else:
                exists.append(stock)
        
        lines = []
        if added:
            lines.append(f"✅ 已添加: {', '.join(added)}")
        if exists:
            lines.append(f"⚠️ 已存在: {', '.join(exists)}")
        
        return "\n".join(lines)
    
    def _remove_stocks(self, stocks: List[str]) -> str:
        """删除自选股"""
        if not stocks:
            return "❌ 请指定股票代码"
        
        removed = []
        not_found = []
        for stock in stocks:
            if self.watchlist.remove(stock):
                removed.append(stock)
            else:
                not_found.append(stock)
        
        lines = []
        if removed:
            lines.append(f"✅ 已删除: {', '.join(removed)}")
        if not_found:
            lines.append(f"⚠️ 不在列表中: {', '.join(not_found)}")
        
        return "\n".join(lines)
    
    def _format_watchlist_enhanced(self) -> str:
        """增强版自选股列表 - 带实时价格"""
        watchlist = self.watchlist.get_all()
        
        if not watchlist:
            return "⭐ 自选股为空\n输入'添加 AAPL'添加"
        
        stocks = [w['stock'] for w in watchlist]
        
        # 批量获取价格
        price_data = self.data_fetcher.fetch_price_batch(stocks)
        
        lines = []
        lines.append(f"⭐ *自选股 ({len(watchlist)}只)*")
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
        lines.append("")
        
        for w in watchlist:
            stock = w['stock']
            note = w.get('note', '')
            
            # 价格
            p = price_data.get(stock, {})
            if p and 'error' not in p:
                price = p.get('price', 'N/A')
                change = p.get('change', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                lines.append(f"{emoji} *{stock}* ${price} ({change:+.2f}%)")
            else:
                lines.append(f"⚪ *{stock}* (暂无数据)")
            
            if note:
                lines.append(f"   📝 {note}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_earnings_calendar_enhanced(self) -> str:
        """增强版财报日历"""
        from earnings_calendar import get_all_upcoming_earnings
        
        earnings = get_all_upcoming_earnings()
        
        if not earnings:
            return "📅 近期无财报发布"
        
        lines = []
        lines.append("📅 *财报日历*")
        lines.append("")
        
        # 按日期分组
        by_date = {}
        for e in earnings[:15]:
            date = e.get('date', 'TBD')
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(e)
        
        for date, items in sorted(by_date.items()):
            lines.append(f"📌 *{date}*")
            for e in items:
                stock = e.get('stock', '')
                cap = e.get('market_cap', 0) / 1e9
                lines.append(f"   • {stock} (${cap:.0f}B)")
            lines.append("")
        
        return "\n".join(lines)
    
    def _analyze_and_respond(self, stocks: List[str]) -> List[str]:
        """分析股票并返回多个消息"""
        # 如果没有指定，分析自选
        if not stocks:
            stocks = self.watchlist.list_stocks()
        
        if not stocks:
            return ["❌ 没有可分析的股票\n请先添加自选股"]
        
        # 获取真实财务数据
        financial_data = self.data_fetcher.fetch_financials_batch(stocks[:5])
        
        # 并行分析
        from main import master_agent
        
        results = {}
        for stock in stocks[:5]:  # 限制最多5只
            try:
                # 从真实数据构建actual_data
                fin = financial_data.get(stock, {}).get('financials', {})
                quarter_date = fin.get('quarter_date', '最新季度')
                
                actual_data = {
                    "revenue": fin.get('revenue', 0),
                    "eps": fin.get('eps', 0) or fin.get('forward_eps', 0),
                    "net_income": fin.get('net_income', 0)
                }
                
                # 使用最新季度
                quarter_label = f"最新季度 ({quarter_date[:7]})"
                
                result = master_agent.analyze(
                    stock=stock,
                    quarter=quarter_label,
                    actual_data=actual_data if any(actual_data.values()) else None
                )
                results[stock] = result
                self.watchlist.update_analysis(stock)
            except Exception as e:
                results[stock] = {"error": str(e)}
        
        # 获取实时价格
        price_data = self.data_fetcher.fetch_price_batch(list(results.keys()))
        
        # 格式化消息
        messages = []
        
        # 第一条: 摘要
        buy = sum(1 for r in results.values() 
                  if not isinstance(r, dict) or 'error' not in r)
        messages.append(f"📊 分析完成 ({len(results)}只)\n🟢 BUY: {buy} | 🟡 HOLD: {len(results)-buy}")
        
        # 后续: 详细分析
        for stock, result in results.items():
            if 'error' in result:
                messages.append(f"❌ {stock}: {result['error']}")
                continue
            
            data = result.get('result', {}).get('structured_data', {})
            rec = data.get('recommendation', 'N/A')
            score = data.get('overall_score', 0) * 100
            
            rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(rec, "⚪")
            
            # 价格
            p = price_data.get(stock, {})
            price_str = f"${p.get('price', 'N/A')}" if p else "N/A"
            
            msg = f"{rec_emoji} *{stock}* {price_str}\n"
            msg += f"   {rec} · 置信度 {score:.0f}%\n"
            
            # 使用真实财务数据 - 完整版
            fin = financial_data.get(stock, {}).get('financials', {})
            
            # 损益
            if fin.get('revenue'):
                rev = fin.get('revenue', 0) / 1e9
                msg += f"   📈 营收: ${rev:.1f}B\n"
            
            if fin.get('net_income'):
                ni = fin.get('net_income', 0) / 1e9
                msg += f"   💰 净利润: ${ni:.1f}B\n"
            
            if fin.get('eps'):
                msg += f"   📊 EPS: ${fin.get('eps'):.2f}\n"
            
            if fin.get('operating_income'):
                oi = fin.get('operating_income', 0) / 1e9
                msg += f"   🏢 营业利润: ${oi:.1f}B\n"
            
            if fin.get('ebitda'):
                ebitda = fin.get('ebitda', 0) / 1e9
                msg += f"   📉 EBITDA: ${ebitda:.1f}B\n"
            
            # 估值
            if fin.get('pe_ratio'):
                msg += f"   🎯 PE: {fin.get('pe_ratio'):.1f}x\n"
            
            if fin.get('forward_pe'):
                msg += f"   🔮 Forward PE: {fin.get('forward_pe'):.1f}x\n"
            
            # 现金流
            if fin.get('free_cash_flow'):
                fcf = fin.get('free_cash_flow', 0) / 1e9
                msg += f"   💵 FCF: ${fcf:.1f}B\n"
            
            # 利润率
            if fin.get('profit_margin'):
                msg += f"   📐 净利润率: {fin.get('profit_margin')*100:.1f}%\n"
            
            if fin.get('gross_margin'):
                msg += f"   📐 毛利率: {fin.get('gross_margin')*100:.1f}%\n"
            
            if fin.get('operating_margin'):
                msg += f"   📐 营业利润率: {fin.get('operating_margin')*100:.1f}%\n"
            
            # 增长
            if fin.get('revenue_growth'):
                msg += f"   📈 营收增长: {fin.get('revenue_growth')*100:.1f}%\n"
            
            # 市场预期对比
            eps_beat = fin.get('eps_beat')
            if eps_beat is not None:
                emoji = "✅" if eps_beat > 0 else "❌"
                msg += f"   {emoji} EPS超预期: {eps_beat:+.1f}%\n"
            
            rev_beat = fin.get('revenue_beat')
            if rev_beat is not None:
                emoji = "✅" if rev_beat > 0 else "❌"
                msg += f"   {emoji} 营收超预期: {rev_beat:+.1f}%\n"
            
            # 未来展望
            outlook = data.get('future_outlook', {})
            if outlook:
                next_q = outlook.get('next_quarter_outlook', 'N/A')
                catalyst = outlook.get('catalyst', '')
                msg += f"   🔮 下季度: {next_q}\n"
                if catalyst:
                    msg += f"   催化剂: {catalyst[:30]}...\n"
            
            # 风险
            risks = data.get('risk_flags', [])
            if risks:
                msg += f"   ⚠️ {risks[0][:25]}\n"
            
            messages.append(msg)
        
        return messages
    
    def _get_market_brief_enhanced(self) -> str:
        """增强版市场简报"""
        lines = []
        lines.append("🌎 *市场概况*")
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
        lines.append("")
        
        # 大盘指数
        indices = [
            ('SPY', 'S&P 500'),
            ('QQQ', 'NASDAQ'),
            ('DIA', '道琼斯')
        ]
        
        price_data = self.data_fetcher.fetch_price_batch([i[0] for i in indices])
        
        for symbol, name in indices:
            p = price_data.get(symbol, {})
            if p and 'error' not in p:
                price = p.get('price', 0)
                change = p.get('change', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                lines.append(f"{emoji} {name}: ${price} ({change:+.2f}%)")
        
        return "\n".join(lines)


# 全局实例
whatsapp_handler = WhatsAppHandler()


if __name__ == "__main__":
    handler = WhatsAppHandler()
    
    # 测试
    print("=== 测试添加 ===")
    print(handler.handle_message("添加 AAPL TSLA"))
    
    print("\n=== 测试列表 ===")
    print(handler.handle_message("列表"))
    
    print("\n=== 测试分析 ===")
    msgs = handler.handle_message("分析 AAPL")
    for m in msgs:
        print(m)
        print("---")
