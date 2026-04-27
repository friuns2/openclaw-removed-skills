#!/usr/bin/env python3
"""
分贝通统一认证状态检查
检查机票和酒店两套系统的认证状态
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# 认证文件路径
FLIGHT_AUTH_FILE = Path.home() / ".fbt_auth.json"  # 机票认证（临时目录）
HOTEL_AUTH_FILE = Path.home() / ".fbt-auth.json"   # 酒店认证

def check_single_auth(auth_file: Path, system_name: str) -> dict:
    """
    检查单个系统的认证状态
    
    Args:
        auth_file: 认证文件路径
        system_name: 系统名称（机票/酒店）
    
    Returns:
        {"status": "ok|expired|missing", "phone": str, "days_remaining": int, "auth_time": str}
    """
    if not auth_file.exists():
        return {"status": "missing", "system": system_name}
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            auth_data = json.load(f)
        
        # 获取认证信息
        auth_time_str = None
        phone = None
        
        # 机票系统格式
        if system_name == "机票":
            auth_time_str = auth_data.get("auth_time")
            phone = auth_data.get("phone")
            expire_days = auth_data.get("expire_days", 90)
        # 酒店系统格式
        else:
            auth_time_str = auth_data.get("created_at") or auth_data.get("updated_at")
            phone = auth_data.get("mobile")
            expire_days = 90  # 酒店默认90天
        
        if not auth_time_str:
            return {"status": "missing", "system": system_name}
        
        # 解析认证时间
        try:
            auth_time = datetime.fromisoformat(auth_time_str)
        except:
            auth_time = datetime.strptime(auth_time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        
        # 计算过期时间
        expire_time = auth_time + timedelta(days=expire_days)
        days_remaining = (expire_time - datetime.now()).days
        
        if days_remaining < 0:
            return {"status": "expired", "system": system_name, "days_remaining": 0}
        
        return {
            "status": "ok",
            "system": system_name,
            "phone": phone,
            "days_remaining": days_remaining,
            "auth_time": auth_time.strftime("%Y-%m-%d %H:%M")
        }
    except Exception as e:
        return {"status": "error", "system": system_name, "error": str(e)}


def check_all_auth() -> dict:
    """
    检查所有系统的认证状态
    
    Returns:
        {
            "flight": {...},  # 机票认证状态
            "hotel": {...},   # 酒店认证状态
            "all_ok": bool,   # 全部认证OK
            "summary": str    # 状态摘要
        }
    """
    flight_status = check_single_auth(FLIGHT_AUTH_FILE, "机票")
    hotel_status = check_single_auth(HOTEL_AUTH_FILE, "酒店")
    
    all_ok = flight_status["status"] == "ok" and hotel_status["status"] == "ok"
    
    # 生成摘要
    summary_lines = []
    for status in [flight_status, hotel_status]:
        system = status.get("system", "?")
        stat = status.get("status", "?")
        if stat == "ok":
            phone = status.get("phone", "?")
            days = status.get("days_remaining", "?")
            summary_lines.append(f"✅ {system}: 已认证（{phone}，剩余{days}天）")
        elif stat == "expired":
            summary_lines.append(f"⚠️ {system}: 已过期，请重新登录")
        elif stat == "missing":
            summary_lines.append(f"❌ {system}: 未认证")
        else:
            summary_lines.append(f"❓ {system}: 检查失败")
    
    return {
        "flight": flight_status,
        "hotel": hotel_status,
        "all_ok": all_ok,
        "summary": "\n".join(summary_lines)
    }


def get_system_to_auth(intent: str) -> str:
    """
    根据意图判断需要哪个系统的认证
    
    Args:
        intent: 用户意图（酒店/机票/订单）
    
    Returns:
        "flight" | "hotel" | "both"
    """
    if intent in ["flight_search", "flight_booking", "flight_change", "flight_refund"]:
        return "flight"
    elif intent in ["hotel_search", "hotel_booking", "hotel_order"]:
        return "hotel"
    else:
        return "both"


def print_auth_status():
    """打印认证状态"""
    result = check_all_auth()
    
    print("\n" + "=" * 50)
    print("分贝通认证状态")
    print("=" * 50)
    print(result["summary"])
    print("=" * 50)
    
    if result["all_ok"]:
        print("\n✅ 全部认证有效，可直接使用所有功能")
    else:
        print("\n⚠️ 需要认证才能使用相关功能")
        print("   - 机票功能：回复手机号认证")
        print("   - 酒店功能：回复手机号认证")


if __name__ == "__main__":
    print_auth_status()