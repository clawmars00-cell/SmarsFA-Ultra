"""
Validator - SubAgent输出校验
"""
from typing import Dict, Any, List
from schemas import SubAgentOutput


class OutputValidator:
    """
    SubAgent输出校验器
    - JSON格式校验
    - 置信度检查
    - 必需字段检查
    """
    
    REQUIRED_FIELDS = ["module", "confidence", "structured_data"]
    
    def validate(self, result: Dict[str, Any]) -> SubAgentOutput:
        """校验并转换"""
        # 检查必需字段
        for field in self.REQUIRED_FIELDS:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        # 置信度检查
        if result.get("confidence", 0) < 0.6:
            result["flagged"] = True
        
        return SubAgentOutput(**result)
    
    def validate_confidence(self, result: Dict[str, Any]) -> bool:
        """检查置信度"""
        confidence = result.get("confidence", 0)
        return confidence >= 0.6
    
    def get_warnings(self, result: Dict[str, Any]) -> List[str]:
        """获取警告"""
        warnings = []
        
        if result.get("confidence", 0) < 0.6:
            warnings.append(f"Low confidence: {result.get('confidence')}")
        
        if result.get("risk_flags"):
            warnings.append(f"Risk flags: {result.get('risk_flags')}")
        
        return warnings
