"""
Message Bus - SubAgent 消息通信总线
基于 PRD 设计的 Pub/Sub 模式
"""
import asyncio
import json
from typing import Dict, List, Callable, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


class MessageType(Enum):
    AGENT_REQUEST = "AGENT_REQUEST"
    AGENT_RESPONSE = "AGENT_RESPONSE"
    CONTROL_SIGNAL = "CONTROL_SIGNAL"
    ERROR = "ERROR"


@dataclass
class Message:
    """消息结构"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    msg_type: MessageType = MessageType.AGENT_REQUEST
    from_agent: str = ""
    to_agent: str = ""
    payload: Dict = field(default_factory=dict)
    correlation_id: str = ""  # 用于关联请求/响应
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['msg_type'] = self.msg_type.value
        return d


class MessageBus:
    """
    消息总线 - SubAgent 间通信
    支持 Pub/Sub 模式
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    async def start(self):
        """启动消息总线"""
        self._running = True
    
    async def stop(self):
        """停止消息总线"""
        self._running = False
    
    def subscribe(self, agent_name: str, callback: Callable):
        """订阅消息"""
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(callback)
    
    def unsubscribe(self, agent_name: str, callback: Callable):
        """取消订阅"""
        if agent_name in self._subscribers:
            self._subscribers[agent_name].remove(callback)
    
    async def publish(self, message: Message):
        """发布消息"""
        await self._queue.put(message)
    
    async def receive(self, agent_name: str, timeout: float = 30.0) -> Message:
        """接收消息 (阻塞)"""
        try:
            while self._running:
                msg = await asyncio.wait_for(self._queue.get(), timeout=timeout)
                
                # 检查是否是发给自己的
                if msg.to_agent == agent_name or msg.to_agent == "BROADCAST":
                    return msg
                
                # 不是发给自己的，放回队列
                await self._queue.put(msg)
                
        except asyncio.TimeoutError:
            return None
    
    def get_queue_size(self) -> int:
        return self._queue.qsize()


# 全局消息总线实例
message_bus = MessageBus()
