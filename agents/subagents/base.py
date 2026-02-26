"""
Base SubAgent - 优化版 (超时控制)
"""
import json
import time
import subprocess
import signal
from typing import Dict, Any
from abc import ABC, abstractmethod


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException("LLM call timeout")


class BaseSubAgent(ABC):
    """优化版 SubAgent - 支持超时"""
    
    def __init__(self, name: str, llm=None):
        self.name = name
        self.llm = llm
        self.latency_ms = 0
        self.tokens_used = 0
        self.timeout = 20  # 20秒超时
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            prompt = self.build_prompt(context)
            response = self._call_llm_with_timeout(prompt)
            result = self.parse_response(response)
            
            result["module"] = self.name
            result["latency_ms"] = int((time.time() - start_time) * 1000)
            result["tokens_used"] = self.estimate_tokens(prompt, response)
            
            return result
            
        except TimeoutException:
            return {
                "module": self.name,
                "confidence": 0.5,
                "key_findings": ["LLM 调用超时"],
                "structured_data": {},
                "error": "timeout",
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                "module": self.name,
                "confidence": 0.0,
                "key_findings": [],
                "structured_data": {},
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
    
    def _call_llm_with_timeout(self, prompt: str) -> str:
        """带超时的 LLM 调用"""
        try:
            # 设置超时
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            result = self.call_llm(prompt)
            
            signal.alarm(0)  # 取消超时
            return result
            
        except TimeoutException:
            signal.alarm(0)
            raise TimeoutException("LLM call timeout")
    
    def call_llm(self, prompt: str) -> str:
        """调用 MiniMax MCP"""
        try:
            cmd = ["/home/mars/.opencode/bin/opencode", "run", prompt]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout
            )
            
            import re
            output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
            return output.strip()
            
        except subprocess.TimeoutExpired:
            return self.mock_response()
        except Exception as e:
            return self.mock_response()
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"confidence": 0.5, "key_findings": [], "structured_data": {}}
    
    def estimate_tokens(self, prompt: str, response: str) -> int:
        return len(prompt.split()) + len(response.split())
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        raise NotImplementedError
    
    def mock_response(self) -> str:
        raise NotImplementedError
