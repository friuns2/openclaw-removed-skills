"""
social-security-advisor 自学习模块

功能：
- 追踪用户常问的城市和险种类型
- 记录计算器脚本成功率
- 检测社保政策变化（费率/基数调整）
- 自动发现新的补贴类型和适用人群
"""
# Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
# Skill: social-security-advisor | Version: 2.0.0
# Author: QQ 1817694478 | Q-Group: 972156177
# Unauthorized copying, modification, or distribution is prohibited.
# This software is provided "as is" without warranty of any kind.

import json
from pathlib import Path
from datetime import datetime

LEARN_FILE = Path(__file__).parent.parent / "data" / "social_security_learn.json"

DEFAULT_LEARN_DATA = {
    "version": 1,
    "skill_name": "social-security-advisor",
    "last_success_date": None,
    "fail_streak": 0,
    "total_runs": 0,
    "total_success": 0,
    "total_failure": 0,
    "parameters": {
        # 用户常问城市（优先推荐）
        "hot_cities": ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉"],
        # 用户常问险种（优先展示）
        "hot_insurance_types": ["养老保险", "医疗保险", "失业保险", "生育保险", "工伤保险"],
        # 用户常问服务模块
        "hot_modules": ["缴费计算", "养老金测算", "灵活就业规划", "补贴优惠查询", "政策查询"],
        # 脚本支持城市列表（与 social_security_calculator.py 同步）
        "calculator_supported_cities": [],
    },
    "discoveries": [],
    "environment": {
        "last_policy_update": None,  # 最近一次政策更新日期
        "base_year": "2026",  # 数据基准年份
        "subsidy_types": ["4050补贴", "高校毕业生补贴", "国办25号文补贴", "平台经济补贴", "困难人员专项补贴"],
    },
    "history": [],
}


def load_learn() -> dict:
    """加载经验文件"""
    if LEARN_FILE.exists():
        try:
            return json.loads(LEARN_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            pass
    LEARN_FILE.parent.mkdir(parents=True, exist_ok=True)
    return json.loads(json.dumps(DEFAULT_LEARN_DATA))


def save_learn(data: dict):
    """保存经验文件（历史只保留最近30条）"""
    if len(data.get("history", [])) > 30:
        data["history"] = data["history"][-30:]
    LEARN_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEARN_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def record_success(data: dict, params_used: dict = None, env_info: dict = None):
    """记录成功执行"""
    data["last_success_date"] = datetime.now().strftime("%Y-%m-%d")
    data["fail_streak"] = 0
    data["total_runs"] = data.get("total_runs", 0) + 1
    data["total_success"] = data.get("total_success", 0) + 1
    if params_used:
        # 更新热门城市排序
        city = params_used.get("city")
        if city:
            hot = data["parameters"].get("hot_cities", [])
            if city in hot:
                hot.remove(city)
            hot.insert(0, city)
            data["parameters"]["hot_cities"] = hot[:15]
        # 更新热门险种排序
        insurance_type = params_used.get("insurance_type")
        if insurance_type:
            hot_types = data["parameters"].get("hot_insurance_types", [])
            if insurance_type in hot_types:
                hot_types.remove(insurance_type)
            hot_types.insert(0, insurance_type)
            data["parameters"]["hot_insurance_types"] = hot_types[:10]
        # 更新热门模块排序
        module = params_used.get("module")
        if module:
            hot_modules = data["parameters"].get("hot_modules", [])
            if module in hot_modules:
                hot_modules.remove(module)
            hot_modules.insert(0, module)
            data["parameters"]["hot_modules"] = hot_modules[:10]
    if env_info:
        data["environment"].update(env_info)
    # 成功后将 discoveries 提升为正式参数
    for d in data.get("discoveries", []):
        category = d.get("category", "")
        keyword = d.get("keyword", "")
        if category == "city" and keyword not in data["parameters"].get("hot_cities", []):
            data["parameters"]["hot_cities"].append(keyword)
        elif category == "insurance_type" and keyword not in data["parameters"].get("hot_insurance_types", []):
            data["parameters"]["hot_insurance_types"].append(keyword)
        elif category == "subsidy_type" and keyword not in data["environment"].get("subsidy_types", []):
            data["environment"]["subsidy_types"].append(keyword)
    data["discoveries"] = []
    save_learn(data)


def record_failure(data: dict, error: str = "", env_info: dict = None):
    """记录失败"""
    data["fail_streak"] = data.get("fail_streak", 0) + 1
    data["total_runs"] = data.get("total_runs", 0) + 1
    data["total_failure"] = data.get("total_failure", 0) + 1
    if env_info:
        data["environment"].update(env_info)
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "failure",
        "error": error,
    }
    data["history"].append(entry)
    # 连续失败3次，临时启用 discoveries
    if data["fail_streak"] >= 3 and data.get("discoveries"):
        _promote_discoveries(data)
    save_learn(data)


