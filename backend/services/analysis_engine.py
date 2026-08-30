# -*- coding: utf-8 -*-
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
import openai
from config import settings


STEP_PROMPTS = [
    "【取用神】根据占事分类{category}，说明用神选取依据",
    "【察世应】分析世爻与应爻的位置关系和生克状态",
    "【观动爻】分析动爻变动趋势和回头生克情况",
    "【断旺衰】综合月建日辰判断各爻旺衰状态",
    "【看格局】分析卦中特殊格局（六冲/六合/三合等）",
    "【参RAG】结合知识库：{rag_context}",
    "【综合判断】给出整体趋势（吉/平/需留意）",
    "【建议参考】给出中性可执行建议+免责声明"
]


def build_analysis_prompt(gua_disk: Dict, rag_context: str, question: str, category: str) -> str:
    yao_summary = chr(10).join([
        "  第" + str(i+1) + "爻：" + yd["yang_yin"] + yd["na_jia"] + " " + yd["liu_qin"] + " " + yd["wang_shuai"] +
        ("【动】" if yd["moving"] else "") +
        ("【空】" if yd["xun_kong"] else "")
        for i, yd in enumerate(gua_disk.get("yao_details", []))
    ])
    step_text = chr(10).join(STEP_PROMPTS)
    step_text = step_text.format(category=category, rag_context=rag_context)
    prompt = """你是六爻解卦分析师。请分析以下卦象并输出JSON。

【卦盘信息】
卦名：""" + str(gua_disk.get("gua_name","")) + """
上卦：""" + str(gua_disk.get("upper_gua","")) + """  下卦：""" + str(gua_disk.get("lower_gua","")) + """
宫位：""" + str(gua_disk.get("palace","")) + """
世爻：第""" + str(gua_disk.get("shi_yao",0)) + """爻  应爻：第""" + str(gua_disk.get("ying_yao",0)) + """爻
动爻：""" + str(gua_disk.get("moving_yao",[])) + """
趋势：""" + str(gua_disk.get("trend","静")) + """
问事：""" + question + """
占事分类：""" + category + """

【六爻详情】
""" + yao_summary + """

【分析步骤】
""" + step_text + """

【输出格式要求】
请按以下JSON格式输出（只用中文）：
{
  "step1_yong_shen": "用神选取说明",
  "step2_shi_ying": "世应关系分析",
  "step3_moving": "动爻分析",
  "step4_wang_shuai": "旺衰综合判断",
  "step5_pattern": "格局分析",
  "step6_rag_ref": "RAG知识库参考",
  "step7_trend": "趋势判断：吉/平/需留意",
  "step8_advice": "可执行建议",
  "disclaimer": "本分析基于传统六爻民俗文化，仅供决策参考，不构成人生定论依据。",
  "confidence": 0.0-1.0,
  "reference_strength": 0.0-1.0,
  "risk_level": "低/中/高"
}

要求：中性表述，禁止绝对化词汇。
"""
    return prompt


