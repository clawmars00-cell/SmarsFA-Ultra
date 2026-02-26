"""
Controller Scheduler v2
- 抓取所有市值>10亿财报
- 触发分析
"""
import time
import json
from datetime import datetime, timedelta
from earnings_calendar import get_all_upcoming_earnings
from main import master_agent


class Controller:
    """
    Controller - 扫描所有符合条件的财报
    """
    
    def __init__(self):
        self.min_market_cap = 10e9  # 10B
        self.results_file = "./storage/controller_results.json"
    
    def run_daily(self):
        """每日运行"""
        print(f"\n{'='*60}")
        print(f"Controller - Daily Run {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Filter: Market Cap > $10B")
        print(f"{'='*60}")
        
        # 1. 获取所有财报
        print("\n[1] Fetching ALL earnings...")
        all_earnings = get_all_upcoming_earnings()
        
        # 2. 过滤市值>10B
        print(f"\n[2] Filtering market cap > $10B...")
        valid_earnings = [
            e for e in all_earnings
            if e.get('market_cap', 0) > self.min_market_cap
        ]
        
        print(f"\n[3] Found {len(valid_earnings)} earnings:")
        for e in valid_earnings[:15]:
            cap = e.get('market_cap', 0) / 1e9
            print(f"  - {e.get('stock')}: {e.get('date')}, ${cap:.0f}B")
        
        # 4. 触发分析 (可选，只分析前10个)
        print(f"\n[4] Triggering analysis (top 10)...")
        
        results = []
        for e in valid_earnings[:10]:
            stock = e.get('stock')
            
            try:
                result = master_agent.analyze(
                    stock=stock,
                    quarter="Q4 2025",
                    actual_data={
                        "revenue": (e.get('expected_revenue') or 50) * 1e9,
                        "eps": e.get('expected_eps') or 1.0
                    }
                )
                
                rec = result.get('result', {}).get('structured_data', {}).get('recommendation', 'N/A')
                print(f"  ✓ {stock}: {rec}")
                
                results.append({
                    "stock": stock,
                    "date": e.get('date'),
                    "market_cap": e.get('market_cap'),
                    "result": result
                })
                
            except Exception as ex:
                print(f"  ❌ {stock}: {ex}")
        
        # 5. 保存
        self._save_results(results)
        
        print(f"\n{'='*60}")
        print(f"Complete! Analyzed {len(results)} stocks")
        print(f"{'='*60}")
        
        return results
    
    def _save_results(self, results: list):
        import os
        os.makedirs("./storage", exist_ok=True)
        
        try:
            with open(self.results_file, 'r') as f:
                all_results = json.load(f)
        except:
            all_results = []
        
        all_results.extend(results)
        
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        all_results = [r for r in all_results if r.get('timestamp', '') > cutoff]
        
        with open(self.results_file, 'w') as f:
            json.dump(all_results, f, indent=2)


if __name__ == "__main__":
    controller = Controller()
    controller.run_daily()
