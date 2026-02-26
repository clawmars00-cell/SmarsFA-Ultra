"""
Controller Scheduler v2
- 定期抓取财报日历
- 触发分析任务
"""
import time
import json
import asyncio
from datetime import datetime, timedelta
from earnings_calendar import get_upcoming_earnings
from main import master_agent


class Controller:
    """
    外部 Controller
    1. 抓取财报日历
    2. 触发分析
    """
    
    def __init__(self):
        self.watchlist = self._load_watchlist()
        self.results_file = "./storage/controller_results.json"
    
    def _load_watchlist(self) -> list:
        """加载关注列表"""
        return [
            "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN",
            "META", "TSLA", "AMD", "INTC", "AVGO"
        ]
    
    def run_daily(self):
        """每日运行"""
        print(f"\n{'='*60}")
        print(f"Controller - Daily Run {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")
        
        # 1. 获取财报日历
        print("\n[1] Fetching earnings calendar...")
        earnings = get_upcoming_earnings()
        
        # 2. 过滤关注列表
        watchlist_earnings = [
            e for e in earnings 
            if e.get('stock') in self.watchlist
        ]
        
        print(f"\n[2] Found {len(watchlist_earnings)} earnings in watchlist:")
        for e in watchlist_earnings[:10]:
            print(f"  - {e.get('stock')}: {e.get('date')}")
        
        # 3. 触发分析
        print(f"\n[3] Triggering analysis...")
        results = []
        
        for e in watchlist_earnings:
            stock = e.get('stock')
            date = e.get('date')
            
            print(f"\n  Analyzing {stock}...")
            
            try:
                # 实际调用 (这里用模拟数据)
                result = master_agent.analyze(
                    stock=stock,
                    quarter="Q4 2025",
                    actual_data={
                        "revenue": e.get('expected_revenue', 50) * 1e9,
                        "eps": e.get('expected_eps', 1.0)
                    }
                )
                
                results.append({
                    "stock": stock,
                    "date": date,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"    ✓ {stock}: {result.get('result', {}).get('structured_data', {}).get('recommendation', 'N/A')}")
                
            except Exception as e:
                print(f"    ❌ {stock}: {e}")
        
        # 4. 保存结果
        self._save_results(results)
        
        print(f"\n{'='*60}")
        print(f"Complete! Analyzed {len(results)} stocks")
        print(f"{'='*60}")
        
        return results
    
    def _save_results(self, results: list):
        """保存结果"""
        import os
        os.makedirs("./storage", exist_ok=True)
        
        # 加载旧结果
        try:
            with open(self.results_file, 'r') as f:
                all_results = json.load(f)
        except:
            all_results = []
        
        # 添加新结果
        all_results.extend(results)
        
        # 只保留最近30天
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        all_results = [r for r in all_results if r.get('timestamp', '') > cutoff]
        
        with open(self.results_file, 'w') as f:
            json.dump(all_results, f, indent=2)


if __name__ == "__main__":
    controller = Controller()
    controller.run_daily()
