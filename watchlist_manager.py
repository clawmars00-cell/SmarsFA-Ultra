"""
Watchlist Manager - 自选股管理
支持持久化存储、与WhatsApp消息集成
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class WatchlistManager:
    """
    自选股管理器
    - 持久化到JSON文件
    - 支持添加/删除/列表操作
    - 记录添加时间和备注
    """
    
    def __init__(self, storage_path: str = "./storage/watchlist.json"):
        self.storage_path = storage_path
        self._ensure_storage()
        self.watchlist = self._load()
    
    def _ensure_storage(self):
        """确保存储目录存在"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
    
    def _load(self) -> List[Dict]:
        """加载自选股"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Load watchlist error: {e}")
        return []
    
    def _save(self):
        """保存自选股"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.watchlist, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Save watchlist error: {e}")
    
    def add(self, stock: str, note: str = "", added_by: str = "whatsapp") -> bool:
        """添加自选股"""
        stock = stock.upper()
        
        # 检查是否存在
        if any(w['stock'] == stock for w in self.watchlist):
            return False
        
        self.watchlist.append({
            'stock': stock,
            'note': note,
            'added_by': added_by,
            'added_at': datetime.now().isoformat(),
            'last_analyzed': None,
            'analysis_count': 0
        })
        self._save()
        return True
    
    def remove(self, stock: str) -> bool:
        """删除自选股"""
        stock = stock.upper()
        original_len = len(self.watchlist)
        self.watchlist = [w for w in self.watchlist if w['stock'] != stock]
        
        if len(self.watchlist) < original_len:
            self._save()
            return True
        return False
    
    def list_stocks(self) -> List[str]:
        """列出所有自选股代码"""
        return [w['stock'] for w in self.watchlist]
    
    def get_all(self) -> List[Dict]:
        """获取完整自选股列表"""
        return self.watchlist
    
    def get(self, stock: str) -> Optional[Dict]:
        """获取单个自选股信息"""
        stock = stock.upper()
        for w in self.watchlist:
            if w['stock'] == stock:
                return w
        return None
    
    def update_analysis(self, stock: str):
        """更新分析记录"""
        stock = stock.upper()
        for w in self.watchlist:
            if w['stock'] == stock:
                w['last_analyzed'] = datetime.now().isoformat()
                w['analysis_count'] = w.get('analysis_count', 0) + 1
                self._save()
                return True
        return False
    
    def clear(self):
        """清空自选股"""
        self.watchlist = []
        self._save()


# 全局实例
watchlist_manager = WatchlistManager()


if __name__ == "__main__":
    # 测试
    wm = WatchlistManager()
    
    # 添加测试
    wm.add("AAPL", "测试添加")
    wm.add("MSFT")
    wm.add("GOOGL")
    
    print("自选股列表:", wm.list_stocks())
    print("完整列表:", wm.get_all())
    
    # 删除
    wm.remove("MSFT")
    print("删除后:", wm.list_stocks())
