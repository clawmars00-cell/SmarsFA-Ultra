"""
Tools - 多数据源财务获取 (SEC + RSS)
"""
import yfinance as yf
from typing import Dict, Any, Optional
import time
import requests
import json


# SEC CIK映射
CIK_MAP = {
    "NVDA": "000104150",
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "TSLA": "0001318605",
}


def get_sec_filings(ticker: str) -> Dict[str, Any]:
    """从SEC获取最新财报"""
    cik = CIK_MAP.get(ticker.upper())
    if not cik:
        return {"error": f"No CIK for {ticker}"}
    
    try:
        url = f"https://efts.sec.gov/LATEST/search-index"
        params = {
            "q": ticker,
            "dateRange": "custom",
            "startdt": "2026-01-01",
            "enddt": "2026-12-31",
            "forms": "10-K,10-Q,8-K"
        }
        
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        hits = data.get("hits", {}).get("hits", [])
        filings = []
        
        for h in hits[:5]:
            source = h.get("_source", {})
            filings.append({
                "form": source.get("form", ""),
                "date": source.get("filingDate", ""),
                "description": source.get("displayName", "")
            })
        
        return {
            "ticker": ticker,
            "cik": cik,
            "filings": filings,
            "source": "SEC"
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_financial_data(ticker: str) -> Dict[str, Any]:
    """获取财务数据 - 优先SEC"""
    try:
        # 先尝试SEC
        sec_data = get_sec_filings(ticker)
        
        # 备用yfinance
        stock = yf.Ticker(ticker)
        qf = stock.quarterly_financials
        info = stock.info
        
        revenue = 0
        net_income = 0
        quarter = ""
        
        if qf is not None and not qf.empty:
            cols = qf.columns
            if len(cols) > 0:
                quarter = str(cols[0])[:7]
                if 'Total Revenue' in qf.index:
                    revenue = float(qf.loc['Total Revenue'].iloc[0])
                if 'Net Income' in qf.index:
                    net_income = float(qf.loc['Net Income'].iloc[0])
        
        return {
            "ticker": ticker,
            "quarter": quarter,
            "source": "yfinance",
            "revenue": revenue,
            "revenue_b": revenue / 1e9,
            "net_income": net_income,
            "net_income_b": net_income / 1e9,
            "market_cap_t": info.get('marketCap', 0) / 1e12,
            "pe_ratio": info.get('trailingPE', 0),
            "price": info.get('currentPrice', 0),
            "sec_filings": sec_data.get("filings", [])
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


def get_options_data(ticker: str) -> Dict[str, Any]:
    """获取期权数据"""
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
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


TOOLS = {
    "get_financial_data": get_financial_data,
    "get_options_data": get_options_data,
    "get_sec_filings": get_sec_filings,
}
