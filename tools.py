"""
Tools - 数据获取工具
"""
import yfinance as yf
from typing import Dict, Any


def get_stock_data(ticker: str) -> Dict[str, Any]:
    """获取股票基本数据"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            "ticker": ticker,
            "price": info.get('currentPrice', 0),
            "previousClose": info.get('previousClose', 0),
            "marketCap": info.get('marketCap', 0),
            "volume": info.get('volume', 0),
            "avgVolume": info.get('averageVolume', 0),
            "peRatio": info.get('trailingPE', 0),
            "eps": info.get('trailingEps', 0),
            "epsForward": info.get('forwardEps', 0),
            "dividendYield": info.get('dividendYield', 0),
            "beta": info.get('beta', 0),
            "52WeekHigh": info.get('fiftyTwoWeekHigh', 0),
            "52WeekLow": info.get('fiftyTwoWeekLow', 0),
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_earnings_data(ticker: str) -> Dict[str, Any]:
    """获取财报数据"""
    try:
        stock = yf.Ticker(ticker)
        
        # 获取历史财报
        financials = stock.financials
        earnings = stock.earnings
        
        return {
            "ticker": ticker,
            "financials": financials.to_dict() if not financials.empty else {},
            "earnings": earnings.to_dict() if not earnings.empty else {},
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
        
        # 计算Call/Put比率
        call_vol = sum(calls.get('volume', [0])) if calls else 0
        put_vol = sum(puts.get('volume', [0])) if puts else 0
        
        return {
            "ticker": ticker,
            "call_volume": call_vol,
            "put_volume": put_vol,
            "call_put_ratio": call_vol / put_vol if put_vol > 0 else 0,
            "calls_heavy": call_vol > put_vol
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_news_sentiment(ticker: str) -> Dict[str, Any]:
    """获取新闻情绪"""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news or []
        
        return {
            "ticker": ticker,
            "news_count": len(news),
            "articles": [{"title": n.get('title', ''), "publisher": n.get('publisher', '')} for n in news[:5]]
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


# 导出所有工具
TOOLS = {
    "get_stock_data": get_stock_data,
    "get_earnings_data": get_earnings_data,
    "get_options_chain": get_options_chain,
    "get_news_sentiment": get_news_sentiment,
}
