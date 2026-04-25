"""
翰林院知识审计 - 请求日志 + 定时报表
Hanlin Knowledge Audit - Request Logging & Periodic Reports

功能：
  1. 记录每次知识检索（谁查了什么、花了多少 token）
  2. 每 2 小时出一份汇总报表
  3. 支持导出 JSON / 文本
"""

import json
import time
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class KnowledgeRequest:
    """单次知识请求记录"""
    timestamp: float
    requester_id: str          # 请求者（哪个节点）
    requester_name: str
    query: str                 # 查询内容
    source: str                # 知识源（tencent_cloud / feishu / notion / local_rag）
    results_count: int         # 返回结果数
    top_score: float           # 最高相关度
    tokens_input: int = 0      # 输入 token
    tokens_output: int = 0     # 输出 token
    tokens_total: int = 0      # 总 token
    elapsed_ms: int = 0        # 耗时 ms


class KnowledgeAudit:
    """翰林院知识审计"""

    def __init__(self, log_dir: str = "./data/audit"):
        self.log_dir = log_dir
        self.requests: list[KnowledgeRequest] = []
        self._report_interval = 7200  # 2 小时 = 7200 秒
        self._last_report_time = time.time()
        os.makedirs(log_dir, exist_ok=True)

    def log(self, request: KnowledgeRequest):
        """记录一次知识请求"""
        self.requests.append(request)

    def log_search(self, requester_id: str, requester_name: str,
                   query: str, source: str, results_count: int,
                   top_score: float, tokens: int = 0,
                   elapsed_ms: int = 0):
        """便捷记录方法"""
        self.requests.append(KnowledgeRequest(
            timestamp=time.time(),
            requester_id=requester_id,
            requester_name=requester_name,
            query=query[:200],
            source=source,
            results_count=results_count,
            top_score=top_score,
            tokens_input=tokens,
            tokens_total=tokens,
            elapsed_ms=elapsed_ms,
        ))

    def generate_report(self, period_seconds: int = 7200) -> dict:
        """
        生成审计报表
        默认统计最近 2 小时的数据
        """
        now = time.time()
        cutoff = now - period_seconds
        recent = [r for r in self.requests if r.timestamp >= cutoff]

        # 按请求者聚合
        by_requester = {}
        for r in recent:
            key = r.requester_id
            if key not in by_requester:
                by_requester[key] = {
                    "name": r.requester_name,
                    "request_count": 0,
                    "total_tokens": 0,
                    "sources_used": set(),
                    "queries": [],
                }
            by_requester[key]["request_count"] += 1
            by_requester[key]["total_tokens"] += r.tokens_total
            by_requester[key]["sources_used"].add(r.source)
            by_requester[key]["queries"].append({
                "query": r.query[:100],
                "source": r.source,
                "tokens": r.tokens_total,
                "results": r.results_count,
                "score": r.top_score,
                "time": time.strftime("%H:%M:%S", time.localtime(r.timestamp)),
            })

        # set → list（JSON 序列化）
        for v in by_requester.values():
            v["sources_used"] = sorted(v["sources_used"])

        # 按知识源聚合
        by_source = {}
        for r in recent:
            key = r.source
            if key not in by_source:
                by_source[key] = {"request_count": 0, "total_tokens": 0}
            by_source[key]["request_count"] += 1
            by_source[key]["total_tokens"] += r.tokens_total

        # 总计
        total_tokens = sum(r.tokens_total for r in recent)
        total_requests = len(recent)

        report = {
            "report_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "period": f"{period_seconds // 3600}h",
            "summary": {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "avg_tokens_per_request": round(total_tokens / max(total_requests, 1), 1),
                "unique_requesters": len(by_requester),
                "sources_used": sorted(by_source.keys()),
            },
            "by_requester": by_requester,
            "by_source": by_source,
        }

        self._last_report_time = now
        return report

    def format_report_text(self, report: dict) -> str:
        """格式化为可读文本"""
        lines = []
        s = report["summary"]
        lines.append(f"{'═' * 55}")
        lines.append(f"  翰林院知识审计报表  {report['report_time']}")
        lines.append(f"  统计周期: {report['period']}")
        lines.append(f"{'─' * 55}")
        lines.append(f"  总请求数: {s['total_requests']}")
        lines.append(f"  总 Token: {s['total_tokens']}")
        lines.append(f"  平均 Token/请求: {s['avg_tokens_per_request']}")
        lines.append(f"  请求节点数: {s['unique_requesters']}")
        lines.append(f"{'─' * 55}")

        # 按请求者
        lines.append(f"\n  📋 各节点请求明细:")
        for rid, info in report["by_requester"].items():
            lines.append(f"\n  🔸 {info['name']} ({rid})")
            lines.append(f"     请求数: {info['request_count']}  总Token: {info['total_tokens']}")
            lines.append(f"     使用知识源: {', '.join(info['sources_used'])}")
            lines.append(f"     最近请求:")
            for q in info["queries"][-5:]:  # 最近 5 条
                lines.append(f"       [{q['time']}] {q['query']}")
                lines.append(f"         → 源:{q['source']} 结果:{q['results']} 分数:{q['score']} Token:{q['tokens']}")

        # 按知识源
        lines.append(f"\n  📊 各知识源统计:")
        for source, info in report["by_source"].items():
            lines.append(f"     {source:16s}  请求:{info['request_count']:4d}  Token:{info['total_tokens']:6d}")

        lines.append(f"{'═' * 55}")
        return "\n".join(lines)

    def save_report(self, report: dict):
        """保存报表到文件"""
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.log_dir, f"report_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return path

    def should_report(self) -> bool:
        """是否到了出报表的时间"""
        return (time.time() - self._last_report_time) >= self._report_interval

    def get_pending_summary(self) -> str:
        """快速获取待报告期间的摘要（不生成完整报表）"""
        cutoff = time.time() - self._report_interval
        recent = [r for r in self.requests if r.timestamp >= cutoff]
        if not recent:
            return "翰林院：过去 2 小时无知识请求。"
        total = sum(r.tokens_total for r in recent)
        return f"翰林院：过去 2 小时 {len(recent)} 次请求，共消耗 {total} token。"
