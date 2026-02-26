"""
Base SubAgent - 所有SubAgent的基类
"""
import json
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseSubAgent(ABC):
    """
    SubAgent基类
    - 标准化输入输出
    - 统一日志记录
    - Token成本追踪
    """
    
    def __init__(self, name: str, llm=None):
        self.name = name
        self.llm = llm
        self.latency_ms = 0
        self.tokens_used = 0
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析"""
        start_time = time.time()
        
        try:
            # 1. 构建prompt
            prompt = self.build_prompt(context)
            
            # 2. 调用LLM (或mock)
            response = self.call_llm(prompt)
            
            # 3. 解析响应
            result = self.parse_response(response)
            
            # 4. 添加元数据
            result["module"] = self.name
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            result["tokens_used"] = self.estimate_tokens(prompt, response)
            
            return result
            
        except Exception as e:
            return {
                "module": self.name,
                "confidence": 0.0,
                "key_findings": [],
                "structured_data": {},
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        """构建prompt - 子类实现"""
        raise NotImplementedError
    
    def call_llm(self, prompt: str) -> str:
        """调用LLM"""
        # Mock模式 - 返回结构化JSON
        return self.mock_response()
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """解析响应"""
        try:
            return json.loads(response)
        except:
            return {"confidence": 0.5, "key_findings": [], "structured_data": {}}
    
    def estimate_tokens(self, prompt: str, response: str) -> int:
        """估算token使用"""
        return len(prompt.split()) + len(response.split())
    
    def mock_response(self) -> str:
        """Mock响应 - 子类实现"""
        raise NotImplementedError
