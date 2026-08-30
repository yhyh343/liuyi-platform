"""
起卦模块 - 封装三种起卦方式，返回完整卦盘
"""
import uuid
from engine.na_jia import perform_divination


def create_gua_case(method, params, question, category, calibrate_info):
    """创建卦例记录"""
    case_id = str(uuid.uuid4()).replace("-", "")[:16]

    gua_disk = perform_divination(method, params, question, category, calibrate_info)
    gua_disk["case_id"] = case_id
    gua_disk["created_at"] = None  # 由DB填充

    return {
        "case_id": case_id,
        "gua_disk": gua_disk,
        "calibrate_info": calibrate_info
    }
