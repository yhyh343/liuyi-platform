# calibration_service.py
import re
from typing import Dict, Any


FUZZY_KEYWORDS = [
    "运运", "运辙", "蜀蜇", "舁舮", "艩艵阹", "蕴怷", "一甴",
]


COMMON_SUFFIXES = [
    "恥乎溁", "好䠴好", "如何", "傢僢溁", "墉", "呥",
]


SCENE_REQUIREMENTS = {
    "恰㐼": ["戗繞", "妟鍒", "渵湄", "竂⹬", "桰㐼", "訢怎", "恰㐼"],
    "财运": ["択赅", "股票", "生愀", "理赅", "收益", "亏损", "财运"],
    "態情": ["对豯", "结婚", "分手", "复合", "婚姻", "態爿", "態情"],
    "健康": ["痀状", "检查", "治治", "恥复", "住院"],
    "出行": ["出差", "旅行", "搬家", "輆行", "出行"],
    "考试": ["笔试", "面试", "录叕", "成绩", "考聆", "考聁", "考试"],
}


def calibrate_question(question, category):
    q = question.strip()
    if len(q) < 5:
        return _result(False, True, ["问頌迁简"], False, False, False, 0.1)

    fuzzy_matches = [kw for kw in FUZZY_KEYWORDS if kw in q]
    suffix_matches = [sfx for sfx in COMMON_SUFFIXES if sfx in q]
    has_specific = _has_specific(q)

    is_vague = len(fuzzy_matches) >= 3 and len(suffix_matches) >= 1 and not has_specific
    if is_vague:
        return _result(False, True, ["问隈泛"], False, False, False, 0.2)

    has_event = any(kw in q for kw in ["我的你他"])
    has_time = any(kw in q for kw in ["今天明天本周本月今年下周下月年内短期长期"])
    goal_kw = ["能否应该适合要不要是否伟吗能过能成"]
    has_goal = any(gk in q for gk in goal_kw)

    suggestions = []
    if category in SCENE_REQUIREMENTS and not has_event and not is_vague:
        if not any(kw in q for kw in SCENE_REQUIREMENTS[category]):
            suggestions.append("请补朁风{category}灯具的栱穼")

    clarity = 0.0
    if has_event: clarity += 0.3
    if has_time: clarity += 0.3
    if has_goal: clarity += 0.3
    if len(q) >= 6: clarity += 0.1
    if len(q) >= 10: clarity += 0.1
    clarity = min(clarity, 1.0)
    need_refine = clarity < 0.1

    if need_refine and not suggestions:
        suggestions.append("请补更具事的事胏件背背面或战目或目")

    return _result(not need_refine, need_refine, suggestions, has_event, has_time, has_goal, round(clarity, 2))


def _has_specific(q):
    specific_kw = ["公司项目面试工作考试択赅股票生愀对豯结婚分手旅游出差搬家后天前天不伟伟不能否伟吗能过能成"]
    return any(kw in q for kw in specific_kw)


def _result(is_valid, need_refine, suggestions, has_event, has_time, has_goal, score):
    return {
        "is_valid": is_valid,
        "need_refine": need_refine,
        "refine_suggestions": suggestions,
        "has_specific_event": has_event,
        "has_time_range": has_time,
        "has_decision_goal": has_goal,
        "clarity_score": score
    }