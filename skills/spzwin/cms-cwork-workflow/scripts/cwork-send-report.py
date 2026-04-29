#!/usr/bin/env python3
"""
cwork-send-report.py
发送汇报：解析接收人 → 全量保存/更新草稿（5.23）→ 输出完整草稿详情（5.25）供用户确认
→ 仅在 --confirm-send 后调用 5.27 将草稿转为正式汇报。

更新草稿前会先拉取详情，与本次参数合并后整包提交，避免全量覆盖导致字段丢失。

Usage:
  # 1) 仅存草稿 + 输出完整预览（默认，不发送）
  python3 scripts/cwork-send-report.py --title "..." --content "<p>...</p>" --receivers "张三"

  # Markdown 正文（须指定 --content-type markdown）
  python3 scripts/cwork-send-report.py --title "..." --content-type markdown --content "## 标题\n正文" --receivers "张三"

  # 2) 用户确认后，仅凭汇报 id 发出（5.27）
  python3 scripts/cwork-send-report.py --draft-id <汇报id> --confirm-send

Auth:
  --app-key (required, injected by cms-auth-skills)
"""

from __future__ import annotations

import sys
import json
import copy
import re
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cwork_client import (
    make_client,
    CWorkError,
    apply_params_file_pre_parse,
    flatten_emp_search_bucket,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Send a CWork report (draft-first, 5.27 to publish)")
    p.add_argument("--title", "-t", default=None, help="汇报标题（发送-only 模式可不填）")
    p.add_argument(
        "--content",
        "-c",
        default=None,
        help=(
            "汇报正文（与 Skill / params 键 content 一致）。"
            "格式由 --content-type 指定（html / markdown）；发送-only 可不填。"
        ),
    )
    p.add_argument(
        "--content-html",
        dest="content_html",
        default=None,
        help="[兼容] 与 --content 相同，勿与 --content 同时指定",
    )
    p.add_argument(
        "--content-type",
        dest="body_content_type",
        choices=["html", "markdown"],
        default=None,
        help=(
            "正文格式 html 或 markdown。新建未指定时默认 html；"
            "带 --draft-id 更新且未指定时沿用当前草稿详情中的格式。"
        ),
    )
    p.add_argument(
        "--receivers", "-r", default="",
        help="Comma-separated receiver names (will be resolved to empId)",
    )
    p.add_argument(
        "--cc", dest="cc_names", default="",
        help="Comma-separated CC recipient names",
    )
    p.add_argument(
        "--grade", "-g", default="一般",
        choices=["一般", "紧急"],
        help="Report urgency",
    )
    p.add_argument(
        "--type-id", dest="type_id", type=int, default=9999,
        help="Report type ID (default 9999)",
    )
    p.add_argument(
        "--file-paths", nargs="*", dest="file_paths", default=[],
        help="Local file paths to attach (up to 10)",
    )
    p.add_argument(
        "--file-names", nargs="*", dest="file_names", default=[],
        help="File names for attachments (same order as --file-paths)",
    )
    p.add_argument(
        "--plan-id", dest="plan_id", default=None,
        help="Linked plan/task ID",
    )
    p.add_argument(
        "--business-unit-id",
        dest="business_unit_id",
        default=None,
        help="业务单元 ID。传入后发汇报按业务单元预设节点流转",
    )
    p.add_argument(
        "--virtual-emp-id",
        dest="virtual_emp_id",
        default=None,
        help="虚拟员工 ID。传入后由虚拟人代发",
    )
    p.add_argument(
        "--preview-only", dest="preview_only", action="store_true",
        help="仅保存草稿并输出完整预览（与默认不发送行为一致，便于显式调用）",
    )
    p.add_argument(
        "--draft-id", dest="draft_id", default=None,
        help="汇报 id：更新已有草稿；与 --confirm-send 单独使用时仅执行 5.27 发出",
    )
    p.add_argument(
        "--confirm-save-draft",
        dest="confirm_save_draft",
        action="store_true",
        help="显式确认允许保存/更新草稿（安全护栏：未确认不执行 5.23）",
    )
    p.add_argument(
        "--confirm-send", dest="confirm_send", action="store_true",
        help="用户已预览完整草稿并同意发出后，再指定此参数才会调用 5.27",
    )
    p.add_argument(
        "--test-mode",
        dest="test_mode",
        action="store_true",
        help="测试/调试模式：默认仅允许接收人为当前用户本人",
    )
    p.add_argument(
        "--current-user-name",
        dest="current_user_name",
        default=None,
        help="当前发起用户姓名（test-mode 下用于默认接收人及校验）",
    )
    p.add_argument(
        "--allow-external-test-receivers",
        dest="allow_external_test_receivers",
        action="store_true",
        help="test-mode 下允许接收人为非当前用户（高风险，需显式开启）",
    )
    p.add_argument(
        "--report-level-json", dest="report_level_json", default=None,
        help="UTF-8 JSON 文件路径，内容为 reportLevelList 数组（覆盖详情中的流程节点）",
    )
    p.add_argument(
        "--params-file", dest="params_file", default=None,
        help="UTF-8 JSON 文件路径，从文件读取参数（用于 Windows 下传递中文内容）",
    )
    p.add_argument(
        "--allow-minimal-body",
        dest="allow_minimal_body",
        action="store_true",
        help="允许正文过短（默认纯文本长度 ≤10 会拒绝保存草稿；超过 10 字不拦截）",
    )
    p.add_argument(
        "--fail-on-literal-newlines",
        dest="fail_on_literal_newlines",
        action="store_true",
        help=(
            "在自动修正前检测：正文若含字面量 \\\\n / \\\\r\\\\n 则直接失败退出（供 CI/自动化）。"
            "终端用户无需使用此参数。"
        ),
    )
    return p.parse_args()


def merge_report_content_args(args) -> None:
    """--content 与 --content-html 二选一，合并到 args.content。"""
    if args.content is not None and args.content_html is not None:
        print(json.dumps({
            "success": False,
            "error": "请勿同时指定 --content 与 --content-html",
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    if args.content is None:
        args.content = args.content_html


def normalize_markdown_escaped_newlines(content: str | None, content_type: str | None) -> str | None:
    """兼容 AI/CLI 传入的字面量转义（如 '\\n'），还原为真实换行。

    仅在 markdown 场景处理，避免影响 html 正文中本就合法的反斜杠字符。
    """
    if content is None:
        return None
    if (content_type or "").lower() != "markdown":
        return content
    if "\\" not in content:
        return content
    normalized = content.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    return normalized


def body_has_literal_escaped_newlines(content: str | None, content_type: str | None) -> bool:
    """检测正文是否含应被自动修正的字面量换行转义。"""
    if content is None:
        return False
    if (content_type or "").lower() != "markdown":
        return False
    return ("\\n" in content) or ("\\r\\n" in content)


# ---------------------------------------------------------------------------
# Resolve / validate names
# ---------------------------------------------------------------------------

# 纯文本长度 ≤ 此值则拒绝保存；须 **严格大于** 该值（即至少 11 字）才放行（与 Issue #37 约定一致）
SHORT_BODY_REJECT_IF_LEN_LE = 10


def split_cli_name_list(s: str) -> list[str]:
    """按英文逗号、中文逗号、顿号、分号拆分姓名列表（修复仅用「，」导致整串当一人）。"""
    s = (s or "").strip()
    if not s:
        return []
    parts = re.split(r"[,，、;；]", s)
    return [p.strip() for p in parts if p.strip()]


def body_plain_length(content: str | None, content_type: str) -> int:
    """与预览一致的「纯文本长度」近似：html 去标签；markdown 按原文字符数。"""
    if content is None:
        return 0
    raw = content.strip()
    if not raw:
        return 0
    ct = (content_type or "html").lower()
    if ct == "markdown":
        return len(raw)
    plain = re.sub(r"<[^>]+>", "", raw)
    return len(plain.strip())


def effective_body_content_type(args, detail: dict | None) -> str:
    if args.body_content_type is not None:
        return args.body_content_type
    if detail:
        raw_ct = detail.get("contentType")
        if isinstance(raw_ct, str) and raw_ct.lower() in ("html", "markdown"):
            return raw_ct.lower()
    return "html"


def _body_has_literal_escaped_newlines(content: str | None) -> bool:
    """检测正文是否含 JSON/Agent 常见的「字面量 \\n」序列（反斜杠 + n），而非真实换行。"""
    text = content or ""
    return ("\\n" in text) or ("\\r\\n" in text) or ("\\r" in text)


def normalize_literal_escaped_newlines(content: str | None) -> str:
    """将字面量 \\n / \\r\\n / \\r 转为真实换行（静默；不区分 html/markdown）。

    典型来源：params 被二次转义、或非 json.dump 手写 JSON。对真实换行无影响。
    """
    if not content:
        return content or ""
    if "\\" not in content:
        return content
    s = content.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    return s


def resolve_receivers(client, names: list[str]) -> dict:
    results = {}
    for name in names:
        if not name.strip():
            continue
        try:
            data = client.search_emp_by_name(name.strip())
        except CWorkError as e:
            results[name] = {"status": "error", "message": str(e)}
            continue

        inside = flatten_emp_search_bucket(data.get("inside"))

        if inside:
            candidates = inside
        else:
            candidates = flatten_emp_search_bucket(data.get("outside"))

        if len(candidates) == 0:
            results[name] = {"status": "not_found"}
        elif len(candidates) == 1:
            emp = candidates[0]
            results[name] = {
                "status": "found",
                "empId": emp["id"],
                "name": emp["name"],
                "title": emp.get("title", ""),
                "dept": emp.get("mainDept", ""),
            }
        else:
            results[name] = {
                "status": "multiple",
                "employees": [
                    {"empId": e["id"], "name": e["name"],
                     "title": e.get("title", ""), "dept": e.get("mainDept", "")}
                    for e in candidates
                ],
            }
    return results


def validate_receivers(resolved: dict) -> tuple[list[dict], list[dict]]:
    confirmed = []
    errors = []
    for name, info in resolved.items():
        if info["status"] == "not_found":
            errors.append({"name": name, "reason": "not_found"})
        elif info["status"] == "multiple":
            errors.append({
                "name": name,
                "reason": "multiple_matches",
                "candidates": [
                    {"empId": e["empId"], "name": e["name"],
                     "title": e.get("title", ""), "dept": e.get("dept", "")}
                    for e in info["employees"]
                ],
            })
        elif info["status"] == "found":
            confirmed.append({"empId": info["empId"], "name": info["name"]})
    return confirmed, errors


# ---------------------------------------------------------------------------
# Draft detail → saveOrUpdate 全量字段
# ---------------------------------------------------------------------------

def _emp_ids_from_detail(emp_list: list | None) -> list[str]:
    if not emp_list:
        return []
    out: list[str] = []
    for e in emp_list:
        if isinstance(e, dict) and e.get("id") is not None:
            out.append(str(e["id"]))
    return out


def _file_vos_from_detail(file_list: list | None) -> list[dict]:
    if not file_list:
        return []
    out: list[dict] = []
    for f in file_list:
        if not isinstance(f, dict):
            continue
        fid = f.get("fileId")
        if not fid:
            continue
        out.append({
            "fileId": str(fid),
            "name": f.get("name") or "",
            "type": f.get("type") or "file",
        })
    return out


def _report_level_param_from_detail(nodes: list | None) -> list[dict] | None:
    if not nodes:
        return None
    result: list[dict] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        emp_list = node.get("empList") or []
        level_users = []
        for e in emp_list:
            if not isinstance(e, dict):
                continue
            eid = e.get("empId", e.get("id"))
            if eid is not None:
                level_users.append({"empId": eid})
        entry = {
            "type": node.get("type"),
            "level": node.get("level"),
            "nodeCode": node.get("nodeCode"),
            "nodeName": node.get("nodeName"),
            "levelUserList": level_users,
            "groupIdList": node.get("groupIdList"),
            "requirement": node.get("requirement"),
        }
        result.append({k: v for k, v in entry.items() if v is not None})
    return result or None


def _receiver_node_index_for_cli_sync(nodes: list[dict]) -> int:
    """选择应将 ``--receivers`` 写入 ``levelUserList`` 的节点（与 5.1/5.23 一致：接收人以 reportLevelList 为准）。"""
    for i, n in enumerate(nodes):
        if isinstance(n, dict) and isinstance(n.get("type"), str) and n["type"].lower() == "read":
            return i
    for i, n in enumerate(nodes):
        if isinstance(n, dict) and n.get("levelUserList"):
            return i
    return 0


def _apply_cli_receivers_to_report_level_list(
    report_level_list: list[dict],
    accept_emp_ids: list[str],
) -> list[dict]:
    """用本次 CLI 解析出的接收人覆盖目标节点 ``levelUserList``，避免仅更新 acceptEmpIdList 时详情仍显示旧人。"""
    if not report_level_list or not accept_emp_ids:
        return report_level_list
    out = copy.deepcopy(report_level_list)
    idx = _receiver_node_index_for_cli_sync(out)
    if idx < 0 or idx >= len(out):
        return report_level_list
    level_users: list[dict] = []
    for eid in accept_emp_ids:
        try:
            level_users.append({"empId": int(str(eid))})
        except (TypeError, ValueError):
            level_users.append({"empId": eid})
    node = dict(out[idx])
    node["levelUserList"] = level_users
    node.pop("groupIdList", None)
    out[idx] = {k: v for k, v in node.items() if v is not None}
    return out


def load_report_level_json(path: str) -> list[dict]:
    raw = Path(path).read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("report-level-json 根节点须为 JSON 数组")
    return data


def _validate_report_level_list_nodes(report_level_list: list[dict] | None) -> dict | None:
    """校验节点至少包含人员/分组/部门其一，返回首个错误信息。"""
    if not isinstance(report_level_list, list):
        return None
    for idx, node in enumerate(report_level_list, start=1):
        if not isinstance(node, dict):
            continue
        users = node.get("levelUserList")
        groups = node.get("groupIdList")
        # 后端字段在不同环境可能命名不同，统一兼容常见部门字段。
        depts = (
            node.get("deptIdList")
            or node.get("departmentIdList")
            or node.get("deptIds")
            or node.get("departmentIds")
        )
        if users or groups or depts:
            continue
        node_name = str(node.get("nodeName") or f"节点{idx}")
        return {
            "index": idx,
            "nodeName": node_name,
            "message": (
                f"{node_name}缺少审批对象：请至少补充人员(levelUserList)、分组(groupIdList)或部门"
                "（deptIdList/departmentIdList）其一；若暂不需要该节点，请删除该节点后重试。"
            ),
        }
    return None


# ---------------------------------------------------------------------------
# Upload files
# ---------------------------------------------------------------------------

def upload_files(client, file_paths: list[str], file_names: list[str]) -> list[dict]:
    if not file_paths:
        return []
    file_vos = []
    for i, path in enumerate(file_paths):
        fname = file_names[i] if i < len(file_names) else Path(path).name
        try:
            result = client.upload_file(path)
            file_id = result.get("fileId", "")
            file_vos.append({
                "fileId": str(file_id) if file_id is not None else "",
                "name": fname,
                "type": "file",
            })
        except CWorkError as e:
            print(json.dumps({
                "step": "upload",
                "file": fname,
                "error": str(e),
            }, ensure_ascii=False), file=sys.stderr)
    return file_vos


# ---------------------------------------------------------------------------
# Merge + save draft (5.23 全量)
# ---------------------------------------------------------------------------

def build_save_draft_kwargs(
    args,
    *,
    detail: dict | None,
    accept_emp_ids: list[str],
    cc_emp_ids: list[str],
    file_vos: list[dict],
    receiver_names_nonempty: bool,
    cc_names_nonempty: bool,
    new_uploads: bool,
) -> dict:
    """构造 save_draft 的完整参数，避免更新时省略字段导致服务端清空。"""
    if args.report_level_json:
        report_level_list = load_report_level_json(args.report_level_json)
    elif detail is not None:
        rll = detail.get("reportLevelList")
        if rll:
            converted = _report_level_param_from_detail(rll)
            report_level_list = converted if converted is not None else []
        else:
            report_level_list = []
    else:
        report_level_list = None

    if detail:
        if receiver_names_nonempty:
            final_accept = accept_emp_ids
        else:
            final_accept = _emp_ids_from_detail(detail.get("acceptEmployeeList"))
        if cc_names_nonempty:
            final_cc = cc_emp_ids
        else:
            final_cc = _emp_ids_from_detail(detail.get("copyEmployeeList"))
        if new_uploads:
            final_files = file_vos
        else:
            final_files = _file_vos_from_detail(detail.get("fileList"))
        privacy_level = detail.get("privacyLevel") or "非涉密"
        template_raw = detail.get("templateId")
        template_id = str(template_raw) if template_raw is not None else None
        plan_raw = args.plan_id if args.plan_id is not None else detail.get("planId")
        plan_id = str(plan_raw) if plan_raw is not None else None
        # 接口约定：传 businessUnitId 时会忽略 reportLevelList。
        # 因此当用户显式提供 --report-level-json 时，不应再继承草稿中的 businessUnitId，
        # 否则会出现“流程节点设置成功但服务端不生效”的假象。
        if args.business_unit_id is not None:
            business_unit_raw = args.business_unit_id
        elif args.report_level_json:
            business_unit_raw = None
        else:
            business_unit_raw = detail.get("businessUnitId")
        business_unit_id = str(business_unit_raw) if business_unit_raw is not None else None
        virtual_emp_raw = (
            args.virtual_emp_id
            if args.virtual_emp_id is not None
            else detail.get("virtualEmpId")
        )
        virtual_emp_id = str(virtual_emp_raw) if virtual_emp_raw is not None else None
        if args.body_content_type is not None:
            content_type = args.body_content_type
        else:
            raw_ct = detail.get("contentType")
            if isinstance(raw_ct, str) and raw_ct.lower() in ("html", "markdown"):
                content_type = raw_ct.lower()
            else:
                content_type = "html"
    else:
        final_accept = accept_emp_ids
        final_cc = cc_emp_ids
        final_files = file_vos
        privacy_level = "非涉密"
        template_id = None
        plan_id = str(args.plan_id) if args.plan_id is not None else None
        business_unit_id = str(args.business_unit_id) if args.business_unit_id is not None else None
        virtual_emp_id = str(args.virtual_emp_id) if args.virtual_emp_id is not None else None
        content_type = args.body_content_type if args.body_content_type is not None else "html"

    # 5.1/5.23：接收人以 reportLevelList 为准；acceptEmpIdList 仅在 reportLevelList 为空时兜底。
    # 更新草稿且用户显式传 --receivers 时，必须把新人写入 reportLevelList，否则详情仍显示旧 empList。
    if (
        receiver_names_nonempty
        and not args.report_level_json
        and isinstance(report_level_list, list)
        and len(report_level_list) > 0
    ):
        report_level_list = _apply_cli_receivers_to_report_level_list(
            report_level_list, final_accept
        )

    return {
        "main": args.title,
        "content_html": args.content,
        "content_type": content_type,
        "type_id": args.type_id,
        "grade": args.grade,
        "privacy_level": privacy_level,
        "plan_id": plan_id,
        "business_unit_id": business_unit_id,
        "template_id": template_id,
        "accept_emp_id_list": final_accept,
        "copy_emp_id_list": final_cc,
        "report_level_list": report_level_list,
        "file_vo_list": final_files,
        "virtual_emp_id": virtual_emp_id,
        "draft_id": args.draft_id,
    }


def save_draft_full(client, kwargs: dict) -> str | None:
    draft_id = kwargs.pop("draft_id", None)
    try:
        result = client.save_draft(draft_id=draft_id, **kwargs)
        if isinstance(result, str):
            return result if result else None
        rid = result.get("id")
        return str(rid) if rid is not None else None
    except CWorkError as e:
        print(json.dumps({"step": "save_draft", "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Preview output（完整草稿，来自 5.25）
# ---------------------------------------------------------------------------

def build_preview_shell(args, confirmed: list[dict], cc_confirmed: list[dict],
                        file_vos: list[dict], *, from_api_detail: dict) -> dict:
    import re
    html = from_api_detail.get("contentHtml") or ""
    plain = re.sub(r"<[^>]+>", "", html)
    plain_stripped = plain.strip()
    plain_len = len(plain_stripped)

    # summary.contentPreview：极短正文不截断，避免占位符被「摘要」误伤；仅超长纯文本才截断
    preview_cap = 4000
    if len(plain) <= preview_cap:
        content_preview = plain
    else:
        content_preview = plain[:preview_cap] + "…"

    # confirmPrompt 内嵌正文：预览用纯文本，避免重复塞入整段 HTML/Markdown
    prompt_body_cap = 2000
    prompt_plain = plain if len(plain) <= prompt_body_cap else plain[:prompt_body_cap] + "…"

    preview_warnings: list[str] = []
    if plain_len <= 30:
        preview_warnings.append(
            f"summary 中的正文预览仅 {plain_len} 个字符（由草稿正文简化得到，"
            "一般应与本次 --content 长度接近），可能过短，发送前请与用户确认"
        )

    accept_names = [e["name"] for e in confirmed]
    cc_names = [e["name"] for e in cc_confirmed]

    summary: dict = {
        "title": from_api_detail.get("main"),
        "grade": from_api_detail.get("grade"),
        "typeId": from_api_detail.get("typeId"),
        "planId": from_api_detail.get("planId"),
        "virtualEmpId": from_api_detail.get("virtualEmpId"),
        "contentType": from_api_detail.get("contentType"),
        "receiversResolved": accept_names,
        "ccResolved": cc_names,
        "attachmentsThisRun": [{"name": f["name"]} for f in file_vos],
        "contentPlainText": plain,
        "contentPreview": content_preview,
        "contentPlainLength": plain_len,
    }
    if preview_warnings:
        summary["previewWarnings"] = preview_warnings

    warn_prefix = ("⚠ " + preview_warnings[0] + "\n\n") if preview_warnings else ""
    confirm_prompt = (
        warn_prefix
        + "【请用户确认以下完整草稿后再发送】\n"
        f"标题：{from_api_detail.get('main')}\n"
        f"优先级：{from_api_detail.get('grade')}\n"
        "正文（以下为预览；定稿请以 draftDetail 为准，其中正文与本次 --content 对应）：\n"
        f"{prompt_plain}\n"
        f"接收人（解析结果）：{', '.join(accept_names) or '（沿用草稿详情）'}\n"
        f"抄送：{', '.join(cc_names) or '（沿用草稿详情）'}\n"
        f"附件：{json.dumps(from_api_detail.get('fileList') or [], ensure_ascii=False)}\n"
        f"流程节点 reportLevelList：{json.dumps(from_api_detail.get('reportLevelList') or [], ensure_ascii=False)}\n"
        "\n用户同意后，执行：--draft-id <汇报id> --confirm-send"
    )

    return {
        "reportId": from_api_detail.get("id"),
        "note": (
            "以下为完整草稿 draftDetail（含接口原始字段）。请向用户展示全文："
            "正文即本次 --content 保存后的结果；确认后再执行 --draft-id <汇报id> --confirm-send。"
        ),
        "draftDetail": from_api_detail,
        "summary": summary,
        "confirmPrompt": confirm_prompt,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    apply_params_file_pre_parse()
    args = parse_args()
    merge_report_content_args(args)
    if args.fail_on_literal_newlines and body_has_literal_escaped_newlines(
        args.content, args.body_content_type
    ):
        print(json.dumps({
            "success": False,
            "step": "validate_content_newline",
            "error": (
                "正文含字面量换行转义序列；已按 --fail-on-literal-newlines 拒绝保存。"
            ),
            "contentTypeUsed": args.body_content_type or "html",
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    # Markdown 兼容：将字面量 \n/\t 还原，避免页面按普通字符展示导致不换行
    args.content = normalize_markdown_escaped_newlines(args.content, args.body_content_type)

    # 安全护栏：--confirm-send 必须搭配 --draft-id（强制两步流程）
    if args.confirm_send and not args.draft_id:
        print(json.dumps({
            "success": False,
            "error": (
                "【安全拦截】--confirm-send 必须搭配 --draft-id 使用。"
                "请先不带 --confirm-send 调用一次以保存草稿并获取 reportId，"
                "向用户展示完整预览，待用户明确确认后，"
                "再执行 --draft-id <reportId> --confirm-send。"
                "禁止跳过预览直接发送。"
            ),
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    send_only = bool(args.confirm_send and args.draft_id and not args.preview_only)

    if send_only:
        if args.title is not None or args.content is not None:
            print(json.dumps({
                "success": False,
                "error": (
                    "发送-only 模式请勿再传 --title/--content；"
                    "仅需 --draft-id 与 --confirm-send（可选 --virtual-emp-id 用于发送前覆盖虚拟人）"
                ),
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
    else:
        if not args.confirm_save_draft:
            print(json.dumps({
                "success": False,
                "error": (
                    "【安全拦截】保存/更新草稿前必须显式确认。"
                    "请先征得用户同意后重试，并添加 --confirm-save-draft。"
                ),
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        if not args.title or args.content is None:
            print(json.dumps({
                "success": False,
                "error": "保存草稿需要 --title 与 --content（或仅 --draft-id + --confirm-send）；可用 --content-html 代替 --content",
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    client = make_client()

    if send_only:
        try:
            detail = client.get_draft_detail(args.draft_id)
        except CWorkError as e:
            print(json.dumps({
                "success": False,
                "step": "get_draft_detail",
                "error": str(e),
                "reportId": args.draft_id,
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

        effective_virtual_emp_id = (
            str(args.virtual_emp_id)
            if args.virtual_emp_id is not None
            else (
                str(detail.get("virtualEmpId"))
                if detail.get("virtualEmpId") is not None
                else None
            )
        )

        # 虚拟人提交场景：改走 5.1 submit(id=草稿id) 以确保 virtualEmpId 在最终发出时参与判定。
        if effective_virtual_emp_id is not None:
            main = detail.get("main")
            content_html = detail.get("contentHtml")
            if not main or content_html is None:
                print(json.dumps({
                    "success": False,
                    "step": "submit_report_5_1",
                    "error": "草稿详情缺少 main 或 contentHtml，无法提交",
                    "reportId": args.draft_id,
                }, ensure_ascii=False), file=sys.stderr)
                sys.exit(1)

            report_level_list = _report_level_param_from_detail(detail.get("reportLevelList")) or []
            node_validation_error = _validate_report_level_list_nodes(report_level_list)
            if node_validation_error:
                print(json.dumps({
                    "success": False,
                    "step": "validate_report_level_list",
                    "error": node_validation_error["message"],
                    "nodeIndex": node_validation_error["index"],
                    "nodeName": node_validation_error["nodeName"],
                }, ensure_ascii=False, indent=2), file=sys.stderr)
                sys.exit(1)

            try:
                result = client.submit_report(
                    main=main,
                    content_html=content_html,
                    report_id=args.draft_id,
                    business_unit_id=detail.get("businessUnitId"),
                    content_type=effective_body_content_type(args, detail),
                    type_id=int(detail.get("typeId") or 9999),
                    grade=detail.get("grade") or "一般",
                    privacy_level=detail.get("privacyLevel") or "非涉密",
                    plan_id=str(detail.get("planId")) if detail.get("planId") is not None else None,
                    template_id=detail.get("templateId"),
                    accept_emp_id_list=_emp_ids_from_detail(detail.get("acceptEmployeeList")),
                    copy_emp_id_list=_emp_ids_from_detail(detail.get("copyEmployeeList")),
                    report_level_list=report_level_list,
                    file_vo_list=_file_vos_from_detail(detail.get("fileList")),
                    virtual_emp_id=effective_virtual_emp_id,
                )
                report_id = result.get("id") if isinstance(result, dict) else None
                print(json.dumps({
                    "success": True,
                    "reportId": str(report_id) if report_id is not None else str(args.draft_id),
                    "submitted": True,
                    "virtualEmpId": effective_virtual_emp_id,
                    "submitApi": "report_record_submit_5_1",
                    "message": "已通过 5.1 提交草稿并按 virtualEmpId 发出",
                }, ensure_ascii=False, indent=2))
                sys.exit(0)
            except CWorkError as e:
                print(json.dumps({
                    "success": False,
                    "step": "submit_report_5_1",
                    "error": str(e),
                    "reportId": args.draft_id,
                    "virtualEmpId": effective_virtual_emp_id,
                }, ensure_ascii=False), file=sys.stderr)
                sys.exit(1)

        try:
            ok = client.submit_draft(args.draft_id)
            print(json.dumps({
                "success": bool(ok),
                "reportId": args.draft_id,
                "submitted": bool(ok),
                "virtualEmpId": None,
                "submitApi": "draft_submit_5_27",
                "message": "已通过 5.27 将草稿转为正式汇报（无 virtualEmpId）" if ok else "5.27 返回未成功",
            }, ensure_ascii=False, indent=2))
            sys.exit(0 if ok else 1)
        except CWorkError as e:
            print(json.dumps({
                "success": False,
                "error": str(e),
                "reportId": args.draft_id,
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    detail: dict | None = None
    if args.draft_id:
        try:
            detail = client.get_draft_detail(args.draft_id)
        except CWorkError as e:
            print(json.dumps({
                "success": False,
                "step": "get_draft_detail",
                "error": str(e),
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    effective_ct = effective_body_content_type(args, detail)
    if args.fail_on_literal_newlines and _body_has_literal_escaped_newlines(args.content):
        print(json.dumps({
            "success": False,
            "step": "validate_content_newline",
            "error": "正文含字面量换行转义序列；已按 --fail-on-literal-newlines 拒绝保存。",
            "contentTypeUsed": effective_ct,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    args.content = normalize_literal_escaped_newlines(args.content)

    if not args.allow_minimal_body:
        plen = body_plain_length(args.content, effective_ct)
        if plen <= SHORT_BODY_REJECT_IF_LEN_LE:
            print(json.dumps({
                "success": False,
                "step": "validate_body",
                "error": (
                    f"正文过短（按 {effective_ct} 估算约 {plen} 字；须超过 {SHORT_BODY_REJECT_IF_LEN_LE} 字才保存。"
                    "请补充内容，或显式传入 --allow-minimal-body 跳过此校验。"
                ),
                "contentPlainLength": plen,
                "contentTypeUsed": effective_ct,
                "rejectIfPlainLengthLte": SHORT_BODY_REJECT_IF_LEN_LE,
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    receiver_names = split_cli_name_list(args.receivers)
    cc_names = split_cli_name_list(args.cc_names)
    if args.test_mode and not receiver_names and args.current_user_name:
        receiver_names = [args.current_user_name.strip()]
    if args.test_mode and not receiver_names:
        print(json.dumps({
            "success": False,
            "step": "validate_test_receivers",
            "error": (
                "test-mode 下必须指定接收人；建议传 --current-user-name 以默认发给本人，"
                "或显式设置 --receivers 为测试账号。"
            ),
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    if (
        args.test_mode
        and args.current_user_name
        and not args.allow_external_test_receivers
    ):
        me = args.current_user_name.strip()
        non_self = [n for n in receiver_names if n.strip() and n.strip() != me]
        if non_self:
            print(json.dumps({
                "success": False,
                "step": "validate_test_receivers",
                "error": (
                    "test-mode 默认仅允许发送给当前用户本人。"
                    "如确需外发，请显式添加 --allow-external-test-receivers 并先获用户确认。"
                ),
                "currentUserName": me,
                "externalReceivers": non_self,
            }, ensure_ascii=False, indent=2), file=sys.stderr)
            sys.exit(1)

    receiver_nonempty = bool(receiver_names)
    cc_nonempty = bool(cc_names)

    resolved = resolve_receivers(client, receiver_names)
    confirmed, errors = validate_receivers(resolved)
    cc_resolved = resolve_receivers(client, cc_names)
    cc_confirmed, cc_errors = validate_receivers(cc_resolved)

    all_errors = []
    if errors:
        all_errors.append({"field": "receivers", "errors": errors})
    if cc_errors:
        all_errors.append({"field": "cc", "errors": cc_errors})
    if all_errors:
        print(json.dumps({
            "success": False,
            "step": "validate_names",
            "message": "部分姓名未能唯一匹配，请确认后重试",
            "details": all_errors,
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    accept_emp_ids = [str(e["empId"]) for e in confirmed]
    cc_emp_ids = [str(e["empId"]) for e in cc_confirmed]

    file_vos = upload_files(client, args.file_paths, args.file_names)
    new_uploads = bool(args.file_paths)

    kwargs = build_save_draft_kwargs(
        args,
        detail=detail,
        accept_emp_ids=accept_emp_ids,
        cc_emp_ids=cc_emp_ids,
        file_vos=file_vos,
        receiver_names_nonempty=receiver_nonempty,
        cc_names_nonempty=cc_nonempty,
        new_uploads=new_uploads,
    )
    node_validation_error = _validate_report_level_list_nodes(kwargs.get("report_level_list"))
    if node_validation_error:
        print(json.dumps({
            "success": False,
            "step": "validate_report_level_list",
            "error": node_validation_error["message"],
            "nodeIndex": node_validation_error["index"],
            "nodeName": node_validation_error["nodeName"],
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    saved_report_id = save_draft_full(client, kwargs)

    if not saved_report_id:
        print(json.dumps({
            "success": False,
            "step": "save_draft",
            "message": "草稿保存失败",
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        fresh_detail = client.get_draft_detail(saved_report_id)
    except CWorkError as e:
        print(json.dumps({
            "success": False,
            "step": "get_draft_detail",
            "error": str(e),
            "reportId": saved_report_id,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    preview = build_preview_shell(
        args, confirmed, cc_confirmed, file_vos, from_api_detail=fresh_detail,
    )
    preview["success"] = True
    preview["identityContext"] = {
        "virtualEmpIdProvided": bool(args.virtual_emp_id),
        "senderAuthMode": "default_app_key",
        "note": (
            "当前脚本仅使用用户 AppKey 鉴权；virtualEmpId 作为业务字段透传。"
            "是否以虚拟员工展示由服务端规则决定。"
        ),
    }
    # draftId：历史 JSON 键名，值为汇报 id，与 reportId / draftDetail.id 相同（非草稿箱记录 id）
    preview["draftId"] = saved_report_id

    if not args.confirm_send or args.preview_only:
        preview["nextStep"] = (
            "用户已确认 draftDetail 全文（正文、附件、流程节点等）后，再执行："
            f"--draft-id {saved_report_id} --confirm-send"
        )
        if args.preview_only and args.confirm_send:
            preview["noteOnFlags"] = "已指定 --preview-only，不会发出；忽略 --confirm-send"
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return

    try:
        ok = client.submit_draft(saved_report_id)
    except CWorkError as e:
        print(json.dumps({
            "success": False,
            "step": "submit_draft_5_27",
            "error": str(e),
            "draftId": saved_report_id,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    if not ok:
        print(json.dumps({
            "success": False,
            "step": "submit_draft_5_27",
            "draftId": saved_report_id,
            "message": "5.27 返回未成功",
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(json.dumps({
        "success": True,
        "reportId": saved_report_id,
        "submitted": True,
        "receivers": accept_emp_ids,
        "cc": cc_emp_ids,
        "attachmentsThisRun": len(file_vos),
        "message": "已通过 5.27 将草稿转为正式汇报",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
