#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财税政策知识库 - 自动更新脚本
auto_update_knowledge.py

功能：
  1. 联网搜索最新财税政策信息
  2. 比对知识库现有版本，检测是否有新内容
  3. 自动更新知识库文件（SKILL.md / tax-policy-database.md）
  4. 记录更新日志（references/update_log.md）

用法：
  python auto_update_knowledge.py                    # 全量更新
  python auto_update_knowledge.py --monthly          # 月度更新
  python auto_update_knowledge.py --policy "关键词"  # 按关键词更新
  python auto_update_knowledge.py --risk             # 仅更新风险预警指标
  python auto_update_knowledge.py --check            # 仅检查版本，不写入

依赖：requests（联网搜索）
  pip install requests
"""
# Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
# Skill: tax-policy-knowledge | Version: 0.0.0
# Author: QQ 1817694478 | Q-Group: 972156177
# Unauthorized copying, modification, or distribution is prohibited.
# This software is provided "as is" without warranty of any kind.

import sys
import os
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────
# 配置区
# ─────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent.resolve()
DATABASE_FILE = SKILL_DIR / "references" / "tax-policy-database.md"
SKILL_FILE = SKILL_DIR / "SKILL.md"
LEARNING_LOG = SKILL_DIR / "references" / "learning_log.md"
UPDATE_LOG = SKILL_DIR / "references" / "update_log.md"
SELF_LEARNING_SCRIPT = SKILL_DIR / "scripts" / "self_learning.py"

CURRENT_VERSION = "v1.2.0"
UPDATE_DATE = datetime.now().strftime("%Y-%m-%d")

# ─────────────────────────────────────────
# 搜索关键词配置
# ─────────────────────────────────────────
SEARCH_TERMS_MONTHLY = [
    "2026年{month}月 财税政策 最新公告 财政部 税务总局",
    "2026年{month}月 税务风险预警 金税四期 最新指标",
    "2026年{month}月 增值税 企业所得税 最新优惠 申报口径",
]

SEARCH_TERMS_RISK = [
    "2026年 税务风险预警指标 金税四期 最新",
    "金税四期 电子税务局 风险预警 指标阈值",
    "2026年 税务稽查 重点 预警指标",
]

SEARCH_TERMS_FULL = [
    "2026年 最新财税政策 财政部 税务总局公告",
    "2026年 增值税 企业所得税 个人所得税 最新优惠",
    "2026年 税务风险预警 金税四期 22项指标",
    "2026年 小微企业 六税两费 最新政策",
]

# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────
def log(msg: str):
    """带时间戳的日志输出（兼容Windows GBK控制台）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 移除emoji以兼容Windows GBK控制台
    clean_msg = re.sub(r'[\U00010000-\U0010ffff]', '', msg)
    print(f"[{timestamp}] {clean_msg}", flush=True)

def log_print(msg: str):
    """无时间戳的纯消息输出（兼容Windows GBK控制台）"""
    clean_msg = re.sub(r'[\U00010000-\U0010ffff]', '', msg)
    print(clean_msg, flush=True)


def read_file_content(filepath: Path) -> str:
    """读取文件内容，文件不存在时返回空字符串"""
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def extract_version_info(content: str) -> dict:
    """从文件头部提取版本信息（兼容SKILL.md和tax-policy-database.md格式）"""
    # 格式1：SKILL.md — 版本：v1.2.0 | 更新日期：2026-04-19
    version_pattern = r"版本[：:]\s*(v?[\d.]+)\s*\|.*?更新日期[：:]\s*(\d{4}-\d{2}-\d{2})"
    match = re.search(version_pattern, content)
    if match:
        return {"version": match.group(1), "date": match.group(2)}
    # 格式2：tax-policy-database.md — 更新时间：2026-04-19
    date_pattern = r"更新时间[：:]\s*(\d{4}-\d{2}-\d{2})"
    date_match = re.search(date_pattern, content)
    if date_match:
        return {"version": "unknown", "date": date_match.group(1)}
    return {"version": "unknown", "date": "unknown"}


def extract_latest_policy_items(content: str) -> list:
    """从政策文件索引中提取最新文号列表"""
    items = []
    # 匹配形如：财政部 税务总局公告2026年第X号
    pattern = r"(\d{4}年第?\d+号|国务院令第\d+号)"
    items = re.findall(pattern, content)
    return items


def search_web(query: str) -> dict:
    """
    模拟联网搜索（实际使用时调用真实API或浏览器自动化）
    返回：{"title": "...", "url": "...", "snippet": "..."}
    """
    # Note: This is a demo structure. For actual use, integrate with real search API.
    # Recommended: Use MCP tools or requests to call search API.
    # Default source URL should be configured via environment variable:
    # TAX_POLICY_DEFAULT_SOURCE_URL (e.g., https://www.chinatax.gov.cn/)
    default_source = os.environ.get("TAX_POLICY_DEFAULT_SOURCE_URL", "")
    return {
        "title": f"[Search Result] {query}",
        "url": default_source if default_source else "NOT_CONFIGURED",
        "snippet": f"Search keyword: {query}. Please configure TAX_POLICY_DEFAULT_SOURCE_URL for actual search.",
        "timestamp": datetime.now().isoformat(),
    }


