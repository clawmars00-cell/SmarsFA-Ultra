"""
Tools - 增强版数据获取
"""
import yfinance as yf
from typing import Dict, Any


def get_financial_data(ticker: str) -> Dict[str, Any]:
    """获取完整财务数据"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 财务数据
        financials = stock.financials
        income = stock.income_stmt
        
        revenue = 0
        net_income = 0
        gross_profit = 0
        operating_income = 0
        
        if not financials.empty:
            if 'Total Revenue' in financials.index:
                revenue = float(financials.loc['Total Revenue'].iloc[0])
            if 'Net Income' in financials.index:
                net_income = float(financials.loc['Net Income'].iloc[0])
            if 'Gross Profit' in financials.index:
                gross_profit = float(financials.loc['Gross Profit'].iloc[0])
            if 'Operating Income' in financials.index:
                operating_income = float(financials.loc['Operating Income'].iloc[0])
        
        # EPS历史
        eps_history = []
        if not income.empty and 'Diluted EPS' in income.index:
            eps_series = income.loc['Diluted EPS']
            for i, (date, eps) in enumerate(eps_series.items()):
                if i < 4:  # 最近4个季度
                    eps_history.append({"quarter": str(date)[:7], "eps": eps})
        
        return {
            "ticker": ticker,
            "revenue": revenue,
            "revenue_b": revenue / 1e9 if revenue else 0,
            "net_income": net_income,
            "net_income_b": net_income / 1e9 if net_income else 0,
            "gross_profit": gross_profit,
            "gross_margin": gross_profit / revenue if revenue else 0,
            "operating_income": operating_income,
            "operating_margin": operating_income / revenue if revenue else 0,
            "net_margin": net_income / revenue if revenue else 0,
            "eps_history": eps_history,
            "market_cap": info.get('marketCap', 0),
            "market_cap_t": info.get('marketCap', 0) / 1e12 if info.get('marketCap') else 0,
            "pe_ratio": info.get('trailingPE', 0),
            "forward_pe": info.get('forwardPE', 0),
            "price": info.get('currentPrice', 0),
            "52w_high": info.get('fiftyTwoWeekHigh', 0),
            "52w_low": info.get('fiftyTwoWeekLow', 0),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_options_chain(ticker: str) -> Dict[str, Any]:
    """获取期权链"""
    try:
        stock = yf.Ticker(ticker)
        options = stock.option_chain()
        
        calls = options.calls.to_dict() if hasattr(options, 'calls') else {}
        puts = options.puts.to_dict() if hasattr(options, 'puts') else {}
        
        call_vol = sum(calls.get('volume', [0])) if calls else 0
        put_vol = sum(puts.get('volume', [0])) if puts else 0
        
        return {
            "ticker": ticker,
            "call_volume": call_vol,
            "put_volume": put_vol,
            "call_put_ratio": round(call_vol / put_vol, 2) if put_vol > 0 else 0,
            "calls_heavy": call_vol > put_vol
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_news_sentiment(ticker: str) -> Dict[str, Any]:
    """获取新闻"""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news or []
        
        return {
            "ticker": ticker,
            "news_count": len(news),
            "articles": [{"title": n.get('title', '')[:80], "publisher": n.get('publisher', '')} for n in news[:5]]
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


TOOLS = {
    "get_financial_data": get_financial_data,
    "get_options_chain": get_options_chain,
    "get_news_sentiment": get_news_sentiment,
}