class AnalysisEngine:
    def __init__(self):
        self._use_mock = not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-placeholder"
        if not self._use_mock:
            try:
                self.client = openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL
                )
                # Test the connection
                self.client.models.list()
            except Exception:
                self._use_mock = True
                print("[AnalysisEngine] API连接失败，使用mock模式")

    def _mock_analyze(self, gua_disk: Dict, rag_context: str, question: str, category: str) -> Dict[str, Any]:
        return {
            "step1_yong_shen": "根据占事分类【" + category + "】，选取对应用神。",
            "step2_shi_ying": "世爻代表求测者，应爻代表所问之事。世应关系反映主客态势。",
            "step3_moving": "动爻主变化，当前动爻为：" + str(gua_disk.get("moving_yao", [])) + "，变动趋势需结合旺衰综合判断。",
            "step4_wang_shuai": "以月建日辰为基准，各爻旺衰状态已纳入分析。",
            "step5_pattern": "卦象格局需结合动爻、世应、六冲六合等综合判定。",
            "step6_rag_ref": rag_context or "暂无知识库匹配条目。",
            "step7_trend": "平",
            "step8_advice": "建议结合实际情况综合判断，保持理性态度。",
            "disclaimer": "本分析基于传统六爻民俗文化，仅供决策参考，不构成人生定论依据。",
            "confidence": 0.5,
            "reference_strength": 0.3,
            "risk_level": "中"
        }

    async def analyze_gua(self, gua_disk: Dict, rag_context: str, question: str, category: str) -> Dict[str, Any]:
        if self._use_mock:
            return self._mock_analyze(gua_disk, rag_context, question, category)
        try:
            prompt = build_analysis_prompt(gua_disk, rag_context, question, category)
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            content = response.choices[0].message.content or ""
            try:
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    result = json.loads(content[start:end+1])
                else:
                    result = {"raw": content}
            except json.JSONDecodeError:
                result = {"raw": content}
            for k in ["step1_yong_shen","step2_shi_ying","step3_moving","step4_wang_shuai",
                      "step5_pattern","step6_rag_ref","step7_trend","step8_advice",
                      "disclaimer","confidence","reference_strength","risk_level"]:
                result.setdefault(k, "")
            return result
        except Exception as e:
            print(f"[AnalysisEngine] API调用失败: {e}，使用mock模式")
            return self._mock_analyze(gua_disk, rag_context, question, category)

    async def stream_analyze(self, gua_disk: Dict, rag_context: str, question: str, category: str) -> AsyncGenerator[str, None]:
        if self._use_mock:
            result = self._mock_analyze(gua_disk, rag_context, question, category)
            full = json.dumps(result, ensure_ascii=False)
            for char in full:
                yield "event: token" + chr(10) + "data: " + json.dumps({"token": char}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: report" + chr(10) + "data: " + json.dumps({"text": full}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: done" + chr(10) + "data: {}" + chr(10) + chr(10)
            return
        try:
            prompt = build_analysis_prompt(gua_disk, rag_context, question, category)
            stream = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
                stream=True
            )
            full_text = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_text += token
                    yield "event: token" + chr(10) + "data: " + json.dumps({"token": token}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: report" + chr(10) + "data: " + json.dumps({"text": full_text}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: done" + chr(10) + "data: {}" + chr(10) + chr(10)
        except Exception as e:
            print(f"[AnalysisEngine] Stream API失败: {e}")
            result = self._mock_analyze(gua_disk, rag_context, question, category)
            full = json.dumps(result, ensure_ascii=False)
            yield "event: report" + chr(10) + "data: " + json.dumps({"text": full}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: done" + chr(10) + "data: {}" + chr(10) + chr(10)

    async def stream_chat(self, case_id, history: list, message: str, context: dict = None) -> AsyncGenerator[str, None]:
        if self._use_mock:
            # 构建有上下文的回复
            resp_parts = []
            q = (context.get("question") if context else None) or message
            cat = context.get("category", "") if context else ""
            gd = context.get("gua_disk") if context else None
            
            resp_parts.append(f"关于【{q}】（{cat or '占事'}）的参考解读：")
            resp_parts.append("")
            
            if gd:
                gname = gd.get("gua_name", "")
                upper = gd.get("upper_gua", "")
                lower = gd.get("lower_gua", "")
                trend = gd.get("trend", "静")
                shi = gd.get("shi_yao", 0)
                ying = gd.get("ying_yao", 0)
                moving = gd.get("moving_yao", [])
                resp_parts.append(f"当前得【{gname}】卦，上{upper}下{lower}，趋势{trend}。")
                if moving:
                    resp_parts.append(f"动爻在第{moving}爻，主事态有变化。")
                else:
                    resp_parts.append("静卦无动爻，主事态平稳发展。")
                resp_parts.append(f"世爻在第{shi}爻代表您，应爻在第{ying}爻代表所问之事。")
                resp_parts.append("")
            
            # 根据问题类型给出针对性回复
            if "天气" in q or "天气" in message or "气温" in q or "下雨" in q:
                resp_parts.append("此问已超出六爻占卜范畴，建议使用天气类应用获取准确预报。")
            elif "运势" in q or "运气" in q:
                resp_parts.append("运势讲究天时地利人和，卦象显示当前状态平稳，建议把握当下，主动求变。")
            elif "面试" in q or "工作" in q or "事业" in q:
                resp_parts.append("事业问卦重在审时度势，卦象提示需观察时机，不宜冒进，稳扎稳打为上。")
            elif "财运" in q or "投资" in q or "股票" in q:
                resp_parts.append("财运问卦需看势态，当前宜守不宜攻，理性判断，切勿盲目。")
            elif "感情" in q or "恋爱" in q or "婚姻" in q:
                resp_parts.append("感情问卦重在缘分与沟通，卦象提示以真诚为本，顺其自然。")
            else:
                resp_parts.append("卦象仅示趋势，具体仍需结合实际情况综合判断。保持理性态度，方为上策。")
            
            resp_parts.append("")
            resp_parts.append("免责声明：本分析基于传统六爻民俗文化，仅供决策参考，不构成人生定论依据。")
            
            resp = "\n".join(resp_parts)

            for char in resp:
                yield "event: token" + chr(10) + "data: " + json.dumps({"token": char}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: report" + chr(10) + "data: " + json.dumps({"text": resp}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: done" + chr(10) + "data: {}" + chr(10) + chr(10)
            return
        try:
            system_prompt = "你是六爻解卦助手，严格遵循规则：基于当前卦盘分析，输出中性参考表述。"
            messages = [{"role": "system", "content": system_prompt}]
            for h in history:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message})
            stream = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
                stream=True
            )
            full_text = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_text += token
                    yield "event: token" + chr(10) + "data: " + json.dumps({"token": token}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: report" + chr(10) + "data: " + json.dumps({"text": full_text}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: done" + chr(10) + "data: {}" + chr(10) + chr(10)
        except Exception as e:
            print(f"[AnalysisEngine] Chat API失败: {e}")
            yield "event: report" + chr(10) + "data: " + json.dumps({"text": "暂时无法连接AI服务，请稍后重试。"}, ensure_ascii=False) + chr(10) + chr(10)
            yield "event: done" + chr(10) + "data: {}" + chr(10) + chr(10)
