import os
#!/usr/bin/env python3
"""
个人数字安全体检工具 - security-health-check Skill
检查邮箱泄露、密码强度、生成安全评分报告
"""

import hashlib
import json
import math
import re
import ssl
import sys
import certifi
import urllib.request
import urllib.error
from datetime import datetime

# SSL 上下文：优先验证，失败时回退
def _get_ssl_context():
    """创建SSL上下文，兼容证书不完整的环境"""
    ctx = ssl.create_default_context()
    ctx.load_verify_locations(certifi.where())
    return ctx


def check_email_breach(email):
    """通过 HIBP API 检查邮箱是否出现在已知数据泄露中"""
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}?truncateResponse=false"
    headers = {
        "User-Agent": "SecurityHealthCheck-Skill/1.0",
        "hibp-api-key": os.environ.get("HIBP_API_KEY", "")  # Optional: set HIBP_API_KEY env var for higher rate limits
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_get_ssl_context()))
        resp = opener.open(req, timeout=15)
        if resp.status == 200:
            breaches = json.loads(resp.read().decode("utf-8"))
            return {"breached": True, "breaches": breaches, "count": len(breaches)}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"breached": False, "breaches": [], "count": 0}
        elif e.code == 429:
            return {"breached": None, "error": "API速率限制，请稍后再试", "breaches": [], "count": 0}
        else:
            return {"breached": None, "error": f"API错误: {e.code}", "breaches": [], "count": 0}
    except Exception as e:
        return {"breached": None, "error": f"网络错误: {str(e)}", "breaches": [], "count": 0}
    return {"breached": False, "breaches": [], "count": 0}
    
    return {"breached": False, "breaches": [], "count": 0}


# ============================================================
# 密码泄露检查 (HIBP k-匿名 API)
# ============================================================

def check_password_pwned(password):
    """使用 HIBP k-匿名前缀查询，密码不离开本地"""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    headers = {"User-Agent": "SecurityHealthCheck-Skill/1.0", "Add-Padding": "true"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_get_ssl_context()))
        resp = opener.open(req, timeout=15)
        text = resp.read().decode("utf-8")
        for line in text.splitlines():
            parts = line.strip().split(":")
            if len(parts) == 2 and parts[0] == suffix:
                count = int(parts[1])
                return {"pwned": True, "count": count}
        return {"pwned": False, "count": 0}
    except Exception as e:
        return {"pwned": None, "error": f"查询失败: {str(e)}", "count": 0}


# ============================================================
# 密码强度分析 (本地计算)
# ============================================================

COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "master",
    "dragon", "login", "princess", "football", "shadow", "sunshine", "trustno1",
    "iloveyou", "batman", "access", "hello", "charlie", "donald", "password1",
    "qwerty123", "letmein", "welcome", "admin", "passw0rd", "1234567890",
    "000000", "123123", "111111", "1q2w3e4r", "password123", "mima123456",
    "woaini", "woaini1314", "abcd1234", "123321", "666666", "888888",
}

COMMON_WORDS = {
    "password", "admin", "login", "welcome", "hello", "love", "secret",
    "sunshine", "dragon", "master", "monkey", "shadow", "qwerty",
    "abcdef", "baseball", "football", "soccer", "hockey",
}


def analyze_password_strength(password):
    """本地分析密码强度"""
    result = {
        "length": len(password),
        "has_upper": bool(re.search(r"[A-Z]", password)),
        "has_lower": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"\d", password)),
        "has_special": bool(re.search(r"[^A-Za-z0-9]", password)),
        "is_common": password.lower() in COMMON_PASSWORDS,
        "has_common_word": any(w in password.lower() for w in COMMON_WORDS),
        "is_sequential": _has_sequential(password),
        "is_repeated": _has_repeated(password),
    }
    
    # 计算熵
    charset_size = 0
    if result["has_upper"]: charset_size += 26
    if result["has_lower"]: charset_size += 26
    if result["has_digit"]: charset_size += 10
    if result["has_special"]: charset_size += 32
    if charset_size == 0: charset_size = 26  # 默认小写
    
    entropy = len(password) * math.log2(charset_size) if charset_size > 0 else 0
    result["entropy_bits"] = round(entropy, 1)
    
    # 估算暴力破解时间（假设10亿次/秒）
    combinations = charset_size ** len(password) if charset_size > 0 else 0
    seconds = combinations / 1e9 if combinations > 0 else 0
    result["crack_time"] = _format_time(seconds)
    result["crack_time_seconds"] = seconds
    
    # 评分 (0-100)
    score = 0
    score += min(len(password) * 4, 40)  # 长度加分，最多40
    if result["has_upper"]: score += 10
    if result["has_lower"]: score += 5
    if result["has_digit"]: score += 10
    if result["has_special"]: score += 15
    if entropy > 60: score += 10
    if entropy > 80: score += 10
    
    # 扣分
    if result["is_common"]: score = max(score - 40, 5)
    if result["has_common_word"]: score = max(score - 20, 5)
    if result["is_sequential"]: score = max(score - 15, 5)
    if result["is_repeated"]: score = max(score - 10, 5)
    if len(password) < 6: score = max(score - 20, 5)
    
    result["score"] = min(max(score, 0), 100)
    
    # 评级
    if result["score"] >= 80:
        result["grade"] = "强"
        result["emoji"] = "🟢"
    elif result["score"] >= 60:
        result["grade"] = "中等"
        result["emoji"] = "🟡"
    elif result["score"] >= 40:
        result["grade"] = "弱"
        result["emoji"] = "🟠"
    else:
        result["grade"] = "极弱"
        result["emoji"] = "🔴"
    
    return result


