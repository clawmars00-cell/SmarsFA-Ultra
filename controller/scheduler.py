"""
Controller - 调度器
外部Controller只负责调度，不参与认知
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime


class TaskQueue:
    """任务队列"""
    
    def __init__(self):
        self.queue: List[Dict] = []
    
    def add(self, task: Dict) -> str:
        """添加任务"""
        task_id = str(uuid.uuid4())
        task["task_id"] = task_id
        task["status"] = "pending"
        task["created_at"] = datetime.now().isoformat()
        self.queue.append(task)
        return task_id
    
    def get(self) -> Optional[Dict]:
        """获取任务"""
        for task in self.queue:
            if task.get("status") == "pending":
                return task
        return None
    
    def mark_done(self, task_id: str, result: Dict):
        """标记完成"""
        for task in self.queue:
            if task.get("task_id") == task_id:
                task["status"] = "done"
                task["result"] = result
                task["completed_at"] = datetime.now().isoformat()
                break
    
    def mark_failed(self, task_id: str, error: str):
        """标记失败"""
        for task in self.queue:
            if task.get("task_id") == task_id:
                task["status"] = "failed"
                task["error"] = error
                break


class Scheduler:
    """
    调度器 - 极简版
    只负责: 调度、存储、重试
    """
    
    def __init__(self):
        self.queue = TaskQueue()
        self.master_agent = None
        self.persister = None
    
    def set_agent(self, agent):
        """设置MasterAgent"""
        self.master_agent = agent
    
    def set_persister(self, persister):
        """设置存储"""
        self.persister = persister
    
    def submit_task(self, stock: str, quarter: str = "Q4 2025", raw_text: str = "") -> str:
        """提交任务"""
        task = {
            "stock": stock,
            "quarter": quarter,
            "raw_text": raw_text
        }
        return self.queue.add(task)
    
    def process_task(self, task: Dict) -> Dict:
        """处理任务"""
        try:
            result = self.master_agent.analyze(
                task["stock"],
                task["quarter"],
                task.get("raw_text", "")
            )
            
            # 存储结果
            if self.persister:
                self.persister.save(task["stock"], task["quarter"], result)
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def run_loop(self):
        """运行循环"""
        while True:
            task = self.queue.get()
            if task:
                result = self.process_task(task)
                self.queue.mark_done(task["task_id"], result)
