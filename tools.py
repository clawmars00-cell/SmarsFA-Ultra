"""
Tools - 增强版数据获取
支持手动输入实际财报数据
"""
import yfinance as yf
from typing import Dict, Any, Optional


def get_financial_data(ticker: str, actual_data: Optional[Dict] = None) -> Dict[str, Any]:
    """获取财务数据"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 如果有手动输入的实际数据，优先使用
        if actual_data:
            return {
                "ticker": ticker,
                "source": "manual",
                "revenue": actual_data.get("revenue", 0),
                "revenue_b": actual_data.get("revenue", 0) / 1e9,
                "net_income": actual_data.get("net_income", 0),
                "net_income_b": actual_data.get("net_income", 0) / 1e9,
                "eps": actual_data.get("eps", 0),
                "beat_percent": actual_data.get("beat_percent", 0),
            }
        
        # 否则从yfinance获取
        qf = stock.quarterly_financials
        qi = stock.quarterly_income_stmt
        
        revenue = 0
        net_income = 0
        if qf is not None and not qf.empty:
            if 'Total Revenue' in qf.index:
                revenue = float(qf.loc['Total Revenue'].iloc[0])
            if 'Net Income' in qf.index:
                net_income = float(qf.loc['Net Income'].iloc[0])
        
        eps = 0
        if qi is not None and not qi.empty:
            if 'Diluted EPS' in qi.index:
                eps = float(qi.loc['Diluted EPS'].iloc[0])
        
        return {
            "ticker": ticker,
            "source": "yfinance",
            "revenue": revenue,
            "revenue_b": revenue / 1e9,
            "net_income": net_income,
            "net_income_b": net_income / 1e9,
            "eps": eps,
            "gross_margin": info.get('grossMargins', 0),
            "operating_margin": info.get('operatingMargins', 0),
            "net_margin": info.get('profitMargins', 0),
            "market_cap_t": info.get('marketCap', 0) / 1e12 if info.get('marketCap') else 0,
            "pe_ratio": info.get('trailingPE', 0),
            "price": info.get('currentPrice', 0),
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
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


TOOLS = {
    "get_financial_data": get_financial_data,
    "get_options_chain": get_options_chain,
}