def _has_sequential(s):
    """检测连续字符序列"""
    sequences = [
        "abcdefghijklmnopqrstuvwxyz",
        "zyxwvutsrqponmlkjihgfedcba",
        "01234567890",
        "09876543210",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm",
    ]
    s_lower = s.lower()
    for seq in sequences:
        for i in range(len(seq) - 2):
            if seq[i:i+3] in s_lower:
                return True
    return False


def _has_repeated(s):
    """检测重复字符"""
    for i in range(len(s) - 2):
        if s[i] == s[i+1] == s[i+2]:
            return True
    return False


def _format_time(seconds):
    """将秒数格式化为可读时间"""
    if seconds < 1:
        return "瞬间"
    elif seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.0f}分钟"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}小时"
    elif seconds < 86400 * 365:
        return f"{seconds/86400:.0f}天"
    elif seconds < 86400 * 365 * 1000:
        return f"{seconds/(86400*365):.0f}年"
    elif seconds < 86400 * 365 * 1e6:
        return f"{seconds/(86400*365*1000):.0f}千年"
    elif seconds < 86400 * 365 * 1e9:
        return f"{seconds/(86400*365*1e6):.0f}百万年"
    else:
        return "宇宙级别"


# ============================================================
# 安全评分计算
# ============================================================

def calculate_security_score(breach_result, password_result=None):
    """综合安全评分 0-100"""
    score = 100
    
    # 邮箱泄露扣分
    if breach_result.get("breached"):
        count = breach_result.get("count", 0)
        score -= min(count * 8, 40)  # 每次泄露扣8分，最多扣40
    elif breach_result.get("breached") is None:
        score -= 5  # 检查失败，略扣
    
    # 密码安全扣分
    if password_result:
        if password_result.get("pwned"):
            score -= 30  # 密码已泄露，重扣
            count = password_result.get("count", 0)
            if count > 1000:
                score -= 10
        pw_strength = password_result.get("score", 50)
        if pw_strength < 60:
            score -= 15
        elif pw_strength < 80:
            score -= 5
    
    score = max(score, 0)
    
    if score >= 80:
        level = "安全"
        emoji = "🟢"
    elif score >= 60:
        level = "基本安全"
        emoji = "🟡"
    elif score >= 40:
        level = "存在风险"
        emoji = "🟠"
    else:
        level = "高危"
        emoji = "🔴"
    
    return {"score": score, "level": level, "emoji": emoji}


# ============================================================
# 报告生成
# ============================================================

