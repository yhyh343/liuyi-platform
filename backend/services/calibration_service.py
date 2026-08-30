# calibration_service.py
import re
from typing import Dict, Any


FUZZY_KEYWORDS = [
    "运势", "运程", "命理", "占卜", "卦象", "测算", "卜卦",
]


COMMON_SUFFIXES = [
    "乎", "好吗", "如何", "怎样", "呢", "吧",
]


SCENE_REQUIREMENTS = {
    "工作事业": ["工作", "事业", "升职", "跳槽", "创业", "面试", "项目", "晋升"],
    "财运投资": ["财运", "股票", "投资", "理财", "收益", "亏损", "赚钱", "财富"],
    "感情婚姻": ["感情", "恋爱", "结婚", "分手", "复合", "婚姻", "对象", "缘分"],
    "健康疾病": ["健康", "疾病", "检查", "治疗", "康复", "住院", "身体"],
    "出行旅行": ["出差", "旅行", "搬家", "出行", "旅途", "远行"],
    "考试学业": ["考试", "笔试", "面试", "录取", "成绩", "考研", "学业"],
}


def calibrate_question(question, category):
    q = question.strip()
    if len(q) < 3:
        return _result(False, True, ["问题太简短，请补充具体内容"], False, False, False, 0.1)

    fuzzy_matches = [kw for kw in FUZZY_KEYWORDS if kw in q]
    suffix_matches = [sfx for sfx in COMMON_SUFFIXES if sfx in q]
    has_specific = _has_specific(q)

    is_vague = len(fuzzy_matches) >= 3 and len(suffix_matches) >= 2 and not has_specific
    if is_vague:
        return _result(False, True, ["问题过于笼统，请补充具体背景或目标"], False, False, False, 0.2)

    has_event = any(kw in q for kw in ["我", "你", "他", "她", "我们", "公司", "项目", "工作", "考试", "面试", "股票", "财运", "感情", "健康", "旅行", "搬家"])
    has_time = any(kw in q for kw in ["今天", "明天", "本周", "本月", "今年", "下周", "下月", "年内", "短期", "长期", "最近", "将来", "未来"])
    goal_kw = ["能否", "应该", "适合", "要不要", "是否", "为", "吗", "能过", "能成", "行吗", "好吗", "结果", "趋势"]
    has_goal = any(gk in q for gk in goal_kw)

    suggestions = []
    if category in SCENE_REQUIREMENTS and not has_event and not is_vague:
        if not any(kw in q for kw in SCENE_REQUIREMENTS[category]):
            suggestions.append("请补充与" + category + "相关的具体事件或背景")

    clarity = 0.0
    if has_event: clarity += 0.2
    if has_time: clarity += 0.2
    if has_goal: clarity += 0.2
    if len(q) >= 5: clarity += 0.1
    if len(q) >= 10: clarity += 0.1
    if len(q) >= 15: clarity += 0.1
    if not is_vague: clarity += 0.1
    clarity = min(clarity, 1.0)
    need_refine = clarity < 0.15

    if need_refine and not suggestions:
        suggestions.append("请补充更多事件背景或具体目标，以便更准确分析")

    return _result(not need_refine, need_refine, suggestions, has_event, has_time, has_goal, round(clarity, 2))


def _has_specific(q):
    specific_kw = ["公司", "项目", "面试", "工作", "考试", "股票", "财运", "感情", "结婚", "分手", "旅游", "出差", "搬家", "前", "后", "天", "不", "为", "能", "否", "吗", "能过", "能成"]
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