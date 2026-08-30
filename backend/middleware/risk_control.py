"""
风控合规模块 - 敏感词拦截 + 话术过滤 + 重复占问检测
"""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any


# 敏感拦截词库
BLOCKED_PATTERNS = [
    r".*(死|亡|病|癌症|治疗|手术|绝症).*",
    r".*(彩票|赌|麻将|扑克|六合彩).*",
    r".*(违法|犯罪|偷|骗|杀|自杀|自残).*",
    r".*(一定.*成功|必定.*顺利|绝对.*大吉|命中注定|铁定).*",
]

# 绝对化话术替换规则
ABSOLUTE_REPLACEMENTS = {
    "一定": "有可能", "必定": "或许", "绝对": "倾向于",
    "命中注定": "存在某种趋势", "精准": "较为", "必然": "可能",
    "注定": "似乎", "肯定": "有可能", "毫无疑问": "值得关注",
    "天定": "存在可能性", "铁定": "有一定概率"
}


def check_blocked(question: str) -> Dict[str, Any]:
    """检查问题是否触发拦截"""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, question):
            return {"blocked": True, "reason": "问题涉及敏感领域，仅作民俗文化参考，不可用于相关决策", "category": "safety"}
    return {"blocked": False, "reason": None, "category": None}


def filter_language(text: str) -> str:
    """过滤绝对化词汇"""
    result = text
    for word, replacement in ABSOLUTE_REPLACEMENTS.items():
        result = result.replace(word, replacement)
    return result


def check_repeat_question(existing_cases: List[Dict], new_question: str, threshold: float = 0.88) -> Dict[str, Any]:
    """检查重复占问（简化版：基于关键词重叠）"""
    if not existing_cases:
        return {"is_repeat": False, "confidence": 0.0}

    new_tokens = set(re.findall(r'[\u4e00-\u9fa5]{2,}', new_question))
    if not new_tokens:
        return {"is_repeat": False, "confidence": 0.0}

    max_similarity = 0.0
    closest_case = None
    for case in existing_cases:
        case_tokens = set(re.findall(r'[\u4e00-\u9fa5]{2,}', case.get("question", "")))
        if not case_tokens:
            continue
        overlap = len(new_tokens & case_tokens) / max(len(new_tokens), len(case_tokens), 1)
        if overlap > max_similarity:
            max_similarity = overlap
            closest_case = case

    return {
        "is_repeat": max_similarity >= threshold,
        "confidence": round(max_similarity, 2),
        "closest_case_id": closest_case.get("case_id") if closest_case else None
    }
