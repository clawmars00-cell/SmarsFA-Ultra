# SmarsFA-Ultra DAG 工作流引擎
# 有条件分支 + 多Agent协作

import asyncio
import json
import os
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from models.earnings import EarningsReport, ExtractionMetrics
except ImportError:
    from models.earnings import EarningsReport, ExtractionMetrics


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """工作流状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowNode:
    """工作流节点"""
    id: str
    node_type: str  # "agent", "decision", "action"
    agent: str = None  # agent name
    action: str = None  # action name
    condition: str = None  # decision condition
    next: str = None  # next node id
    branches: list = field(default_factory=list)  # branches for decision
    status: NodeStatus = NodeStatus.PENDING
    input_data: dict = field(default_factory=dict)
    output_data: Any = None
    error: str = None
    started_at: datetime = None
    completed_at: datetime = None


@dataclass
class WorkflowExecution:
    """工作流执行记录"""
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.RUNNING
    nodes: dict[str, WorkflowNode] = field(default_factory=dict)
    current_node: str = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = None
    fallback_triggered: bool = False
    metadata: dict = field(default_factory=dict)
    
    @property
    def is_complete(self) -> bool:
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
    
    @property
    def duration_seconds(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.now() - self.started_at).total_seconds()


class WorkflowEngine:
    """
    DAG 工作流引擎
    
    支持:
    - 有条件分支 (Conditional Branching)
    - Agent 调用
    - 状态持久化
    - Fallback 机制
    - 超时处理
    - 重试机制 (最多3次)
    - 暂停/恢复功能
    """
    
    # 默认配置
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_TIMEOUT_SECONDS = 300
    DEFAULT_RETRY_DELAY = 1.0  # 重试间隔(秒)
    
    def __init__(self, workflow_config: dict):
        self.config = workflow_config
        self.workflow_id = workflow_config.get("workflow_id", "default")
        self.nodes = self._build_nodes(workflow_config)
        self.execution: Optional[WorkflowExecution] = None
        
        # 错误处理配置
        self.max_retries = workflow_config.get("max_retries", self.DEFAULT_MAX_RETRIES)
        self.timeout_seconds = workflow_config.get("timeout_seconds", self.DEFAULT_TIMEOUT_SECONDS)
        self.retry_delay = workflow_config.get("retry_delay", self.DEFAULT_RETRY_DELAY)
        
        # 暂停/恢复状态
        self._paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # 默认不暂停
        
        # 持久化路径
        self.state_file = workflow_config.get("state_file", f"/tmp/workflow_{self.workflow_id}_state.json")
        
        # 日志记录
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录器"""
        self.logger = logging.getLogger(f"workflow.{self.workflow_id}")
        self.logger.setLevel(logging.INFO)
        
    def _build_nodes(self, config: dict) -> dict[str, WorkflowNode]:
        """构建节点"""
        nodes = {}
        for node_config in config.get("states", []):
            node = WorkflowNode(
                id=node_config["id"],
                node_type=node_config.get("type", "agent"),
                agent=node_config.get("agent"),
                action=node_config.get("action"),
                condition=node_config.get("condition"),
                next=node_config.get("next"),
                branches=node_config.get("branches", [])
            )
            nodes[node.id] = node
        return nodes
    
    async def run(
        self,
        input_data: dict,
        context: dict = None
    ) -> WorkflowExecution:
        """
        执行工作流
        
        Args:
            input_data: 输入数据
            context: 上下文 (包含 agent 调用函数等)
            
        Returns:
            WorkflowExecution: 执行结果
        """
        self.logger.info(f"开始执行工作流: {self.workflow_id}")
        
        # 初始化执行
        self.execution = WorkflowExecution(
            workflow_id=self.workflow_id,
            nodes={k: WorkflowNode(**{**v.__dict__, 'status': NodeStatus.PENDING}) 
                   for k, v in self.nodes.items()}
        )
        
        # 设置上下文
        self.context = context or {}
        self.input_data = input_data
        
        # 重置暂停状态
        self._paused = False
        self._pause_event.set()
        
        # 找到起始节点
        start_node = self._find_start_node()
        if not start_node:
            self.logger.error("未找到起始节点")
            raise ValueError("未找到起始节点")
        
        self.logger.info(f"起始节点: {start_node.id}")
        
        # 执行工作流
        current = start_node
        while current and not self.execution.is_complete:
            # 检查是否暂停
            await self._check_pause()
            
            # 更新节点状态
            if current.id in self.execution.nodes:
                self.execution.nodes[current.id].status = NodeStatus.RUNNING
            
            # 执行节点 (带重试和超时)
            await self._execute_node_with_retry(current, input_data)
            
            # 更新节点状态
            if current.id in self.execution.nodes:
                self.execution.nodes[current.id].status = current.status
            
            # 持久化状态
            self._persist_state()
            
            # 确定下一个节点
            next_node = self._get_next_node(current)
            
            # 如果没有下一个节点且当前已完成，标记工作流完成
            if next_node is None and current.status == NodeStatus.COMPLETED:
                self.execution.status = WorkflowStatus.COMPLETED
                self.logger.info(f"工作流完成: {self.workflow_id}")
            
            current = next_node
        
        self.execution.completed_at = datetime.now()
        
        # 最终持久化
        self._persist_state()
        
        return self.execution
    
    async def _check_pause(self):
        """检查是否需要暂停"""
        if self._paused:
            self.logger.info("工作流已暂停，等待恢复...")
            await self._pause_event.wait()
            self.logger.info("工作流恢复执行")
    
    async def _execute_node_with_retry(self, node: WorkflowNode, data: dict):
        """
        执行节点 (带重试机制)
        
        最多重试 max_retries 次
        """
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                # 检查超时
                result = await asyncio.wait_for(
                    self._execute_node(node, data),
                    timeout=self.timeout_seconds
                )
                self.logger.info(f"节点 {node.id} 执行成功 (尝试 {attempt + 1}/{self.max_retries})")
                return result
                
            except asyncio.TimeoutError:
                last_error = f"节点 {node.id} 执行超时 ({self.timeout_seconds}秒)"
                self.logger.warning(f"{last_error} (尝试 {attempt + 1}/{self.max_retries})")
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"节点 {node.id} 执行失败: {last_error} (尝试 {attempt + 1}/{self.max_retries})")
            
            attempt += 1
            
            if attempt < self.max_retries:
                # 重试延迟
                self.logger.info(f"等待 {self.retry_delay} 秒后重试...")
                await asyncio.sleep(self.retry_delay)
        
        # 所有重试都失败
        self.logger.error(f"节点 {node.id} 执行失败，已重试 {self.max_retries} 次: {last_error}")
        node.status = NodeStatus.FAILED
        node.error = last_error
        self.execution.status = WorkflowStatus.FAILED
    
    def _find_start_node(self) -> Optional[WorkflowNode]:
        """找到起始节点 (没有其他节点指向它)"""
        # 简单实现：找到第一个
        return list(self.nodes.values())[0] if self.nodes else None
    
    async def _execute_node(self, node: WorkflowNode, data: dict):
        """执行单个节点"""
        print(f"[Workflow] 执行节点: {node.id}")
        
        node.status = NodeStatus.RUNNING
        node.started_at = datetime.now()
        self.execution.current_node = node.id
        
        try:
            if node.node_type == "agent":
                # 执行 Agent
                result = await self._execute_agent(node, data)
                node.output_data = result
                
            elif node.node_type == "decision":
                # 执行决策
                next_node = await self._execute_decision(node, data)
                node.output_data = {"next": next_node}
                
            elif node.node_type == "action":
                # 执行动作
                result = await self._execute_action(node, data)
                node.output_data = result
            
            node.status = NodeStatus.COMPLETED
            node.completed_at = datetime.now()
            
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.completed_at = datetime.now()
            print(f"[Workflow] 节点 {node.id} 失败: {e}")
            self.execution.status = WorkflowStatus.FAILED
    
    async def _execute_agent(self, node: WorkflowNode, data: dict) -> Any:
        """执行 Agent 节点"""
        agent_name = node.agent
        action = node.action
        
        # 从上下文获取 Agent 调用函数
        agent_func = self.context.get(f"agent_{agent_name}")
        
        if agent_func:
            # 调用 Agent
            result = await agent_func(node.input_data)
            return result
        else:
            # 模拟执行
            print(f"[Workflow] 模拟执行 Agent: {agent_name}")
            await asyncio.sleep(0.5)
            return {"status": "completed", "agent": agent_name}
    
    async def _execute_decision(self, node: WorkflowNode, data: dict) -> str:
        """执行决策节点"""
        condition = node.condition
        
        try:
            # 简化决策逻辑
            # 检查是否需要 fallback
            confidence = data.get('confidence_score', 1.0)
            guidance = data.get('guidance')
            
            # 决策: confidence < 0.8 或 guidance == null
            need_fallback = confidence < 0.8 or guidance is None
            
            print(f"[Workflow] 决策: confidence={confidence}, guidance={guidance}, fallback={need_fallback}")
            
            if need_fallback:
                return "spawn_searcher"
            else:
                return "finalize_report"
                        
        except Exception as e:
            print(f"[Workflow] 决策评估失败: {e}")
        
        return node.next
    
    async def _execute_action(self, node: WorkflowNode, data: dict) -> Any:
        """执行动作节点"""
        action = node.action
        
        if action == "save_to_db":
            # 保存到数据库
            print(f"[Workflow] 保存到数据库: {data}")
            return {"saved": True}
        
        return {"action": action}
    
    def _get_next_node(self, node: WorkflowNode) -> Optional[WorkflowNode]:
        """获取下一个节点"""
        if node.status == NodeStatus.FAILED:
            return None
        
        if node.node_type == "decision" and node.output_data:
            # 决策节点根据结果跳转
            next_id = node.output_data.get("next", node.next)
        else:
            next_id = node.next
        
        if next_id and next_id in self.nodes:
            return self.nodes[next_id]
        
        return None
    
    def get_status(self) -> dict:
        """获取工作流状态"""
        if not self.execution:
            return {"status": "not_started"}
        
        # 计算节点执行时间
        node_timings = {}
        for k, v in self.execution.nodes.items():
            timing = {}
            if v.started_at:
                timing["started_at"] = v.started_at.isoformat()
            if v.completed_at:
                timing["completed_at"] = v.completed_at.isoformat()
            if v.started_at and v.completed_at:
                timing["duration_seconds"] = (v.completed_at - v.started_at).total_seconds()
            node_timings[k] = timing
        
        return {
            "workflow_id": self.workflow_id,
            "status": self.execution.status.value,
            "current_node": self.execution.current_node,
            "duration_seconds": self.execution.duration_seconds,
            "fallback_triggered": self.execution.fallback_triggered,
            "paused": self._paused,
            "nodes": {
                k: {
                    "status": v.status.value, 
                    "error": v.error,
                    "started_at": v.started_at.isoformat() if v.started_at else None,
                    "completed_at": v.completed_at.isoformat() if v.completed_at else None,
                    "duration_seconds": (v.completed_at - v.started_at).total_seconds() 
                                        if v.started_at and v.completed_at else None
                }
                for k, v in self.execution.nodes.items()
            },
            "node_timings": node_timings
        }
    
    def get_node_status(self, node_id: str) -> Optional[dict]:
        """
        获取指定节点状态
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点状态字典，如果节点不存在返回 None
        """
        if not self.execution or node_id not in self.execution.nodes:
            return None
        
        node = self.execution.nodes[node_id]
        return {
            "node_id": node_id,
            "status": node.status.value,
            "error": node.error,
            "started_at": node.started_at.isoformat() if node.started_at else None,
            "completed_at": node.completed_at.isoformat() if node.completed_at else None,
            "duration_seconds": (node.completed_at - node.started_at).total_seconds() 
                               if node.started_at and node.completed_at else None,
            "output_data": node.output_data,
            "input_data": node.input_data
        }
    
    def pause(self) -> bool:
        """
        暂停工作流
        
        Returns:
            是否成功暂停
        """
        if self.execution and self.execution.status == WorkflowStatus.RUNNING:
            self._paused = True
            self._pause_event.clear()
            self.logger.info(f"工作流已暂停: {self.workflow_id}")
            self._persist_state()
            return True
        return False
    
    def resume(self) -> bool:
        """
        恢复工作流
        
        Returns:
            是否成功恢复
        """
        if self._paused:
            self._paused = False
            self._pause_event.set()
            self.logger.info(f"工作流已恢复: {self.workflow_id}")
            self._persist_state()
            return True
        return False
    
    def _persist_state(self):
        """持久化工作流状态到文件"""
        try:
            if self.execution:
                state = {
                    "workflow_id": self.workflow_id,
                    "status": self.execution.status.value,
                    "current_node": self.execution.current_node,
                    "started_at": self.execution.started_at.isoformat() if self.execution.started_at else None,
                    "completed_at": self.execution.completed_at.isoformat() if self.execution.completed_at else None,
                    "paused": self._paused,
                    "nodes": {
                        k: {
                            "status": v.status.value,
                            "error": v.error,
                            "started_at": v.started_at.isoformat() if v.started_at else None,
                            "completed_at": v.completed_at.isoformat() if v.completed_at else None
                        }
                        for k, v in self.execution.nodes.items()
                    }
                }
                
                os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
                with open(self.state_file, 'w') as f:
                    json.dump(state, f, indent=2, default=str)
                
                self.logger.debug(f"状态已持久化: {self.state_file}")
        except Exception as e:
            self.logger.warning(f"状态持久化失败: {e}")
    
    def load_state(self) -> bool:
        """
        从文件加载工作流状态
        
        Returns:
            是否成功加载
        """
        if not os.path.exists(self.state_file):
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # 恢复状态
            self._paused = state.get("paused", False)
            
            if self.execution:
                status_str = state.get("status")
                if status_str:
                    self.execution.status = WorkflowStatus(status_str)
                
                self.execution.current_node = state.get("current_node")
                
                # 恢复节点状态
                nodes_state = state.get("nodes", {})
                for node_id, node_state in nodes_state.items():
                    if node_id in self.execution.nodes:
                        status_val = node_state.get("status")
                        if status_val:
                            self.execution.nodes[node_id].status = NodeStatus(status_val)
                        self.execution.nodes[node_id].error = node_state.get("error")
            
            self.logger.info(f"状态已加载: {self.state_file}")
            return True
            
        except Exception as e:
            self.logger.warning(f"状态加载失败: {e}")
            return False