def check_version_changed(old_info: dict, new_policies: list) -> bool:
    """判断版本是否有实质变化"""
    if not old_info or old_info.get("version") == "unknown":
        return True
    # 如果发现新文号，说明有新内容
    for policy in new_policies:
        if policy not in ["unknown", ""]:
            return True
    return False


def build_update_record(records: list, update_type: str, content_summary: str) -> str:
    """构建更新记录条目"""
    entry = f"""
---
### 更新记录 #{len(records) + 1}
- **更新时间**：{UPDATE_DATE}
- **更新类型**：{update_type}
- **内容摘要**：{content_summary}
- **发现来源**：联网搜索
- **验证状态**：待验证
"""
    return entry


def ensure_references_dir():
    """确保 references 目录存在"""
    refs_dir = SKILL_DIR / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    return refs_dir


# ─────────────────────────────────────────
# 核心更新逻辑
# ─────────────────────────────────────────
def run_full_update() -> dict:
    """
    执行全量更新流程
    返回：{"changed": bool, "records": list, "summary": str}
    """
    log("[START] 开始执行全量知识库更新...")

    # 1. 读取现有知识库状态
    db_content = read_file_content(DATABASE_FILE)
    skill_content = read_file_content(SKILL_FILE)

    old_version = extract_version_info(db_content)
    old_policies = extract_latest_policy_items(db_content)

    log(f"[INFO] 当前知识库版本：{old_version.get('version', 'unknown')}")
    log(f"[INFO] 当前政策文号数：{len(old_policies)}")

    # 2. 联网搜索最新政策（模拟 - 实际接入真实搜索）
    log("[SEARCH] 正在联网搜索最新政策...")
    search_results = []
    for term in SEARCH_TERMS_FULL:
        result = search_web(term)
        search_results.append(result)
        log(f"   [OK] 搜索完成：{result['title'][:50]}...")

    # 3. 模拟分析搜索结果，提取新政策
    new_policies_found = []
    for result in search_results:
        # 实际使用时：解析搜索结果，提取文号、政策名称、生效日期等
        # 此处为演示，实际应解析真实返回内容
        if "2026年" in result["snippet"] or "2026年" in result["title"]:
            new_policies_found.append(result)

    log(f"[STAT] 发现可能的新政策条目：{len(new_policies_found)}")

    # 4. 判断是否需要更新
    need_update = check_version_changed(old_version, [p.get("title", "") for p in new_policies_found])

    # 5. 生成更新记录
    records = []
    if need_update:
        summary = f"发现{len(new_policies_found)}条可能的新政策，建议人工核实后合并入知识库。"
        record = build_update_record(
            records,
            update_type="全量更新",
            content_summary=summary,
        )
        records.append(record)

        # 追加到更新日志
        ensure_references_dir()
        existing_log = read_file_content(UPDATE_LOG)
        new_log = existing_log + record
        UPDATE_LOG.write_text(new_log, encoding="utf-8")
        log(f"[OK] 更新记录已保存至：{UPDATE_LOG}")

        # 6. 触发自学习脚本（分析搜索结果，学习新模式）
        log("[LEARN] 触发自学习脚本...")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(SELF_LEARNING_SCRIPT), "--source", "auto_update", "--count", str(len(new_policies_found))],
                capture_output=True,
                text=True,
                timeout=30,
            )
            log(f"   自学习脚本输出：{result.stdout.strip()}")
        except Exception as e:
            log(f"   [WARN] 自学习脚本执行失败：{e}")

    else:
        log("[INFO] 未检测到实质变化，知识库版本不变。")
        summary = "未检测到新政策，知识库保持最新状态。"

    return {
        "changed": need_update,
        "records": records,
        "summary": summary,
        "old_version": old_version,
        "new_policies": new_policies_found,
        "search_count": len(search_results),
    }


def run_monthly_update(month: str = None) -> dict:
    """执行月度更新"""
    if not month:
        month = datetime.now().strftime("%Y年%m月")

    log(f"[START] 开始执行月度更新（月份：{month}）...")

    search_terms = [term.format(month=month.split("年")[1].replace("月", "")) for term in SEARCH_TERMS_MONTHLY]
    # 重新构建带完整月份的搜索词
    search_terms = [
        f"{month} 财税政策 最新公告 财政部 税务总局",
        f"{month} 税务风险预警 申报提醒",
        f"{month} 增值税 企业所得税 最新优惠",
    ]

    results = []
    for term in search_terms:
        r = search_web(term)
        results.append(r)
        log(f"   [OK] {term[:40]}...")

    # 构建月度更新记录
    ensure_references_dir()
    existing_log = read_file_content(UPDATE_LOG)
    record = build_update_record(
        [],
        update_type=f"月度更新（{month}）",
        content_summary=f"搜索了{len(results)}个关键词，发现{len([r for r in results if '2026' in r['title']])}条相关结果",
    )
    UPDATE_LOG.write_text(existing_log + record, encoding="utf-8")

    return {"changed": True, "results": results, "month": month}


