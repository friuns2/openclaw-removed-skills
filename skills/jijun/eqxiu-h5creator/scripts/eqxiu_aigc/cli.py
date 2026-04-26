"""命令行入口：argparse 与子命令分发。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .client import EqxiuAigcClient
from .config_store import check_auth_status, load_config, login_interactive, token_from_config
from .constants import (
    CONFIG_PATH,
    DEFAULT_BASE_URL,
    DEFAULT_COS_BUCKET,
    DEFAULT_COS_PREFIX,
    DEFAULT_MATERIAL_SOURCE,
    EQXIU_COS_TOKEN_API_BASE,
    EQXIU_MATERIAL_API_BASE,
)
from .errors import EqxiuAigcApiError
from .upload_material import CosClientError, CosServiceError, upload_local_material


def load_json_arg(s: str) -> Any:
    return json.loads(s)


def main() -> int:
    parser = argparse.ArgumentParser(description="易企秀 AIGC HTTP API 客户端")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API 根地址（默认来自环境变量 EQXIU_AIGC_API_BASE 或 {DEFAULT_BASE_URL!r}）",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=900.0,
        help="请求超时秒数（scene-tpl 可能很慢）",
    )
    parser.add_argument(
        "--access-token",
        default=None,
        help=f"X-Openclaw-Token（默认从 {CONFIG_PATH} 读取）",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("login", help="交互式登录，保存 X-Openclaw-Token")
    p_auth = sub.add_parser("auth", help="认证相关命令")
    auth_sub = p_auth.add_subparsers(dest="auth_cmd", required=True)
    auth_sub.add_parser("status", help="验证 token 是否有效")

    p_cat = sub.add_parser("category", help="GET /iaigc/category")
    p_sty = sub.add_parser("style", help="GET /iaigc/style")
    p_sty.add_argument("--two", type=int, required=True, dest="two_level")
    p_sty.add_argument("--three", type=int, required=True, dest="three_level")

    p_out = sub.add_parser("outline", help="POST /iaigc/outline")
    p_out.add_argument("--category-id", type=int, required=True)
    p_out.add_argument(
        "--fields-json",
        required=True,
        help='sceneFields JSON 数组，如 \'[{"id":1,"value":"活动主题"}]\'',
    )

    p_tpl = sub.add_parser("scene-tpl", help="POST /iaigc/scene-tpl")
    p_tpl.add_argument("--json-file", required=True, help="完整请求体 JSON 文件路径")

    p_pipe = sub.add_parser("pipeline", help="依次调用 outline + scene-tpl")
    p_pipe.add_argument("--category-id", type=int, required=True)
    p_pipe.add_argument("--title", required=True)
    p_pipe.add_argument("--fields-json", required=True)
    p_pipe.add_argument("--style-id", type=int, default=None)
    p_vf = sub.add_parser("validate-fix", help="文本可用性修正并发布")
    p_vf.add_argument("--scene-id", type=int, required=True)
    p_vf.add_argument("--element-id", type=int, required=True)
    p_vf.add_argument("--content", required=True)
    p_vf.add_argument("--page-id", type=int, required=True)
    p_vf.add_argument("--css-json", default=None, help='可选，元素 css JSON，如 \'{"fontSize":"32"}\'')
    p_vf.add_argument("--preview-url", default=None, help="可选，修正后原样回传")

    p_bi = sub.add_parser("body-images", help="GET /iaigc/h5_scene/get_body_images 查询正文配图")
    p_bi.add_argument("--scene-id", type=int, required=True)
    p_bi.add_argument("--page-id", type=int, default=None)

    p_rb = sub.add_parser("replace-body-image", help="POST /iaigc/h5_scene/replace_body_image 换正文配图")
    p_rb.add_argument("--scene-id", type=int, required=True)
    p_rb.add_argument("--page-id", type=int, required=True)
    p_rb.add_argument("--element-id", required=True, help="正文配图元素 id")
    p_rb.add_argument("--src", required=True, help="新图 src 或素材 path")
    p_rb.add_argument("--source-id", default=None, help="可选，写入 properties.sourceId")

    p_up = sub.add_parser(
        "upload",
        help="COS 上传后登记易企秀素材库（与投票鸭 upload 相同流程，域名为 eqxiu.com）",
    )
    p_up.add_argument("--file", type=str, required=True, help="本地文件路径")
    p_up.add_argument("--bucket", type=str, default=DEFAULT_COS_BUCKET, help=f"业务 bucket（默认 {DEFAULT_COS_BUCKET}）")
    p_up.add_argument(
        "--prefix",
        type=str,
        default=DEFAULT_COS_PREFIX,
        help=f"与 token-upload 一致的 prefix（默认 {DEFAULT_COS_PREFIX!r}）",
    )
    p_up.add_argument("--name", type=str, default=None, help="COS 对象名；默认使用本地文件 basename")
    p_up.add_argument("--tmb-path", type=str, default=None, help="saveFile 的 tmbPath；默认与 COS key 相同")
    p_up.add_argument(
        "--source",
        type=str,
        default=DEFAULT_MATERIAL_SOURCE,
        help=f"saveFile 的 source（默认 {DEFAULT_MATERIAL_SOURCE!r}，可用环境变量 EQXIU_MATERIAL_SOURCE）",
    )
    p_up.add_argument("--tag-id", type=int, default=-1, help="saveFile 的 tagId（默认 -1）")
    p_up.add_argument("--file-type", type=int, default=1, help="saveFile 的 fileType（默认 1 图片）")
    p_up.add_argument(
        "--cos-api-base",
        type=str,
        default=EQXIU_COS_TOKEN_API_BASE,
        help=f"COS 凭证接口根（默认 {EQXIU_COS_TOKEN_API_BASE}）",
    )
    p_up.add_argument(
        "--material-api-base",
        type=str,
        default=EQXIU_MATERIAL_API_BASE,
        help=f"素材 saveFile 接口根（默认 {EQXIU_MATERIAL_API_BASE}）",
    )

    p_ml = sub.add_parser(
        "material-list",
        help="GET material-api …/m/material/user/upload/list2 查询当前用户上传素材",
    )
    p_ml.add_argument("--file-type", type=int, default=1, help="文件类型，1 一般为图片（默认 1）")
    p_ml.add_argument("--page-no", type=int, default=1, dest="page_no")
    p_ml.add_argument("--page-size", type=int, default=30, dest="page_size")
    p_ml.add_argument("--tag-id", type=int, default=-1, dest="tag_id")
    p_ml.add_argument(
        "--material-api-base",
        type=str,
        default=EQXIU_MATERIAL_API_BASE,
        help=f"素材接口根（默认 {EQXIU_MATERIAL_API_BASE}）",
    )

    args = parser.parse_args()
    cfg = load_config()
    token = (args.access_token or "").strip() or token_from_config(cfg)

    if args.cmd == "login":
        return login_interactive()

    try:
        if args.cmd == "auth":
            if args.auth_cmd != "status":
                print("未知 auth 子命令", file=sys.stderr)
                return 2
            if not token:
                print("缺少 X-Openclaw-Token：请先执行 login 或传 --access-token", file=sys.stderr)
                return 1
            out = check_auth_status(token, args.timeout)
        else:
            client = EqxiuAigcClient(base_url=args.base_url, timeout=args.timeout, access_token=token or None)
            if args.cmd == "category":
                out = client.list_categories()
            elif args.cmd == "style":
                out = client.list_styles(args.two_level, args.three_level)
            elif args.cmd == "outline":
                fields = load_json_arg(args.fields_json)
                if not isinstance(fields, list):
                    print("fields-json 必须是 JSON 数组", file=sys.stderr)
                    return 2
                out = client.create_outline(fields, args.category_id)
            elif args.cmd == "scene-tpl":
                with open(args.json_file, encoding="utf-8") as f:
                    body = json.load(f)
                out = client.create_scene_tpl(
                    scene_fields=body["sceneFields"],
                    scene_id=body["sceneId"],
                    title=body["title"],
                    outline_task_id=body["outlineTaskId"],
                    outline=body["outline"],
                    image_id=body.get("imageId"),
                    style_id=body.get("styleId"),
                )
            elif args.cmd == "pipeline":
                fields = load_json_arg(args.fields_json)
                if not isinstance(fields, list):
                    print("fields-json 必须是 JSON 数组", file=sys.stderr)
                    return 2
                out = client.run_pipeline(
                    fields,
                    args.category_id,
                    args.title,
                    style_id=args.style_id,
                )
            elif args.cmd == "validate-fix":
                css_obj: Optional[Dict[str, Any]] = None
                if args.css_json:
                    css_raw = load_json_arg(args.css_json)
                    if not isinstance(css_raw, dict):
                        print("css-json 必须是 JSON 对象", file=sys.stderr)
                        return 2
                    css_obj = css_raw
                fix_result = client.update_editable_text(
                    scene_id=args.scene_id,
                    page_id=args.page_id,
                    element_id=args.element_id,
                    content=args.content.strip(),
                    css=css_obj,
                )
                out = {
                    "scene_id": args.scene_id,
                    "fix": fix_result,
                    "previewUrl": (args.preview_url or "").strip() or None,
                }
            elif args.cmd == "material-list":
                out = client.list_user_material_uploads(
                    file_type=args.file_type,
                    page_no=args.page_no,
                    page_size=args.page_size,
                    tag_id=args.tag_id,
                    material_api_base=args.material_api_base,
                )
            elif args.cmd == "body-images":
                out = client.get_body_images(args.scene_id, page_id=args.page_id)
            elif args.cmd == "replace-body-image":
                sid: Any = None
                if args.source_id is not None and str(args.source_id).strip() != "":
                    try:
                        sid = int(args.source_id)
                    except ValueError:
                        sid = args.source_id
                out = client.replace_body_image(
                    args.scene_id,
                    args.page_id,
                    args.element_id,
                    args.src,
                    source_id=sid,
                )
            elif args.cmd == "upload":
                if not token:
                    print(
                        json.dumps(
                            {
                                "success": False,
                                "code": 401,
                                "msg": "缺少 X-Openclaw-Token：请先执行 login 或传 --access-token。",
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                path = Path(args.file).expanduser()
                try:
                    out = upload_local_material(
                        token,
                        path,
                        bucket=args.bucket,
                        prefix=args.prefix,
                        object_name=args.name,
                        tmb_path=args.tmb_path,
                        source=args.source,
                        tag_id=args.tag_id,
                        file_type=args.file_type,
                        cos_api_base=args.cos_api_base,
                        material_api_base=args.material_api_base,
                    )
                except FileNotFoundError as e:
                    print(
                        json.dumps(
                            {"success": False, "code": 400, "msg": str(e)},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                except ValueError as e:
                    print(
                        json.dumps(
                            {"success": False, "code": 400, "msg": str(e)},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                except ImportError as e:
                    print(
                        json.dumps(
                            {"success": False, "code": 500, "msg": str(e)},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                except RuntimeError as e:
                    print(
                        json.dumps(
                            {"success": False, "code": 400, "msg": str(e)},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                except requests.RequestException as e:
                    print(
                        json.dumps(
                            {"success": False, "code": 502, "msg": f"上传相关 HTTP 失败: {e}"},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                except CosServiceError as e:
                    detail = e.get_digest_msg() if hasattr(e, "get_digest_msg") else str(e)
                    print(
                        json.dumps(
                            {"success": False, "code": 502, "msg": "COS 上传失败", "detail": detail},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                except CosClientError as e:
                    print(
                        json.dumps(
                            {"success": False, "code": 502, "msg": f"COS 客户端错误: {e}"},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                except Exception as e:
                    print(
                        json.dumps(
                            {"success": False, "code": 500, "msg": str(e)},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
            else:
                print(f"未知子命令: {args.cmd}", file=sys.stderr)
                return 2
    except EqxiuAigcApiError as e:
        print(json.dumps({"error": str(e), "raw": e.raw}, ensure_ascii=False, indent=2))
        return 1
    except requests.RequestException as e:
        print(json.dumps({"error": f"HTTP 错误: {e}"}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0
