"""
纳甲排盘引擎 - 纯硬编码，无任何AI参与
核心功能：起卦 → 排六爻 → 纳甲 → 安六亲 → 定世应 → 排日月 → 旺衰计算
"""
import hashlib
from datetime import datetime, timezone, timedelta
from .bagua import (
    BAGUA_ORDER, BAGUA_BIN, NA_JIA, WUXING, DI_ZHI, DI_ZHI_NUM,
    ZHIXING_WUXING, MONTH_ZHI, PALACE_INFO, XUN_KONG
)


def _get_zhi_element(zhi):
    return ZHIXING_WUXING.get(zhi, "土")


def _get_liu_qin(gua_gong_wuxing, zhi):
    """以卦宫五行为主，判断地支对应的六亲"""
    zhi_wx = _get_zhi_element(zhi)
    host_wx = gua_gong_wuxing
    wuxing_cycle = ["木","火","土","金","水"]

    def generates(a, b):
        return wuxing_cycle.index(b) == (wuxing_cycle.index(a) + 1) % 5

    if zhi_wx == host_wx:
        return "兄弟"
    if generates(host_wx, zhi_wx):
        return "子孙"
    if generates(zhi_wx, host_wx):
        return "父母"
    if wuxing_cycle.index(zhi_wx) == (wuxing_cycle.index(host_wx) + 1) % 5:
        return "妻财"
    if wuxing_cycle.index(host_wx) == (wuxing_cycle.index(zhi_wx) + 1) % 5:
        return "官鬼"
    return "兄弟"


def _get_gua_palace(upper, lower):
    """确定卦所属宫"""
    upper_name = BAGUA_ORDER[upper]
    wux = WUXING[upper_name]
    for palace, info in PALACE_INFO.items():
        if info["五行"] == wux:
            return palace, info["世爻"]
    return "乾宫", 6


def _get_xun_kong(year_zhi_num, month, day, hour):
    """计算旬空"""
    total = (year_zhi_num + month + day + hour) % 60
    xun_index = total // 10
    xun_offsets = ["甲子旬","甲戌旬","甲申旬","甲午旬","甲辰旬","甲寅旬"]
    xun_name = xun_offsets[xun_index]
    return XUN_KONG[xun_name]


def calc_wang_shuai(na_jia_list, month_zhi, day_zhi):
    """旺衰计算（纯硬编码公式）"""
    month_wx = ZHIXING_WUXING.get(month_zhi, "土")
    day_wx = ZHIXING_WUXING.get(day_zhi, "土")
    wuxing_cycle = ["木","火","土","金","水"]

    def generates(a, b):
        return wuxing_cycle.index(b) == (wuxing_cycle.index(a) + 1) % 5

    wang_shuai_result = []
    for nz in na_jia_list:
        zhi = nz[-1]
        zhi_wx = _get_zhi_element(zhi)

        if zhi_wx == month_wx:
            yue_state = "旺"
        elif generates(month_wx, zhi_wx):
            yue_state = "相"
        elif generates(zhi_wx, month_wx):
            yue_state = "休"
        else:
            yue_state = "死"

        if zhi_wx == day_wx:
            ri_state = "旺"
        elif generates(day_wx, zhi_wx):
            ri_state = "相"
        else:
            ri_state = "平"

        if yue_state in ("旺", "相") and ri_state == "旺":
            overall = "旺"
        elif yue_state in ("旺", "相"):
            overall = "相"
        elif ri_state == "旺":
            overall = "相"
        elif yue_state == "死" and ri_state == "死":
            overall = "死"
        else:
            overall = "平"

        wang_shuai_result.append(overall)

    return wang_shuai_result


def perform_divination(method, params, question, category, calibrate_info):
    """起卦主入口"""
    if method == "coin":
        return _coin_divination(params, question, category, calibrate_info)
    elif method == "time":
        return _time_divination(params, question, category, calibrate_info)
    elif method == "number":
        return _number_divination(params, question, category, calibrate_info)
    else:
        raise ValueError(f"Unknown method: {method}")


def _coin_divination(params, question, category, calibrate_info):
    """铜钱起卦 - CSPRNG模拟"""
    import secrets
    lines = []
    for _ in range(6):
        coin_sum = sum(secrets.randbelow(2) + 2 for _ in range(3))
        if coin_sum == 2:
            lines.append({"yao": 0, "moving": True, "label": "少阴"})
        elif coin_sum == 3:
            lines.append({"yao": 0, "moving": False, "label": "少阴"})
        elif coin_sum == 4:
            lines.append({"yao": 1, "moving": False, "label": "少阳"})
        elif coin_sum == 5:
            lines.append({"yao": 1, "moving": True, "label": "老阳"})
        else:
            lines.append({"yao": 1, "moving": False, "label": "少阳"})
    return _build_gua_disk(lines, question, category, calibrate_info or {}, "铜钱")