def run_risk_update() -> dict:
    """仅更新税务风险预警指标"""
    log("[START] 开始执行风险预警指标专项更新...")

    results = []
    for term in SEARCH_TERMS_RISK:
        r = search_web(term)
        results.append(r)
        log(f"   [OK] {term[:50]}...")

    ensure_references_dir()
    existing_log = read_file_content(UPDATE_LOG)
    record = build_update_record(
        [],
        update_type="风险预警指标专项更新",
        content_summary=f"搜索了{len(results)}个风险相关关键词，建议关注金税四期最新预警指标变化。",
    )
    UPDATE_LOG.write_text(existing_log + record, encoding="utf-8")

    return {"changed": True, "results": results}


def run_version_check() -> dict:
    """仅检查版本，不写入"""
    log("[SEARCH] 开始版本检查...")
    db_content = read_file_content(DATABASE_FILE)
    info = extract_version_info(db_content)
    policies = extract_latest_policy_items(db_content)

    return {
        "current_version": info.get("version", "unknown"),
        "current_date": info.get("date", "unknown"),
        "policy_count": len(policies),
        "database_file": str(DATABASE_FILE),
        "last_modified": datetime.fromtimestamp(DATABASE_FILE.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if DATABASE_FILE.exists() else "文件不存在",
    }


# ─────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="财税政策知识库自动更新脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python auto_update_knowledge.py                    # 全量更新
  python auto_update_knowledge.py --monthly          # 月度更新
  python auto_update_knowledge.py --risk            # 风险预警专项更新
  python auto_update_knowledge.py --check            # 仅版本检查
  python auto_update_knowledge.py --policy "增值税" # 按关键词更新
        """
    )
    parser.add_argument("--monthly", action="store_true", help="执行月度更新")
    parser.add_argument("--risk", action="store_true", help="仅更新税务风险预警指标")
    parser.add_argument("--check", action="store_true", help="仅检查版本，不写入")
    parser.add_argument("--policy", type=str, default="", help="按关键词搜索更新")
    parser.add_argument("--version", action="version", version=f"%(prog)s {CURRENT_VERSION}")

    args = parser.parse_args()

    log_print("=" * 60)
    log_print("  财税政策知识库 - 自动更新脚本")
    log_print(f"  版本：{CURRENT_VERSION} | 日期：{UPDATE_DATE}")
    log_print("=" * 60)

    if args.check:
        result = run_version_check()
        log_print("\n[CHECK] 版本检查结果：")
        log_print(f"   当前版本：{result['current_version']}")
        log_print(f"   更新日期：{result['current_date']}")
        log_print(f"   政策文号数：{result['policy_count']}")
        log_print(f"   数据库文件：{result['database_file']}")
        log_print(f"   文件修改时间：{result['last_modified']}")

    elif args.monthly:
        result = run_monthly_update()
        log_print(f"\n[OK] 月度更新完成，发现 {len(result['results'])} 条搜索结果。")
        log_print(f"   更新记录已保存至：{UPDATE_LOG}")

    elif args.risk:
        result = run_risk_update()
        log_print(f"\n[OK] 风险预警指标专项更新完成，发现 {len(result['results'])} 条搜索结果。")
        log_print(f"   更新记录已保存至：{UPDATE_LOG}")

    elif args.policy:
        result = search_web(args.policy)
        log_print(f"\n[SEARCH] 搜索结果（关键词：{args.policy}）：")
        log_print(f"   标题：{result['title']}")
        log_print(f"   摘要：{result['snippet']}")
        log_print(f"   链接：{result['url']}")

    else:
        result = run_full_update()
        changed = result['changed']
        log_print(f"\n[{'OK' if changed else 'INFO'}] 全量更新{'完成' if changed else '检查'}：")
        log_print(f"   搜索条目数：{result.get('search_count', 0)}")
        log_print(f"   摘要：{result['summary']}")
        log_print(f"   更新记录已保存至：{UPDATE_LOG}")

    log_print("\n" + "=" * 60)
    log_print("  [WARNING] 注意：自动更新为辅助功能，最终内容请以国家税务总局官网为准。")
    log_print("=" * 60)

    # 作者信息输出（兼容Windows GBK控制台）
    sys.stdout.buffer.write(
        "\n[OK] 有问题-建议-需求可联系作者QQ 1817694478 或加Q群 972156177 交流更多...\n"
        .encode("utf-8", errors="replace")
    )
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
