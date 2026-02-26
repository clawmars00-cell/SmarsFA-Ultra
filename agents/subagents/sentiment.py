"""
SentimentSubAgent - 情绪分析专家
集成 LLM + MCP web_search 获取实时新闻
"""
from .base import BaseSubAgent


class SentimentAgent(BaseSubAgent):
    """情绪分析 - LLM + 实时新闻"""
    
    def __init__(self, llm=None):
        super().__init__("sentiment", llm)
    
    def build_prompt(self, context: dict) -> str:
        financial = context.get("financial_metrics", {})
        
        return f"""你是情绪分析专家。基于以下财务数据和市场新闻分析投资者情绪:

股票: {context.get('stock')}
季度: {context.get('quarter')}

财务指标:
{financial}

请返回JSON格式:
{{
    "confidence": 0.75,
    "key_findings": ["发现1", "发现2"],
    "structured_data": {{
        "analyst_sentiment": 0.65,
        "social_sentiment": 0.58,
        "sentiment_velocity": "UPWARD/DOWNWARD/STABLE",
        "news_count": 10,
        "key_topics": ["话题1", "话题2"]
    }},
    "risk_flags": []
}}"""
    
    def run(self, context: dict) -> dict:
        """执行分析"""
        import time
        import subprocess
        start = time.time()
        
        stock = context.get("stock", "NVDA")
        
        # 1. 通过 MCP web_search 获取新闻
        news_summary = ""
        try:
            cmd = ["/home/mars/.opencode/bin/opencode", "run", 
                   f"用 web_search 搜索 {stock} 最新财报新闻"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            import re
            news_summary = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
            # 截取前500字
            news_summary = news_summary[:500] if len(news_summary) > 500 else news_summary
        except:
            news_summary = "无法获取新闻"
        
        # 2. 构建 prompt
        prompt = self.build_prompt(context)
        
        # 3. 调用 LLM
        llm_result = self.call_llm(prompt)
        analysis = self.parse_response(llm_result)
        
        return {
            "module": "sentiment",
            "confidence": analysis.get("confidence", 0.70),
            "key_findings": analysis.get("key_findings", []),
            "structured_data": {
                **analysis.get("structured_data", {}),
                "news_summary": news_summary[:200]
            },
            "risk_flags": analysis.get("risk_flags", []),
            "latency_ms": int((time.time() - start) * 1000),
            "tokens_used": self.estimate_tokens(prompt, llm_result)
        }
    
    def mock_response(self) -> str:
        return """{
    "confidence": 0.75,
    "key_findings": ["分析师情绪偏正面", "社交媒体讨论增加"],
    "structured_data": {
        "analyst_sentiment": 0.65,
        "social_sentiment": 0.58,
        "sentiment_velocity": "UPWARD",
        "news_count": 15
    },
    "risk_flags": []
}"""
