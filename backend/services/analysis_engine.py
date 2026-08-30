# -*- coding: utf-8 -*-
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
import openai
from config import settings


STEP_PROMPTS = [
    "Step1【取用神】：根据占事分类{category}，说明用神选取的依据和当前用神是哪一爻",
    "Step2【察世应】：分析世爻与应爻的位置关系，判断彼此生克与旺衰状态",
    "Step3【观动爻】：分析动爻的变动趋势，是否化进神或退神，回头生克情况",
    "Step4【断旺衰】：综合月建日辰判断各关键爻的旺衰状态，说明旺衰对事态的影响",
    "Step5【看格局】：分析卦中是否存在特殊格局（如六冲、六合、三合局等）及其含义",
    "Step6【参RAG】：结合以下知识库条目进行分析：{rag_context}",
    "Step7【综合判断】：综合以上分析，给出整体趋势判断（趋势：吉/平/需留意）",
    "Step8【建议参考】：给出中性、可执行的参考建议，并附加合规免责声明"
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
    prompt = """你是六爻解卦分析师，严格遵循以下8步流程输出结构化报告。

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
严格按以下JSON Schema输出，不得遗漏任何字段：
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

重要：所有输出必须为中性参考表述，禁止使用绝对化词汇。
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
            resp = "基于卦象分析，针对您的问题【"
            if context and context.get("question"):
                resp += context["question"]
            else:
                resp += message
            resp += "】，以下是参考解读。\n\n"
            if context and context.get("gua_disk"):
                gd = context["gua_disk"]
                resp += "当前卦象：" + str(gd.get("gua_name", "")) + "（" + str(gd.get("upper_gua", "")) + "上" + str(gd.get("lower_gua", "")) + "下）"
                resp += "，趋势：" + str(gd.get("trend", "静")) + "。"
            resp += "请结合卦象信息综合判断。"

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
