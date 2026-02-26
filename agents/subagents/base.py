"""
Base SubAgent - 所有SubAgent的基类
集成 MiniMax MCP 进行真正的 LLM 调用
"""
import json
import time
import subprocess
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


OPENCODE_CMD = "/home/mars/.opencode/bin/opencode"


class BaseSubAgent(ABC):
    """
    SubAgent基类
    - 标准化输入输出
    - 统一日志记录
    - Token成本追踪
    - MiniMax MCP LLM 集成
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
            
            # 2. 调用LLM (MiniMax MCP)
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
        """调用 MiniMax MCP LLM"""
        try:
            # 使用 opencode 调用 MiniMax MCP
            cmd = [OPENCODE_CMD, "run", prompt]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 清理 ANSI 颜色码
            import re
            output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
            return output.strip()
            
        except subprocess.TimeoutExpired:
            return self.mock_response()
        except Exception as e:
            print(f"LLM call failed: {e}, using mock")
            return self.mock_response()
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """解析响应"""
        try:
            # 尝试提取 JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"confidence": 0.5, "key_findings": [], "structured_data": {}}
    
    def estimate_tokens(self, prompt: str, response: str) -> int:
        """估算token使用"""
        return len(prompt.split()) + len(response.split())
    
    def mock_response(self) -> str:
        """Mock响应 - 子类实现"""
        raise NotImplementedError