# ====================
# 工作流加载
# ====================

def load_workflow(config_path: str) -> WorkflowEngine:
    """从 YAML 加载工作流"""
    import yaml
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return WorkflowEngine(config)


# ====================
# 预定义工作流
# ====================

def get_earnings_extraction_workflow() -> dict:
    """获取财报提取工作流配置"""
    return {
        "workflow_id": "earnings_extraction_pipeline",
        "config": {
            "name": "Earnings Data Extraction Pipeline",
            "max_retries": 2,
            "timeout_seconds": 300
        },
        "states": [
            {
                "id": "primary_extraction",
                "type": "agent",
                "agent": "smars-coder",
                "action": "extract_from_pdf",
                "next": "validate_data"
            },
            {
                "id": "validate_data",
                "type": "decision",
                "condition": "${confidence_score} < 0.8 || ${guidance} == null",
                "branches": [
                    {"condition": "true", "next": "spawn_searcher"},
                    {"condition": "false", "next": "finalize_report"}
                ]
            },
            {
                "id": "spawn_searcher",
                "type": "agent",
                "agent": "smars-searcher",
                "action": "web_search_and_extract",
                "next": "merge_results"
            },
            {
                "id": "merge_results",
                "type": "agent",
                "agent": "smars-reviewer",
                "action": "resolve_conflicts",
                "next": "finalize_report"
            },
            {
                "id": "finalize_report",
                "type": "action",
                "action": "save_to_db",
                "next": None
            }
        ]
    }


async def main():
    """测试工作流"""
    # 创建工作流
    workflow_config = get_earnings_extraction_workflow()
    engine = WorkflowEngine(workflow_config)
    
    # 执行
    result = await engine.run(
        input_data={
            "ticker": "NVDA",
            "input_file": "./data/NVDA_10Q.pdf",
            "confidence_score": 0.85,
            "guidance": "We expect Q2 revenue to be $36 billion"
        }
    )
    
    print("\n" + "="*60)
    print("📊 工作流执行结果")
    print("="*60)
    print(json.dumps(engine.get_status(), indent=2, default=str))
    
    return result


if __name__ == "__main__":
    asyncio.run(main())
