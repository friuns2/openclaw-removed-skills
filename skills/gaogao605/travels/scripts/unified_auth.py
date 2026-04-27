#!/usr/bin/env python3
"""
分贝通统一认证助手
一次输入手机号，自动完成机票和酒店双系统认证
"""
import sys
import time
from pathlib import Path

# 导入认证模块
sys.path.insert(0, str(Path(__file__).parent))
from auth import send_verification_code as flight_send_code, verify_and_get_api_key as flight_verify
from hotel_api import FbHotelApi, save_auth_token


def unified_send_captcha(mobile: str) -> dict:
    """
    统一发送验证码（同时发送机票和酒店）
    
    Args:
        mobile: 手机号
    
    Returns:
        {"flight": bool, "hotel": bool, "success": bool}
    """
    print(f"\n📱 正向 {mobile} 发送验证码...")
    
    results = {"flight": False, "hotel": False}
    
    # 发送机票验证码
    try:
        flight_send_code(mobile)
        results["flight"] = True
        print("  ✅ 机票验证码已发送")
    except Exception as e:
        print(f"  ⚠️ 机票验证码发送失败: {e}")
    
    # 等待2秒避免并发限制
    time.sleep(2)
    
    # 发送酒店验证码
    try:
        api = FbHotelApi()
        res = api.send_captcha(mobile)
        if res.get("code") == 0:
            results["hotel"] = True
            print("  ✅ 酒店验证码已发送")
        else:
            print(f"  ⚠️ 酒店验证码发送失败: {res.get('msg', '未知错误')}")
    except Exception as e:
        print(f"  ⚠️ 酒店验证码发送失败: {e}")
    
    results["success"] = results["flight"] or results["hotel"]
    
    if results["success"]:
        print("\n✅ 验证码已发送，请在5分钟内输入收到的验证码")
    else:
        print("\n❌ 验证码发送失败，请稍后重试")
    
    return results


def unified_verify(mobile: str, captcha: str) -> dict:
    """
    统一验证（同时验证机票和酒店）
    
    Args:
        mobile: 手机号
        captcha: 验证码
    
    Returns:
        {"flight": bool, "hotel": bool, "success": bool, "flight_ok": bool, "hotel_ok": bool}
    """
    print(f"\n🔐 正在验证...")
    
    results = {"flight": False, "hotel": False, "flight_ok": False, "hotel_ok": False}
    
    # 验证机票
    try:
        flight_verify(mobile, captcha)
        results["flight"] = True
        results["flight_ok"] = True
        print("  ✅ 机票认证成功")
    except Exception as e:
        print(f"  ⚠️ 机票认证失败: {e}")
    
    # 验证酒店
    try:
        api = FbHotelApi()
        res = api.verify_captcha(mobile, captcha)
        identity_code = res.get("data", {}).get("identity_code", "")
        if identity_code:
            save_auth_token(identity_code, mobile)
            results["hotel"] = True
            results["hotel_ok"] = True
            print("  ✅ 酒店认证成功")
        else:
            print(f"  ⚠️ 酒店认证失败: {res.get('msg', '未知错误')}")
    except Exception as e:
        print(f"  ⚠️ 酒店认证失败: {e}")
    
    results["success"] = results["flight_ok"] or results["hotel_ok"]
    
    if results["success"]:
        print("\n🎉 认证成功！现在可以使用分贝通所有功能了")
    else:
        print("\n❌ 认证失败，请检查验证码是否正确")
    
    return results


def quick_auth(mobile: str) -> bool:
    """
    快速认证流程（发送验证码 + 等待用户输入）
    
    这是一个辅助函数，用于简化认证对话流程
    
    Args:
        mobile: 手机号
    
    Returns:
        认证是否成功
    """
    # 发送验证码
    send_result = unified_send_captcha(mobile)
    
    if not send_result["success"]:
        return False
    
    # 提示用户输入验证码
    print("\n请输入验证码: ")
    
    # 注意：实际使用中需要用户输入验证码
    # 这里只是示例，实际调用应该分开执行
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("""
================================================================================
分贝通统一认证助手
================================================================================
用法: python3 unified_auth.py <命令> <手机号> [验证码]

命令:
  send <手机号>           发送验证码（机票+酒店）
  verify <手机号> <验证码>  验证并完成认证（机票+酒店）

示例:
  python3 unified_auth.py send 13800138000
  python3 unified_auth.py verify 13800138000 1234
================================================================================
""")
        sys.exit(0)
    
    command = sys.argv[1]
    mobile = sys.argv[2]
    
    if command == "send":
        unified_send_captcha(mobile)
    
    elif command == "verify":
        if len(sys.argv) < 4:
            print("用法: unified_auth.py verify <手机号> <验证码>")
            sys.exit(1)
        captcha = sys.argv[3]
        unified_verify(mobile, captcha)
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)