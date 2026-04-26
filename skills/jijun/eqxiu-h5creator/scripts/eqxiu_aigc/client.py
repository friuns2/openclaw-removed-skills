"""易企秀 /iaigc 主客户端：品类、大纲、场景模板与 H5 页能力。"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

import requests

from .constants import CONFIG_TOKEN_KEY, DEFAULT_UPLOAD_TIMEOUT, EQXIU_MATERIAL_API_BASE
from .errors import EqxiuAigcApiError
from .h5_scene_api import H5SceneApiMixin
from .upload_material import list_user_upload_materials


def preview_url_from_scene_tpl(scene_tpl_data: Any) -> Optional[str]:
    if isinstance(scene_tpl_data, dict):
        v = scene_tpl_data.get("previewUrl")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


class EqxiuAigcClient(H5SceneApiMixin):
    """调用 /iaigc/* 接口。outline 与 scene-tpl 可能耗时数分钟，默认 timeout 较大。"""

    def __init__(
        self, base_url: str, timeout: float = 900.0, access_token: Optional[str] = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        if access_token:
            self._session.headers.update({CONFIG_TOKEN_KEY: access_token})

    def _access_token(self) -> str:
        return (self._session.headers.get(CONFIG_TOKEN_KEY) or "").strip()

    def list_user_material_uploads(
        self,
        *,
        file_type: int = 1,
        page_no: int = 1,
        page_size: int = 30,
        tag_id: int = -1,
        material_api_base: str = EQXIU_MATERIAL_API_BASE,
    ) -> Dict[str, Any]:
        """查询当前用户在素材库中的上传列表（易企秀 material-api，非 iaigc）。"""
        token = self._access_token()
        if not token:
            raise EqxiuAigcApiError("缺少 X-Openclaw-Token，无法查询素材", raw=None)
        t = min(int(self.timeout), max(DEFAULT_UPLOAD_TIMEOUT, 60))
        try:
            return list_user_upload_materials(
                token,
                file_type=file_type,
                page_no=page_no,
                page_size=page_size,
                tag_id=tag_id,
                material_api_base=material_api_base,
                timeout=t,
            )
        except RuntimeError as e:
            raise EqxiuAigcApiError(str(e), raw=None) from e

    def _unwrap(self, resp: requests.Response) -> Any:
        try:
            payload = resp.json()
        except json.JSONDecodeError as e:
            raise EqxiuAigcApiError(
                f"无效 JSON 响应: {e}", status_code=resp.status_code, raw=resp.text
            ) from e
        if not isinstance(payload, dict):
            raise EqxiuAigcApiError("响应不是 JSON 对象", status_code=resp.status_code, raw=payload)
        if payload.get("success") is False:
            raise EqxiuAigcApiError(
                str(payload.get("msg", "请求失败")),
                status_code=resp.status_code if resp.status_code >= 400 else payload.get("code"),
                raw=payload,
            )
        if "data" in payload:
            return payload["data"]
        return payload

    def list_categories(self) -> List[Dict[str, Any]]:
        r = self._session.get(f"{self.base_url}/iaigc/category", timeout=self.timeout)
        r.raise_for_status()
        return self._unwrap(r)

    def list_styles(
        self, two_level_category_id: int, three_level_category_id: int
    ) -> Dict[str, Any]:
        r = self._session.get(
            f"{self.base_url}/iaigc/style",
            params={
                "twoLevelCategoryId": two_level_category_id,
                "threeLevelCategoryIds": three_level_category_id,
            },
            timeout=self.timeout,
        )
        r.raise_for_status()
        return self._unwrap(r)

    def create_outline(self, scene_fields: List[Dict[str, Any]], category_id: int) -> Dict[str, Any]:
        r = self._session.post(
            f"{self.base_url}/iaigc/outline",
            json={"sceneFields": scene_fields, "categoryId": category_id},
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = self._unwrap(r)
        if not isinstance(data, dict):
            raise EqxiuAigcApiError("outline 返回的 data 不是对象", raw=data)
        return data

    def create_scene_tpl(
        self,
        scene_fields: List[Dict[str, Any]],
        scene_id: int,
        title: str,
        outline_task_id: Union[int, str],
        outline: Any,
        image_id: Any = None,
        style_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "sceneFields": scene_fields,
            "sceneId": scene_id,
            "title": title,
            "outlineTaskId": outline_task_id,
            "outline": outline,
        }
        if image_id is not None:
            body["imageId"] = image_id
        if style_id is not None:
            body["styleId"] = style_id
        r = self._session.post(f"{self.base_url}/iaigc/scene-tpl", json=body, timeout=self.timeout)
        r.raise_for_status()
        data = self._unwrap(r)
        if not isinstance(data, dict):
            raise EqxiuAigcApiError("scene-tpl 返回的 data 不是对象", raw=data)
        return data

    def run_pipeline(
        self,
        scene_fields: List[Dict[str, Any]],
        category_id: int,
        title: str,
        *,
        style_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        按正确顺序：先 outline，再 scene-tpl（复用同一份 sceneFields 与 category_id 作为 sceneId）。
        """
        outline_result = self.create_outline(scene_fields, category_id)
        tpl_result = self.create_scene_tpl(
            scene_fields=scene_fields,
            scene_id=category_id,
            title=title,
            outline_task_id=outline_result["outlineTaskId"],
            outline=outline_result["outline"],
            image_id=outline_result.get("imageId"),
            style_id=style_id,
        )
        scene_id = tpl_result.get("sceneId") if isinstance(tpl_result, dict) else None

        editable_text = self.get_editable_text(scene_id) if scene_id else []
        body_images: List[Dict[str, Any]] = []
        if scene_id:
            try:
                body_images = self.get_body_images(int(scene_id))
            except EqxiuAigcApiError:
                body_images = []

        return {
            "outline": outline_result,
            "scene_tpl": tpl_result,
            "previewUrl": preview_url_from_scene_tpl(tpl_result),
            "validation": {
                "scene_id": scene_id,
                "editable_text": editable_text,
                "body_images": body_images,
                "instruction": "请大模型检查以上可编辑文本；若发现问题，调用 validate-fix 子命令修正并发布，修正时注意保持原有风格和样式。"
                "换图可使用 replace-body-image 子命令（需 page_id、element_id、src）。",
            },
        }