def _auto_discover(data: dict, user_query: str):
    """从用户提问中发现新的城市、险种和补贴类型"""
    # 城市发现：如果用户提到了中国城市名
    import re
    city_pattern = re.search(r'([\u4e00-\u9fff]{2,4}[市省区州县])', user_query)
    if city_pattern:
        city_name = city_pattern.group(1).replace("市", "").replace("省", "")
        if city_name and city_name not in data["parameters"].get("hot_cities", []):
            data.setdefault("discoveries", []).append({"category": "city", "keyword": city_name})

    # 险种发现
    insurance_markers = ["保险", "险", "养老", "医疗", "工伤", "生育", "失业", "公积金"]
    for marker in insurance_markers:
        match = re.search(rf'(\S*{marker}\S*)', user_query)
        if match and match.group(1) not in data["parameters"].get("hot_insurance_types", []):
            data.setdefault("discoveries", []).append({"category": "insurance_type", "keyword": match.group(1)})
            break

    # 补贴类型发现
    subsidy_markers = ["补贴", "优惠", "减免", "返还", "补助", "津贴", "救助"]
    for marker in subsidy_markers:
        match = re.search(rf'(\S*{marker}\S*)', user_query)
        if match and match.group(1) not in data["environment"].get("subsidy_types", []):
            data.setdefault("discoveries", []).append({"category": "subsidy_type", "keyword": match.group(1)})
            break


def _promote_discoveries(data: dict):
    """将发现的模式临时加入搜索范围"""
    for d in data.get("discoveries", []):
        category = d.get("category", "")
        keyword = d.get("keyword", "")
        if category == "city" and keyword not in data["parameters"].get("hot_cities", []):
            data["parameters"]["hot_cities"].append(keyword)
        elif category == "insurance_type" and keyword not in data["parameters"].get("hot_insurance_types", []):
            data["parameters"]["hot_insurance_types"].append(keyword)


def get_hot_cities(data: dict) -> list:
    """获取热门城市列表"""
    hot = data.get("parameters", {}).get("hot_cities", DEFAULT_LEARN_DATA["parameters"]["hot_cities"])
    for c in DEFAULT_LEARN_DATA["parameters"]["hot_cities"]:
        if c not in hot:
            hot.append(c)
    return hot


def get_hot_insurance_types(data: dict) -> list:
    """获取热门险种列表"""
    hot = data.get("parameters", {}).get("hot_insurance_types", DEFAULT_LEARN_DATA["parameters"]["hot_insurance_types"])
    for t in DEFAULT_LEARN_DATA["parameters"]["hot_insurance_types"]:
        if t not in hot:
            hot.append(t)
    return hot


def stats(data: dict = None) -> str:
    """输出学习统计"""
    if data is None:
        data = load_learn()
    lines = [
        f"📊 社保顾问自学习统计",
        f"  总执行: {data.get('total_runs', 0)} 次",
        f"  成功: {data.get('total_success', 0)} 次",
        f"  失败: {data.get('total_failure', 0)} 次",
        f"  连续失败: {data.get('fail_streak', 0)} 次",
        f"  最后成功: {data.get('last_success_date', '无')}",
        f"  热门城市: {data.get('parameters', {}).get('hot_cities', [])[:5]}",
        f"  热门险种: {data.get('parameters', {}).get('hot_insurance_types', [])[:5]}",
        f"  热门模块: {data.get('parameters', {}).get('hot_modules', [])[:5]}",
        f"  补贴类型: {len(data.get('environment', {}).get('subsidy_types', []))}",
        f"  待确认发现: {len(data.get('discoveries', []))}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    data = load_learn()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--stats":
            print(stats(data))
        elif cmd == "--success":
            city = sys.argv[2] if len(sys.argv) > 2 else None
            insurance_type = sys.argv[3] if len(sys.argv) > 3 else None
            module = sys.argv[4] if len(sys.argv) > 4 else None
            record_success(data, params_used={"city": city, "insurance_type": insurance_type, "module": module})
            print("✅ 已记录成功")
        elif cmd == "--failure":
            error = sys.argv[2] if len(sys.argv) > 2 else "未知错误"
            record_failure(data, error=error)
            print(f"❌ 已记录失败: {error}")
        elif cmd == "--reset":
            save_learn(json.loads(json.dumps(DEFAULT_LEARN_DATA)))
            print("🔄 已重置经验文件")
    else:
        print(stats(data))