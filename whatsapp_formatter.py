"""
WhatsApp Report Formatter - IM友好的财报汇报格式
专为WhatsApp/Telegram等IM优化的格式化器
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import yfinance as yf


class WhatsAppFormatter:
    """
    生成WhatsApp友好的财报汇报
    - 短消息 + 多媒体卡片
    - 支持多个股票批量汇报
    - 丰富的财务数据 + 深度分析
    """
    
    def __init__(self):
        self.max_card_lines = 20  # WhatsApp每条消息最大行数
        
    def format_single_stock(self, result: Dict, include_charts: bool = False) -> str:
        """格式化单只股票报告"""
        data = result.get('result', {}).get('structured_data', {})
        stock = result.get('stock', 'N/A')
        quarter = result.get('quarter', 'Q4 2025')
        
        # 获取实时价格
        price_info = self._get_live_price(stock)
        
        lines = []
        lines.append(f"📊 *{stock} {quarter}财报分析*")
        lines.append("")
        
        # 核心指标 (第一行)
        if price_info:
            lines.append(f"💰 ${price_info['price']} ({price_info['change']:+.2f}%)")
        
        # 建议
        rec = data.get('recommendation', 'N/A')
        rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(rec, "⚪")
        lines.append(f"{rec_emoji} *建议: {rec}* (置信度: {data.get('overall_score', 0)*100:.0f}%)")
        lines.append("")
        
        # 营收数据
        fin = data.get('financial_metrics', {})
        revenue = fin.get('revenue', 0)
        if revenue:
            rev_b = revenue / 1e9
            exp_rev = fin.get('expected_revenue', 0) / 1e9 if fin.get('expected_revenue') else 0
            beat = ((rev_b - exp_rev) / exp_rev * 100) if exp_rev > 0 else 0
            lines.append(f"📈 营收: ${rev_b:.1f}B (预期 ${exp_rev:.1f}B)")
            lines.append(f"   超出预期: {'✅' if beat > 0 else '❌'} {beat:+.1f}%")
        
        # EPS
        eps = fin.get('eps')
        exp_eps = fin.get('expected_eps')
        if eps:
            beat_eps = ((eps - exp_eps) / exp_eps * 100) if exp_eps else 0
            lines.append(f"💵 EPS: ${eps:.2f} (预期 ${exp_eps:.2f})")
            lines.append(f"   超出预期: {'✅' if beat_eps > 0 else '❌'} {beat_eps:+.1f}%")
        
        # 净利润
        net_income = fin.get('net_income', 0)
        if net_income:
            ni_b = net_income / 1e9
            lines.append(f"💰 净利润: ${ni_b:.1f}B")
        
        # 营业利润
        op_income = fin.get('operating_income', 0)
        if op_income:
            oi_b = op_income / 1e9
            lines.append(f"🏢 营业利润: ${oi_b:.1f}B")
        
        # EBITDA
        ebitda = fin.get('ebitda', 0)
        if ebitda:
            ebitda_b = ebitda / 1e9
            lines.append(f"📉 EBITDA: ${ebitda_b:.1f}B")
        
        lines.append("")
        
        # 估值指标
        pe = fin.get('pe_ratio')
        if pe:
            lines.append(f"🎯 PE: {pe:.1f}x")
        
        fpe = fin.get('forward_pe')
        if fpe:
            lines.append(f"🔮 Forward PE: {fpe:.1f}x")
        
        peg = fin.get('peg_ratio')
        if peg:
            lines.append(f"📊 PEG: {peg:.2f}x")
        
        # 现金流
        fcf = fin.get('free_cash_flow', 0)
        if fcf:
            fcf_b = fcf / 1e9
            lines.append(f"💵 自由现金流: ${fcf_b:.1f}B")
        
        # 利润率
        pm = fin.get('profit_margin')
        if pm:
            lines.append(f"📐 净利润率: {pm*100:.1f}%")
        
        gm = fin.get('gross_margin')
        if gm:
            lines.append(f"📐 毛利率: {gm*100:.1f}%")
        
        om = fin.get('operating_margin')
        if om:
            lines.append(f"📐 营业利润率: {om*100:.1f}%")
        
        # 增长
        rg = fin.get('revenue_growth')
        if rg:
            lines.append(f"📈 营收增长: {rg*100:.1f}%")
        
        eg = fin.get('earnings_growth')
        if eg:
            lines.append(f"📈 盈利增长: {eg*100:.1f}%")
        
        lines.append("")
        
        # 趋势信号
        trend = data.get('trend_signals', {})
        if trend:
            signals = trend.get('signals', [])
            if signals:
                signal_str = ", ".join([s.get('name', '')[:8] for s in signals[:3]])
                lines.append(f"📉 趋势信号: {signal_str}")
        
        # 资金流
        whale = data.get('whale_activity', {})
        if whale:
            flow = whale.get('institutional_flow', 'N/A')
            if flow != 'N/A':
                flow_emoji = "📥" if flow == 'INFLOW' else "📤"
                lines.append(f"{flow_emoji} 机构资金: {flow}")
        
        lines.append("")
        
        # 风险标记
        risks = data.get('risk_flags', [])
        if risks:
            lines.append("⚠️ *风险提醒:*")
            for r in risks[:3]:
                lines.append(f"   • {r}")
        
        # 未来展望 (新功能)
        outlook = data.get('future_outlook', {})
        if outlook:
            lines.append("")
            lines.append("🔮 *未来展望:*")
            next_quarter = outlook.get('next_quarter_outlook', 'N/A')
            lines.append(f"   下季度: {next_quarter}")
            catalyst = outlook.get('catalyst', '')
            if catalyst:
                lines.append(f"   催化剂: {catalyst[:50]}")
        
        return "\n".join(lines)
    
    def format_batch_report(self, results: List[Dict], title: str = "📊 每日财报总结") -> List[str]:
        """批量格式化多只股票报告"""
        messages = []
        
        # 标题
        messages.append(f"{title}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # 快速摘要
        buy_count = sum(1 for r in results if r.get('result', {}).get('structured_data', {}).get('recommendation') == 'BUY')
        sell_count = sum(1 for r in results if r.get('result', {}).get('structured_data', {}).get('recommendation') == 'SELL')
        
        summary = f"\n🟢 BUY: {buy_count} | 🔴 SELL: {sell_count} | 🟡 HOLD: {len(results) - buy_count - sell_count}"
        messages.append(summary)
        messages.append("─" * 20)
        
        # 每只股票简报
        for result in results:
            stock = result.get('stock', 'N/A')
            data = result.get('result', {}).get('structured_data', {})
            rec = data.get('recommendation', 'N/A')
            score = data.get('overall_score', 0) * 100
            
            # 获取实时价格
            price_info = self._get_live_price(stock)
            price_str = f"${price_info['price']}" if price_info else "N/A"
            
            rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(rec, "⚪")
            
            # 简报格式
            msg = f"{rec_emoji} *{stock}* {price_str}\n"
            msg += f"   {rec} · {score:.0f}% 置信度"
            
            # 添加关键数据
            fin = data.get('financial_metrics', {})
            if fin.get('revenue'):
                rev = fin.get('revenue', 0) / 1e9
                msg += f" · 营收 ${rev:.1f}B"
            
            messages.append(msg)
        
        # 详细报告 (每只股票)
        messages.append("")
        messages.append("📋 *详细分析*")
        messages.append("─" * 20)
        
        for result in results[:5]:  # 最多5只详细
            detail = self.format_single_stock(result)
            # 分隔
            messages.append("")
            messages.append(detail)
            messages.append("─" * 20)
        
        return messages
    
    def format_watchlist_report(self, watchlist: List[str], results: Dict[str, Dict]) -> str:
        """自选股汇报"""
        lines = []
        lines.append("⭐ *自选股财报动态*")
        lines.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
        lines.append("")
        
        for stock in watchlist:
            result = results.get(stock)
            if result:
                data = result.get('result', {}).get('structured_data', {})
                rec = data.get('recommendation', 'N/A')
                score = data.get('overall_score', 0) * 100
                
                price_info = self._get_live_price(stock)
                price_str = f"${price_info['price']}" if price_info else "N/A"
                
                rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(rec, "⚪")
                
                lines.append(f"{rec_emoji} *{stock}* {price_str}")
                lines.append(f"   {rec} · {score:.0f}%")
                
                # 营收
                fin = data.get('financial_metrics', {})
                if fin.get('revenue'):
                    rev = fin.get('revenue', 0) / 1e9
                    lines.append(f"   营收: ${rev:.1f}B")
                
                # 风险
                risks = data.get('risk_flags', [])
                if risks:
                    lines.append(f"   ⚠️ {risks[0][:30]}")
                
                lines.append("")
            else:
                # 未分析
                lines.append(f"⚪ *{stock}* (待分析)")
                lines.append("")
        
        return "\n".join(lines)
    
    def _get_live_price(self, symbol: str) -> Optional[Dict]:
        """获取实时价格"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'change': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0)
            }
        except:
            return None
    
    def format_earnings_calendar(self, earnings: List[Dict]) -> str:
        """财报日历"""
        lines = []
        lines.append("📅 *即将发布财报*")
        lines.append("")
        
        for e in earnings[:10]:
            stock = e.get('stock', 'N/A')
            date = e.get('date', 'N/A')
            cap = e.get('market_cap', 0) / 1e9
            
            lines.append(f"• {stock} - {date}")
            lines.append(f"  市值: ${cap:.0f}B")
            lines.append("")
        
        return "\n".join(lines)


