#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TaxRiskGuard -  ( Skill API)
: 

Security:
- USCC: 6+****+4
- API Key(XOR+base64)
- (MD5 hash)
- (If-None-Match)

Usage:
    python learn_sync.py --upload              # learn_data.json
    python learn_sync.py --query               # 
    python learn_sync.py --sync                # ()
    python learn_sync.py --status              # 
    python learn_sync.py --test-api            # API

Author: QQ 1817694478 | Q-Group: 972156177
"""
# Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
# Skill: tax-policy-knowledge | Version: 1.3.5
# Author: QQ 1817694478 | Q-Group: 972156177
# Unauthorized copying, modification, or distribution is prohibited.
import sys
import io
import re
import json
import os
import hashlib
import time
import base64
import argparse
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Windows GBK console compatibility (skip if already set by entry module)
if sys.platform == 'win32' and not getattr(sys, '_tax_risk_utf8_set', False):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    sys._tax_risk_utf8_set = True

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
ASSETS_DIR = SKILL_DIR / "assets"
DATA_DIR = SKILL_DIR / "data"

# ============================================================
#  - API Key
# ============================================================
_OBFUSCATED_API_KEY = "QdI7X4yy/Ie432lRYgPSX5YHw7m56HsPTySAew=="

# API (XOR+base64)
_OBFUSCATED_API_BASE = "FSkRDx8fDklMT0lRXVhXXR0eRklITUtGR0pJXVtOExwZTEVLSE1LRkdKSV1bTkxL"

SKILL_NAME = "tax-policy-knowledge"


def log(msg: str, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean = re.sub(r'[\U00010000-\U0010ffff]', '', str(msg))
    print(f"[{ts}] [{level}] {clean}", flush=True)


def derive_key() -> bytes:
    """"""
    # 
    return hashlib.sha256(b"TaxRiskGuard_Skill_Learning_Sync_2026").digest()


def _deobfuscate_string(obfuscated: str) -> str:
    """"""
    key = derive_key()
    try:
        xored = base64.b64decode(obfuscated)
        key_stream = key
        while len(key_stream) < len(xored):
            key_stream += hashlib.sha256(key_stream[-32:]).digest()
        plain_bytes = bytes(a ^ b for a, b in zip(xored, key_stream[:len(xored)]))
        return plain_bytes.decode('utf-8')
    except Exception as e:
        log(f": {e}", "ERROR")
        return ""


def get_api_key() -> str:
    """API Key"""
    key = _deobfuscate_string(_OBFUSCATED_API_KEY)
    # key
    if not key:
        log("[WARNING] API Key", "WARNING")
        return "sk-stustar-test-key"
    return key


def get_api_base() -> str:
    """Get API base URL from obfuscated config or environment."""
    base = _deobfuscate_string(_OBFUSCATED_API_BASE)
    # Fallback to environment variable (obfuscated)
    if not base:
        base = os.environ.get("TAX_POLICY_API_BASE", "")
    if not base:
        log("[WARNING] API base not configured, cloud sync disabled", "WARNING")
        return ""  # Return empty string to disable cloud sync
    return base


# ============================================================
# 
# ============================================================
def mask_uscc(uscc: str) -> str:
    """USCC: 6+****+4"""
    if not uscc or len(uscc) < 10:
        return "***"
    return uscc[:6] + "********" + uscc[-4:]


def desensitize_data(data: dict) -> dict:
    """"""
    safe = json.loads(json.dumps(data))
    
    def _mask(obj):
        if isinstance(obj, dict):
            sensitive_keys = {
                "uscc": mask_uscc,
                "tax_number": lambda x: "***MASKED***" if x else "",
                "credit_code": mask_uscc,
                "id_card": lambda x: x[:3] + "***********" + x[-4:] if x and len(x) > 7 else "***",
                "phone": lambda x: x[:3] + "****" + x[-4:] if x and len(x) > 7 else "***",
                "email": lambda x: x[:2] + "***@" + x.split("@")[-1] if x and "@" in x else "***",
            }
            for key in sensitive_keys:
                if key in obj and obj[key]:
                    obj[key] = sensitive_keys[key](str(obj[key]))
            
            for v in obj.values():
                if isinstance(v, dict):
                    _mask(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            _mask(item)
        return obj
    
    return _mask(safe)


# ============================================================
# 
# ============================================================
def load_local_learn_data() -> dict:
    """learn_data.json"""
    learn_path = ASSETS_DIR / "learn_data.json"
    if not learn_path.exists():
        return create_default_learn_data()
    
    try:
        with open(learn_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f": {e}", "ERROR")
        return create_default_learn_data()


def save_local_learn_data(data: dict) -> bool:
    """learn_data.json"""
    learn_path = ASSETS_DIR / "learn_data.json"
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(learn_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log(f": {e}", "ERROR")
        return False


def create_default_learn_data() -> dict:
    """"""
    return {
        "version": "1.0.0",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "interaction_count": 0,
        "discoveries": [],
        "policy_updates": [],
        "knowledge_base_updates": [],
        "training_cases": [],
        "user_profiles": {},
        "cloud_sync": {
            "last_upload_hash": None,
            "last_download_time": None,
            "merge_count": 0
        }
    }


def calc_data_hash(data: dict) -> str:
    """(MD5)"""
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()


# ============================================================
# API
# ============================================================
def api_request(method: str, endpoint: str, data: dict = None, 
                headers: dict = None, timeout: int = 15) -> dict:
    """API"""
    api_base = get_api_base()
    url = f"{api_base}{endpoint}"
    
    default_headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "User-Agent": "TaxRiskGuard/1.2.1"
    }
    if headers:
        default_headers.update(headers)
    
    try:
        if method == "GET":
            req = Request(url, headers=default_headers, method="GET")
        else:  # POST
            body = json.dumps(data, ensure_ascii=False).encode('utf-8') if data else b''
            default_headers["Content-Type"] = "application/json"
            req = Request(url, data=body, headers=default_headers, method="POST")
        
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    
    except HTTPError as e:
        # code
        if e.code in (401, 403):
            return {"code": e.code, "msg": f": API Key", "data": None, "auth_error": True}
        return {"code": e.code, "msg": f"HTTP Error: {e.reason}", "data": None}
    except URLError as e:
        return {"code": -1, "msg": f"URL Error: {e.reason}", "data": None}
    except Exception as e:
        return {"code": -2, "msg": f"Request Error: {str(e)}", "data": None}


# ============================================================
# 
# ============================================================
def upload_learn_data(remark: str = "") -> dict:
    """"""
    log("...")
    
    # 1. 
    local_data = load_local_learn_data()
    safe_data = desensitize_data(local_data)
    
    # 2. 
    data_hash = calc_data_hash(safe_data)
    
    # 3. ()
    last_hash = local_data.get("cloud_sync", {}).get("last_upload_hash")
    if last_hash == data_hash:
        log("")
        return {"success": True, "skipped": True, "reason": ""}
    
    # 4. 
    payload = {
        "skillName": SKILL_NAME,
        "skillJson": safe_data,
        "remark": remark or f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    # 5. API
    result = api_request("POST", "/upload", payload)
    
    # 
    if result.get("auth_error"):
        log("[WARNING] ()", "WARNING")
        return {"success": False, "auth_error": True, "error": result.get("msg"), "code": result.get("code")}
    
    if result.get("code") == 0:
        data = result.get("data", {})
        is_new = data.get("isNew", False)
        data_changed = data.get("dataChanged", False)
        
        # hash
        local_data["cloud_sync"] = local_data.get("cloud_sync", {})
        local_data["cloud_sync"]["last_upload_hash"] = data_hash
        local_data["cloud_sync"]["last_upload_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_local_learn_data(local_data)
        
        log(f"! ID: {data.get('id')}, : {is_new}, : {data_changed}")
        return {
            "success": True,
            "skipped": False,
            "is_new": is_new,
            "data_changed": data_changed,
            "data_hash": data_hash,
            "record_id": data.get("id")
        }
    else:
        log(f": {result.get('msg')}", "ERROR")
        return {"success": False, "error": result.get("msg"), "code": result.get("code")}


# ============================================================
# 
# ============================================================
# last_data_hashIf-None-Match
def get_cached_data_hash() -> str:
    """hash"""
    cache_file = DATA_DIR / "learn_sync_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                return cache.get("cloud_data_hash", "")
        except:
            pass
    return ""


def save_cached_data_hash(data_hash: str, data: dict = None):
    """hash"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = DATA_DIR / "learn_sync_cache.json"
    cache = {
        "cloud_data_hash": data_hash,
        "last_update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if data:
        cache["cloud_data_summary"] = {
            "version": data.get("version"),
            "interaction_count": data.get("interaction_count"),
            "discoveries_count": len(data.get("discoveries", [])),
            "policy_count": len(data.get("policy_updates", []))
        }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def query_cloud_data() -> dict:
    """()"""
    log("...")
    
    # hash
    last_hash = get_cached_data_hash()
    
    headers = {}
    if last_hash:
        headers["If-None-Match"] = last_hash
        log(f": {last_hash[:16]}...")
    
    endpoint = f"/query?skillName={SKILL_NAME}"
    result = api_request("GET", endpoint, headers=headers)
    
    # 
    if result.get("auth_error"):
        log("[WARNING] ()", "WARNING")
        return {"success": False, "auth_error": True, "error": result.get("msg"), "code": result.get("code")}
    
    if result.get("code") == 0:
        data = result.get("data", {})
        
        # 
        if not data.get("changed", True):
            log("")
            return {"success": True, "changed": False, "quota": data.get("quotaRemaining")}
        
        # skillJson
        cloud_data_str = data.get("skillJson", "{}")
        try:
            cloud_data = json.loads(cloud_data_str) if isinstance(cloud_data_str, str) else cloud_data_str
        except:
            cloud_data = {}
        
        # hash
        new_hash = data.get("dataHash", "")
        save_cached_data_hash(new_hash, cloud_data)
        
        log(f"! : {data.get('quotaRemaining')}")
        return {
            "success": True,
            "changed": True,
            "data": cloud_data,
            "data_hash": new_hash,
            "quota": data.get("quotaRemaining")
        }
    else:
        log(f": {result.get('msg')}", "ERROR")
        return {"success": False, "error": result.get("msg"), "code": result.get("code")}


def merge_cloud_to_local(cloud_data: dict) -> dict:
    """"""
    log("...")
    
    local_data = load_local_learn_data()
    merge_stats = {
        "discoveries_added": 0,
        "policies_added": 0,
        "kb_updates_added": 0,
        "cases_added": 0,
        "profiles_merged": 0
    }
    
    # discoveries(ID)
    local_ids = {d.get("id") for d in local_data.get("discoveries", []) if d.get("id")}
    for discovery in cloud_data.get("discoveries", []):
        if discovery.get("id") and discovery["id"] not in local_ids:
            local_data["discoveries"].append(discovery)
            merge_stats["discoveries_added"] += 1
            local_ids.add(discovery["id"])
    
    # policy_updates()
    local_policies = {(p.get("date"), p.get("title")) for p in local_data.get("policy_updates", [])}
    for policy in cloud_data.get("policy_updates", []):
        key = (policy.get("date"), policy.get("title"))
        if key not in local_policies:
            local_data["policy_updates"].append(policy)
            merge_stats["policies_added"] += 1
            local_policies.add(key)
    
    # knowledge_base_updates
    local_kb = {(k.get("date"), k.get("type"), k.get("field")) for k in local_data.get("knowledge_base_updates", [])}
    for kb in cloud_data.get("knowledge_base_updates", []):
        key = (kb.get("date"), kb.get("type"), kb.get("field"))
        if key not in local_kb:
            local_data["knowledge_base_updates"].append(kb)
            merge_stats["kb_updates_added"] += 1
            local_kb.add(key)
    
    # training_cases
    local_cases = {c.get("case_id") for c in local_data.get("training_cases", [])}
    for case in cloud_data.get("training_cases", []):
        if case.get("case_id") and case["case_id"] not in local_cases:
            local_data["training_cases"].append(case)
            merge_stats["cases_added"] += 1
            local_cases.add(case["case_id"])
    
    # user_profiles()
    local_profiles = local_data.get("user_profiles", {})
    for uscc, profile in cloud_data.get("user_profiles", {}).items():
        if uscc not in local_profiles:
            local_profiles[uscc] = profile
            merge_stats["profiles_merged"] += 1
    local_data["user_profiles"] = local_profiles
    
    # 
    local_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    local_data["cloud_sync"] = local_data.get("cloud_sync", {})
    local_data["cloud_sync"]["last_download_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    local_data["cloud_sync"]["merge_count"] = local_data["cloud_sync"].get("merge_count", 0) + 1
    
    # 
    if save_local_learn_data(local_data):
        total_added = sum(merge_stats.values())
        log(f"!  {total_added} ")
        
        # 
        achievement_report = generate_achievement_report(merge_stats, cloud_data)
        
        return {
            "success": True, 
            "stats": merge_stats, 
            "total_added": total_added,
            "achievement_report": achievement_report
        }
    else:
        return {"success": False, "error": ""}


def generate_achievement_report(stats: dict, cloud_data: dict) -> str:
    """"""
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("[CELEBRATE] ")
    lines.append("=" * 60)
    
    total = sum(stats.values())
    if total == 0:
        lines.append("[MAIL] ")
    else:
        lines.append(f"\n[STAT]  {total} \n")
        
        #  discoveries
        if stats["discoveries_added"] > 0:
            lines.append(f"  [BOOK] {stats['discoveries_added']} ")
            # 3
            for i, d in enumerate(cloud_data.get("discoveries", [])[:3]):
                keyword = d.get("keyword", "")
                lines.append(f"      {keyword}")
            if stats["discoveries_added"] > 3:
                lines.append(f"      ...  {stats['discoveries_added'] - 3} ")
        
        #  policies
        if stats["policies_added"] > 0:
            lines.append(f"  [LIST] {stats['policies_added']} ")
            for i, p in enumerate(cloud_data.get("policy_updates", [])[:3]):
                title = p.get("title", "")[:30]
                lines.append(f"      {title}...")
            if stats["policies_added"] > 3:
                lines.append(f"      ...  {stats['policies_added'] - 3} ")
        
        #  cases
        if stats["cases_added"] > 0:
            lines.append(f"  [FOLDER] {stats['cases_added']} ")
            for i, c in enumerate(cloud_data.get("training_cases", [])[:3]):
                company = c.get("company", "")
                industry = c.get("industry", "")
                lines.append(f"      {company} ({industry})")
            if stats["cases_added"] > 3:
                lines.append(f"      ...  {stats['cases_added'] - 3} ")
        
        #  profiles
        if stats["profiles_merged"] > 0:
            lines.append(f"  [USER] {stats['profiles_merged']} ")
        
        #  kb_updates
        if stats["kb_updates_added"] > 0:
            lines.append(f"  [EMOJI] {stats['kb_updates_added']} ")
    
    lines.append("\n ")
    lines.append("=" * 60)
    
    return "\n".join(lines)


# ============================================================
# 
# ============================================================
def bidirectional_sync(silent: bool = False) -> dict:
    """: 
    
    Args:
        silent: True()
    """
    log("=" * 50)
    log("...")
    log("=" * 50)
    
    results = {
        "upload": None,
        "download": None,
        "merge": None,
        "auth_error": False  # 
    }
    
    # Step 1: 
    log("\n[Step 1/3] ...")
    results["upload"] = upload_learn_data("-")
    
    # 
    if results["upload"].get("auth_error"):
        results["auth_error"] = True
        if not silent:
            log("[INFO] ", "INFO")
        # 
    
    # Step 2: 
    log("\n[Step 2/3] ...")
    results["download"] = query_cloud_data()
    
    if results["download"].get("auth_error"):
        results["auth_error"] = True
        if not silent:
            log("[INFO] ", "INFO")
    
    # Step 3: ()
    if results["download"].get("success") and results["download"].get("changed"):
        log("\n[Step 3/3] ...")
        cloud_data = results["download"].get("data", {})
        results["merge"] = merge_cloud_to_local(cloud_data)
        
        # 
        if results["merge"].get("success") and results["merge"].get("total_added", 0) > 0:
            achievement = results["merge"].get("achievement_report", "")
            if achievement:
                print(achievement)  # 
    else:
        if results["auth_error"]:
            log("\n[Step 3/3] ")
        else:
            log("\n[Step 3/3] ")
        results["merge"] = {"success": True, "skipped": True}
    
    # 
    log("\n" + "=" * 50)
    log("!")
    if results["auth_error"]:
        log("  [NOTICE] ")
    log(f"  : {'' if results['upload'].get('success') else ''} ")
    log(f"  : {'' if results['download'].get('changed') else '/'} ")
    log(f"  : {'' if results['merge'].get('success') else ''} ")
    log("=" * 50)
    
    # 
    if results["auth_error"]:
        results["notice"] = ""
        # (silent=True)
        if not silent:
            log("\n" + "=" * 60)
            log(":")
            log("  API")
            log("  " + results["notice"])
            log("=" * 60)
    
    return results


# ============================================================
# 
# ============================================================
def get_sync_status() -> dict:
    """"""
    local_data = load_local_learn_data()
    cloud_sync = local_data.get("cloud_sync", {})
    
    # 
    status = {
        "local": {
            "version": local_data.get("version"),
            "last_updated": local_data.get("last_updated"),
            "interaction_count": local_data.get("interaction_count", 0),
            "discoveries_count": len(local_data.get("discoveries", [])),
            "policies_count": len(local_data.get("policy_updates", [])),
            "cases_count": len(local_data.get("training_cases", [])),
        },
        "cloud_sync": {
            "last_upload_hash": cloud_sync.get("last_upload_hash", "")[:16] + "..." if cloud_sync.get("last_upload_hash") else "",
            "last_upload_time": cloud_sync.get("last_upload_time", ""),
            "last_download_time": cloud_sync.get("last_download_time", ""),
            "merge_count": cloud_sync.get("merge_count", 0)
        }
    }
    
    # 
    cache_file = DATA_DIR / "learn_sync_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                status["cache"] = {
                    "cloud_data_hash": cache.get("cloud_data_hash", "")[:16] + "..." if cache.get("cloud_data_hash") else "",
                    "last_update_time": cache.get("last_update_time", "")
                }
        except:
            pass
    
    return status


# ============================================================
# API
# ============================================================
def test_api() -> dict:
    """Test API connection."""
    log("Testing API...")
    
    # Check if API base is configured
    api_base = get_api_base()
    if not api_base:
        log("API base not configured, cloud sync disabled", "WARNING")
        log("To enable cloud sync, set TAX_POLICY_API_BASE environment variable", "INFO")
        return {"available": False, "error": "API base not configured", "mode": "local_only"}
    
    result = api_request("GET", "/ping", timeout=10)
    
    if result.get("code") == 0:
        data = result.get("data", {})
        log(f"API OK! Service: {data.get('service')}")
        return {"available": True, "service": data.get("service")}
    else:
        log(f"API Error: {result.get('msg')}", "ERROR")
        return {"available": False, "error": result.get("msg")}


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="TaxRiskGuard ")
    parser.add_argument("--upload", action="store_true", help="")
    parser.add_argument("--query", action="store_true", help="")
    parser.add_argument("--sync", action="store_true", help="(++)")
    parser.add_argument("--status", action="store_true", help="")
    parser.add_argument("--test-api", action="store_true", help="API")
    parser.add_argument("--remark", type=str, default="", help="")
    parser.add_argument("--merge-only", action="store_true", help="")
    
    args = parser.parse_args()
    
    if args.test_api:
        result = test_api()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    if args.status:
        status = get_sync_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    
    if args.upload:
        result = upload_learn_data(args.remark)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("success") else 1)
    
    if args.query:
        result = query_cloud_data()
        if result.get("success") and result.get("changed"):
            # 
            merge_result = merge_cloud_to_local(result.get("data", {}))
            print(json.dumps({"query": result, "merge": merge_result}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    if args.sync:
        results = bidirectional_sync()
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    
    # : 
    status = get_sync_status()
    print("=" * 60)
    print("TaxRiskGuard ")
    print("=" * 60)
    print(f"\n:")
    for k, v in status["local"].items():
        print(f"  {k}: {v}")
    print(f"\n:")
    for k, v in status["cloud_sync"].items():
        print(f"  {k}: {v}")
    if "cache" in status:
        print(f"\n:")
        for k, v in status["cache"].items():
            print(f"  {k}: {v}")
    print("\n" + "=" * 60)
    print(" --upload , --query , --sync ")
    print("=" * 60)


if __name__ == "__main__":
    main()
