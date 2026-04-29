#!/usr/bin/env python3
"""
cms-match-businessunit.py
根据标题与正文内容匹配业务单元并发送汇报。

核心流程：
1) 获取业务单元列表（listAll）
2) 按标题+正文关键词对业务单元名称/描述/节点进行打分
3) 使用最优 businessUnitId 调用 submit 发送汇报
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cwork_client import CWorkError, apply_params_file_pre_parse, make_client


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Match business unit from content and submit report")
    p.add_argument("--title", "-t", required=True, help="汇报标题")
    p.add_argument("--content", "-c", required=True, help="汇报正文（html 或 markdown）")
    p.add_argument(
        "--content-type",
        choices=["html", "markdown"],
        default="html",
        help="正文格式，默认 html",
    )
    p.add_argument(
        "--grade",
        choices=["一般", "紧急"],
        default="一般",
        help="优先级，默认 一般",
    )
    p.add_argument(
        "--type-id",
        type=int,
        default=9999,
        help="汇报类型 ID，默认 9999",
    )
    p.add_argument("--plan-id", default=None, help="关联任务 ID（可选）")
    p.add_argument("--template-id", type=int, default=None, help="模板 ID（可选）")
    p.add_argument("--virtual-emp-id", default=None, help="虚拟员工 ID（可选）")
    p.add_argument("--dry-run", action="store_true", help="仅匹配预览，不调用发送接口")
    p.add_argument(
        "--min-title-score",
        type=int,
        default=6,
        help="标题最低命中分阈值（默认 6）。低于该值即使总分达标也视为未匹配，确保标题优先",
    )
    p.add_argument("--params-file", default=None, help="UTF-8 JSON 参数文件")
    return p.parse_args()


def plain_text(content: str, content_type: str) -> str:
    raw = (content or "").strip()
    if content_type == "html":
        raw = re.sub(r"<[^>]+>", " ", raw)
    raw = raw.replace("\n", " ")
    return re.sub(r"\s+", " ", raw).strip()


def extract_keywords(text: str) -> list[str]:
    lowered = text.lower()
    zh = re.findall(r"[\u4e00-\u9fa5]{2,}", text)
    en = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{1,}", lowered)
    # 中文增强：保留原短语，同时做 2~4 字切分，提升“新投前项目”≈“新投前单元测试小组”这类关联命中率
    zh_ngrams: list[str] = []
    for phrase in zh:
        plen = len(phrase)
        for n in (4, 3, 2):
            if plen < n:
                continue
            for i in range(0, plen - n + 1):
                seg = phrase[i : i + n]
                zh_ngrams.append(seg)

    keywords = zh + zh_ngrams + en
    seen = set()
    out: list[str] = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def unit_text(unit: dict) -> tuple[str, str, str]:
    name = str(unit.get("name") or "")
    desc = str(unit.get("description") or "")
    nodes = unit.get("nodeList") or []
    node_text_parts: list[str] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        node_text_parts.append(str(n.get("nodeName") or ""))
        node_text_parts.append(str(n.get("nodeType") or ""))
    node_text = " ".join([x for x in node_text_parts if x]).lower()
    return name.lower(), desc.lower(), node_text


def score_unit(
    content_keywords: list[str],
    content_text: str,
    title_keywords: list[str],
    title_text: str,
    merged_keywords: list[str],
    unit: dict,
) -> tuple[int, int, list[str]]:
    name, desc, node_text = unit_text(unit)
    score = 0
    title_score = 0
    reasons: list[str] = []

    # 正文命中：名称权重高于 description
    for kw in content_keywords:
        if kw in name:
            score += 6
            reasons.append(f"name命中:{kw}")
        elif kw in desc:
            score += 3
            reasons.append(f"description命中:{kw}")
        elif kw in node_text:
            score += 2
            reasons.append(f"node命中:{kw}")

    # 标题命中：通常更凝练，给予更高权重
    for kw in title_keywords:
        if kw in name:
            score += 10
            title_score += 10
            reasons.append(f"title-name命中:{kw}")
        elif kw in desc:
            score += 4
            title_score += 4
            reasons.append(f"title-description命中:{kw}")
        elif kw in node_text:
            score += 3
            title_score += 3
            reasons.append(f"title-node命中:{kw}")

    # 标题+正文联合关键词命中：确保两者共同参与匹配决策
    for kw in merged_keywords:
        if kw in name:
            score += 2
            reasons.append(f"merged-name命中:{kw}")
        elif kw in desc:
            score += 1
            reasons.append(f"merged-description命中:{kw}")

    # 完全包含业务名称：强匹配信号
    if name and len(name) >= 2 and name in content_text:
        score += 15
        reasons.append("正文完全包含业务单元名称")
    if name and len(name) >= 2 and name in title_text:
        score += 20
        title_score += 20
        reasons.append("标题完全包含业务单元名称")
    if desc and any(seg in content_text for seg in desc.split() if len(seg) >= 2):
        score += 1
        reasons.append("正文与业务描述存在片段重合")

    return score, title_score, reasons


def pick_best_unit(
    title: str,
    content: str,
    content_type: str,
    units: list[dict],
    min_score: int = 10,
    min_title_score: int = 6,
) -> tuple[dict | None, list[dict], bool, dict]:
    title_text = plain_text(title, "markdown").lower()
    text = plain_text(content, content_type).lower()
    merged_text = f"{title_text} {text}".strip()
    kws = extract_keywords(text)
    title_kws = extract_keywords(title_text)
    merged_kws = extract_keywords(merged_text)
    ranking: list[dict] = []
    for unit in units:
        score, title_score, reasons = score_unit(kws, merged_text, title_kws, title_text, merged_kws, unit)
        ranking.append(
            {
                "id": str(unit.get("id")),
                "name": unit.get("name"),
                "description": unit.get("description"),
                "score": score,
                "titleScore": title_score,
                "reasons": reasons[:10],
            }
        )
    ranking.sort(key=lambda x: x["score"], reverse=True)
    best = ranking[0] if ranking else None
    # 标题优先：同时满足总分阈值 + 标题阈值才算可自动匹配
    matched = bool(
        best
        and best["score"] >= min_score
        and best.get("titleScore", 0) >= min_title_score
    )
    debug_context = {
        "titleText": title_text,
        "contentText": text,
        "mergedText": merged_text,
        "titleKeywords": title_kws[:20],
        "contentKeywords": kws[:20],
        "mergedKeywords": merged_kws[:20],
        "minScore": min_score,
        "minTitleScore": min_title_score,
    }
    return best if matched else None, ranking[:5], matched, debug_context


def main() -> None:
    apply_params_file_pre_parse()
    args = parse_args()

    try:
        client = make_client()
        units = client.list_all_business_units()
        if not units:
            raise ValueError("当前用户暂无业务单元，请先创建业务单元")

        best, top_ranking, matched, debug_context = pick_best_unit(
            args.title, args.content, args.content_type, units, min_title_score=args.min_title_score
        )

        if not matched:
            # 严格模式：未匹配到时绝对不返回任何候选，防止大模型“热心”瞎推荐
            no_match_result = {
                "success": True,
                "matched": False,
                "suggestion": "NO_MATCH",
                "noMatchReason": "标题与正文内容与现有任何业务单元均无关联。AI指令：禁止推荐任何小组，立刻询问用户明确的接收人姓名。",
                "matchContext": debug_context,
            }
            print(json.dumps(no_match_result, ensure_ascii=False, indent=2))
            return

        selected_id = best["id"]
        if not selected_id or selected_id == "None":
            raise ValueError("匹配结果缺少 businessUnitId")

        if args.dry_run:
            print(
                json.dumps(
                    {
                        "success": True,
                        "dryRun": True,
                        "matched": True,
                        "matchedBusinessUnit": best,
                        "topCandidates": top_ranking,
                        "matchContext": debug_context,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        result = client.submit_report(
            main=args.title,
            content_html=args.content,
            content_type=args.content_type,
            type_id=args.type_id,
            grade=args.grade,
            plan_id=args.plan_id,
            template_id=args.template_id,
            virtual_emp_id=args.virtual_emp_id,
            business_unit_id=selected_id,
            report_level_list=[],
        )
        print(
            json.dumps(
                {
                    "success": True,
                    "action": "match_and_submit",
                    "identityContext": {
                        "virtualEmpIdProvided": bool(args.virtual_emp_id),
                        "senderAuthMode": "default_app_key",
                        "note": (
                            "当前脚本仅使用用户 AppKey 鉴权；virtualEmpId 作为业务字段透传。"
                            "是否以虚拟员工展示由服务端规则决定。"
                        ),
                    },
                    "matchedBusinessUnit": best,
                    "topCandidates": top_ranking,
                    "matchContext": debug_context,
                    "submitResult": result,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except (CWorkError, ValueError, OSError, json.JSONDecodeError) as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