def _time_divination(params, question, category, calibrate_info):
    """时间起卦"""
    bj = datetime.now(timezone(timedelta(hours=8)))
    year = bj.year
    month = bj.month
    day = bj.day
    hour = bj.hour

    year_zhi_name = MONTH_ZHI[(year - 4) % 12 + 1] if (year - 4) % 12 + 1 < len(MONTH_ZHI) and MONTH_ZHI[(year - 4) % 12 + 1] else "子"
    year_zhi_num = DI_ZHI_NUM.get(year_zhi_name, 0)

    upper = (year_zhi_num + month + day) % 8
    lower = (year_zhi_num + month + day + hour) % 8
    move = (year_zhi_num + month + day + hour) % 6

    lower_bin = BAGUA_BIN[lower][::-1]
    upper_bin = BAGUA_BIN[upper][::-1]

    lines = []
    for b in lower_bin:
        lines.append({"yao": b, "moving": False, "label": "少阴" if b == 0 else "少阳"})
    for i, b in enumerate(upper_bin):
        lines.append({"yao": b, "moving": (i + 3 == move), "label": "少阴" if b == 0 else "少阳"})

    info = calibrate_info or {}
    info["time_params"] = {"year": year, "month": month, "day": day, "hour": hour}
    return _build_gua_disk(lines, question, category, info, "时间")


def _number_divination(params, question, category, calibrate_info):
    """数字起卦"""
    input_num = params.get("input_num", 0)
    upper_num = input_num % 8
    lower_num = (input_num // 8 + input_num) % 8
    move_num = input_num % 6
    if move_num == 0:
        move_num = 6
    seed_hash = hashlib.md5(str(input_num).encode()).hexdigest()[:16]

    lower_bin = BAGUA_BIN[lower_num][::-1]
    upper_bin = BAGUA_BIN[upper_num][::-1]

    lines = []
    for b in lower_bin:
        lines.append({"yao": b, "moving": False, "label": "少阴" if b == 0 else "少阳"})
    for i, b in enumerate(upper_bin):
        lines.append({"yao": b, "moving": (i + 3 == move_num), "label": "少阴" if b == 0 else "少阳"})

    info = calibrate_info or {}
    info["number_params"] = {"input_num": input_num, "seed_hash": seed_hash}
    return _build_gua_disk(lines, question, category, info, "数字")


def _build_gua_disk(lines, question, category, calibrate_info, method_name):
    """构建完整卦盘JSON"""
    upper_idx = sum(l["yao"] << (2 - i) for i, l in enumerate(lines[3:]))
    lower_idx = sum(l["yao"] << (2 - i) for i, l in enumerate(lines[:3]))
    upper_name = BAGUA_ORDER[upper_idx]
    lower_name = BAGUA_ORDER[lower_idx]
    gua_name = f"{upper_name}{lower_name}"

    na_jia_upper = NA_JIA[upper_name]
    na_jia_lower = NA_JIA[lower_name]
    all_na_jia = na_jia_lower + na_jia_upper

    palace, shi_yao = _get_gua_palace(upper_idx, lower_idx)
    ying_yao = 7 - shi_yao if shi_yao <= 6 else 1

    host_wuxing = PALACE_INFO.get(palace, {}).get("五行", "金")
    liu_qin_list = [_get_liu_qin(host_wuxing, nz) for nz in all_na_jia]
    moving_indices = [i for i, l in enumerate(lines) if l["moving"]]

    bj = datetime.now(timezone(timedelta(hours=8)))
    month_zhi = MONTH_ZHI[bj.month] if bj.month < len(MONTH_ZHI) and MONTH_ZHI[bj.month] else "子"
    day_zhi = DI_ZHI[bj.day % 12]
    wang_shuai = calc_wang_shuai(all_na_jia, month_zhi, day_zhi)

    year_zhi_num = DI_ZHI_NUM.get(MONTH_ZHI[(bj.year - 4) % 12 + 1] if (bj.year - 4) % 12 + 1 < len(MONTH_ZHI) and MONTH_ZHI[(bj.year - 4) % 12 + 1] else "子", 0)
    xun_kong_list = _get_xun_kong(year_zhi_num, bj.month, bj.day, bj.hour)

    yao_details = []
    for i in range(6):
        line = lines[i]
        nz = all_na_jia[i]
        zhi_char = nz[-1]
        yao_details.append({
            "position": i + 1,
            "zhi": zhi_char,
            "na_jia": nz,
            "liu_qin": liu_qin_list[i],
            "yang_yin": "阳" if line["yao"] else "阴",
            "moving": line["moving"],
            "moving_label": line["label"],
            "wang_shuai": wang_shuai[i],
            "xun_kong": zhi_char in xun_kong_list
        })

    moving_count = len(moving_indices)
    trend = ["静","一动","二动","三动","多动"][min(moving_count, 4)]

    return {
        "case_id": calibrate_info.get("case_id", ""),
        "gua_name": gua_name,
        "upper_gua": upper_name,
        "lower_gua": lower_name,
        "palace": palace,
        "shi_yao": shi_yao,
        "ying_yao": ying_yao,
        "moving_yao": moving_indices,
        "yao_details": yao_details,
        "trend": trend,
        "method": method_name,
        "calibrate_info": calibrate_info,
        "question": question,
        "category": category,
        "raw_lines": [{"yao": l["yao"], "moving": l["moving"]} for l in lines]
    }
