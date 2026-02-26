"""
Persistence - 结果持久化
"""
import json
import os
from typing import Dict, Any, List
from datetime import datetime


class ResultStorage:
    """结果存储 - JSON文件"""
    
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.results_file = f"{storage_path}/results.json"
        self._load()
    
    def _load(self):
        """加载数据"""
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                self.results = json.load(f)
        else:
            self.results = []
    
    def _save(self):
        """保存数据"""
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def save(self, stock: str, quarter: str, result: Dict):
        """保存结果"""
        record = {
            "id": f"{stock}_{quarter}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "stock": stock,
            "quarter": quarter,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        self.results.append(record)
        self._save()
    
    def get_all(self, stock: str = None) -> List[Dict]:
        """获取所有结果"""
        if stock:
            return [r for r in self.results if r.get("stock") == stock]
        return self.results
    
    def get_latest(self, stock: str) -> Dict:
        """获取最新结果"""
        stock_results = self.get_all(stock)
        if stock_results:
            return stock_results[-1]
        return None
