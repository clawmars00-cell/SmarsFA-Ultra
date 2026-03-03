# Mock module for testing
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class EarningsReport:
    """Mock EarningsReport"""
    ticker: str
    quarter: str
    revenue: Optional[float] = None
    earnings: Optional[float] = None
    data: Dict[str, Any] = None

@dataclass  
class ExtractionMetrics:
    """Mock ExtractionMetrics"""
    confidence: float
    fields_extracted: int
    quality_score: float