def generate_report(email, breach_result, password_result=None, password_strength=None, format="markdown"):
    """生成安全体检报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 遮蔽邮箱
    if email and "@" in email:
        local, domain = email.split("@", 1)
        masked = f"{local[0]}***@{domain}"
    elif email:
        masked = f"{email[:2]}***"
    else:
        masked = "未提供"
    
    # 安全评分
    sec_score = calculate_security_score(breach_result, password_result)
    
    lines = []
    lines.append(f"🔒 个人数字安全体检报告")
    lines.append(f"━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"")
    lines.append(f"📧 邮箱：{masked}")
    lines.append(f"🕐 检查时间：{now}")
    lines.append(f"📊 安全评分：{sec_score['emoji']} {sec_score['score']}/100（{sec_score['level']}）")
    lines.append(f"")
    
    # 邮箱泄露详情
    lines.append(f"├─ 邮箱泄露检查：")
    if breach_result.get("breached") is True:
        lines.append(f"│  ⚠️ 发现{breach_result['count']}次泄露")
        for b in breach_result.get("breaches", []):
            name = b.get("Name", "未知")
            date = b.get("BreachDate", "未知")
            data = ", ".join(b.get("DataClasses", []))
            lines.append(f"│  ├─ {name} ({date}) — {data}")
    elif breach_result.get("breached") is False:
        lines.append(f"│  ✅ 未发现泄露")
    else:
        err = breach_result.get("error", "未知错误")
        lines.append(f"│  ❓ 检查失败：{err}")
    
    lines.append(f"")
    
    # 密码安全
    if password_result or password_strength:
        lines.append(f"├─ 密码安全检查：")
        if password_result:
            if password_result.get("pwned"):
                lines.append(f"│  🔴 密码已泄露！出现在{password_result['count']:,}次泄露中")
                lines.append(f"│  → 立即更换此密码！")
            elif password_result.get("pwned") is False:
                lines.append(f"│  ✅ 密码未出现在已知泄露中")
            else:
                lines.append(f"│  ❓ 密码泄露检查失败：{password_result.get('error', '')}")
        
        if password_strength:
            lines.append(f"│  ")
            lines.append(f"│  密码强度：{password_strength['emoji']} {password_strength['grade']}（{password_strength['score']}/100）")
            lines.append(f"│  ├─ 长度：{password_strength['length']}字符")
            chars = []
            if password_strength["has_upper"]: chars.append("大写")
            if password_strength["has_lower"]: chars.append("小写")
            if password_strength["has_digit"]: chars.append("数字")
            if password_strength["has_special"]: chars.append("特殊字符")
            lines.append(f"│  ├─ 包含：{'、'.join(chars) if chars else '无'}")
            lines.append(f"│  ├─ 熵：{password_strength['entropy_bits']} bits")
            lines.append(f"│  └─ 暴力破解时间：{password_strength['crack_time']}")
            
            if password_strength["is_common"]:
                lines.append(f"│  ⚠️ 这是常见密码，极易被破解！")
            if password_strength["has_common_word"]:
                lines.append(f"│  ⚠️ 包含常见词汇，建议替换")
    
    lines.append(f"")
    
    # 安全建议
    lines.append(f"├─ 💡 安全建议：")
    suggestions = []
    
    if breach_result.get("breached"):
        suggestions.append(("🔴", "立即更换相关泄露网站的密码"))
        suggestions.append(("🔴", "不同网站使用不同密码"))
    
    suggestions.append(("🟡", "启用两步验证（2FA）— 推荐 Google Authenticator"))
    suggestions.append(("🟡", "使用密码管理器（推荐 Bitwarden/1Password）"))
    suggestions.append(("🟢", "定期进行安全体检（建议每30天一次）"))
    suggestions.append(("🟢", "不要在公共WiFi下输入重要密码"))
    
    if password_strength and password_strength["score"] < 60:
        suggestions.insert(0, ("🔴", "当前密码过弱，请立即更换为12位以上的复杂密码"))
    
    for emoji, text in suggestions:
        lines.append(f"│  {emoji} {text}")
    
    lines.append(f"")
    lines.append(f"━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"💡 下次检查建议：30天后")
    
    return "\n".join(lines)


# ============================================================
# 主入口
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="🔒 个人数字安全体检工具")
    parser.add_argument("--email", help="要检查的邮箱地址")
    parser.add_argument("--password", help="要检查强度的密码")
    parser.add_argument("--check", choices=["breach", "password"], help="仅检查某一项")
    parser.add_argument("--report", choices=["markdown", "json"], default="markdown", help="报告格式")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    
    args = parser.parse_args()
    
    if not args.email and not args.password:
        parser.print_help()
        print("\n⚠️ 请至少提供 --email 或 --password 参数")
        sys.exit(1)
    
    breach_result = {"breached": None, "breaches": [], "count": 0}
    password_result = None
    password_strength = None
    
    # 邮箱泄露检查
    if args.email and (not args.check or args.check == "breach"):
        print(f"🔍 正在检查邮箱泄露情况...", file=sys.stderr)
        breach_result = check_email_breach(args.email)
    
    # 密码检查
    if args.password and (not args.check or args.check == "password"):
        print(f"🔍 正在检查密码泄露情况...", file=sys.stderr)
        password_result = check_password_pwned(args.password)
        print(f"🔍 正在分析密码强度...", file=sys.stderr)
        password_strength = analyze_password_strength(args.password)
    
    # 输出
    if args.json or args.report == "json":
        output = {
            "timestamp": datetime.now().isoformat(),
            "email": args.email,
            "breach_check": breach_result,
            "password_check": password_result,
            "password_strength": password_strength,
            "security_score": calculate_security_score(breach_result, password_result),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        report = generate_report(args.email, breach_result, password_result, password_strength)
        print(report)


if __name__ == "__main__":
    import urllib.parse
    main()
