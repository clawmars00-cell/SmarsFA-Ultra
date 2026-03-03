"""
Comprehensive Report Template - 完整汇报模板
包含:
1. 基础信息 (价格、建议、置信度)
2. 财务数据 (营收、净利润、EPS、营业利润、EBITDA)
3. 估值 (PE、Forward PE、PEG)
4. 现金流 (FCF)
5. 利润率 (净利润率、毛利率、营业利润率)
6. 增长 (营收增长、盈利增长)
7. 市场预期对比 (EPS超预期、营收超预期)
8. 财报电话会议要点
9. 未来展望 (下季度指引、风险)
"""
from datetime import datetime
from typing import Dict, List, Optional
import yfinance as yf


class ComprehensiveReport:
    """
    完整财报汇报模板
    """
    
    def __init__(self):
        pass
    
    def generate(self, symbol: str, financial_data: Dict, analysis_result: Dict = None, 
                 earnings_call: List[str] = None, guidance: Dict = None) -> List[str]:
        """
        生成完整汇报
        
        Args:
            symbol: 股票代码
            financial_data: 财务数据字典
            analysis_result: 分析结果 (可选)
            earnings_call: 电话会议要点 (可选)
            guidance: 业绩指引 (可选)
        
        Returns:
            多条消息列表
        """
        messages = []
        
        fin = financial_data.get('financials', {})
        
        # ===== 1. 标题 + 建议 =====
        rec = analysis_result.get('recommendation', 'N/A') if analysis_result else 'N/A'
        score = analysis_result.get('overall_score', 0) * 100 if analysis_result else 0
        rec_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(rec, "⚪")
        
        price = fin.get('current_price', 'N/A')
        
        msg = f"📊 *{symbol} 财报综合分析*\n\n"
        msg += f"{rec_emoji} *建议: {rec}* (置信度: {score:.0f}%)\n"
        msg += f"💰 价格: ${price}\n"
        messages.append(msg)
        
        # ===== 2. 财务数据 =====
        msg = "📈 *损益数据*\n"
        
        if fin.get('revenue'):
            rev = fin.get('revenue', 0) / 1e9
            msg += f"   营收: ${rev:.1f}B\n"
        
        if fin.get('net_income'):
            ni = fin.get('net_income', 0) / 1e9
            msg += f"   净利润: ${ni:.1f}B\n"
        
        if fin.get('eps'):
            msg += f"   EPS: ${fin.get('eps'):.2f}\n"
        
        if fin.get('operating_income'):
            oi = fin.get('operating_income', 0) / 1e9
            msg += f"   营业利润: ${oi:.1f}B\n"
        
        if fin.get('ebitda'):
            ebitda = fin.get('ebitda', 0) / 1e9
            msg += f"   EBITDA: ${ebitda:.1f}B\n"
        
        messages.append(msg)
        
        # ===== 3. 估值 =====
        msg = "🎯 *估值指标*\n"
        
        if fin.get('pe_ratio'):
            msg += f"   PE: {fin.get('pe_ratio'):.1f}x\n"
        
        if fin.get('forward_pe'):
            msg += f"   Forward PE: {fin.get('forward_pe'):.1f}x\n"
        
        if fin.get('peg_ratio'):
            msg += f"   PEG: {fin.get('peg_ratio'):.2f}x\n"
        
        if fin.get('market_cap'):
            cap = fin.get('market_cap', 0) / 1e12
            msg += f"   市值: ${cap:.1f}T\n"
        
        messages.append(msg)
        
        # ===== 4. 现金流 =====
        msg = "💵 *现金流*\n"
        
        if fin.get('free_cash_flow'):
            fcf = fin.get('free_cash_flow', 0) / 1e9
            msg += f"   自由现金流: ${fcf:.1f}B\n"
        
        if fin.get('operating_cashflow'):
            ocf = fin.get('operating_cashflow', 0) / 1e9
            msg += f"   营业现金流: ${ocf:.1f}B\n"
        
        messages.append(msg)
        
        # ===== 5. 利润率 =====
        msg = "📐 *利润率*\n"
        
        if fin.get('profit_margin'):
            msg += f"   净利润率: {fin.get('profit_margin')*100:.1f}%\n"
        
        if fin.get('gross_margin'):
            msg += f"   毛利率: {fin.get('gross_margin')*100:.1f}%\n"
        
        if fin.get('operating_margin'):
            msg += f"   营业利润率: {fin.get('operating_margin')*100:.1f}%\n"
        
        messages.append(msg)
        
        # ===== 6. 增长 =====
        msg = "📈 *增长指标*\n"
        
        if fin.get('revenue_growth'):
            msg += f"   营收增长: {fin.get('revenue_growth')*100:+.1f}%\n"
        
        if fin.get('earnings_growth'):
            msg += f"   盈利增长: {fin.get('earnings_growth')*100:+.1f}%\n"
        
        messages.append(msg)
        
        # ===== 7. 市场预期对比 =====
        msg = "📊 *市场预期对比*\n"
        
        eps_beat = fin.get('eps_beat')
        if eps_beat is not None:
            emoji = "✅" if eps_beat > 0 else "❌"
            exp_eps = fin.get('expected_eps', 0)
            msg += f"   {emoji} EPS: 实际${fin.get('eps', 0):.2f} vs 预期${exp_eps:.2f} ({eps_beat:+.1f}%)\n"
        
        rev_beat = fin.get('revenue_beat')
        if rev_beat is not None:
            emoji = "✅" if rev_beat > 0 else "❌"
            exp_rev = fin.get('expected_revenue', 0)
            msg += f"   {emoji} 营收: 实际${fin.get('revenue', 0)/1e9:.1f}B vs 预期${exp_rev:.1f}B ({rev_beat:+.1f}%)\n"
        
        messages.append(msg)
        
        # ===== 8. 电话会议要点 =====
        if earnings_call:
            msg = "📞 *财报电话会议要点*\n"
            for i, h in enumerate(earnings_call[:5], 1):
                # 清理格式
                h = h.replace('**', '').strip()
                if len(h) > 60:
                    h = h[:60] + "..."
                msg += f"   {i}. {h}\n"
            messages.append(msg)
        
        # ===== 9. 未来展望 =====
        if guidance:
            msg = "🔮 *未来展望*\n"
            
            if guidance.get('next_quarter'):
                msg += f"   下季度指引: {guidance['next_quarter']}\n"
            
            if guidance.get('full_year'):
                msg += f"   全年指引: {guidance['full_year']}\n"
            
            if guidance.get('catalysts'):
                for c in guidance['catalysts'][:3]:
                    msg += f"   催化剂: {c}\n"
            
            if guidance.get('risks'):
                msg += "   ⚠️ 风险: "
                msg += ", ".join(guidance['risks'][:2])
                msg += "\n"
            
            messages.append(msg)
        
        return messages


# 快速测试
if __name__ == "__main__":
    from data_fetcher import AsyncDataFetcher
    
    fetcher = AsyncDataFetcher()
    data = fetcher.fetch_financials_batch(['NVDA'])
    
    # 模拟分析结果
    analysis = {
        'recommendation': 'BUY',
        'overall_score': 0.78
    }
    
    # 模拟电话会议要点
    earnings_call = [
        "Q4 Revenue: $68.1B (up 73% YoY)",
        "Data Center: $62.3B (up 75% YoY)",
        "Gross margins: 75.0-75.2%",
        "Free cash flow: $35B",
        "Agentic AI driving growth"
    ]
    
    # 模拟指引
    guidance = {
        'next_quarter': '~$68B (+/- 2%)',
        'full_year': '$97B FCF',
        'catalysts': ['Blackwell Ultra', 'Rubin platform', 'Agentic AI'],
        'risks': ['China regulatory approval']
    }
    
    # 生成报告
    report = ComprehensiveReport()
    messages = report.generate('NVDA', data['NVDA'], analysis, earnings_call, guidance)
    
    for m in messages:
        print(m)
        print("---")
    
    fetcher.shutdown()
