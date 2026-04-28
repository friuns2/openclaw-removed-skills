#!/usr/bin/env python3
"""
CWork API Client — 共享 API 封装
由所有编排脚本 import 使用
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import argparse
from datetime import datetime

# 在模块加载时强制 stdout/stderr 使用 UTF-8，避免在 LANG=en_US 等环境下
# argparse --help 或任何 print() 输出中文时崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


# ---------------------------------------------------------------------------
# HTTP redirect handler — preserves method on 307/308
# ---------------------------------------------------------------------------

class _MethodPreservingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """urllib 默认不跟随 307 的 POST 请求；此 handler 保留原始 method 和 body。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_headers = {k: v for k, v in req.header_items()
                       if k.lower() not in ("host", "content-length")}
        return urllib.request.Request(
            newurl,
            data=req.data,
            headers=new_headers,
            method=req.method,
            origin_req_host=req.origin_req_host,
            unverifiable=True,
        )

    def http_error_307(self, req, fp, code, msg, headers):
        return self.http_error_302(req, fp, code, msg, headers)

    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_302(req, fp, code, msg, headers)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CWorkError(Exception):
    """Raised on API errors (non-1 resultCode or HTTP non-OK)."""
    pass


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class CWorkClient:
    BASE_URL = "https://sg-al-cwork-web.mediportal.com.cn"

    def __init__(self, app_key: str | None = None):
        self.app_key = app_key
        if not self.app_key:
            raise CWorkError("缺少 AppKey。请先通过 cms-auth-skills 获取并注入 --app-key。")

    # ---- HTTP helpers -------------------------------------------------------

    def _headers(self, json_body: bool = False) -> dict:
        h = {"appKey": self.app_key}
        if json_body:
            h["Content-Type"] = "application/json"
        return h

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        if params:
            q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{q}&appKey={self.app_key}"
        else:
            url = f"{url}?appKey={self.app_key}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        return self._request(req)

    def _post(self, path: str, body: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url,
            data=data,
            headers=self._headers(json_body=body is not None),
            method="POST",
        )
        return self._request(req)

    def _request(self, req: urllib.request.Request) -> dict:
        try:
            opener = urllib.request.build_opener(_MethodPreservingRedirectHandler)
            with opener.open(req, timeout=30) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                result = json.loads(raw.decode(charset))
        except urllib.error.HTTPError as e:
            raise CWorkError(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise CWorkError(f"URL error: {e.reason}")

        if result.get("resultCode", -1) != 1:
            raise CWorkError(
                f"API Error ({result.get('resultCode')}): {result.get('resultMsg', 'unknown')}"
            )
        return result.get("data", {})

    # -------------------------------------------------------------------------
    # Employee
    # -------------------------------------------------------------------------

    def search_emp_by_name(self, search_key: str) -> dict:
        """Returns {inside: {empList:[]}, outside: {empList:[]}}"""
        normalized_key = (search_key or "").strip()
        try:
            return self._get("/open-api/cwork-user/searchEmpByName", {"searchKey": normalized_key})
        except CWorkError:
            # 某些租户环境下带中文 searchKey 会返回非 1 resultCode；兜底为全量后本地过滤。
            if not normalized_key:
                raise
            raw = self._get("/open-api/cwork-user/searchEmpByName", {"searchKey": ""})
            return _filter_emp_search_result(raw, normalized_key)

    # -------------------------------------------------------------------------
    # Reports — inbox / outbox / detail
    # -------------------------------------------------------------------------

    def get_inbox_list(
        self,
        page_size: int,
        page_index: int = 1,
        *,
        report_record_type: int | None = None,
        emp_id_list: list[str] | None = None,
        begin_time: int | None = None,
        end_time: int | None = None,
        read_status: int | None = None,
        order_column: str | None = None,
        grade: str | None = None,
        template_id: int | None = None,
    ) -> dict:
        """PaginatedResult<ReportListItem>"""
        params = {
            "pageSize": page_size,
            "pageIndex": page_index,
            "reportRecordType": report_record_type,
            "empIdList": emp_id_list,
            "beginTime": begin_time,
            "endTime": end_time,
            "readStatus": read_status,
            "orderColumn": order_column,
            "grade": grade,
            "templateId": template_id,
        }
        return self._post("/open-api/work-report/report/record/inbox", params)

    def get_outbox_list(
        self,
        page_size: int,
        page_index: int = 1,
        *,
        report_record_type: int | None = None,
        emp_id_list: list[str] | None = None,
        begin_time: int | None = None,
        end_time: int | None = None,
        grade: str | None = None,
        template_id: int | None = None,
    ) -> dict:
        params = {
            "pageSize": page_size,
            "pageIndex": page_index,
            "reportRecordType": report_record_type,
            "empIdList": emp_id_list,
            "beginTime": begin_time,
            "endTime": end_time,
            "grade": grade,
            "templateId": template_id,
        }
        return self._post("/open-api/work-report/report/record/outbox", params)

    def get_report_info(self, report_id: str) -> dict:
        """5.5 获取汇报内容。开放 API 响应体为 **6.6 ReportDTO**：含 ``reportId``、``content``（正文纯文本）、``writeEmpId``、``writeEmpName``、``createTime``、``replies``。

        **不含** ``main``（标题）、``acceptEmpIdList`` 等；查标题与流程节点/接收人请用 ``get_report_node_detail``（5.33）。
        """
        return self._get("/open-api/work-report/report/info", {"reportId": report_id})

    def get_report_node_detail(self, report_id: str | int) -> dict:
        """
        获取汇报详情（含节点与处理意见）
        API: 5.33 /work-report/report/getReportNodeDetail

        Returns:
          {
            "id": 汇报ID,
            "main": 标题,
            "content": 正文,
            "writeEmpId": 汇报人ID,
            "writeEmpName": 汇报人姓名,
            "createTime": 发起时间,
            "nodeList": [
              {
                "nodeName": "建议人",
                "type": "建议/决策/传阅",
                "status": "未开始/已完成/进行中/已取消",
                "level": 1,
                "userList": [
                  {
                    "empId": 员工ID,
                    "name": 姓名,
                    "status": "待处理/已处理",
                    "operate": "同意/不同意/建议",
                    "content": "处理意见",
                    "finishTime": "完成时间"
                  }
                ]
              }
            ]
          }
        """
        return self._get("/open-api/work-report/report/getReportNodeDetail", {"reportId": report_id})

    def get_unread_list(self, page_index: int, page_size: int) -> dict:
        return self._post("/open-api/work-report/reportInfoOpenQuery/unreadList", {
            "pageIndex": page_index,
            "pageSize": page_size,
        })

    def is_report_read(self, report_id: str | int, employee_id: str | int) -> bool:
        return self._get(
            "/open-api/work-report/reportInfoOpenQuery/isReportRead",
            {"reportId": str(report_id), "employeeId": str(employee_id)},
        )

    def mark_report_read(self, report_id: str | int) -> None:
        self._get(
            "/open-api/work-report/open-platform/report/readReport",
            {"reportId": str(report_id)},
        )

    def create_share_link(self, biz_id: str | int, biz_type: int) -> str:
        """创建汇报/任务分享链接。

        biz_type:
          1 = 汇报
          2 = 任务
        """
        if biz_type not in (1, 2):
            raise ValueError("create_share_link: biz_type 仅支持 1(汇报) 或 2(任务)")
        data = self._post("/open-api/work-report/report/share/create", {
            "bizId": int(str(biz_id)),
            "bizType": biz_type,
        })
        return str(data)

    # -------------------------------------------------------------------------
    # Report — reply / submit / remind
    # -------------------------------------------------------------------------

    def submit_report(
        self,
        main: str,
        content_html: str,
        *,
        report_id: str | None = None,
        business_unit_id: str | int | None = None,
        content_type: str = "html",
        type_id: int = 9999,
        grade: str = "一般",
        privacy_level: str = "非涉密",
        plan_id: str | None = None,
        template_id: int | None = None,
        accept_emp_id_list: list[str] | None = None,
        copy_emp_id_list: list[str] | None = None,
        report_level_list: list[dict] | None = None,
        file_vo_list: list[dict] | None = None,
        virtual_emp_id: str | None = None,
    ) -> dict:
        """Submit a report. Pass report_id to promote an existing draft.

        正文写入 JSON 键 ``contentHtml``（历史命名）；语义由 ``contentType`` 决定，
        ``markdown`` 时传 Markdown 源码即可。
        """
        payload = {
            "appKey": self.app_key,
            "main": main,
            "contentHtml": content_html,
            "contentType": content_type,
            "typeId": type_id,
            "businessUnitId": business_unit_id,
            "grade": grade,
            "privacyLevel": privacy_level,
            "planId": plan_id,
            "templateId": template_id,
            "acceptEmpIdList": accept_emp_id_list,
            "copyEmpIdList": copy_emp_id_list,
            "reportLevelList": report_level_list,
            "fileVOList": file_vo_list,
            "virtualEmpId": virtual_emp_id,
        }
        if report_id is not None:
            payload["id"] = report_id
        return self._post("/open-api/work-report/report/record/submit", payload)

    def reply_report(
        self,
        report_record_id: str,
        content_html: str,
        *,
        content_type: str = "html",
        add_emp_id_list: list[str] | None = None,
        send_msg: bool = True,
        media_vo_list: list[dict] | None = None,
        virtual_emp_id: str | None = None,
    ) -> int:
        """回复汇报。正文写入 ``contentHtml``；``content_type=markdown`` 时为 Markdown。

        附件走 ``mediaVOList``，并由 ``isMedia`` 标记是否带附件。
        """
        return self._post("/open-api/work-report/report/record/reply", {
            "appKey": self.app_key,
            "reportRecordId": report_record_id,
            "isMedia": 1 if media_vo_list else 0,
            "mediaVOList": media_vo_list,
            "contentHtml": content_html,
            "contentType": content_type,
            "addEmpIdList": add_emp_id_list,
            "sendMsg": send_msg,
            "virtualEmpId": virtual_emp_id,
        })

    # -------------------------------------------------------------------------
    # Draft box
    # -------------------------------------------------------------------------

    def save_draft(
        self,
        main: str,
        content_html: str,
        *,
        draft_id: str | None = None,
        id: str | None = None,  # noqa: A002 — 兼容误用 save_draft(id=汇报id) 的调用方
        business_unit_id: str | int | None = None,
        content_type: str = "markdown",
        type_id: int = 9999,
        grade: str = "一般",
        privacy_level: str = "非涉密",
        plan_id: str | None = None,
        template_id: str | None = None,
        accept_emp_id_list: list[str] | None = None,
        copy_emp_id_list: list[str] | None = None,
        report_level_list: list[dict] | None = None,
        file_vo_list: list[dict] | None = None,
        virtual_emp_id: str | None = None,
    ) -> dict:
        """5.23 草稿 saveOrUpdate。正文写入 ``contentHtml``；``content_type=markdown`` 时传 Markdown 字符串。"""
        effective_draft_id = draft_id if draft_id is not None else id
        if draft_id is not None and id is not None and str(draft_id) != str(id):
            raise ValueError("save_draft: pass only one of draft_id and id")
        payload = {
            "appKey": self.app_key,
            "main": main,
            "contentHtml": content_html,
            "contentType": content_type,
            "typeId": type_id,
            "businessUnitId": business_unit_id,
            "grade": grade,
            "privacyLevel": privacy_level,
            "planId": plan_id,
            "templateId": template_id,
            "acceptEmpIdList": accept_emp_id_list,
            "copyEmpIdList": copy_emp_id_list,
            "reportLevelList": report_level_list,
            "fileVOList": file_vo_list,
            "virtualEmpId": virtual_emp_id,
        }
        if effective_draft_id is not None:
            payload["id"] = effective_draft_id
        return self._post("/open-api/work-report/draftBox/saveOrUpdate", payload)

    def list_drafts(self, page_index: int, page_size: int) -> dict:
        """5.24 草稿箱分页。``data.list[]`` 中 ``id`` 为草稿箱记录 id（用于 5.26 删除）；``businessId`` 为汇报 id（``bizType=report`` 时）。"""
        return self._post("/open-api/work-report/draftBox/listByPage", {
            "pageIndex": page_index,
            "pageSize": page_size,
        })

    def get_draft_detail(self, report_record_id: str) -> dict:
        return self._get(f"/open-api/work-report/draftBox/detail/{report_record_id}")

    def submit_draft(self, report_id: str) -> bool:
        """API 5.27: 将草稿转为正式汇报发出。路径参数 id 为汇报 id（与 saveOrUpdate 返回的 id 一致）。"""
        rid = urllib.parse.quote(str(report_id), safe="")
        # 注意：部分环境成功时 data 可能为空对象/空值；若强转 bool 会被误判为失败，
        # 上层自动重试将导致重复发送。只要 _post 未抛错（resultCode=1）即视为成功。
        self._post(f"/open-api/work-report/draftBox/submit/{rid}")
        return True

    def delete_draft(self, draft_id: str) -> bool:
        """5.26 删除草稿。路径 ``id`` 必须是 **5.24 列表项的 ``id``**（草稿箱记录主键）。

        **不是** ``businessId``，也**不是** 汇报 id（与 5.25/5.27、``--draft-id`` 所用相同的那份汇报 id 不同）。
        误传汇报 id 时，部分环境仍可能返回 ``data: true``，但草稿仍在列表中。
        若只有汇报 id，请用 ``delete_draft_by_report_id``。
        """
        did = urllib.parse.quote(str(draft_id), safe="")
        # 与 submit_draft 一致：成功判定以 resultCode=1 为准，避免 data 为空值导致误判失败。
        self._post(f"/open-api/work-report/draftBox/delete/{did}")
        return True

    def delete_draft_by_report_id(
        self,
        report_id: str | int,
        *,
        page_size: int = 50,
        max_pages: int = 20,
    ) -> bool:
        """按汇报 id 删除草稿：先 5.24 查找 ``bizType=report`` 且 ``businessId`` 匹配的行，再 5.26。

        未在列表中找到对应行时返回 ``False``（不调用删除接口）。
        """
        rid = str(report_id)
        for page in range(1, max_pages + 1):
            data = self.list_drafts(page_index=page, page_size=page_size)
            items = data.get("list") or []
            for row in items:
                if not isinstance(row, dict):
                    continue
                if row.get("bizType") != "report":
                    continue
                if str(row.get("businessId")) != rid:
                    continue
                box_id = row.get("id")
                if box_id is None:
                    continue
                return self.delete_draft(str(box_id))
            if len(items) < page_size:
                break
        return False

    def batch_delete_drafts(
        self,
        *,
        id_list: list[str | int] | None = None,
        begin_time_ms: int | None = None,
        end_time_ms: int | None = None,
    ) -> int:
        """5.28 批量删除草稿。开放 API 约定 **时间范围优先**：同时传时间与 idList 时仅按时间删除。

        请求体仅含文档所列字段：``beginTime`` / ``endTime`` 或 ``idList``（草稿箱记录 id，同 5.24 的 ``id``）。
        """
        body: dict = {}
        if begin_time_ms is not None and end_time_ms is not None:
            body["beginTime"] = int(begin_time_ms)
            body["endTime"] = int(end_time_ms)
        elif id_list:
            body["idList"] = [int(str(x)) for x in id_list]
        else:
            raise ValueError(
                "batch_delete_drafts: 请传入 begin_time_ms 与 end_time_ms，或传入 id_list"
            )
        data = self._post("/open-api/work-report/draftBox/batchDelete", body)
        if isinstance(data, int):
            return data
        if data is None:
            return 0
        return int(data)

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    def search_task_page(
        self,
        page_size: int,
        page_index: int = 1,
        *,
        key_word: str | None = None,
        status: int | None = None,
        report_status: int | None = None,
        emp_id_list: list[str] | None = None,
        grades: list[str] | None = None,
        label_list: list[str] | None = None,
        is_read: int | None = None,
    ) -> dict:
        params = {
            "pageSize": page_size,
            "pageIndex": page_index,
            "keyWord": key_word,
            "status": status,
            "reportStatus": report_status,
            "empIdList": emp_id_list,
            "grades": grades,
            "labelList": label_list,
            "isRead": is_read,
        }
        return self._post("/open-api/work-report/report/plan/searchPage", params)

    def get_simple_plan_and_report_info(self, plan_id: str) -> dict:
        return self._get(
            "/open-api/work-report/report/plan/getSimplePlanAndReportInfo",
            {"planId": plan_id},
        )

    def create_plan(
        self,
        main: str,
        needful: str,
        target: str,
        end_time: int,
        type_id: int = 9999,
        *,
        report_emp_id_list: list[str] | None = None,
        owner_emp_id_list: list[str] | None = None,
        assist_emp_id_list: list[str] | None = None,
        supervisor_emp_id_list: list[str] | None = None,
        copy_emp_id_list: list[str] | None = None,
        observer_emp_id_list: list[str] | None = None,
        push_now: bool = True,
        virtual_emp_id: str | None = None,
    ) -> str:
        """Returns plan ID string."""
        result = self._post("/open-api/work-report/open-platform/report/plan/create", {
            "appKey": self.app_key,
            "main": main,
            "needful": needful,
            "target": target,
            "typeId": type_id,
            "reportEmpIdList": report_emp_id_list,
            "ownerEmpIdList": owner_emp_id_list,
            "assistEmpIdList": assist_emp_id_list,
            "supervisorEmpIdList": supervisor_emp_id_list,
            "copyEmpIdList": copy_emp_id_list,
            "observerEmpIdList": observer_emp_id_list,
            "pushNow": 1 if push_now else 0,
            "endTime": end_time,
            "virtualEmpId": virtual_emp_id,
        })
        return str(result)

    # -------------------------------------------------------------------------
    # Virtual employee
    # -------------------------------------------------------------------------

    def add_virtual_employee(self, name: str, remark: str | None = None) -> str:
        payload: dict = {"name": name}
        if remark is not None:
            payload["remark"] = remark
        result = self._post("/open-api/cwork-user/virtual-employee/add", payload)
        return str(result)

    def list_virtual_employees(self) -> list:
        data = self._get("/open-api/cwork-user/virtual-employee/list")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("list", "items", "records", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        return []

    def update_virtual_employee(
        self,
        virtual_emp_id: str | int,
        *,
        name: str | None = None,
        remark: str | None = None,
    ) -> bool:
        payload: dict = {"id": str(virtual_emp_id)}
        if name is not None:
            payload["name"] = name
        if remark is not None:
            payload["remark"] = remark
        if len(payload) == 1:
            raise ValueError("update_virtual_employee: 至少需要 name 或 remark 之一")
        # 仅以是否抛错判定成功，避免 data 为空值时误报失败。
        self._post("/open-api/cwork-user/virtual-employee/update", payload)
        return True

    def delete_virtual_employee(self, virtual_emp_id: str | int) -> bool:
        # API expects `virtualEmpId` as URL query parameter: ?virtualEmpId=xxx
        params = {"virtualEmpId": str(virtual_emp_id)}
        q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = (
            f"{self.BASE_URL}/open-api/cwork-user/virtual-employee/delete"
            f"?{q}&appKey={self.app_key}"
        )
        req = urllib.request.Request(url, headers=self._headers(), data=None, method="POST")
        # 仅以是否抛错判定成功，避免 data 为空值时误报失败。
        self._request(req)
        return True

    # -------------------------------------------------------------------------
    # Todo / feedback
    # -------------------------------------------------------------------------

    def list_created_feedbacks(self, emp_id: str | None = None) -> list:
        """API 5.12: GET, optional empId filter."""
        params = {}
        if emp_id is not None:
            params["empId"] = emp_id
        return self._get(
            "/open-api/work-report/todoTask/listCreatedFeedbacks", params
        )

    def get_todo_list(self, page_index: int, page_size: int, *, status: str | None = None) -> dict:
        """5.15 待办列表。成功时 ``data`` 为 PageInfo（``total`` + ``list``，见开放 API 6.3 / 6.18）。"""
        params = {"pageIndex": page_index, "pageSize": page_size}
        if status:
            params["status"] = status
        return self._post("/open-api/work-report/reportInfoOpenQuery/todoList", params)

    def complete_todo(
        self,
        todo_id: str,
        content: str,
        *,
        content_type: str = "html",
        operate: str | None = None,
    ) -> bool:
        payload: dict = {
            "appKey": self.app_key,
            "todoId": todo_id,
            "content": content,
            "contentType": content_type,
        }
        if operate is not None:
            payload["operate"] = operate
        return self._post("/open-api/work-report/open-platform/todo/completeTodo", payload)

    # -------------------------------------------------------------------------
    # File upload
    # -------------------------------------------------------------------------

    def upload_file(self, file_path: str) -> dict:
        import mimetypes
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        filename = os.path.basename(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            file_data = f.read()
        body_parts = [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_data,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
        body = b"".join(body_parts)
        req = urllib.request.Request(
            f"{self.BASE_URL}/open-api/cwork-file/uploadWholeFile",
            data=body,
            headers={
                "appKey": self.app_key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        result = self._request(req)
        if isinstance(result, str):
            return {"fileId": result}
        return result

    # -------------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------------

    def list_templates(
        self, begin_time: int | None = None, end_time: int | None = None, limit: int | None = None
    ) -> dict:
        return self._post("/open-api/work-report/template/listTemplates", {
            "appKey": self.app_key,
            "beginTime": begin_time,
            "endTime": end_time,
            "limit": limit,
        })

    # -------------------------------------------------------------------------
    # Business unit
    # -------------------------------------------------------------------------

    def save_business_unit(
        self,
        name: str,
        node_list: list[dict],
        *,
        description: str | None = None,
        business_unit_id: str | int | None = None,
    ) -> str:
        """保存/更新业务单元。传 business_unit_id 代表更新。"""
        payload: dict = {
            "name": name,
            "description": description,
            "nodeList": node_list,
        }
        if business_unit_id is not None:
            payload["id"] = business_unit_id
        result = self._post("/open-api/work-report/businessUnit/save", payload)
        return str(result)

    def list_all_business_units(self) -> list:
        """查询当前用户的业务单元列表（含节点）。

        兼容后端返回：
        - list: 直接数组
        - dict: {"list": [...]} / {"items": [...]} / {"records": [...]}
        """
        data = self._get("/open-api/work-report/businessUnit/listAll")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("list", "items", "records", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        return []

    def get_business_unit_by_id(self, business_unit_id: str | int) -> dict:
        """按业务单元 ID 查询详情。"""
        return self._get(
            "/open-api/work-report/businessUnit/getById",
            {"id": str(business_unit_id)},
        )

    def delete_business_unit(self, business_unit_id: str | int) -> bool:
        """删除业务单元。"""
        # 仅以是否抛错判定成功，避免 data 为空值时误报失败。
        self._post("/open-api/work-report/businessUnit/delete", {"id": business_unit_id})
        return True

    # -------------------------------------------------------------------------
    # History context retrieval (for approval decision support)
    # -------------------------------------------------------------------------

    def get_sender_history(
        self,
        sender_emp_id: str | int,
        days: int = 90,
        max_count: int = 20
    ) -> dict:
        """
        Get sender's historical reports (for approval context)
        
        Args:
            sender_emp_id: Sender employee ID
            days: Days to look back (default 90)
            max_count: Max results (default 20)
        
        Returns:
            {
              "senderEmpId": "xxx",
              "totalReports": 15,
              "recentReports": [...]
            }
        """
        import time
        end_time = int(time.time() * 1000)
        begin_time = end_time - (days * 24 * 60 * 60 * 1000)
        
        # Query inbox for sender's reports
        inbox = self.get_inbox_list(
            page_size=max_count,
            emp_id_list=[str(sender_emp_id)],
            begin_time=begin_time,
            end_time=end_time
        )
        
        return {
            "senderEmpId": str(sender_emp_id),
            "totalReports": inbox.get("total", 0),
            "recentReports": inbox.get("list", [])[:max_count]
        }

    def search_reports_by_keyword(
        self,
        keyword: str,
        days: int = 90,
        max_count: int = 100
    ) -> dict:
        """
        Search reports by keyword (client-side filtering)
        
        Args:
            keyword: Search keyword
            days: Days to look back (default 90)
            max_count: Max results to fetch (default 100)
        
        Returns:
            {
              "keyword": "公章",
              "total": 5,
              "reports": [...]
            }
        """
        import time
        end_time = int(time.time() * 1000)
        begin_time = end_time - (days * 24 * 60 * 60 * 1000)
        
        # Fetch inbox
        inbox = self.get_inbox_list(
            page_size=max_count,
            begin_time=begin_time,
            end_time=end_time
        )
        
        # Client-side filtering
        all_reports = inbox.get("list", [])
        matched = [
            r for r in all_reports
            if keyword in r.get("main", "") or keyword in r.get("content", "")
        ]
        
        return {
            "keyword": keyword,
            "total": len(matched),
            "reports": matched[:20]  # Return top 20
        }


# ---------------------------------------------------------------------------
# Runtime auth context
# ---------------------------------------------------------------------------

_RUNTIME_APP_KEY: str | None = None


def capture_auth_context_pre_parse() -> None:
    """Capture --app-key from sys.argv and remove it before argparse parsing.

    This allows all business scripts to receive AppKey from upstream orchestration
    (e.g. cms-auth-skills) without requiring each script to declare --app-key.
    """
    global _RUNTIME_APP_KEY
    if _RUNTIME_APP_KEY:
        return

    argv = sys.argv[1:]
    new_argv: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--app-key":
            if i + 1 >= len(argv):
                raise CWorkError("--app-key 缺少值")
            _RUNTIME_APP_KEY = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--app-key="):
            _RUNTIME_APP_KEY = arg.split("=", 1)[1]
            i += 1
            continue
        new_argv.append(arg)
        i += 1

    sys.argv = [sys.argv[0], *new_argv]


# Convenience factory
# ---------------------------------------------------------------------------

def make_client(app_key: str | None = None) -> CWorkClient:
    resolved_app_key = app_key or _RUNTIME_APP_KEY
    if not resolved_app_key:
        raise CWorkError(
            "未获取到 AppKey。请先调用 cms-auth-skills，并将结果通过 --app-key 注入当前脚本。"
        )
    return CWorkClient(resolved_app_key)


# ---------------------------------------------------------------------------
# CLI argument helpers
# ---------------------------------------------------------------------------

def flatten_emp_search_bucket(raw) -> list:
    """Normalize ``inside`` / ``outside`` from searchEmpByName to a flat emp dict list.

    API may return a dict with ``empList``, a list of group dicts (each with
    ``empList``), or a flat list of employee records.
    """
    if raw is None:
        return []
    if isinstance(raw, dict):
        emp_list = raw.get("empList")
        return list(emp_list) if isinstance(emp_list, list) else []
    if isinstance(raw, list):
        out: list = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            nested = item.get("empList")
            if isinstance(nested, list) and nested:
                out.extend(nested)
            elif item.get("id") is not None or item.get("empId") is not None or item.get("empid") is not None:
                out.append(item)
        return out
    return []


def _match_emp_name(emp: dict, search_key: str) -> bool:
    name = str(emp.get("name") or "")
    if not name:
        return False
    return (search_key == name) or (search_key in name)


def _filter_emp_search_result(raw: dict, search_key: str) -> dict:
    """Filter searchEmpByName payload client-side by employee name."""
    if not isinstance(raw, dict):
        return {"inside": {"empList": []}, "outside": []}

    inside_raw = raw.get("inside")
    outside_raw = raw.get("outside")

    filtered_inside = {"empList": []}
    if isinstance(inside_raw, dict):
        filtered_inside = dict(inside_raw)
        emp_list = inside_raw.get("empList")
        if isinstance(emp_list, list):
            filtered_inside["empList"] = [e for e in emp_list if isinstance(e, dict) and _match_emp_name(e, search_key)]
        else:
            filtered_inside["empList"] = []

    filtered_outside: list = []
    if isinstance(outside_raw, list):
        for group in outside_raw:
            if not isinstance(group, dict):
                continue
            copied_group = dict(group)
            emp_list = group.get("empList")
            if isinstance(emp_list, list):
                copied_group["empList"] = [
                    e for e in emp_list if isinstance(e, dict) and _match_emp_name(e, search_key)
                ]
            else:
                copied_group["empList"] = []
            if copied_group["empList"]:
                filtered_outside.append(copied_group)

    return {"inside": filtered_inside, "outside": filtered_outside}


def parse_deadline(value: str | None) -> int | None:
    """Parse deadline string to milliseconds timestamp."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return int(dt.timestamp() * 1000)
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(f"Invalid deadline format: {value}. Use YYYY-MM-DD or milliseconds.")


def resolve_names_to_empids(client: CWorkClient, names: list[str]) -> list[str]:
    """Resolve a list of names to empIds via search API.

    Priority: internal employees (inside) > external contacts (outside).
    If inside has any matches, outside is ignored entirely.
    Raises CWorkError if any name is not found or matches more than one employee
    within the same category (inside or outside).
    """
    empids = []
    for name in names:
        result = client.search_emp_by_name(name)
        inside_list = flatten_emp_search_bucket(result.get("inside"))
        # Only fall back to outside when inside has no match at all
        if inside_list:
            all_emps = inside_list
        else:
            all_emps = flatten_emp_search_bucket(result.get("outside"))
        if not all_emps:
            raise CWorkError(
                f'未找到姓名为"{name}"的员工，请确认姓名或直接提供员工 ID'
            )
        if len(all_emps) > 1:
            candidates = [
                {
                    "empId": e.get("id") or e.get("empId") or e.get("empid"),
                    "name": e.get("name", ""),
                    "title": e.get("title", ""),
                    "dept": e.get("mainDept", ""),
                }
                for e in all_emps
            ]
            raise CWorkError(
                f'"{name}" 匹配到多名员工，请指定唯一员工后重试：'
                + json.dumps(candidates, ensure_ascii=False)
            )
        empids.append(
            all_emps[0].get("id") or all_emps[0].get("empId") or all_emps[0].get("empid")
        )
    return empids


def apply_params_file(args) -> None:
    """[Deprecated: use apply_params_file_pre_parse() instead]
    Post-parse merge — cannot satisfy required argparse args from file.
    """
    apply_params_file_pre_parse()


def apply_params_file_pre_parse() -> None:
    """Pre-scan sys.argv for --params-file, load JSON, and inject missing flags
    back into sys.argv BEFORE argparse.parse_args() is called.

    This allows required arguments (e.g. --mode) to be provided from a file,
    which is the primary workaround for Windows PowerShell encoding issues when
    passing Chinese content on the command line.

    Call this at the very start of main(), before parse_args():

        def main():
            apply_params_file_pre_parse()
            args = parse_args()
            ...

    File format example (params.json, UTF-8):
        {
          "mode": "inbox",
          "content": "本周工作进展",
          "receivers": "张三,李四"
        }

    cwork-send-report：JSON 键 ``content`` 表示正文（映射 API ``contentHtml``）；旧键 ``content-html`` 同 ``--content-html``。

    CLI args always take precedence over file values.
    """
    # Step 0: capture runtime auth context before argparse sees unknown auth flags
    capture_auth_context_pre_parse()

    # Step 1: find --params-file in sys.argv without a full parse
    params_file = None
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--params-file" and i + 1 < len(argv):
            params_file = argv[i + 1]
            break
        if arg.startswith("--params-file="):
            params_file = arg.split("=", 1)[1]
            break
    if not params_file:
        return

    # Step 2: load the JSON file
    try:
        # utf-8-sig strips the UTF-8 BOM that PowerShell Out-File adds by default
        with open(params_file, "r", encoding="utf-8-sig") as f:
            file_params = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps({"success": False, "error": f"--params-file: {exc}"},
                       ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 3: build set of flags already present in sys.argv (CLI wins)
    existing_flags: set[str] = set()
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            existing_flags.add(arg.split("=")[0])

    # Step 4: append missing flags to sys.argv
    extra: list[str] = []
    for key, value in file_params.items():
        flag = f"--{key}"
        if key == "app_key":
            flag = "--app-key"
            _capture = value if isinstance(value, str) else str(value)
            global _RUNTIME_APP_KEY
            _RUNTIME_APP_KEY = _capture
            continue
        if flag in existing_flags:
            continue
        if isinstance(value, bool):
            if value:
                extra.append(flag)
        elif isinstance(value, list):
            for v in value:
                extra.extend([flag, str(v)])
        else:
            extra.extend([flag, str(value)])

    if extra:
        sys.argv.extend(extra)


def _write_utf8(text: str, stream=None) -> None:
    """Write text as UTF-8 to stream's binary buffer, falling back to print."""
    target = stream or sys.stdout
    try:
        target.buffer.write((text + "\n").encode("utf-8"))
        target.buffer.flush()
    except AttributeError:
        print(text, file=target)


def output_json(data: dict) -> None:
    """Output JSON to stdout (UTF-8, regardless of terminal codepage)."""
    _write_utf8(json.dumps(data, ensure_ascii=False, indent=2))


def output_error(message: str) -> None:
    """Output error JSON to stderr (UTF-8) and exit."""
    _write_utf8(
        json.dumps({"success": False, "message": message}, ensure_ascii=False, indent=2),
        sys.stderr,
    )
    sys.exit(1)


def interactive_confirm(step_name: str, description: str) -> bool:
    """Print step description and wait for 'confirm' from stdin."""
    print(f"\n[STEP] {step_name}: {description}", file=sys.stderr)
    print("Type 'confirm' to proceed (or press Enter to skip): ", file=sys.stderr, end="")
    sys.stderr.flush()
    try:
        user_input = input().strip().lower()
        return user_input == "confirm"
    except (EOFError, KeyboardInterrupt):
        return False
