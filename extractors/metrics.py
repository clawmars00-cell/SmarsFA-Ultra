# SmarsFA-Ultra 核心指标提取器
# 使用黄金 Prompt 从财报原文中提取财务指标

import asyncio
import json
import os
import re
from typing import Optional
from datetime import datetime
from pathlib import Path

# 数据模型
try:
    from ..models.earnings import (
        EarningsReport, FinancialMetrics, FinancialMetric,
        SentimentScore, DataQuality, ExtractionMetrics
    )
except ImportError:
    from models.earnings import (
        EarningsReport, FinancialMetrics, FinancialMetric,
        SentimentScore, DataQuality, ExtractionMetrics
    )


class EarningsExtractor:
    """
    财报指标提取器
    
    使用 Qwen 3.5-plus 的长文本能力 + 黄金 Prompt
    支持 CoT (思维链) + Schema 强约束
    """
    
    def __init__(
        self,
        prompt_template: str = "earnings_v3",
        model_name: str = "qwen3.5-plus",
        output_dir: str = "./storage/extractions"
    ):
        self.prompt_template = prompt_template
        self.model_name = model_name
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载 Prompt 模板
        self._load_prompt_template()
        
    def _load_prompt_template(self):
        """加载 Prompt 模板"""
        # 尝试从 prompts 目录加载
        possible_paths = [
            f"./prompts/{self.prompt_template}.yaml",
            f"../prompts/{self.prompt_template}.yaml",
            f"../../prompts/{self.prompt_template}.yaml",
            f"/home/mars/.openclaw/workspace/SmarsFA/prompts/{self.prompt_template}.yaml"
        ]
        
        self.prompt = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    content = f.read()
                    # 提取 prompt 部分
                    if 'prompt: |' in content:
                        start = content.find('prompt: |') + len('prompt: |')
                        end = content.find('# =', start)
                        if end == -1:
                            end = len(content)
                        self.prompt = content[start:end].strip()
                        print(f"[Extractor] 加载 Prompt: {path}")
                        break
        
        if not self.prompt:
            print("[Extractor] 未找到 Prompt 模板，使用内置版本")
            self.prompt = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """内置默认 Prompt"""
        return """# Role
你是一位拥有 CFA 资格的高级金融数据分析师。

# Task
从提供的财报原文中，提取关键财务指标。

# Output Format
{"ticker": "", "financials": {"revenue": {"actual": 0}, "eps": {"actual": 0}}}
"""
    
    async def extract(
        self,
        ticker: str,
        raw_text: str,
        fiscal_quarter: str = None,
        source: str = "10-Q"
    ) -> tuple[EarningsReport, ExtractionMetrics]:
        """
        从财报原文中提取指标
        
        Args:
            ticker: 股票代码
            raw_text: 财报原文
            fiscal_quarter: 财报季度 (如 "2026 Q1")
            source: 数据来源 (10-Q, 10-K, etc.)
            
        Returns:
            (EarningsReport, ExtractionMetrics)
        """
        start_time = datetime.now()
        
        # 构建 Prompt
        prompt = self._build_prompt(raw_text)
        
        # 调用 LLM (模拟)
        response_text = await self._call_llm(prompt)
        
        # 解析 JSON
        extracted_data = self._parse_json_response(response_text)
        
        # 构建 EarningsReport
        report = self._build_report(
            ticker=ticker,
            extracted_data=extracted_data,
            fiscal_quarter=fiscal_quarter,
            source=source,
            raw_text_length=len(raw_text)
        )
        
        # 计算指标
        metrics = self._calculate_metrics(
            prompt=prompt,
            response=response_text,
            start_time=start_time,
            report=report
        )
        
        # 保存结果
        self._save_result(ticker, report, metrics)
        
        return report, metrics
    
    def _build_prompt(self, raw_text: str) -> str:
        """构建完整的 Prompt"""
        # 动态 Token 路由：如果文本过长，先截取关键部分
        text = self._preprocess_text(raw_text)
        
        return f"""
{self.prompt}

# Context (Raw Text)
### START OF TEXT ###
{text}
### END OF TEXT ###
"""
    
    def _preprocess_text(self, text: str, max_tokens: int = 50000) -> str:
        """
        预处理文本 - 动态 Token 路由
        
        如果文本过长，提取关键章节
        """
        # 简单截断 (实际应该用 token 计数)
        if len(text) > max_tokens * 4:  # 粗略估算 1 token ~ 4 字符
            # 提取关键部分
            key_sections = [
                "Financial Highlights",
                "Results of Operations", 
                "Management Discussion",
                "Earnings Call"
            ]
            
            truncated = text
            for section in key_sections:
                if section.lower() in text.lower():
                    idx = text.lower().find(section.lower())
                    # 保留该章节及后面 5000 字符
                    truncated = text[idx:idx+8000]
                    break
            
            print(f"[Extractor] 文本从 {len(text)} 截断到 {len(truncated)} 字符")
            return truncated
        
        return text
    
    async def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM (这里模拟，实际需要接入 OpenClaw 或 API)
        
        实际实现应该:
        1. 调用 OpenClaw SDK
        2. 或直接调用 Qwen API
        """
        # 模拟 LLM 调用
        print(f"[Extractor] 正在调用 {self.model_name}...")
        await asyncio.sleep(1)  # 模拟 API 延迟
        
        # 模拟返回的 JSON
        mock_response = {
            "ticker": "NVDA",
            "company_name": "NVIDIA Corporation",
            "fiscal_quarter": "2026 Q1",
            "fiscal_year": 2026,
            "report_date": "2026-02-15",
            "earnings_call_date": "2026-02-16",
            "financials": {
                "revenue": {"actual": 35100.0, "estimate": 33000.0, "growth_yoy": 25.5},
                "eps": {"actual": 0.81, "estimate": 0.75, "growth_yoy": 15.2},
                "net_income": {"actual": 8500.0, "growth_yoy": 18.3},
                "operating_income": {"actual": 12000.0, "growth_yoy": 20.1},
                "ebitda": {"actual": 15000.0, "growth_yoy": 22.1},
                "gross_margin": 55.2,
                "net_margin": 24.3,
                "operating_margin": 34.3
            },
            "guidance": "We expect Q2 revenue to be approximately $36 billion, driven by strong data center demand.",
            "guidance_direction": "up",
            "sentiment": {
                "label": "Bullish",
                "confidence": 0.92,
                "reasoning": "Revenue beat estimates by 6%, guidance raised on strong AI chip demand.",
                "positive_signals": ["Data center revenue at record high", "AI chip demand unprecedented"],
                "negative_signals": ["Supply chain constraints"]
            },
            "source": "10-Q",
            "is_data_complete": True,
            "data_quality": "high",
            "missing_fields": [],
            "extraction_notes": None
        }
        
        return json.dumps(mock_response, ensure_ascii=False)
    
    def _parse_json_response(self, response_text: str) -> dict:
        """解析 LLM 返回的 JSON"""
        try:
            # 尝试直接解析
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            print("[Extractor] JSON 解析失败")
            return {}
    
    def _build_report(
        self,
        ticker: str,
        extracted_data: dict,
        fiscal_quarter: str,
        source: str,
        raw_text_length: int
    ) -> EarningsReport:
        """构建 EarningsReport 对象"""
        
        # 构建 FinancialMetrics
        financials_data = extracted_data.get("financials", {})
        
        def build_financial_metric(data: dict) -> FinancialMetric:
            if isinstance(data, dict):
                return FinancialMetric(
                    actual=data.get("actual"),
                    estimate=data.get("estimate"),
                    growth_yoy=data.get("growth_yoy")
                )
            return FinancialMetric()
        
        financials = FinancialMetrics(
            revenue=build_financial_metric(financials_data.get("revenue", {})),
            eps=build_financial_metric(financials_data.get("eps", {})),
            net_income=build_financial_metric(financials_data.get("net_income", {})),
            operating_income=build_financial_metric(financials_data.get("operating_income", {})),
            ebitda=build_financial_metric(financials_data.get("ebitda", {})),
            gross_margin=financials_data.get("gross_margin"),
            net_margin=financials_data.get("net_margin"),
            operating_margin=financials_data.get("operating_margin")
        )
        
        # 构建 Sentiment
        sentiment_data = extracted_data.get("sentiment", {})
        sentiment = None
        if sentiment_data:
            sentiment = SentimentScore(
                label=sentiment_data.get("label", "Neutral"),
                confidence=sentiment_data.get("confidence", 0.5),
                reasoning=sentiment_data.get("reasoning", ""),
                positive_signals=sentiment_data.get("positive_signals", []),
                negative_signals=sentiment_data.get("negative_signals", [])
            )
        
        # 构建 Report
        return EarningsReport(
            ticker=ticker,
            company_name=extracted_data.get("company_name"),
            fiscal_quarter=fiscal_quarter or extracted_data.get("fiscal_quarter", "Unknown"),
            fiscal_year=extracted_data.get("fiscal_year", datetime.now().year),
            report_date=extracted_data.get("report_date"),
            earnings_call_date=extracted_data.get("earnings_call_date"),
            financials=financials,
            guidance=extracted_data.get("guidance"),
            guidance_direction=extracted_data.get("guidance_direction"),
            sentiment=sentiment,
            source=source,
            raw_text_length=raw_text_length,
            is_data_complete=extracted_data.get("is_data_complete", True),
            data_quality=DataQuality(extracted_data.get("data_quality", "high")),
            missing_fields=extracted_data.get("missing_fields", []),
            extraction_notes=extracted_data.get("extraction_notes")
        )
    
    def _calculate_metrics(
        self,
        prompt: str,
        response: str,
        start_time: datetime,
        report: EarningsReport
    ) -> ExtractionMetrics:
        """计算提取指标"""
        
        # 估算 token 使用量
        token_usage = len(prompt) // 4 + len(response) // 4
        
        # 计算置信度 (基于数据质量)
        confidence = 0.5  # 默认
        if report.sentiment:
            confidence = report.sentiment.confidence
        elif report.data_quality == DataQuality.HIGH:
            confidence = 0.9
        elif report.data_quality == DataQuality.MEDIUM:
            confidence = 0.7
        elif report.data_quality == DataQuality.LOW:
            confidence = 0.5
        
        # 处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 确定状态
        status = "success"
        if report.data_quality == DataQuality.LOW:
            status = "partial"
        elif len(report.missing_fields) > 3:
            status = "failed"
        
        return ExtractionMetrics(
            model_used=self.model_name,
            token_usage=token_usage,
            processing_time_seconds=processing_time,
            confidence_score=confidence,
            status=status,
            requires_manual_review=confidence < 0.7,
            fallback_triggered=report.data_quality in [DataQuality.LOW, DataQuality.MISSING]
        )
    
    def _save_result(
        self,
        ticker: str,
        report: EarningsReport,
        metrics: ExtractionMetrics
    ):
        """保存提取结果"""
        
        # 保存报告
        report_file = os.path.join(
            self.output_dir,
            f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "report": report.model_dump(),
                "metrics": metrics.model_dump()
            }, f, indent=2, default=str)
        
        print(f"[Extractor] 结果已保存: {report_file}")


async def main():
    """测试函数"""
    extractor = EarningsExtractor()
    
    # 模拟财报原文 (简化版)
    sample_text = """
    NVIDIA Corporation Reports Financial Results for the Fourth Quarter and Fiscal Year 2026
    
    Financial Highlights:
    - Revenue: $35.1 billion, up 25% year-over-year
    - EPS: $0.81, compared to $0.72 in the previous year
    - Net Income: $8.5 billion
    - Gross Margin: 55.2%
    
    Management Discussion:
    Our data center business reached record highs, driven by unprecedented demand for AI chips.
    We expect continued strong demand in the coming quarters.
    """
    
    report, metrics = await extractor.extract(
        ticker="NVDA",
        raw_text=sample_text,
        fiscal_quarter="2026 Q4",
        source="10-Q"
    )
    
    print("\n" + "="*60)
    print("📊 提取结果")
    print("="*60)
    print(f"Ticker: {report.ticker}")
    print(f"Revenue: ${report.financials.revenue.actual}B")
    print(f"EPS: ${report.financials.eps.actual}")
    print(f"Sentiment: {report.sentiment.label if report.sentiment else 'N/A'}")
    print(f"Confidence: {metrics.confidence_score}")
    print(f"Status: {metrics.status}")
    
    return report, metrics


if __name__ == "__main__":
    asyncio.run(main())