# ========== Command Parser ==========
class CommandParser:
    """解析WhatsApp消息指令"""
    
    COMMANDS = {
        'add': ['添加', 'add', '加入', 'watch'],
        'remove': ['删除', 'remove', 'unwatch', '取消'],
        'list': ['列表', 'list', '自选', 'watchlist'],
        'analyze': ['分析', 'analyze', 'report', '报告'],
        'calendar': ['日历', 'calendar', '财报日历'],
        'help': ['帮助', 'help'],
        'tracker': ['持仓', 'tracker', 'position', '仓位']
    }
    
    @staticmethod
    def parse(message: str) -> Dict:
        """解析消息返回指令和参数"""
        msg = message.strip().upper()
        
        # 检查 SmarsCho 价值分析
        if '价值' in message:
            import re
            stocks = re.findall(r'\b[A-Z]{1,5}\b', msg)
            stocks = [s for s in stocks if s != '价值']
            return {'action': 'value_analyze', 'stocks': stocks}
        
        # 检查单独股票代码 (如 MSFT, AAPL) - SmarsFA-Ultra分析
        import re
        stock_match = re.match(r'^[A-Z]{1,5}$', msg)
        if stock_match and len(msg) >= 2:
            return {'action': 'llm_analyze', 'stocks': [msg]}
        
        # 检查 Ultra 分析
        if 'ULTRA' in msg or 'ULTRA' in message.upper():
            stocks = re.findall(r'\b[A-Z]{1,5}\b', msg)
            stocks = [s for s in stocks if s != 'ULTRA']
            return {'action': 'llm_analyze', 'stocks': stocks}
        
        # 添加自选
        for kw in CommandParser.COMMANDS['add']:
            if kw in msg:
                # 提取股票代码
                import re
                stocks = re.findall(r'\b[A-Z]{1,5}\b', msg)
                stocks = [s for s in stocks if s not in ['ADD', 'WATCH', '添加', '加入']]
                if stocks:
                    return {'action': 'add', 'stocks': stocks}
        
        # 删除自选
        for kw in CommandParser.COMMANDS['remove']:
            if kw in msg:
                import re
                stocks = re.findall(r'\b[A-Z]{1,5}\b', msg)
                return {'action': 'remove', 'stocks': stocks}
        
        # 查看列表
        for kw in CommandParser.COMMANDS['list']:
            if kw in msg:
                return {'action': 'list', 'stocks': []}
        
        # 分析
        for kw in CommandParser.COMMANDS['analyze']:
            if kw in msg:
                import re
                stocks = re.findall(r'\b[A-Z]{1,5}\b', msg)
                return {'action': 'analyze', 'stocks': stocks}
        
        # 日历
        for kw in CommandParser.COMMANDS['calendar']:
            if kw in msg:
                return {'action': 'calendar', 'stocks': []}
        
        # 帮助
        for kw in CommandParser.COMMANDS['help']:
            if kw in msg:
                return {'action': 'help', 'stocks': []}
        
        # 持仓追踪
        for kw in CommandParser.COMMANDS['tracker']:
            if kw in msg:
                # 检查是否有子命令
                report_type = None
                if '开盘' in msg or 'OPEN' in msg:
                    report_type = 'open'
                elif '收盘' in msg or 'CLOSE' in msg:
                    report_type = 'close'
                return {'action': 'tracker', 'stocks': [], 'report_type': report_type}
        
        return {'action': 'unknown', 'stocks': []}


if __name__ == "__main__":
    # 测试
    formatter = WhatsAppFormatter()
    
    # 模拟结果
    test_result = {
        'stock': 'AAPL',
        'quarter': 'Q1 2026',
        'result': {
            'structured_data': {
                'recommendation': 'BUY',
                'overall_score': 0.75,
                'financial_metrics': {
                    'revenue': 124e9,
                    'expected_revenue': 120e9,
                    'eps': 2.10,
                    'expected_eps': 2.00
                },
                'trend_signals': {'signals': [{'name': 'RSI'}]},
                'whale_activity': {'institutional_flow': 'INFLOW'},
                'risk_flags': ['估值偏高'],
                'future_outlook': {
                    'next_quarter_outlook': 'Positive',
                    'catalyst': 'iPhone SE4发布'
                }
            }
        }
    }
    
    print(formatter.format_single_stock(test_result))
