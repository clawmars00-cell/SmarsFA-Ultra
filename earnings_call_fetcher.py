"""
Earnings Call Highlights Fetcher - 财报电话会议要点获取
使用MCP搜索获取财报电话会议要点
"""
import subprocess
import re
from datetime import datetime


class EarningsCallFetcher:
    """
    获取财报电话会议要点
    """
    
    def __init__(self, timeout: int = 45):
        self.timeout = timeout
    
    def fetch_highlights(self, symbol: str, quarter: str = "Q4 2026") -> dict:
        """
        获取财报电话会议要点
        
        Args:
            symbol: 股票代码 (如NVDA)
            quarter: 季度 (如Q4 2026)
        
        Returns:
            dict: {
                'highlights': ['要点1', '要点2'],
                'source': 'search',
                'timestamp': '...'
            }
        """
        query = f"{symbol} {quarter} earnings call transcript key highlights"
        
        result = self._search(query)
        
        if result:
            return {
                'symbol': symbol,
                'quarter': quarter,
                'highlights': result,
                'source': 'mcp_search',
                'fetched_at': datetime.now().isoformat()
            }
        
        return None
    
    def _search(self, query: str) -> list:
        """执行搜索"""
        cmd = [
            "/home/mars/.opencode/bin/opencode", "run",
            query
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # 清理输出
            output = self._clean_output(result.stdout)
            
            # 提取要点
            highlights = self._extract_highlights(output)
            
            return highlights
        
        except subprocess.TimeoutExpired:
            print(f"Search timeout for: {query}")
            return None
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    def _clean_output(self, output: str) -> str:
        """清理输出"""
        # 移除ANSI颜色码
        output = re.sub(r'\x1b\[[0-9;]*m', '', output)
        return output.strip()
    
    def _extract_highlights(self, text: str) -> list:
        """从搜索结果中提取关键要点"""
        lines = text.split('\n')
        
        highlights = []
        for line in lines:
            line = line.strip()
            
            # 跳过空行和系统消息
            if not line or line.startswith('[') or line.startswith('◈'):
                continue
            
            # 清理前缀
            if '**' in line:
                # 移除markdown bold
                line = line.replace('**', '')
            
            # 过滤太短的行
            if len(line) < 20:
                continue
            
            # 保留关键行
            if any(kw in line.lower() for kw in ['revenue', 'growth', 'ai', 'data center', 'eps', 'profit', 'guidance', 'outlook', 'jensen', 'billion', '%']):
                highlights.append(line)
        
        # 返回前10条
        return highlights[:10]


# 测试
if __name__ == "__main__":
    fetcher = EarningsCallFetcher()
    
    result = fetcher.fetch_highlights('NVDA', 'Q4 2026')
    
    if result:
        print(f"=== {result['symbol']} {result['quarter']} 财报电话会议要点 ===")
        for i, h in enumerate(result['highlights'], 1):
            print(f"{i}. {h}")
    else:
        print("未获取到要点")
