#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


# Internal affect axes are converted to positive interaction axes before they
# reach the default host contract.
STATE_DIMS = ("urgency", "frustration", "clarity", "satisfaction", "trust", "engagement")
INTERACTION_DIMS = ("clarity", "trust", "engagement")
EMOTION_DIMS = ("urgency", "frustration", "confusion", "skepticism", "satisfaction", "cautiousness", "openness")
DIMS = STATE_DIMS
DEFAULT_BASELINE = {
    "response_delay_seconds": 35.0,
    "politeness": 0.2,
    "terseness": 0.35,
    "punctuation": 0.15,
    "directness": 0.3,
}
DEFAULT_PERSONA_TRAITS = {
    "patience": 0.5,
    "skepticism": 0.35,
    "caution": 0.35,
    "openness": 0.5,
    "assertiveness": 0.4,
}
SCHEMA_VERSION = "1.2.0"
MAX_DEGRADATION_REASONS = 32
LABEL_ORDER = ("urgent", "frustrated", "confused", "skeptical", "cautious", "exploratory", "satisfied", "neutral")
LABEL_ORDER_INDEX = {label: index for index, label in enumerate(LABEL_ORDER)}
STATE_SHIFT_ALIASES = {
    "rising_frustration": "needs_concrete_unblock",
    "rising_urgency": "needs_priority_action",
    "falling_trust": "needs_evidence_first",
    "falling_clarity": "needs_alignment_check",
    "rising_satisfaction": "ready_for_closeout",
    "satisfaction_drop": "needs_stabilization",
    "changed": "needs_recheck",
    "stable": "stable",
    "new_turn": "new_turn",
}
ROUTE_REASON_ENUM = {
    "runtime_priority",
    "urgent_pressure",
    "repeat_failure_pressure",
    "evidence_requested",
    "scope_guard_requested",
    "low_clarity",
    "post_success_guard",
    "stall_risk",
    "needs_concrete_unblock",
    "needs_priority_action",
    "needs_evidence_first",
    "needs_alignment_check",
    "needs_stabilization",
    "ready_for_closeout",
    "task_specific",
}
RAW_HOST_CAPABILITY_KEYS = ("include_raw_emotion", "include_internal_diagnostics")

ANGER_TERMS = {
    "气死", "烦", "垃圾", "离谱", "扯", "蠢", "废物", "火大", "崩溃", "受不了", "妈的",
    "shit", "stupid", "wtf", "damn", "useless", "annoying",
}
URGENCY_TERMS = {
    "快", "赶紧", "立刻", "马上", "现在", "别停", "直接", "先处理",
    "asap", "urgent", "immediately", "right now", "hurry", "prioritize this", "high urgency",
    "pick up where you left off", "progress feedback", "blocks my workflow",
}
SOFT_URGENCY_TERMS = {"for several minutes", "forty minutes"}
RUSH_TYPO_TERMS = {
    "pls", "plz", "plss", "urgnt", "stcuk", "brokn", "fixx", "fiex", "hlp", "tmrw", "rn",
    "w我", "n你", "t他", "d的", "b不",
}
TEXTISM_TERMS = {
    "idk", "imo", "imho", "tbh", "btw", "rn", "irl", "afaik", "fyi", "asap", "lol", "lmao",
    "u", "ur", "tho", "bc", "cuz", "pls", "plz", "tmrw",
}
NONSTANDARD_SPELLING_TERMS = {
    "gonna", "wanna", "gotta", "lemme", "kinda", "sorta", "ain't", "ya", "tho", "cuz",
    "brokn", "stcuk", "fiex", "fixx", "teh", "thx", "sry",
}
FRUSTRATION_TERMS = {
    "还没好", "还没修好", "还在", "还是这个", "同一个问题", "重复", "又坏了", "又挂了", "反复", "几轮",
    "卡了很久", "没反应", "卡死", "卡住", "死循环", "修了又坏",
    "忽略规则", "加回归", "又重定向回来", "fix-one-break-one", "ignored the rules again", "added regressions", "worked yesterday", "broke it today",
    "still not fixed", "still broken", "same issue", "same error", "again", "reoccurred",
    "keeps breaking", "endless", "time sink", "not this error", "stops responding", "bug-fixing loops",
    "cannot use it", "cannot use it at all", "burned cpu", "comes back tomorrow", "back tomorrow", "fails silently",
    "stop doubting", "stop blaming previous sessions", "wasted time", "redirected back", "sign in again", "goes quiet", "disappears again",
    "resets itself", "drops the earlier context", "interrupt mid-response", "core workflow break", "workflow break",
    "crawls", "no retry logic", "no append mode", "no error handling", "reminder disappears", "failed renames",
    "disappears right after the notification", "dead state", "tool result missing", "tool_result missing", "sign-in loop", "activation loop",
    "silently broke for days", "nobody noticed", "shared context", "painfully slow", "feels broken", "file handling is wrong",
    "sit there forever", "return an error", "return anything", "silent hang", "silent hangs", "wasting time",
    "pass locally but fail ci", "freezes when i ask", "forty minutes and nothing", "stuck in a loop",
    "feels worse", "damaged project files", "harder to trust", "brick a working install",
    "say so", "one thing i need it for", "health monitor gets stuck", "everything is silent",
    "defeats the whole point", "defeats the whole point of automated workflows", "trigger path stays silent",
    "same failure", "already tried", "same error again", "still will not activate", "already paid",
    "does not execute", "heartbeat simply does not execute", "blocks my workflow", "cannot see them",
    "progress feedback", "hanging on the same step", "silent failure on every hook", "generic reinstall",
    "not another generic reinstall", "created a new file from scratch", "instead of modifying the existing one",
    "what exactly is blocking",
}
STALL_TERMS = {
    "卡住", "卡死", "没反应", "一直转", "卡这", "hang", "hung", "stuck", "stall",
    "spinner", "loading", "timeout", "no response", "stops responding",
    "for hours", "activating for hours", "activating", "cannot use", "hangs installing", "installing packages for hours", "fails silently",
    "freeze", "freezes", "freezing", "sit there forever", "silent hang", "silent hangs", "minutes and nothing",
}
CONFUSION_TERMS = {
    "啥情况", "不懂", "看不懂", "迷糊", "不知道", "不清楚", "分不清", "到底哪里", "哪一步",
    "confused", "unclear", "cannot tell", "can't tell", "not sure which", "which one", "what exactly is wrong",
    "logged in but", "resets itself", "drops the earlier context", "interrupt mid-response", "path resolution", "quoting", "escaping",
    "what that thing was", "no idea what that thing was", "special character handling", "dies here",
    "nothing changes", "get redirected back", "what exactly is blocking", "exact failing step",
    "token fetch fails after login",
}
SATISFACTION_TERMS = {
    "好了", "可以", "不错", "满意", "谢谢", "太好了", "解决了",
    "great", "nice", "works", "solved", "thanks", "good",
}
CONTINUE_TERMS = {
    "继续", "接着", "补完", "收尾", "剩下", "继续推进",
    "continue", "keep going", "finish the rest", "wrap the rest", "next",
}
BLOCKING_TERMS = {
    "阻塞", "卡住发布", "卡住我今天的发布", "发布", "上线", "卡住进度",
    "blocking", "blocked", "blocks productive use", "severely impacts", "regression", "ship today", "release",
    "core workflow break", "workflow break", "cannot use the extension", "stuck in a loop", "kills the core workflow",
    "blocks my workflow", "blocks workflow", "cannot see them",
}
CAUTION_TERMS = {
    "小心", "稳一点", "谨慎", "别搞砸", "不要搞砸", "千万别", "别出事", "别弄坏", "注意边界",
    "护栏", "保护文件", "稳定路径", "降级路径", "迁移说明", "回滚", "guardrail", "guardrails",
    "careful", "be careful", "don't break", "do not break", "safely", "stable path", "protected files", "downgrade path", "migration note", "rollback",
    "handle the error gracefully", "recover safely", "wipe my setup", "session exposure path", "recover from bad tool calls", "bad tool calls",
    "keep the architecture modular", "architecture modular", "one method", "keep the handoff path scoped", "handoff path scoped",
    "missing tool result", "silently ending the turn",
}
BOUNDARY_TERMS = {
    "只改", "只动", "只碰", "别碰", "不要动", "不能动", "不可改", "先别动", "不要删", "别删",
    "保护文件", "repo-wide changes", "任何破坏性操作", "destructive", "before any more edits", "before another change",
    "only change", "touch only", "leave it alone", "do not touch", "must not change", "keep within", "anything destructive",
    "before i wipe my setup", "session exposure path", "show the plan before another change", "keep the handoff path scoped", "architecture modular", "one method",
}
ASSURANCE_TERMS = {
    "验证", "确认", "检查一下", "过一遍", "保险一点", "稳一点", "最稳", "保守一点",
    "verify", "verify first", "double check", "check first", "safest", "safe path", "conservative",
    "check that path", "before another workaround", "before telling me to", "精确定位", "失败路径", "show the plan", "exact failing step", "exact failing point", "failure path",
    "handle the error gracefully", "recover safely", "before i wipe my setup", "session exposure path", "recover from bad tool calls", "bad tool calls", "scan the file",
    "show the plan before another change", "keep the handoff path scoped", "exact detection path",
    "missing tool result", "silently ending the turn",
}
SKEPTICISM_TERMS = {
    "你确定", "确定吗", "真的吗", "靠谱吗", "有把握吗", "凭什么", "依据", "证据", "给我证据",
    "怎么证明", "别瞎猜", "别脑补", "别自作主张", "别拍脑袋", "先证明", "误导", "配置明明对", "根因",
    "截图", "用户报告", "用户都说了", "先看你自己的代码", "失败路径", "精确步骤", "精确失败点", "别再盲修", "不信任",
    "despite correct configuration", "without warning", "misleading", "working perfectly yesterday",
    "are you sure", "how do you know", "based on what", "show me", "evidence", "proof", "prove", "cite", "root cause", "exact root cause",
    "source", "don't guess", "stop guessing", "back it up", "despite", "misleading error",
    "generic auth advice", "check that path", "before another workaround", "before telling me to",
    "screenshot", "clear evidence", "user report", "user reports", "doubting the report", "doubt the report", "trust the user report", "check your own code",
    "exact failing step", "exact failing point", "failure path", "real failure", "show the plan", "show your limits",
    "do not trust", "don't trust", "trust it with", "which setting", "what changed", "show what changed",
    "do not tell me it is gone", "comes back tomorrow", "failure mode", "surface the failure clearly",
    "without respecting the plan", "worked yesterday", "先说依据", "reminder disappears",
    "missing tool result", "tool result", "tool_result", "dead state", "shared context", "path handling", "file path",
    "special character handling", "path resolution", "quoting", "escaping", "ground the answer in the repo",
    "ground the answer in the codebase", "blind assumption", "monitoring failed", "nobody noticed", "no alert",
    "ci rules", "pass locally but fail ci", "wasting time", "session exposure path", "what the session layer misses", "file handling is wrong",
    "harder to trust", "reliable fix", "feedback when commands fail", "automatic execution never fires", "hooks work manually", "wsl", "silent hangs are useless", "blind patch",
    "correct git bash configuration", "git bash configuration", "health monitor gets stuck", "everything is silent", "say so",
    "current settings", "fixed it for some people", "compare that path with",
    "same failure", "regression still open", "why is the regression still open", "logs and configs ready",
    "generic reinstall", "not another generic reinstall", "concrete root cause",
    "created a new file from scratch", "instead of modifying the existing one",
}
SPECULATION_TERMS = {
    "猜的", "瞎猜", "脑补", "臆测", "别猜", "别编", "编的", "猜出来", "靠猜", "乱猜",
    "guesswork", "speculation", "speculating", "speculative", "guessed the rest", "guessing the rest",
    "unchecked assumptions", "assumption", "assumptions", "fabricated", "made up", "hallucinated",
    "only analyzed", "fraction of the codebase", "part of the codebase", "part of the repo",
    "based on assumptions", "stop speculating", "repo-grounded", "grounded in the repo",
    "guess wrong", "guessing again", "keep guessing", "ungrounded", "blind assumption", "guessing my ci rules",
    "ground the answer in the repo", "ground the answer in the codebase",
}
CONTEXT_LOSS_TERMS = {
    "丢上下文", "上下文丢了", "忘了规则", "忘了之前", "像新会话", "重新开始", "记不住", "会话断了",
    "lost context", "loses context", "context loss", "drops continuity", "conversational thread", "starts fresh",
    "fresh session", "forgets this rule", "forgets my rules", "forgets everything", "no memory of the previous session",
    "fallback workspace", "agent_home", "no prior session workspace", "context plumbing", "projectid = null",
    "workspaceid = null", "actual dialogue just vanishes", "dialogue just vanishes",
    "previous session", "previous sessions", "stayed idle", "held off", "nothing changed in this session", "nothing changes", "get redirected back",
    "forgot the edits", "forgot edits", "survived compaction",
    "drops the earlier context", "interrupt mid-response", "shared context",
}
EXECUTION_PLUMBING_TERMS = {
    "不执行", "忽略参数", "网关超时", "一直超时", "看起来健康", "连上了但没事件",
    "doesn't execute", "doesnt execute", "never executes", "ignores parameters", "ignores isolatedsession",
    "ignores lightcontext", "zero inbound events", "no inbound events", "receives zero inbound events",
    "stale-socket", "stale socket", "gateway timeout", "timeout after 30000ms", "connected but receives nothing",
    "then silence", "no cron/jobs.json file", "action send requires a target", "gateway healthy", "cron status --json",
    "cron list --json", "health monitor restarts", "socket connected", "still no events", "tool_result", "tool result",
    "tool_use", "missing tool result", "non-existent tool", "dead state", "ci rules", "pass locally but fail ci",
    "wsl2", "wsl", "session exposure path", "sign in again", "config page resets", "logged in but",
    "automatic execution never fires", "hooks work manually", "trigger path", "automated workflows",
    "does not execute", "heartbeat simply does not execute", "isolatedsession", "lightcontext",
    "ai session cannot see", "cannot see them",
}
HEDGE_TERMS = {
    "不一定", "未必", "可能", "也许", "大概", "应该", "恐怕", "我怀疑", "我觉得未必", "我不太认同",
    "maybe", "perhaps", "probably", "might", "i guess", "i suspect", "not sure", "unsure", "i doubt",
}
DISMISSIVE_TERMS = {
    "行吧", "算了", "呵", "随便", "你继续", "行。", "哦。", "好吧", "fine.", "sure...", "whatever",
    "again?", "i guess", "fine then", "right...", "sure.", "okay...", "still broken",
}
PRAISE_TERMS = {"牛", "厉害", "优秀", "赞", "棒", "great", "perfect", "excellent", "well done"}
POLITE_TERMS = {"请", "麻烦", "辛苦", "谢谢", "拜托", "please", "thanks", "thank you"}
EXPLORATION_TERMS = {
    "想法", "方案", "架构", "设计", "比较", "发散", "可行性", "取舍", "建议", "方向", "思路",
    "两个方案", "两种方案", "两条路径", "两种方式", "两个方向", "对比", "差异", "最短修复路径",
    "brainstorm", "options", "tradeoff", "tradeoffs", "design", "architecture", "compare", "compare against", "compare both", "compare the two paths",
    "feasibility", "suggest", "direction", "directions", "ideas", "two ways", "two paths", "two options", "differences", "what changed", "shortest fix path", "which path",
    "pick one stable path", "logs and configs ready",
}
COMMAND_TERMS = {"修", "改", "做", "上", "给我", "继续", "直接", "fix", "ship", "do it", "change", "implement", "patch"}
VAGUE_TERMS = {"随便", "差不多", "大概", "something", "whatever", "somehow"}
TASK_OBJECT_TERMS = {
    "问题", "文件", "配置", "流程", "主流程", "接口", "线程", "路由", "权限", "根因", "路径", "发布", "用例",
    "issue", "error", "file", "config", "configuration", "flow", "main flow", "interface", "thread", "router", "path", "release", "case", "test", "build", "root cause",
    "extension", "remote ssh", "ssh", "auth", "cron job", "packages", "tool result", "tool_use", "dead state",
    "shared context", "codebase", "repo", "file path", "special character", "path resolution", "quoting", "escaping",
    "activation", "sign-in", "login", "monitoring", "alert", "notification",
    "ci", "wsl2", "wsl", "session exposure", "file handling",
}
SUCCESS_TERMS = {
    "完成", "成功", "通过", "跑通", "通了", "稳了", "搞定", "done", "fixed", "resolved", "green", "passed", "works now", "working now",
}
GUARD_TERMS = {"收口", "守住", "稳住", "防漂移", "防回归", "guard", "stabilize", "lock it", "smoke check"}
MISSED_EXPECTATION_TERMS = {
    "来不及", "错过了", "晚了", "太晚了", "又晚了", "没提醒", "提醒没来", "没告警", "静默失败", "没有任何提醒", "什么都没发生",
    "too late", "missed it", "came late", "fired late", "never fired", "never fires", "never came", "no alert", "no notification",
    "silent failure", "stays silent", "nothing happened", "should have fired", "should have run", "was supposed to alert", "showed up late", "works manually",
    "goes quiet", "too quiet", "no alert at all", "manual refresh", "suddenly appears", "running but nothing works", "overdue",
    "reminder disappears", "disappears right after the notification", "resets itself", "core workflow break", "failed renames",
    "silently broke for days", "nobody noticed", "return an error", "return anything", "feedback when commands fail",
    "say so", "everything is silent", "health monitor gets stuck", "reopen the app", "defeats the whole point", "trigger path stays silent",
}
TECHNICAL_TERMS = {
    "bug", "traceback", "stack", "stacktrace", "api", "hook", "plugin", "queue", "thread", "prompt",
    "workflow", "agent", "router", "mcp", "session", "heartbeat", "schema", "deploy", "cron", "logs",
    "test", "tests", "failing", "报错", "线程", "路由", "工作流", "接口", "脚本", "配置", "回归", "日志", "测试", "错误",
    "tool result", "tool_result", "tool_use", "shared context", "codebase", "repo", "file path", "path resolution", "quoting", "escaping",
    "ci", "wsl2",
}

PUNCT_RUN_PATTERN = re.compile(r"[!?！？]{2,}|\.{3,}|…{2,}|。{2,}")
LATIN_ELONGATION_PATTERN = re.compile(r"([A-Za-z])\1{2,}")
CJK_ELONGATION_PATTERN = re.compile(r"([\u4e00-\u9fff])\1{1,}")
MIXED_SCRIPT_PATTERN = re.compile(r"[A-Za-z][\u4e00-\u9fff]|[\u4e00-\u9fff][A-Za-z]")
NO_SPACE_PUNCT_PATTERN = re.compile(r"[,;:!?](?=[A-Za-z])")
SPACED_DOTS_PATTERN = re.compile(r"(?:\.\s){2,}\.")
DOUBLE_DOT_PATTERN = re.compile(r"(?<!\.)\.\.(?!\.)")
HALF_SENTENCE_CUT_PATTERN = re.compile(r"[,，、;；:：\-—/]\s*$")
CASE_SHIFT_PATTERN = re.compile(r"[a-z][A-Z]|[A-Z]{3,}[a-z]{2,}|[a-z]{3,}[A-Z]{2,}")
TOKEN_REPEAT_PATTERN = re.compile(r"\b([A-Za-z]+|[\u4e00-\u9fff]{1,4})\b(?:\s+\1\b){1,}", re.IGNORECASE)
ABRUPT_EN_PATTERN = re.compile(r"^\s*(ok(?:ay)?|fine|sure|right|great|good|thanks)\.\s*$", re.IGNORECASE)
ABRUPT_ZH_PATTERN = re.compile(r"^\s*(行|好|可以|收到|知道了|嗯|哦)[。\.]\s*$")
SOFT_CORRECTION_PATTERN = re.compile(r"(但|但是|不过|只是|然而|but|however|though|yet)", re.IGNORECASE)
EVIDENCE_REQUEST_PATTERN = re.compile(
    r"(exact failing (?:step|point)|failure path|failing step|failing point|real failure|show (?:me )?(?:what changed|the plan|your limits)|"
    r"which setting|what changed|exact basis|missing tool result|tool_result|shared context|file path|special character handling|path resolution|"
    r"quoting|escaping|session exposure path|detection path|exact detection path|what the session layer misses|scan the file|why it dies here|ground the answer in the (?:repo|codebase)|给我依据|先给依据|先说依据|失败路径|精确步骤|精确失败点|具体哪一步|surface the failure clearly)",
    re.IGNORECASE,
)
COMPARISON_REQUEST_PATTERN = re.compile(
    r"(two ways|two paths|two options|compare (?:the )?(?:two )?(?:paths|options|versions|approaches)|compare .* against|"
    r"compare .* with|compare (?:that|this|the )?path with|pick one stable path|difference|differences|tradeoffs?|what changed|downgrade path|migration note|shortest fix path|which path|"
    r"两个方案|两种方案|两条路径|两种方式|最短修复路径|"
    r"两个方向|对比|比较一下|取舍|差异)",
    re.IGNORECASE,
)
GUARDRAIL_REQUEST_PATTERN = re.compile(
    r"(stable path|guardrails?|protected files?|before another change|before any more edits|repo-wide changes|anything destructive|"
    r"destructive|scope tight|keep the scope tight|verify (?:that|the)? path|downgrade path|migration note|shortest fix path|只改|别碰|保护文件|"
    r"稳定路径|护栏|回滚|降级路径|迁移说明|先验证|再动手|handle the error gracefully|recover safely|before i wipe my setup|session exposure path|"
    r"show the plan before another change|keep the handoff path scoped|keep the architecture modular|architecture modular|one method)",
    re.IGNORECASE,
)
EXPLICIT_CONFUSION_PATTERN = re.compile(
    r"(confused|unclear|cannot tell|can't tell|not sure which|what exactly is wrong|what exactly is blocking|exact failing step|which state|which one|what that thing was|no idea what that thing was|why it dies here|dies here|迷糊|为什么会这样|不清楚|不知道|看不懂|分不清|到底哪里|哪一步)",
    re.IGNORECASE,
)
CLAIMED_RESOLUTION_PATTERN = re.compile(r"(fixed|resolved|done|solved|passed|green|works now|好了|解决了|完成了|跑通了|通过|通过了)")
STILL_BROKEN_PATTERN = re.compile(
    r"(still (?:not fixed|broken|happening)|same (?:issue|error)|keeps? breaking|stuck|hang(?:s|ing)?|stop(?:s)? responding|not this error|"
    r"comes back tomorrow|still comes back|还没好|还没修好|还是这个|同一个问题|卡住|卡死|没反应|一直转|又坏了)"
)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return low
    if not math.isfinite(number):
        return low
    return max(low, min(high, number))


def load_json_file(path: str | None) -> Any:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON input file not found: {file_path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def require_json_object(value: Any, source: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    value_type = type(value).__name__
    raise ValueError(f"Top-level JSON object required: {source} got {value_type}")


def dump_json(data: Any, pretty: bool) -> str:
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(text)
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_language(text: str) -> str:
    return "zh" if re.search(r"[\u4e00-\u9fff]", text or "") else "en"


def count_terms(text: str, terms: set[str]) -> int:
    norm = normalize_text(text)
    return sum(1 for term in terms if term in norm)


def count_token_terms(text: str, terms: set[str]) -> int:
    norm = normalize_text(text)
    tokens = re.findall(r"[a-z']+|[\u4e00-\u9fff]+", norm)
    return sum(1 for token in tokens if token in terms)


def count_hybrid_terms(text: str, terms: set[str]) -> int:
    norm = normalize_text(text)
    compact_norm = norm.replace(" ", "")
    tokens = set(re.findall(r"[a-z']+|[\u4e00-\u9fff]+", norm))
    hits = 0
    for term in terms:
        term_norm = normalize_text(term)
        if re.fullmatch(r"[a-z']+", term_norm):
            hits += 1 if term_norm in tokens else 0
        else:
            compact_term = term_norm.replace(" ", "")
            hits += 1 if term_norm in norm or compact_term in compact_norm else 0
    return hits


def ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def unique_labels(labels: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for label in labels:
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


def intensity_band(score: float) -> str:
    if score >= 0.75:
        return "dominant"
    if score >= 0.55:
        return "strong"
    if score >= 0.3:
        return "present"
    return "background"


def normalized_label_set(labels: list[str]) -> set[str]:
    raw = {str(label) for label in labels if str(label).strip()}
    if not raw:
        return set()
    trimmed = {label for label in raw if label != "neutral"}
    return trimmed or raw


def label_overlap_score(labels_a: list[str], labels_b: list[str]) -> float:
    set_a = normalized_label_set(labels_a)
    set_b = normalized_label_set(labels_b)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return round(clamp(len(set_a & set_b) / len(set_a | set_b)), 4)


def vector_alignment_score(vector_a: dict[str, Any], vector_b: dict[str, Any], dims: tuple[str, ...]) -> float:
    if not vector_a or not vector_b:
        return 0.0
    diff = 0.0
    for dim in dims:
        diff += abs(float(vector_a.get(dim, 0.0)) - float(vector_b.get(dim, 0.0)))
    return round(clamp(1.0 - (diff / max(len(dims), 1))), 4)


def dominant_axes(vector: dict[str, Any], dims: tuple[str, ...], top_n: int = 2, floor: float = 0.32) -> set[str]:
    ranked = sorted(((dim, float(vector.get(dim, 0.0))) for dim in dims), key=lambda item: item[1], reverse=True)
    picked = [dim for dim, value in ranked[:top_n] if value >= floor]
    return set(picked)


def axis_overlap_score(vector_a: dict[str, Any], vector_b: dict[str, Any], dims: tuple[str, ...]) -> float:
    axes_a = dominant_axes(vector_a, dims)
    axes_b = dominant_axes(vector_b, dims)
    if not axes_a and not axes_b:
        return 1.0
    if not axes_a or not axes_b:
        return 0.0
    return round(clamp(len(axes_a & axes_b) / len(axes_a | axes_b)), 4)


def clamp_dict(raw: Any, keys: tuple[str, ...], defaults: dict[str, float] | None = None) -> dict[str, float]:
    base = {key: clamp(float((defaults or {}).get(key, 0.0))) for key in keys}
    if not isinstance(raw, dict):
        return base
    for key in keys:
        if key in raw and raw[key] is not None:
            try:
                base[key] = clamp(float(raw[key]))
            except (TypeError, ValueError):
                continue
    return base


def mark_degraded(diagnostics: dict[str, Any], reason: str) -> None:
    reasons = diagnostics.setdefault("degradation_reasons", [])
    if reason not in reasons:
        reasons.append(reason)
    diagnostics["degraded"] = True


def as_mapping(value: Any, diagnostics: dict[str, Any], reason: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                mark_degraded(diagnostics, reason)
                return {}
            if isinstance(parsed, dict):
                mark_degraded(diagnostics, f"{reason}.parsed_from_json_string")
                return parsed
    mark_degraded(diagnostics, reason)
    return {}


def normalize_string_list(value: Any, diagnostics: dict[str, Any], reason: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        mark_degraded(diagnostics, reason)
        return []
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            mark_degraded(diagnostics, f"{reason}.contains_non_string")
            continue
        text = item.strip()
        if text:
            result.append(text)
    return result


def canonicalize_labels(labels: list[str]) -> list[str]:
    ordered = unique_labels([str(label).strip() for label in labels if str(label).strip()])
    return sorted(ordered, key=lambda label: (LABEL_ORDER_INDEX.get(label, len(LABEL_ORDER_INDEX)), label))


def normalize_history(value: Any, diagnostics: dict[str, Any]) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        mark_degraded(diagnostics, "history_not_list")
        return []
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            mark_degraded(diagnostics, f"history_item_{index}_not_mapping")
            continue
        role = item.get("role", "")
        if role is None:
            role = ""
        elif not isinstance(role, str):
            mark_degraded(diagnostics, f"history_item_{index}_role_not_string")
            role = str(role) if isinstance(role, (int, float, bool)) else ""
        text = item.get("text")
        if text is None:
            text = item.get("content")
        if text is None:
            text = ""
        elif not isinstance(text, str):
            mark_degraded(diagnostics, f"history_item_{index}_text_not_string")
            text = str(text) if isinstance(text, (int, float, bool)) else ""
        if not role and not text:
            continue
        normalized.append({
            "role": role.strip(),
            "text": text,
        })
    return normalized


def finalize_degradation_reasons(diagnostics: dict[str, Any]) -> list[str]:
    reasons = unique_labels([str(reason).strip() for reason in diagnostics.get("degradation_reasons", []) if str(reason).strip()])
    if len(reasons) > MAX_DEGRADATION_REASONS:
        overflow = len(reasons) - (MAX_DEGRADATION_REASONS - 2)
        reasons = reasons[: MAX_DEGRADATION_REASONS - 2] + ["degradation_reasons_truncated", f"...+{overflow} more"]
    diagnostics["degradation_reasons"] = reasons
    diagnostics["degraded"] = bool(reasons) or bool(diagnostics.get("degraded"))
    return reasons


def normalize_payload(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    diagnostics: dict[str, Any] = {"degraded": False, "degradation_reasons": []}
    if not isinstance(payload, dict):
        mark_degraded(diagnostics, "payload_not_mapping")
        payload = {}
    normalized = dict(payload)
    message = normalized.get("message", "")
    if message is None:
        message = ""
    elif not isinstance(message, str):
        mark_degraded(diagnostics, "message_coerced_to_string")
        message = str(message)
    normalized["message"] = message
    normalized["context"] = as_mapping(normalized.get("context"), diagnostics, "context_not_mapping")
    normalized["runtime"] = as_mapping(normalized.get("runtime"), diagnostics, "runtime_not_mapping")
    user_profile = as_mapping(normalized.get("user_profile"), diagnostics, "user_profile_not_mapping")
    if user_profile:
        user_profile = dict(user_profile)
        user_profile["baseline"] = as_mapping(user_profile.get("baseline"), diagnostics, "user_profile.baseline_not_mapping")
        user_profile["persona_traits"] = as_mapping(user_profile.get("persona_traits"), diagnostics, "user_profile.persona_traits_not_mapping")
        user_profile["big5"] = as_mapping(user_profile.get("big5"), diagnostics, "user_profile.big5_not_mapping")
        user_profile["affective_prior"] = as_mapping(user_profile.get("affective_prior"), diagnostics, "user_profile.affective_prior_not_mapping")
    normalized["user_profile"] = user_profile
    last_state = as_mapping(normalized.get("last_state"), diagnostics, "last_state_not_mapping")
    if last_state:
        last_state = dict(last_state)
        last_state["vector"] = as_mapping(last_state.get("vector"), diagnostics, "last_state.vector_not_mapping")
        last_state["emotion_vector"] = as_mapping(last_state.get("emotion_vector"), diagnostics, "last_state.emotion_vector_not_mapping")
    normalized["last_state"] = last_state
    for key in ("llm_semantic", "review_semantic", "posthoc_semantic"):
        semantic = as_mapping(normalized.get(key), diagnostics, f"{key}_not_mapping")
        if semantic:
            semantic = dict(semantic)
            semantic["vector"] = as_mapping(semantic.get("vector"), diagnostics, f"{key}.vector_not_mapping")
            semantic["emotion_vector"] = as_mapping(semantic.get("emotion_vector"), diagnostics, f"{key}.emotion_vector_not_mapping")
            semantic["labels"] = canonicalize_labels(normalize_string_list(semantic.get("labels"), diagnostics, f"{key}.labels_not_list"))
        normalized[key] = semantic
    normalized["calibration_state"] = as_mapping(normalized.get("calibration_state"), diagnostics, "calibration_state_not_mapping")
    normalized["host_capabilities"] = as_mapping(normalized.get("host_capabilities"), diagnostics, "host_capabilities_not_mapping")
    normalized["history"] = normalize_history(normalized.get("history"), diagnostics)
    return normalized, diagnostics


def combine_named_vectors(weighted_vectors: list[tuple[dict[str, Any], float]], dims: tuple[str, ...]) -> dict[str, float]:
    """Combine partial vectors with independent per-dimension weighted averages."""
    totals = {dim: 0.0 for dim in dims}
    weight_sum = {dim: 0.0 for dim in dims}
    for vector, weight in weighted_vectors:
        if not vector or weight <= 0:
            continue
        for dim in dims:
            value = vector.get(dim)
            if value is None:
                continue
            totals[dim] += float(value) * weight
            weight_sum[dim] += weight
    result: dict[str, float] = {}
    for dim in dims:
        if weight_sum[dim] > 0:
            result[dim] = round(clamp(totals[dim] / weight_sum[dim]), 4)
        else:
            result[dim] = 0.0
    return result


def derive_persona_traits(user_profile: dict[str, Any]) -> tuple[dict[str, float], str]:
    persona_traits = clamp_dict(user_profile.get("persona_traits"), tuple(DEFAULT_PERSONA_TRAITS.keys()), DEFAULT_PERSONA_TRAITS)
    source = "default"
    big5 = clamp_dict(user_profile.get("big5"), ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"))
    if any(value > 0 for value in big5.values()):
        source = "big5"
        persona_traits = {
            "patience": round(clamp(0.42 + 0.22 * big5["agreeableness"] - 0.18 * big5["neuroticism"]), 4),
            "skepticism": round(clamp(0.14 + 0.18 * big5["conscientiousness"] + 0.12 * (1.0 - big5["agreeableness"])), 4),
            "caution": round(clamp(0.16 + 0.34 * big5["conscientiousness"] + 0.08 * big5["neuroticism"]), 4),
            "openness": round(clamp(big5["openness"]), 4),
            "assertiveness": round(clamp(0.1 + 0.8 * big5["extraversion"]), 4),
        }
    explicit_raw = user_profile.get("persona_traits")
    explicit = clamp_dict(explicit_raw, tuple(DEFAULT_PERSONA_TRAITS.keys()))
    explicit_mapping = explicit_raw if isinstance(explicit_raw, dict) else {}
    if any(value > 0 for value in explicit.values()):
        source = "persona_traits"
        persona_traits = {
            key: round(explicit[key] if key in explicit_mapping else persona_traits[key], 4)
            for key in DEFAULT_PERSONA_TRAITS
        }
    return persona_traits, source


def derive_affective_prior(user_profile: dict[str, Any], persona_traits: dict[str, float], persona_source: str) -> tuple[dict[str, float], str, float]:
    explicit_prior = clamp_dict(user_profile.get("affective_prior") or user_profile.get("background_emotion"), EMOTION_DIMS)
    if any(value > 0 for value in explicit_prior.values()):
        return explicit_prior, "explicit", 0.22
    patience = persona_traits["patience"]
    skepticism = persona_traits["skepticism"]
    caution = persona_traits["caution"]
    openness = persona_traits["openness"]
    assertiveness = persona_traits["assertiveness"]
    inferred = {
        "urgency": round(clamp(0.04 + 0.12 * (1.0 - patience) + 0.08 * assertiveness), 4),
        "frustration": round(clamp(0.03 + 0.14 * (1.0 - patience)), 4),
        "confusion": 0.04,
        "skepticism": round(clamp(0.04 + 0.26 * skepticism + 0.08 * caution), 4),
        "satisfaction": round(clamp(0.08 + 0.08 * patience), 4),
        "cautiousness": round(clamp(0.05 + 0.24 * caution), 4),
        "openness": round(clamp(0.06 + 0.24 * openness), 4),
    }
    weight = 0.1 if persona_source in {"persona_traits", "big5"} else 0.0
    return inferred, "persona_heuristic", weight


def recent_user_messages(history: list[dict[str, Any]], limit: int = 5) -> list[str]:
    messages = []
    for item in history or []:
        if str(item.get("role", "")).lower() == "user":
            text = item.get("text") or item.get("content") or ""
            if text:
                messages.append(str(text))
    return messages[-limit:]


def last_assistant_message(history: list[dict[str, Any]]) -> str:
    for item in reversed(history or []):
        if str(item.get("role", "")).lower() == "assistant":
            return str(item.get("text") or item.get("content") or "")
    return ""


def load_review_semantic(payload: dict[str, Any]) -> dict[str, Any]:
    review_semantic = payload.get("review_semantic")
    if isinstance(review_semantic, dict) and review_semantic:
        return review_semantic
    legacy_review = payload.get("posthoc_semantic")
    if isinstance(legacy_review, dict) and legacy_review:
        return legacy_review
    return {}


def max_similarity(text: str, candidates: list[str]) -> float:
    norm = normalize_text(text)
    if not norm or not candidates:
        return 0.0
    scores = [SequenceMatcher(None, norm, normalize_text(candidate)).ratio() for candidate in candidates if candidate]
    return max(scores, default=0.0)


def parse_hour_window(raw: Any) -> tuple[int, int]:
    try:
        if isinstance(raw, (list, tuple)) and len(raw) >= 2:
            start = int(raw[0])
            end = int(raw[1])
        else:
            start, end = 9, 22
    except (TypeError, ValueError):
        start, end = 9, 22
    return max(0, min(23, start)), max(0, min(23, end))


def hour_in_window(hour: int | None, start: int, end: int) -> bool | None:
    if hour is None:
        return None
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def infer_local_hour(payload: dict[str, Any], timezone_name: str | None, diagnostics: dict[str, Any]) -> int | None:
    context = payload.get("context") or {}
    runtime = payload.get("runtime") or {}
    explicit_hour = context.get("local_hour")
    if explicit_hour is None:
        explicit_hour = runtime.get("local_hour")
    if explicit_hour is not None:
        try:
            return max(0, min(23, int(explicit_hour)))
        except (TypeError, ValueError):
            mark_degraded(diagnostics, "local_hour_invalid")
            return None
    if not timezone_name:
        return None
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        mark_degraded(diagnostics, "timezone_unavailable")
        return None
    now_iso = context.get("now_iso") or runtime.get("now_iso")
    if not now_iso:
        return None
    try:
        dt = datetime.fromisoformat(str(now_iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)
        return int(dt.hour)
    except Exception:
        mark_degraded(diagnostics, "now_iso_invalid")
        return None


def load_user_profile(payload: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    user_profile = payload.get("user_profile") or {}
    baseline = as_mapping(user_profile.get("baseline"), diagnostics, "user_profile.baseline_not_mapping")
    persona_traits, persona_source = derive_persona_traits(user_profile)
    affective_prior, affective_prior_source, affective_prior_weight = derive_affective_prior(user_profile, persona_traits, persona_source)
    timezone_name = user_profile.get("timezone") or payload.get("context", {}).get("timezone")
    work_start, work_end = parse_hour_window(user_profile.get("work_hours_local") or user_profile.get("work_hours"))
    local_hour = infer_local_hour(payload, timezone_name, diagnostics)
    in_work_window = hour_in_window(local_hour, work_start, work_end)
    baseline_delay = max(12.0, float(baseline.get("response_delay_seconds", DEFAULT_BASELINE["response_delay_seconds"]) or DEFAULT_BASELINE["response_delay_seconds"]))
    baseline_politeness = clamp(float(baseline.get("politeness", DEFAULT_BASELINE["politeness"]) or DEFAULT_BASELINE["politeness"]))
    baseline_terseness = clamp(float(baseline.get("terseness", baseline.get("terse", DEFAULT_BASELINE["terseness"])) or DEFAULT_BASELINE["terseness"]))
    baseline_punctuation = clamp(float(baseline.get("punctuation", DEFAULT_BASELINE["punctuation"]) or DEFAULT_BASELINE["punctuation"]))
    baseline_directness = clamp(float(baseline.get("directness", DEFAULT_BASELINE["directness"]) or DEFAULT_BASELINE["directness"]))
    availability_multiplier = 1.35 if in_work_window is False else 1.0
    return {
        "id": user_profile.get("id", ""),
        "timezone": timezone_name or "",
        "local_hour": local_hour,
        "work_hours_local": [work_start, work_end],
        "in_work_window": in_work_window,
        "availability_multiplier": availability_multiplier,
        "baseline": {
            "response_delay_seconds": baseline_delay,
            "politeness": baseline_politeness,
            "terseness": baseline_terseness,
            "punctuation": baseline_punctuation,
            "directness": baseline_directness,
        },
        "persona_traits": persona_traits,
        "persona_source": persona_source,
        "affective_prior": affective_prior,
        "affective_prior_source": affective_prior_source,
        "affective_prior_weight": affective_prior_weight,
    }


def build_features(payload: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("message") or "")
    history = payload.get("history") or []
    runtime = payload.get("runtime") or {}
    user_profile = load_user_profile(payload, diagnostics)
    language = detect_language(message)
    norm_message = normalize_text(message)
    recent_users = recent_user_messages(history)
    previous_users = recent_users[:-1] if recent_users and normalize_text(recent_users[-1]) == norm_message else recent_users
    last_assistant = last_assistant_message(history)
    norm_last_assistant = normalize_text(last_assistant)

    chars = len(message.strip())
    words = len(re.findall(r"[A-Za-z0-9_./:-]+|[\u4e00-\u9fff]", message))
    questions = message.count("?") + message.count("？")
    exclamations = message.count("!") + message.count("！")
    ellipsis = message.count("...") + message.count("……") + message.count("…")
    uppercase_tokens = len(re.findall(r"\b[A-Z]{2,}\b", message))
    code_markers = int("```" in message or "`" in message or bool(re.search(r"\b[A-Za-z_]+\.[A-Za-z0-9_]+\b", message)))
    file_refs = len(re.findall(r"[A-Za-z0-9_./\\-]+\.[A-Za-z0-9_]+", message))
    list_markers = len(re.findall(r"\b\d+\.", message)) + len(re.findall(r"[;；、]", message))
    punctuation_runs = len(PUNCT_RUN_PATTERN.findall(message))
    latin_elongations = len(LATIN_ELONGATION_PATTERN.findall(message))
    cjk_elongations = len(CJK_ELONGATION_PATTERN.findall(message))
    mixed_script_runs = len(MIXED_SCRIPT_PATTERN.findall(message))
    no_space_punct_runs = len(NO_SPACE_PUNCT_PATTERN.findall(message))
    spaced_pause_runs = len(SPACED_DOTS_PATTERN.findall(message))
    double_dot_runs = len(DOUBLE_DOT_PATTERN.findall(message))
    case_shift_runs = len(CASE_SHIFT_PATTERN.findall(message))
    token_repeat_runs = len(TOKEN_REPEAT_PATTERN.findall(message))
    half_sentence_cut = 1.0 if HALF_SENTENCE_CUT_PATTERN.search(message) else 0.0
    abrupt_period_reply = 1.0 if (ABRUPT_EN_PATTERN.match(message) or ABRUPT_ZH_PATTERN.match(message)) else 0.0

    anger_hits = count_terms(message, ANGER_TERMS)
    urgency_hits = count_terms(message, URGENCY_TERMS)
    soft_urgency_hits = count_terms(message, SOFT_URGENCY_TERMS)
    rush_typo_hits = count_hybrid_terms(message, RUSH_TYPO_TERMS)
    textism_hits = count_token_terms(message, TEXTISM_TERMS)
    nonstandard_spelling_hits = count_token_terms(message, NONSTANDARD_SPELLING_TERMS)
    frustration_hits = count_terms(message, FRUSTRATION_TERMS)
    stall_hits = count_terms(message, STALL_TERMS)
    confusion_hits = count_terms(message, CONFUSION_TERMS)
    satisfaction_hits = count_terms(message, SATISFACTION_TERMS)
    continue_hits = count_terms(message, CONTINUE_TERMS)
    blocking_hits = count_terms(message, BLOCKING_TERMS)
    caution_hits = count_terms(message, CAUTION_TERMS)
    boundary_hits = count_terms(message, BOUNDARY_TERMS)
    assurance_hits = count_terms(message, ASSURANCE_TERMS)
    skepticism_hits = count_terms(message, SKEPTICISM_TERMS)
    speculation_hits = count_terms(message, SPECULATION_TERMS)
    context_loss_hits = count_terms(message, CONTEXT_LOSS_TERMS)
    execution_plumbing_hits = count_terms(message, EXECUTION_PLUMBING_TERMS)
    hedge_hits = count_terms(message, HEDGE_TERMS)
    dismissive_hits = count_terms(message, DISMISSIVE_TERMS)
    praise_hits = count_terms(message, PRAISE_TERMS)
    polite_hits = count_terms(message, POLITE_TERMS)
    explore_hits = count_terms(message, EXPLORATION_TERMS)
    command_hits = count_terms(message, COMMAND_TERMS)
    vague_hits = count_terms(message, VAGUE_TERMS)
    task_object_hits = count_terms(message, TASK_OBJECT_TERMS)
    success_hits = count_terms(message, SUCCESS_TERMS)
    guard_hits = count_terms(message, GUARD_TERMS)
    missed_expectation_hits = count_terms(message, MISSED_EXPECTATION_TERMS)
    technical_hits = count_terms(message, TECHNICAL_TERMS)
    evidence_request = 1.0 if EVIDENCE_REQUEST_PATTERN.search(norm_message) else 0.0
    comparison_request = 1.0 if COMPARISON_REQUEST_PATTERN.search(norm_message) else 0.0
    guardrail_request = 1.0 if GUARDRAIL_REQUEST_PATTERN.search(norm_message) else 0.0
    explicit_confusion_request = 1.0 if EXPLICIT_CONFUSION_PATTERN.search(norm_message) else 0.0
    if STILL_BROKEN_PATTERN.search(norm_message):
        success_hits = 0

    repeat_similarity = max_similarity(message, previous_users)
    short_burst = 1.0 if chars <= 18 else 0.75 if chars <= 48 else 0.35 if chars <= 120 else 0.1
    question_units = 1 if questions and confusion_hits == 0 and re.search(r"[?？]{2,}", message) else questions
    question_density = clamp(ratio(question_units, max(chars, 1)) * 22.0)
    exclamation_pressure = clamp(exclamations / 3.0)
    uppercase_pressure = clamp(uppercase_tokens / 2.0)
    vague_ratio = clamp(vague_hits / 3.0)
    technical_ratio = clamp(technical_hits / 5.0)
    command_ratio = clamp(command_hits / 3.0)
    praise_ratio = clamp((praise_hits + satisfaction_hits) / 4.0)
    polite_ratio = clamp(polite_hits / 3.0)
    explore_ratio = clamp((explore_hits + 1.3 * comparison_request) / 3.0)
    task_object_ratio = clamp(task_object_hits / 3.0)
    success_ratio = clamp(success_hits / 3.0)
    continue_ratio = clamp(continue_hits / 3.0)
    blocking_ratio = clamp(blocking_hits / 3.0)
    caution_ratio = clamp((caution_hits + 1.1 * guardrail_request) / 3.0)
    boundary_ratio = clamp((boundary_hits + 0.9 * guardrail_request) / 3.0)
    assurance_ratio = clamp((assurance_hits + 0.7 * evidence_request + 0.8 * guardrail_request) / 3.0)
    skepticism_ratio = clamp((skepticism_hits + 1.25 * evidence_request) / 3.0)
    speculation_ratio = clamp(speculation_hits / 3.0)
    context_loss_ratio = clamp(context_loss_hits / 3.0)
    execution_plumbing_ratio = clamp(execution_plumbing_hits / 3.0)
    hedge_ratio = clamp(hedge_hits / 2.0)
    dismissive_ratio = clamp(dismissive_hits / 3.0)
    textism_ratio = clamp(textism_hits / 4.0)
    nonstandard_spelling_ratio = clamp(nonstandard_spelling_hits / 4.0)
    guard_ratio = clamp(guard_hits / 3.0)
    missed_expectation_ratio = clamp(missed_expectation_hits / 3.0)
    frustration_ratio = clamp(frustration_hits / 3.0)
    stall_ratio = clamp(stall_hits / 3.0)
    soft_correction = 1.0 if SOFT_CORRECTION_PATTERN.search(message) and (hedge_hits >= 1 or skepticism_hits >= 1) else 0.0
    punctuation_pressure = clamp(
        0.36 * clamp(punctuation_runs / 2.0)
        + 0.22 * exclamation_pressure
        + 0.16 * question_density
        + 0.18 * clamp((latin_elongations + cjk_elongations) / 2.0)
        + 0.08 * clamp(ellipsis / 2.0)
    )
    tempo_pause_ratio = clamp(
        0.32 * clamp((ellipsis + spaced_pause_runs + double_dot_runs) / 3.0)
        + 0.22 * half_sentence_cut
        + 0.18 * clamp(token_repeat_runs / 2.0)
        + 0.14 * clamp(case_shift_runs / 2.0)
        + 0.14 * clamp(punctuation_runs / 2.0)
    )
    goal_specificity = clamp(
        0.3 * technical_ratio
        + 0.24 * command_ratio
        + 0.16 * task_object_ratio
        + 0.18 * clamp(file_refs / 2.0)
        + 0.12 * clamp(code_markers)
        + 0.08 * success_ratio
        + 0.08 * evidence_request
        + 0.1 * comparison_request
        + 0.1 * guardrail_request
        + 0.06 * boundary_ratio
        + 0.04 * assurance_ratio
    )
    typing_chaos = clamp(
        0.34 * clamp(rush_typo_hits / 2.0)
        + 0.26 * clamp(mixed_script_runs / 2.0)
        + 0.2 * clamp(no_space_punct_runs / 2.0)
        + 0.1 * clamp((latin_elongations + cjk_elongations) / 2.0)
        + 0.1 * short_burst
    )

    response_delay_seconds = float(runtime.get("response_delay_seconds", 0) or 0)
    unresolved_turns = float(runtime.get("unresolved_turns", 0) or 0)
    bug_retries = float(runtime.get("bug_retries", 0) or 0)
    task_age_minutes = float(runtime.get("task_age_minutes", 0) or 0)
    queue_depth = float(runtime.get("queue_depth", 0) or 0)
    background_tasks_running = float(runtime.get("background_tasks_running", 0) or 0)
    same_issue_mentions = float(runtime.get("same_issue_mentions", 0) or 0)
    contradiction_signal = clamp(float(runtime.get("contradiction_signal", 0) or 0))
    raw_last_outcome = runtime.get("last_routing_outcome")
    if raw_last_outcome is None:
        last_routing_outcome: dict[str, Any] = {}
    elif isinstance(raw_last_outcome, dict):
        last_routing_outcome = raw_last_outcome
    else:
        mark_degraded(diagnostics, "runtime.last_routing_outcome_not_mapping")
        last_routing_outcome = {}
    outcome_text = normalize_text(str(last_routing_outcome.get("user_followed_up_with") or last_routing_outcome.get("result") or ""))
    last_outcome_success = 1.0 if outcome_text in {"thanks", "works", "resolved", "success", "accepted", "done"} or CLAIMED_RESOLUTION_PATTERN.search(outcome_text) else 0.0
    last_outcome_retry = 1.0 if outcome_text in {"still broken", "same issue", "failed", "not fixed", "retry"} or STILL_BROKEN_PATTERN.search(outcome_text) else 0.0
    last_outcome_complaint = 1.0 if outcome_text in {"explicit_complaint", "complaint", "bad", "worse"} else 0.0
    resolution_claimed = 1.0 if CLAIMED_RESOLUTION_PATTERN.search(norm_last_assistant) else 0.0
    resolution_mismatch = 1.0 if resolution_claimed and STILL_BROKEN_PATTERN.search(norm_message) else 0.0

    effective_delay_budget_seconds = user_profile["baseline"]["response_delay_seconds"] * float(user_profile["availability_multiplier"])
    delay_pressure = clamp(response_delay_seconds / max(12.0, effective_delay_budget_seconds))
    stuck_pressure = clamp(
        (unresolved_turns * 0.16)
        + (bug_retries * 0.24)
        + (task_age_minutes / 75.0)
        + (same_issue_mentions * 0.18)
        + (stall_ratio * 0.14)
        + (repeat_similarity * 0.12)
        + (resolution_mismatch * 0.08)
        + (last_outcome_retry * 0.2)
        + (last_outcome_complaint * 0.16)
        - (last_outcome_success * 0.08)
    )
    if soft_urgency_hits and (delay_pressure >= 0.34 or stall_hits >= 1 or blocking_hits >= 1 or frustration_hits >= 1 or stuck_pressure >= 0.42):
        urgency_hits += soft_urgency_hits
    background_pressure = clamp((queue_depth * 0.2) + (background_tasks_running * 0.15))
    politeness_delta = clamp(polite_ratio - user_profile["baseline"]["politeness"] + 0.15)
    terseness_delta = clamp(short_burst - user_profile["baseline"]["terseness"] + 0.15)
    punctuation_delta = clamp(punctuation_pressure - user_profile["baseline"]["punctuation"] + 0.15)
    directness_delta = clamp(command_ratio - user_profile["baseline"]["directness"] + 0.15)
    abrupt_delta = clamp(abrupt_period_reply * (1.0 - 0.55 * user_profile["baseline"]["terseness"]))
    surface_signal_reliability = clamp(
        0.28 * delay_pressure
        + 0.24 * stuck_pressure
        + 0.18 * repeat_similarity
        + 0.12 * contradiction_signal
        + 0.1 * goal_specificity
        + 0.08 * blocking_ratio
        + 0.08 * context_loss_ratio
        + 0.08 * execution_plumbing_ratio
    )
    dismissive_pressure = clamp(dismissive_ratio * (0.34 + 0.66 * surface_signal_reliability))
    tempo_pause_pressure = clamp(tempo_pause_ratio * (0.38 + 0.62 * max(delay_pressure, stall_ratio, frustration_ratio, skepticism_ratio, blocking_ratio)))
    textism_pressure = clamp(
        (0.56 * textism_ratio + 0.44 * nonstandard_spelling_ratio)
        * (0.32 + 0.68 * max(delay_pressure, short_burst, clamp(urgency_hits / 2.0), directness_delta))
    )
    surface_only_pressure = clamp(0.42 * dismissive_ratio + 0.3 * textism_ratio + 0.28 * tempo_pause_ratio)
    surface_uncertainty = clamp(surface_only_pressure * (1.0 - surface_signal_reliability))

    evidence: list[str] = []
    if urgency_hits:
        evidence.append("urgency_terms")
    if frustration_hits or anger_hits:
        evidence.append("frustration_terms")
    if stall_hits:
        evidence.append("stall_terms")
    if repeat_similarity >= 0.72:
        evidence.append("repeated_user_emphasis")
    if punctuation_pressure >= 0.36:
        evidence.append("punctuation_intensity")
    if typing_chaos >= 0.32:
        evidence.append("typing_chaos")
    if dismissive_pressure >= 0.28:
        evidence.append("dismissive_cue")
    if tempo_pause_pressure >= 0.3:
        evidence.append("tempo_pause_cue")
    if textism_pressure >= 0.28:
        evidence.append("textism_cue")
    if abrupt_period_reply:
        evidence.append("abrupt_short_reply")
    if task_object_ratio >= 0.24:
        evidence.append("task_object_anchor")
    if evidence_request >= 1.0:
        evidence.append("evidence_request")
    if comparison_request >= 1.0:
        evidence.append("structured_compare")
    if delay_pressure >= 0.35:
        evidence.append("delay_pressure")
    if stuck_pressure >= 0.42:
        evidence.append("stuck_issue_pressure")
    if guardrail_request >= 1.0:
        evidence.append("guardrail_request")
    if resolution_mismatch:
        evidence.append("resolution_mismatch")
    if last_outcome_retry or last_outcome_complaint:
        evidence.append("last_routing_outcome_retry")
    if last_outcome_success:
        evidence.append("last_routing_outcome_success")
    if guard_hits:
        evidence.append("guard_terms")
    if blocking_hits:
        evidence.append("blocking_terms")
    if caution_hits or boundary_hits or assurance_hits:
        evidence.append("boundary_terms")
    if skepticism_hits or hedge_hits or contradiction_signal >= 0.34:
        evidence.append("skepticism_terms")
    if speculation_ratio >= 0.24:
        evidence.append("guesswork_terms")
    if context_loss_ratio >= 0.24:
        evidence.append("context_loss_terms")
    if execution_plumbing_ratio >= 0.24:
        evidence.append("execution_plumbing_terms")
    if missed_expectation_ratio >= 0.24:
        evidence.append("missed_expectation")
    if technical_hits:
        evidence.append("technical_context")

    return {
        "message": message,
        "language": language,
        "chars": chars,
        "words": words,
        "questions": questions,
        "exclamations": exclamations,
        "ellipsis": ellipsis,
        "uppercase_tokens": uppercase_tokens,
        "code_markers": code_markers,
        "file_refs": file_refs,
        "list_markers": list_markers,
        "punctuation_runs": punctuation_runs,
        "latin_elongations": latin_elongations,
        "cjk_elongations": cjk_elongations,
        "mixed_script_runs": mixed_script_runs,
        "no_space_punct_runs": no_space_punct_runs,
        "spaced_pause_runs": spaced_pause_runs,
        "double_dot_runs": double_dot_runs,
        "case_shift_runs": case_shift_runs,
        "token_repeat_runs": token_repeat_runs,
        "half_sentence_cut": half_sentence_cut,
        "abrupt_period_reply": abrupt_period_reply,
        "anger_hits": anger_hits,
        "urgency_hits": urgency_hits,
        "rush_typo_hits": rush_typo_hits,
        "textism_hits": textism_hits,
        "nonstandard_spelling_hits": nonstandard_spelling_hits,
        "frustration_hits": frustration_hits,
        "stall_hits": stall_hits,
        "confusion_hits": confusion_hits,
        "satisfaction_hits": satisfaction_hits,
        "continue_hits": continue_hits,
        "blocking_hits": blocking_hits,
        "caution_hits": caution_hits,
        "boundary_hits": boundary_hits,
        "assurance_hits": assurance_hits,
        "skepticism_hits": skepticism_hits,
        "speculation_hits": speculation_hits,
        "context_loss_hits": context_loss_hits,
        "execution_plumbing_hits": execution_plumbing_hits,
        "hedge_hits": hedge_hits,
        "dismissive_hits": dismissive_hits,
        "praise_hits": praise_hits,
        "polite_hits": polite_hits,
        "explore_hits": explore_hits,
        "command_hits": command_hits,
        "vague_hits": vague_hits,
        "task_object_hits": task_object_hits,
        "success_hits": success_hits,
        "guard_hits": guard_hits,
        "missed_expectation_hits": missed_expectation_hits,
        "technical_hits": technical_hits,
        "evidence_request": evidence_request,
        "comparison_request": comparison_request,
        "guardrail_request": guardrail_request,
        "explicit_confusion_request": explicit_confusion_request,
        "repeat_similarity": round(repeat_similarity, 4),
        "short_burst": short_burst,
        "question_density": round(question_density, 4),
        "exclamation_pressure": round(exclamation_pressure, 4),
        "uppercase_pressure": round(uppercase_pressure, 4),
        "vague_ratio": round(vague_ratio, 4),
        "technical_ratio": round(technical_ratio, 4),
        "command_ratio": round(command_ratio, 4),
        "praise_ratio": round(praise_ratio, 4),
        "polite_ratio": round(polite_ratio, 4),
        "politeness_delta": round(politeness_delta, 4),
        "explore_ratio": round(explore_ratio, 4),
        "task_object_ratio": round(task_object_ratio, 4),
        "success_ratio": round(success_ratio, 4),
        "continue_ratio": round(continue_ratio, 4),
        "blocking_ratio": round(blocking_ratio, 4),
        "caution_ratio": round(caution_ratio, 4),
        "boundary_ratio": round(boundary_ratio, 4),
        "assurance_ratio": round(assurance_ratio, 4),
        "skepticism_ratio": round(skepticism_ratio, 4),
        "speculation_ratio": round(speculation_ratio, 4),
        "context_loss_ratio": round(context_loss_ratio, 4),
        "execution_plumbing_ratio": round(execution_plumbing_ratio, 4),
        "hedge_ratio": round(hedge_ratio, 4),
        "dismissive_ratio": round(dismissive_ratio, 4),
        "textism_ratio": round(textism_ratio, 4),
        "nonstandard_spelling_ratio": round(nonstandard_spelling_ratio, 4),
        "guard_ratio": round(guard_ratio, 4),
        "missed_expectation_ratio": round(missed_expectation_ratio, 4),
        "frustration_ratio": round(frustration_ratio, 4),
        "stall_ratio": round(stall_ratio, 4),
        "soft_correction": round(soft_correction, 4),
        "punctuation_pressure": round(punctuation_pressure, 4),
        "tempo_pause_ratio": round(tempo_pause_ratio, 4),
        "typing_chaos": round(typing_chaos, 4),
        "punctuation_delta": round(punctuation_delta, 4),
        "terseness_delta": round(terseness_delta, 4),
        "directness_delta": round(directness_delta, 4),
        "abrupt_delta": round(abrupt_delta, 4),
        "surface_signal_reliability": round(surface_signal_reliability, 4),
        "dismissive_pressure": round(dismissive_pressure, 4),
        "tempo_pause_pressure": round(tempo_pause_pressure, 4),
        "textism_pressure": round(textism_pressure, 4),
        "surface_only_pressure": round(surface_only_pressure, 4),
        "surface_uncertainty": round(surface_uncertainty, 4),
        "goal_specificity": round(goal_specificity, 4),
        "effective_delay_budget_seconds": round(effective_delay_budget_seconds, 4),
        "response_delay_seconds": response_delay_seconds,
        "unresolved_turns": unresolved_turns,
        "bug_retries": bug_retries,
        "task_age_minutes": task_age_minutes,
        "queue_depth": queue_depth,
        "background_tasks_running": background_tasks_running,
        "same_issue_mentions": same_issue_mentions,
        "contradiction_signal": contradiction_signal,
        "resolution_claimed": resolution_claimed,
        "resolution_mismatch": resolution_mismatch,
        "last_routing_outcome": last_routing_outcome,
        "last_outcome_success": last_outcome_success,
        "last_outcome_retry": last_outcome_retry,
        "last_outcome_complaint": last_outcome_complaint,
        "delay_pressure": round(delay_pressure, 4),
        "stuck_pressure": round(stuck_pressure, 4),
        "background_pressure": round(background_pressure, 4),
        "user_profile": user_profile,
        "evidence": evidence,
    }


def derive_emotion_vector(state_vector: dict[str, float], features: dict[str, Any]) -> dict[str, float]:
    confusion = clamp(
        0.48 * (1.0 - state_vector["clarity"])
        + 0.12 * clamp(features["confusion_hits"] / 2.0)
        + 0.14 * features["explicit_confusion_request"]
        + 0.05 * features["vague_ratio"]
        + 0.04 * clamp(features["questions"] / 3.0)
        - 0.08 * state_vector["urgency"]
        - 0.06 * state_vector["frustration"]
        - 0.1 * features["skepticism_ratio"]
        + 0.06 * features["hedge_ratio"]
        - 0.12 * features["speculation_ratio"]
        - 0.08 * features["context_loss_ratio"]
        - 0.08 * features["execution_plumbing_ratio"]
        - 0.06 * features["contradiction_signal"]
        - 0.08 * features["goal_specificity"]
        - 0.05 * features["task_object_ratio"]
        - 0.08 * features["evidence_request"]
        - 0.08 * features["comparison_request"]
        - 0.08 * features["guardrail_request"]
    )
    skepticism = clamp(
        0.46 * features["skepticism_ratio"]
        + 0.24 * features["speculation_ratio"]
        + 0.14 * features["context_loss_ratio"]
        + 0.18 * features["execution_plumbing_ratio"]
        + 0.08 * features["hedge_ratio"]
        + 0.16 * features["resolution_mismatch"]
        + 0.14 * features["contradiction_signal"]
        + 0.1 * features["soft_correction"]
        + 0.08 * features["question_density"]
        + 0.06 * features["assurance_ratio"]
        + 0.06 * (1.0 - state_vector["trust"])
        + 0.06 * features["stuck_pressure"]
        + 0.04 * features["goal_specificity"]
        + 0.05 * features["dismissive_pressure"]
        + 0.03 * features["tempo_pause_pressure"]
        + 0.24 * features["evidence_request"]
    )
    cautiousness = clamp(
        0.48 * features["caution_ratio"]
        + 0.28 * features["boundary_ratio"]
        + 0.18 * features["assurance_ratio"]
        + 0.08 * state_vector["trust"]
        + 0.06 * features["polite_ratio"]
        + 0.22 * features["guardrail_request"]
    )
    openness = clamp(
        0.68 * features["explore_ratio"]
        + 0.16 * state_vector["engagement"]
        + 0.06 * clamp(features["questions"] / 3.0)
        + 0.28 * features["comparison_request"]
        - 0.1 * state_vector["urgency"]
        - 0.08 * state_vector["frustration"]
    )
    return {
        "urgency": round(clamp(state_vector["urgency"]), 4),
        "frustration": round(clamp(state_vector["frustration"]), 4),
        "confusion": round(confusion, 4),
        "skepticism": round(skepticism, 4),
        "satisfaction": round(clamp(state_vector["satisfaction"]), 4),
        "cautiousness": round(cautiousness, 4),
        "openness": round(openness, 4),
    }


def build_interaction_state(state_vector: dict[str, float]) -> dict[str, float]:
    return {
        "clarity": round(clamp(state_vector["clarity"]), 4),
        "trust": round(clamp(state_vector["trust"]), 4),
        "engagement": round(clamp(state_vector["engagement"]), 4),
    }


def build_mode_scores(emotion_vector: dict[str, float], features: dict[str, Any]) -> dict[str, float]:
    return {
        "urgent": round(clamp(emotion_vector["urgency"] * 1.04 + 0.08 * features["delay_pressure"] + 0.1 * features["blocking_ratio"] + 0.08 * features["missed_expectation_ratio"] + 0.06 * features["typing_chaos"] + 0.05 * features["textism_pressure"] + 0.04 * features["command_ratio"] + 0.04 * features["directness_delta"] + 0.08 * features["stall_ratio"] + 0.04 * features["tempo_pause_pressure"] + 0.04 * features["execution_plumbing_ratio"] + 0.04 * clamp(features["same_issue_mentions"] / 3.0) - 0.03 * features["evidence_request"] - 0.04 * features["guardrail_request"]), 4),
        "frustrated": round(clamp(emotion_vector["frustration"] * 1.14 + 0.12 * features["stuck_pressure"] + 0.08 * features["missed_expectation_ratio"] + 0.08 * features["context_loss_ratio"] + 0.08 * features["execution_plumbing_ratio"] + 0.08 * features["stall_ratio"] + 0.06 * features["resolution_mismatch"] + 0.08 * features["abrupt_delta"] + 0.06 * features["delay_pressure"] + 0.08 * features["dismissive_pressure"] + 0.04 * features["tempo_pause_pressure"] + 0.06 * features["contradiction_signal"] + 0.04 * features["soft_correction"] + 0.04 * features["guardrail_request"]), 4),
        "confused": round(clamp(emotion_vector["confusion"] * 0.92 + 0.06 * clamp(features["confusion_hits"] / 2.0) + 0.1 * features["explicit_confusion_request"] + 0.08 * features["explicit_confusion_request"] * features["evidence_request"] + 0.03 * features["vague_ratio"] - 0.1 * features["goal_specificity"] - 0.12 * features["speculation_ratio"] - 0.08 * features["context_loss_ratio"] - 0.08 * features["execution_plumbing_ratio"] - 0.06 * features["contradiction_signal"] - 0.08 * features["evidence_request"] - 0.08 * features["comparison_request"] - 0.08 * features["guardrail_request"]), 4),
        "skeptical": round(clamp(emotion_vector["skepticism"] * 1.08 + 0.12 * features["speculation_ratio"] + 0.08 * features["context_loss_ratio"] + 0.1 * features["execution_plumbing_ratio"] + 0.08 * features["resolution_mismatch"] + 0.06 * features["contradiction_signal"] + 0.06 * features["stuck_pressure"] + 0.04 * features["delay_pressure"] + 0.04 * features["goal_specificity"] + 0.05 * features["dismissive_pressure"] + 0.18 * features["evidence_request"]), 4),
        "satisfied": round(clamp(emotion_vector["satisfaction"] + 0.1 * features["guard_ratio"] + 0.08 * features["success_ratio"] + 0.08 * features["continue_ratio"] + 0.06 * features["resolution_claimed"]), 4),
        "cautious": round(clamp(emotion_vector["cautiousness"] * 1.1 + 0.06 * features["goal_specificity"] + 0.04 * features["polite_ratio"] + 0.08 * features["assurance_ratio"] + 0.06 * features["boundary_ratio"] + 0.06 * features["context_loss_ratio"] + 0.04 * features["contradiction_signal"] + 0.16 * features["guardrail_request"]), 4),
        "exploratory": round(clamp(emotion_vector["openness"] * 1.08 + 0.06 * features["explore_ratio"] + 0.04 * features["technical_ratio"] + 0.22 * features["comparison_request"] + 0.04 * features["goal_specificity"]), 4),
        "neutral": 0.22,
    }


def build_intensity_profile(emotion_vector: dict[str, float]) -> dict[str, str]:
    return {dim: intensity_band(score) for dim, score in emotion_vector.items()}


def build_emotion_composition(emotion_vector: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(emotion_vector.get(dim, 0.0))) for dim in EMOTION_DIMS)
    if total <= 1e-6:
        return {dim: 0.0 for dim in EMOTION_DIMS}
    return {
        dim: round(clamp(float(emotion_vector.get(dim, 0.0)) / total), 4)
        for dim in EMOTION_DIMS
    }


def build_emotionality_metrics(emotion_vector: dict[str, float], features: dict[str, Any]) -> dict[str, Any]:
    active_values = sorted((float(emotion_vector.get(dim, 0.0)) for dim in EMOTION_DIMS), reverse=True)
    dominant = active_values[0] if active_values else 0.0
    mean_signal = sum(active_values) / max(len(active_values), 1)
    emotionality = clamp(
        0.44 * dominant
        + 0.22 * mean_signal
        + 0.1 * features["punctuation_pressure"]
        + 0.08 * features["delay_pressure"]
        + 0.08 * features["stuck_pressure"]
        + 0.08 * features["skepticism_ratio"]
    )
    composition = build_emotion_composition(emotion_vector)
    top_axes = [
        {"axis": dim, "share": composition[dim], "score": round(float(emotion_vector.get(dim, 0.0)), 4)}
        for dim in sorted(EMOTION_DIMS, key=lambda axis: float(emotion_vector.get(axis, 0.0)), reverse=True)
        if float(emotion_vector.get(dim, 0.0)) >= 0.18
    ][:3]
    return {
        "emotionality": round(emotionality, 4),
        "composition": composition,
        "top_axes": top_axes,
    }


def build_posthoc_shadow(payload: dict[str, Any], features: dict[str, Any], confirmed: dict[str, Any], analysis: dict[str, Any], posthoc_plan: dict[str, Any]) -> dict[str, Any]:
    review_semantic = load_review_semantic(payload)
    source_vector = clamp_dict(review_semantic.get("emotion_vector"), EMOTION_DIMS) if review_semantic.get("emotion_vector") else confirmed["emotion_vector"]
    source_labels = canonicalize_labels(list(review_semantic.get("labels") or [])) if review_semantic.get("labels") else canonicalize_labels(confirmed["labels"])
    metrics = build_emotionality_metrics(source_vector, features)
    dominant_axis = max(EMOTION_DIMS, key=lambda dim: float(source_vector.get(dim, 0.0)))
    available = bool(review_semantic.get("emotion_vector") or review_semantic.get("labels"))
    return {
        "enabled": True,
        "available": available,
        "source": "review_semantic" if available else "confirmed_estimate",
        "is_estimate": not available,
        "mode": "shadow_review",
        "style": posthoc_plan["style"],
        "weight": round(float(posthoc_plan["weight"]), 4),
        "target_ms": int(posthoc_plan["target_ms"]),
        "emotionality": metrics["emotionality"],
        "composition": metrics["composition"],
        "top_axes": metrics["top_axes"],
        "dominant_axis": dominant_axis,
        "dominant_axis_score": round(float(source_vector.get(dominant_axis, 0.0)), 4),
        "labels": source_labels,
        "confidence": round(clamp(float(review_semantic.get("confidence", 0.0) or 0.0)), 4) if available else round(float(confirmed["confidence"]), 4),
        "stance_cues": analysis["priority_reason"][:3],
    }


def build_collection_stack(weight_schedule: dict[str, Any], features: dict[str, Any], posthoc_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "sources": ["front_prompt", "review_prompt", "history_context", "time_runtime_context"],
        "front_weight": round(float(weight_schedule["screen_weight"]), 4),
        "review_weight": round(float(weight_schedule["posthoc_weight"]), 4),
        "posthoc_weight": round(float(weight_schedule["posthoc_weight"]), 4),
        "history_active": True,
        "time_runtime_active": True,
        "review_mode": posthoc_plan["style"],
        "posthoc_mode": posthoc_plan["style"],
        "consistency_rate": round(float(weight_schedule["consistency_rate"]), 4),
        "effective_consistency": round(float(weight_schedule["effective_consistency"]), 4),
        "response_delay_seconds": float(features["response_delay_seconds"]),
        "effective_delay_budget_seconds": round(float(features["effective_delay_budget_seconds"]), 4),
    }


def build_constraint_signals(features: dict[str, Any]) -> dict[str, float]:
    return {
        "boundary_strength": round(clamp(0.62 * features["boundary_ratio"] + 0.2 * features["caution_ratio"] + 0.18 * features["assurance_ratio"]), 4),
        "verification_preference": round(clamp(0.52 * features["assurance_ratio"] + 0.26 * features["caution_ratio"] + 0.12 * features["boundary_ratio"] + 0.1 * features["goal_specificity"]), 4),
        "scope_tightness": round(clamp(0.74 * features["boundary_ratio"] + 0.16 * features["command_ratio"] + 0.1 * features["goal_specificity"]), 4),
        "evidence_requirement": round(clamp(0.56 * features["skepticism_ratio"] + 0.18 * features["resolution_mismatch"] + 0.14 * features["contradiction_signal"] + 0.12 * features["goal_specificity"]), 4),
    }


def build_weight_schedule(payload: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    calibration = payload.get("calibration_state") or {}
    observed_turns = int(calibration.get("observed_turns", features.get("unresolved_turns", 0)) or 0)
    posthoc_samples = int(calibration.get("posthoc_samples", calibration.get("calibrated_samples", 0)) or 0)
    consistency_samples = int(calibration.get("consistency_samples", posthoc_samples) or 0)
    stable_prediction_hits = int(calibration.get("stable_prediction_hits", 0) or 0)
    prediction_agreement = clamp(float(calibration.get("prediction_agreement", 0.0) or 0.0))
    consistency_rate = clamp(float(calibration.get("consistency_rate", calibration.get("front_posthoc_consistency", prediction_agreement)) or prediction_agreement))
    agreement_confidence = clamp(consistency_samples / 18.0)
    effective_consistency = clamp((consistency_rate * agreement_confidence) + (prediction_agreement * (1.0 - agreement_confidence)))
    profile_seed = features["user_profile"]
    explicit_prior = 1.0 if profile_seed.get("affective_prior_source") == "explicit" else 0.0
    persona_seed = 1.0 if profile_seed.get("persona_source") in {"persona_traits", "big5"} else 0.0
    maturity = clamp(
        0.28 * clamp(posthoc_samples / 24.0)
        + 0.22 * clamp(observed_turns / 30.0)
        + 0.2 * clamp(stable_prediction_hits / 18.0)
        + 0.18 * effective_consistency
        + 0.07 * explicit_prior
        + 0.05 * persona_seed
    )
    if posthoc_samples < 8 or observed_turns < 12:
        stage = "bootstrap"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.24, 0.08, 0.56, 0.12
    elif maturity < 0.42:
        stage = "calibrating"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.3, 0.12, 0.44, 0.14
    elif maturity < 0.72:
        stage = "adapting"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.4, 0.18, 0.28, 0.14
    else:
        stage = "stable"
        base_screen_weight, prior_weight, base_posthoc_weight, carryover_weight = 0.5, 0.22, 0.14, 0.14
    consistency_shift = (effective_consistency - 0.5) * (0.16 if stage in {"bootstrap", "calibrating"} else 0.22)
    screen_weight = round(clamp(base_screen_weight + consistency_shift, 0.18, 0.58), 4)
    posthoc_weight = round(clamp(base_posthoc_weight - consistency_shift, 0.12, 0.62), 4)
    prior_weight = round(prior_weight, 4)
    carryover_weight = round(carryover_weight, 4)
    screen_semantic_weight = round(clamp(0.16 + 0.22 * maturity + 0.08 * (effective_consistency - 0.5)), 4)
    front_trust = round(clamp(screen_weight / max(screen_weight + posthoc_weight, 1e-6)), 4)
    return {
        "stage": stage,
        "maturity": round(maturity, 4),
        "observed_turns": observed_turns,
        "posthoc_samples": posthoc_samples,
        "consistency_samples": consistency_samples,
        "stable_prediction_hits": stable_prediction_hits,
        "prediction_agreement": round(prediction_agreement, 4),
        "consistency_rate": round(consistency_rate, 4),
        "agreement_confidence": round(agreement_confidence, 4),
        "effective_consistency": round(effective_consistency, 4),
        "consistency_shift": round(consistency_shift, 4),
        "weight_model": "independent_signal_weights",
        "screen_weight": screen_weight,
        "screen_semantic_weight": screen_semantic_weight,
        "prior_weight": prior_weight,
        "posthoc_weight": posthoc_weight,
        "carryover_weight": carryover_weight,
        "front_trust": front_trust,
        "posthoc_trust": round(clamp(1.0 - front_trust), 4),
    }


def infer_labels(emotion_vector: dict[str, float], features: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    if emotion_vector["urgency"] >= 0.62 or features["blocking_ratio"] >= 0.25 or features["missed_expectation_ratio"] >= 0.34 or (features["typing_chaos"] >= 0.42 and (features["delay_pressure"] >= 0.4 or features["urgency_hits"] >= 1)) or (features["textism_pressure"] >= 0.34 and (features["delay_pressure"] >= 0.34 or features["urgency_hits"] >= 1)) or (features["delay_pressure"] >= 0.5 and (features["command_ratio"] >= 0.34 or features["directness_delta"] >= 0.34)) or (features["delay_pressure"] >= 0.8 and (features["stall_ratio"] >= 0.25 or features["stuck_pressure"] >= 0.8)) or (features["stuck_pressure"] >= 0.9 and (features["delay_pressure"] >= 0.45 or features["same_issue_mentions"] >= 1 or features["stall_ratio"] >= 0.25)) or (features["stuck_pressure"] >= 0.78 and features["delay_pressure"] >= 0.55 and (features["frustration_ratio"] >= 0.25 or features["stall_ratio"] >= 0.25)) or (features["stall_ratio"] >= 0.25 and features["delay_pressure"] >= 0.45 and emotion_vector["urgency"] >= 0.34) or (features["short_burst"] >= 0.75 and features["urgency_hits"] >= 1 and features["frustration_hits"] >= 1) or (features["missed_expectation_ratio"] >= 0.28 and features["delay_pressure"] >= 0.45 and (features["same_issue_mentions"] >= 1 or features["frustration_ratio"] >= 0.75)) or (features["explicit_confusion_request"] >= 1.0 and features["evidence_request"] >= 1.0 and features["goal_specificity"] <= 0.18 and features["unresolved_turns"] >= 2):
        labels.append("urgent")
    if emotion_vector["frustration"] >= 0.6 or features["frustration_ratio"] >= 0.32 or features["missed_expectation_ratio"] >= 0.34 or features["context_loss_ratio"] >= 0.34 or features["execution_plumbing_ratio"] >= 0.34 or features["resolution_mismatch"] >= 0.5 or features["stall_ratio"] >= 0.5 or (features["stall_ratio"] >= 0.25 and features["delay_pressure"] >= 0.42 and (features["urgency_hits"] >= 1 or features["missed_expectation_ratio"] >= 0.25 or features["same_issue_mentions"] >= 1)) or (features["abrupt_delta"] >= 0.35 and features["delay_pressure"] >= 0.45) or (features["dismissive_pressure"] >= 0.38 and (features["delay_pressure"] >= 0.28 or features["stuck_pressure"] >= 0.42 or features["resolution_mismatch"] >= 0.5)) or (features["stuck_pressure"] >= 0.8 and (features["frustration_ratio"] >= 0.25 or features["stall_ratio"] >= 0.25 or features["delay_pressure"] >= 0.35)) or ((features["contradiction_signal"] >= 0.4 or features["soft_correction"] >= 0.8) and features["same_issue_mentions"] >= 1 and (features["skepticism_ratio"] >= 0.25 or features["speculation_ratio"] >= 0.25 or features["context_loss_ratio"] >= 0.25)) or (features["speculation_ratio"] >= 0.75 and (features["delay_pressure"] >= 0.28 or features["contradiction_signal"] >= 0.28 or features["stuck_pressure"] >= 0.28)) or (features["skepticism_ratio"] >= 0.3 and features["stuck_pressure"] >= 0.52 and features["contradiction_signal"] >= 0.28):
        labels.append("frustrated")
    if "urgent" not in labels and (
        (features["urgency_hits"] >= 1 and (features["goal_specificity"] >= 0.25 or features["guardrail_request"] >= 1.0 or features["command_ratio"] >= 0.25))
        or (features["delay_pressure"] >= 0.6 and (features["frustration_ratio"] >= 0.25 or features["stuck_pressure"] >= 0.55 or features["same_issue_mentions"] >= 1))
        or (features["frustration_ratio"] >= 0.75 and features["same_issue_mentions"] >= 1 and features["delay_pressure"] >= 0.4)
        or (features["frustration_ratio"] >= 0.5 and features["same_issue_mentions"] >= 1 and features["delay_pressure"] >= 0.35 and features["stuck_pressure"] >= 0.7)
        or features["blocking_ratio"] >= 0.25
    ):
        labels.append("urgent")
    if "frustrated" not in labels and (
        features["blocking_ratio"] >= 0.25
        or (features["execution_plumbing_ratio"] >= 0.25 and (features["task_object_ratio"] >= 0.25 or features["same_issue_mentions"] >= 1))
        or (features["frustration_ratio"] >= 0.25 and (features["stuck_pressure"] >= 0.45 or features["delay_pressure"] >= 0.42))
        or (features["missed_expectation_ratio"] >= 0.25 and (features["evidence_request"] >= 1.0 or features["technical_ratio"] >= 0.15))
    ):
        labels.append("frustrated")
    confused_signal = (
        emotion_vector["confusion"] >= 0.58
        and (
            features["explicit_confusion_request"] >= 1.0
            or features["questions"] >= 1
            or (
                features["vague_ratio"] >= 0.3
                and features["hedge_ratio"] >= 0.3
                and features["goal_specificity"] <= 0.18
            )
            or (
                features["goal_specificity"] <= 0.22
                and features["evidence_request"] == 0.0
                and features["comparison_request"] == 0.0
                and features["guardrail_request"] == 0.0
            )
        )
    ) or (features["explicit_confusion_request"] >= 1.0 and features["goal_specificity"] <= 0.68) or (
        features["vague_ratio"] >= 0.3
        and features["hedge_ratio"] >= 0.3
        and features["goal_specificity"] <= 0.18
        and emotion_vector["urgency"] <= 0.45
        and emotion_vector["frustration"] <= 0.42
    )
    if confused_signal and emotion_vector["urgency"] <= 0.78 and emotion_vector["frustration"] <= 0.76:
        labels.append("confused")
    if "confused" not in labels and features["confusion_hits"] >= 2 and features["context_loss_ratio"] >= 0.25 and emotion_vector["urgency"] <= 0.42:
        labels.append("confused")
    if "confused" not in labels and features["confusion_hits"] >= 2 and features["execution_plumbing_ratio"] >= 0.34 and features["goal_specificity"] <= 0.18 and emotion_vector["urgency"] <= 0.45:
        labels.append("confused")
    if "confused" not in labels and features["confusion_hits"] >= 1 and features["evidence_request"] >= 1.0 and features["contradiction_signal"] >= 0.18 and features["goal_specificity"] <= 0.24:
        labels.append("confused")
    if "confused" not in labels and features["confusion_hits"] >= 1 and features["evidence_request"] >= 1.0 and features["skepticism_ratio"] >= 0.25 and features["contradiction_signal"] >= 0.18:
        labels.append("confused")
    if emotion_vector["skepticism"] >= 0.42 or features["skepticism_ratio"] >= 0.32 or features["speculation_ratio"] >= 0.25 or features["context_loss_ratio"] >= 0.25 or features["execution_plumbing_ratio"] >= 0.25 or (features["hedge_ratio"] >= 0.34 and (features["contradiction_signal"] >= 0.25 or features["speculation_ratio"] >= 0.25 or features["evidence_request"] >= 1.0)) or features["resolution_mismatch"] >= 0.5 or features["contradiction_signal"] >= 0.45 or features["evidence_request"] >= 1.0 or (features["dismissive_pressure"] >= 0.42 and (features["hedge_ratio"] >= 0.2 or features["contradiction_signal"] >= 0.25 or features["goal_specificity"] >= 0.28)) or (features["missed_expectation_ratio"] >= 0.25 and features["contradiction_signal"] >= 0.24 and features["delay_pressure"] >= 0.5):
        labels.append("skeptical")
    if "skeptical" not in labels and (
        features["skepticism_ratio"] >= 0.25
        or (features["questions"] >= 1 and features["stuck_pressure"] >= 0.5)
        or (features["evidence_request"] >= 1.0 and features["task_object_ratio"] >= 0.3)
    ):
        labels.append("skeptical")
    if emotion_vector["satisfaction"] >= 0.6 or (features["guard_ratio"] >= 0.3 and (features["success_ratio"] >= 0.3 or features["satisfaction_hits"] >= 1 or features["resolution_claimed"] >= 0.5)) or ((features["satisfaction_hits"] >= 1 or features["resolution_claimed"] >= 0.5 or features["success_hits"] >= 1) and features["continue_ratio"] >= 0.25):
        labels.append("satisfied")
    if emotion_vector["cautiousness"] >= 0.42 or features["caution_ratio"] >= 0.3 or features["boundary_ratio"] >= 0.3 or features["assurance_ratio"] >= 0.3 or features["guardrail_request"] >= 1.0 or (features["context_loss_ratio"] >= 0.25 and features["speculation_ratio"] >= 0.25) or (features["context_loss_ratio"] >= 0.25 and features["evidence_request"] >= 1.0 and features["contradiction_signal"] >= 0.25):
        labels.append("cautious")
    if (emotion_vector["openness"] >= 0.4 or features["comparison_request"] >= 1.0) and emotion_vector["urgency"] <= 0.72 and emotion_vector["frustration"] <= 0.72:
        labels.append("exploratory")
    if "exploratory" not in labels and features["explore_ratio"] >= 0.3 and (features["comparison_request"] >= 1.0 or features["evidence_request"] >= 1.0 or features["guardrail_request"] >= 1.0) and emotion_vector["frustration"] <= 0.72:
        labels.append("exploratory")
    if not labels:
        labels.append("neutral")
    return canonicalize_labels(labels)


def initial_screen(features: dict[str, Any]) -> dict[str, Any]:
    urgency = clamp(
        0.23 * clamp(features["urgency_hits"] / 2.0)
        + 0.12 * features["blocking_ratio"]
        + 0.12 * features["missed_expectation_ratio"]
        + 0.04 * features["execution_plumbing_ratio"]
        + 0.1 * features["command_ratio"]
        + 0.08 * features["directness_delta"]
        + 0.06 * features["short_burst"]
        + 0.06 * features["terseness_delta"]
        + 0.08 * features["typing_chaos"]
        + 0.1 * features["repeat_similarity"]
        + 0.18 * features["delay_pressure"]
        + 0.16 * features["stuck_pressure"]
        + 0.06 * features["punctuation_pressure"]
        + 0.04 * features["punctuation_delta"]
        + 0.05 * features["textism_pressure"]
        + 0.04 * features["tempo_pause_pressure"]
        + 0.1 * features["stall_ratio"]
        + 0.06 * features["goal_specificity"]
    )
    frustration = clamp(
        0.22 * clamp(features["anger_hits"] / 2.0)
        + 0.26 * features["frustration_ratio"]
        + 0.12 * features["missed_expectation_ratio"]
        + 0.08 * features["context_loss_ratio"]
        + 0.1 * features["execution_plumbing_ratio"]
        + 0.14 * features["stall_ratio"]
        + 0.1 * features["repeat_similarity"]
        + 0.14 * features["delay_pressure"]
        + 0.18 * features["stuck_pressure"]
        + 0.04 * features["punctuation_pressure"]
        + 0.06 * features["punctuation_delta"]
        + 0.16 * features["abrupt_delta"]
        + 0.08 * features["dismissive_pressure"]
        + 0.05 * features["tempo_pause_pressure"]
        + 0.03 * features["textism_pressure"]
        + 0.1 * features["resolution_mismatch"]
        + 0.04 * features["contradiction_signal"]
        + 0.04 * features["soft_correction"]
    )
    clarity = clamp(
        0.56
        + 0.12 * features["goal_specificity"]
        + 0.08 * features["task_object_ratio"]
        + 0.08 * features["technical_ratio"]
        + 0.06 * clamp(features["file_refs"] / 2.0)
        + 0.06 * clamp(features["code_markers"])
        + 0.05 * clamp(features["list_markers"] / 4.0)
        + 0.04 * features["boundary_ratio"]
        + 0.03 * features["guard_ratio"]
        + 0.05 * features["evidence_request"]
        + 0.05 * features["comparison_request"]
        + 0.05 * features["guardrail_request"]
        - (0.02 if features["explicit_confusion_request"] == 0 else 0.08) * features["question_density"]
        - 0.12 * features["vague_ratio"]
        - 0.04 * clamp(features["confusion_hits"] / 2.0)
        - 0.08 * features["explicit_confusion_request"]
        - 0.04 * (1.0 if features["chars"] <= 10 and features["goal_specificity"] < 0.3 else 0.0)
    )
    satisfaction = clamp(
        0.06
        + 0.24 * features["praise_ratio"]
        + 0.22 * features["success_ratio"]
        + 0.14 * features["continue_ratio"] * (1.0 if features["satisfaction_hits"] >= 1 or features["resolution_claimed"] >= 0.5 else 0.35)
        + 0.18 * features["guard_ratio"]
        + 0.08 * features["resolution_claimed"]
        + 0.04 * features["polite_ratio"]
        + 0.06 * features["politeness_delta"]
        - 0.28 * frustration
    )
    trust = clamp(
        0.4
        + 0.08 * features["polite_ratio"]
        + 0.08 * features["politeness_delta"]
        + 0.08 * features["caution_ratio"]
        + 0.06 * features["boundary_ratio"]
        + 0.1 * satisfaction
        - 0.14 * clamp(features["anger_hits"] / 2.0)
        - 0.14 * features["frustration_ratio"]
        - 0.14 * features["speculation_ratio"]
        - 0.08 * features["context_loss_ratio"]
        - 0.1 * features["execution_plumbing_ratio"]
        - 0.08 * features["dismissive_pressure"]
        - 0.08 * features["resolution_mismatch"]
        - 0.1 * features["contradiction_signal"]
    )
    engagement = clamp(
        0.28
        + 0.08 * clamp(features["chars"] / 220.0)
        + 0.08 * features["question_density"]
        + 0.12 * features["technical_ratio"]
        + 0.12 * clamp(features["same_issue_mentions"] / 3.0)
        + 0.08 * clamp(features["list_markers"] / 4.0)
        + 0.12 * features["stuck_pressure"]
        + 0.08 * clamp((features["punctuation_runs"] + features["latin_elongations"] + features["cjk_elongations"]) / 3.0)
    )

    vector = {
        "urgency": round(urgency, 4),
        "frustration": round(frustration, 4),
        "clarity": round(clarity, 4),
        "satisfaction": round(satisfaction, 4),
        "trust": round(trust, 4),
        "engagement": round(engagement, 4),
    }
    emotion_vector = derive_emotion_vector(vector, features)
    mode_scores = build_mode_scores(emotion_vector, features)
    confidence = clamp(
        0.54
        + 0.08 * clamp(len(features["evidence"]) / 5.0)
        + 0.08 * abs(vector["urgency"] - 0.5)
        + 0.08 * abs(vector["frustration"] - 0.5)
        + 0.06 * features["goal_specificity"]
        + 0.04 * features["surface_signal_reliability"]
        - 0.12 * features["surface_uncertainty"]
    )
    return {
        "vector": vector,
        "state_vector": vector,
        "interaction_state": build_interaction_state(vector),
        "emotion_vector": emotion_vector,
        "emotion_intensity": build_intensity_profile(emotion_vector),
        "mode_scores": mode_scores,
        "labels": infer_labels(emotion_vector, features),
        "confidence": round(confidence, 4),
        "evidence": features["evidence"],
    }


def blend_named_vector(base: dict[str, float], incoming: dict[str, Any], dims: tuple[str, ...], weight: float) -> dict[str, float]:
    if not incoming:
        return base
    result = dict(base)
    for dim in dims:
        incoming_value = incoming.get(dim)
        if incoming_value is None:
            continue
        result[dim] = round(clamp((1.0 - weight) * result[dim] + weight * float(incoming_value)), 4)
    return result


def blend_vectors(base: dict[str, float], incoming: dict[str, Any], weight: float) -> dict[str, float]:
    return blend_named_vector(base, incoming, DIMS, weight)


def derive_state_vector_from_emotion(emotion_vector: dict[str, Any], features: dict[str, Any]) -> dict[str, float]:
    emotion = clamp_dict(emotion_vector, EMOTION_DIMS)
    return {
        "urgency": round(emotion["urgency"], 4),
        "frustration": round(emotion["frustration"], 4),
        "clarity": round(clamp(0.64 - 0.46 * emotion["confusion"] - 0.12 * emotion["urgency"] - 0.08 * emotion["frustration"] + 0.08 * emotion["openness"] + 0.06 * features["task_object_ratio"] + 0.04 * features["goal_specificity"]), 4),
        "satisfaction": round(emotion["satisfaction"], 4),
        "trust": round(clamp(0.56 - 0.34 * emotion["skepticism"] - 0.22 * emotion["frustration"] + 0.1 * emotion["cautiousness"] + 0.08 * emotion["satisfaction"] + 0.04 * features["assurance_ratio"]), 4),
        "engagement": round(clamp(0.3 + 0.24 * emotion["urgency"] + 0.22 * emotion["frustration"] + 0.18 * emotion["openness"] + 0.08 * features["technical_ratio"]), 4),
    }


def dominant_mode(emotion_vector: dict[str, float], features: dict[str, Any], scores: dict[str, float] | None = None) -> str:
    scores = scores or build_mode_scores(emotion_vector, features)
    skeptical_gap = scores["confused"] - scores["skeptical"]
    if (scores["satisfied"] >= 0.24 and features["guard_ratio"] >= 0.3 and (features["satisfaction_hits"] >= 1 or features["success_hits"] >= 1 or features["resolution_claimed"] >= 0.5)) or (scores["satisfied"] >= 0.28 and features["continue_ratio"] >= 0.25 and (features["satisfaction_hits"] >= 1 or features["resolution_claimed"] >= 0.5 or features["success_hits"] >= 1)) or (scores["satisfied"] >= 0.62 and emotion_vector["frustration"] <= 0.42):
        return "satisfied"
    if scores["cautious"] >= 0.34 and (features["caution_ratio"] >= 0.25 or features["boundary_ratio"] >= 0.25 or features["assurance_ratio"] >= 0.25) and scores["urgent"] - scores["cautious"] <= 0.18 and (features["evidence_request"] == 0.0 or scores["skeptical"] <= scores["cautious"] + 0.06) and not (features["evidence_request"] >= 1.0 and (features["same_issue_mentions"] >= 1 or features["frustration_hits"] >= 1 or features["stall_ratio"] >= 0.25)):
        return "cautious"
    if scores["confused"] >= 0.18 and features["explicit_confusion_request"] >= 1.0 and features["evidence_request"] >= 1.0 and features["goal_specificity"] <= 0.18 and features["unresolved_turns"] >= 2 and scores["urgent"] <= 0.32:
        return "confused"
    if features["comparison_request"] >= 1.0 and scores["exploratory"] >= 0.3 and features["frustration_ratio"] == 0.0 and scores["exploratory"] >= scores["skeptical"] - 0.14:
        return "exploratory"
    if scores["frustrated"] >= 0.42 and features["stuck_pressure"] >= 0.8 and features["delay_pressure"] >= 0.5 and features["frustration_ratio"] >= 0.25 and features["urgency_hits"] == 0 and features["blocking_ratio"] < 0.25 and features["comparison_request"] == 0.0:
        return "frustrated"
    if scores["skeptical"] >= 0.34 and features["evidence_request"] >= 1.0 and scores["urgent"] - scores["skeptical"] <= 0.14:
        return "skeptical"
    if scores["skeptical"] >= 0.34 and features["skepticism_ratio"] >= 0.25 and (features["evidence_request"] >= 1.0 or features["contradiction_signal"] >= 0.3 or features["stuck_pressure"] >= 0.6) and scores["frustrated"] - scores["skeptical"] <= 0.1:
        return "skeptical"
    if scores["exploratory"] >= 0.3 and features["comparison_request"] >= 1.0 and emotion_vector["urgency"] <= 0.72 and emotion_vector["frustration"] <= 0.72 and scores["exploratory"] >= scores["confused"] - 0.06 and scores["exploratory"] >= max(scores["frustrated"], scores["skeptical"]) - 0.02 and features["stuck_pressure"] <= 0.52:
        return "exploratory"
    if scores["cautious"] >= 0.28 and features["guardrail_request"] >= 1.0 and scores["urgent"] - scores["cautious"] <= 0.14:
        return "cautious"
    if scores["urgent"] >= 0.5 and (features["urgency_hits"] >= 1 or features["rush_typo_hits"] >= 1 or features["textism_hits"] >= 1):
        return "urgent"
    if features["urgency_hits"] >= 1 and features["blocking_ratio"] >= 0.25 and scores["urgent"] >= scores["frustrated"] - 0.12:
        return "urgent"
    if scores["confused"] >= 0.24 and features["explicit_confusion_request"] >= 1.0 and features["goal_specificity"] <= 0.18 and features["evidence_request"] == 0.0 and features["comparison_request"] == 0.0 and features["guardrail_request"] == 0.0 and scores["confused"] >= scores["skeptical"] - 0.04:
        return "confused"
    if scores["confused"] >= 0.16 and ((features["explicit_confusion_request"] >= 1.0 and features["questions"] >= 1) or (features["confusion_hits"] >= 1 and features["questions"] >= 1 and scores["urgent"] - scores["confused"] <= 0.24)):
        return "confused"
    if features["vague_ratio"] >= 0.3 and features["hedge_ratio"] >= 0.3 and features["goal_specificity"] <= 0.18 and emotion_vector["urgency"] <= 0.45 and emotion_vector["frustration"] <= 0.42:
        return "confused"
    if features["abrupt_delta"] >= 0.35 and features["delay_pressure"] >= 0.45:
        return "frustrated"
    if features["dismissive_pressure"] >= 0.34 and (features["stuck_pressure"] >= 0.6 or features["delay_pressure"] >= 0.5):
        return "frustrated"
    if features["stall_ratio"] >= 0.6 and features["stuck_pressure"] >= 0.8 and features["blocking_ratio"] < 0.25 and scores["frustrated"] >= scores["urgent"] - 0.05:
        return "frustrated"
    if scores["urgent"] >= 0.5 and features["blocking_ratio"] >= 0.25 and features["delay_pressure"] >= 0.85 and scores["urgent"] >= scores["frustrated"] - 0.04:
        return "urgent"
    if scores["frustrated"] >= 0.42 and scores["frustrated"] >= scores["urgent"] - 0.08 and (features["stuck_pressure"] >= 0.72 or features["delay_pressure"] >= 0.45 or features["frustration_ratio"] >= 0.25 or features["blocking_ratio"] >= 0.25):
        return "frustrated"
    if scores["urgent"] >= 0.72 and (features["blocking_ratio"] >= 0.25 or scores["urgent"] - max(scores["frustrated"], scores["skeptical"], scores["cautious"]) >= 0.08):
        return "urgent"
    if scores["frustrated"] >= 0.64 and scores["frustrated"] >= scores["confused"] - 0.02:
        return "frustrated"
    if features["delay_pressure"] >= 0.8 and (features["stall_ratio"] >= 0.25 or features["stuck_pressure"] >= 0.8) and scores["urgent"] >= scores["frustrated"] + 0.08:
        return "urgent"
    if scores["urgent"] >= 0.64 and scores["urgent"] >= max(scores["confused"], scores["frustrated"] + 0.08, scores["skeptical"] + 0.1, scores["cautious"] + 0.12):
        return "urgent"
    if scores["skeptical"] >= 0.38 and (
        (features["evidence_request"] >= 1.0 and skeptical_gap <= 0.2)
        or (features["speculation_ratio"] >= 0.25 and skeptical_gap <= 0.16)
        or (features["context_loss_ratio"] >= 0.25 and skeptical_gap <= 0.16)
        or (features["execution_plumbing_ratio"] >= 0.25 and skeptical_gap <= 0.16)
        or (features["skepticism_ratio"] >= 0.25 and skeptical_gap <= 0.12)
        or (features["contradiction_signal"] >= 0.3 and skeptical_gap <= 0.12)
        or features["resolution_mismatch"] >= 0.4
    ):
        return "skeptical"
    if scores["skeptical"] >= 0.36 and (emotion_vector["skepticism"] >= 0.34 or features["skepticism_ratio"] >= 0.25 or features["context_loss_ratio"] >= 0.25 or features["execution_plumbing_ratio"] >= 0.25 or features["resolution_mismatch"] >= 0.4 or features["contradiction_signal"] >= 0.4):
        return "skeptical"
    if scores["cautious"] >= 0.34 and (emotion_vector["cautiousness"] >= 0.3 or features["caution_ratio"] >= 0.25 or features["boundary_ratio"] >= 0.25 or features["assurance_ratio"] >= 0.25):
        return "cautious"
    if scores["exploratory"] >= 0.54:
        return "exploratory"
    if scores["confused"] >= 0.56:
        return "confused"
    best_non_neutral = max((name for name in scores if name != "neutral"), key=scores.get)
    if scores[best_non_neutral] >= 0.18 and (
        features["frustration_hits"] >= 1
        or features["stall_ratio"] >= 0.25
        or features["skepticism_hits"] >= 1
        or features["speculation_ratio"] >= 0.25
        or features["context_loss_ratio"] >= 0.25
        or features["execution_plumbing_ratio"] >= 0.25
        or features["evidence_request"] >= 1.0
        or features["guardrail_request"] >= 1.0
        or features["comparison_request"] >= 1.0
    ):
        return best_non_neutral
    return "neutral"


def confirm_state(payload: dict[str, Any], features: dict[str, Any], screen: dict[str, Any], weight_schedule: dict[str, Any]) -> dict[str, Any]:
    llm_semantic = payload.get("llm_semantic") or {}
    llm_confidence = clamp(float(llm_semantic.get("confidence", 0.0) or 0.0))
    llm_state_vector = clamp_dict(llm_semantic.get("vector"), STATE_DIMS) if llm_semantic.get("vector") else {}
    if not llm_state_vector and llm_semantic.get("emotion_vector"):
        llm_state_vector = derive_state_vector_from_emotion(llm_semantic["emotion_vector"], features)
    last_state = payload.get("last_state") or {}
    previous_vector = last_state.get("vector") or {}
    ttl_seconds = int(last_state.get("ttl_seconds", 0) or 0)
    prev_weight = weight_schedule["carryover_weight"] if ttl_seconds > 0 else 0.0
    vector_inputs: list[tuple[dict[str, Any], float]] = [(screen["vector"], weight_schedule["screen_weight"])]
    if llm_state_vector:
        vector_inputs.append((llm_state_vector, weight_schedule["screen_semantic_weight"] * llm_confidence))
    if previous_vector:
        vector_inputs.append((previous_vector, prev_weight))
    vector = combine_named_vectors(vector_inputs, STATE_DIMS)
    emotion_vector = derive_emotion_vector(vector, features)
    profile_prior = features["user_profile"].get("affective_prior") or {}
    profile_prior_weight = clamp(float(features["user_profile"].get("affective_prior_weight", 0.0) or 0.0), 0.0, 0.24)
    review_semantic = load_review_semantic(payload)
    posthoc_confidence = clamp(float(review_semantic.get("confidence", 0.0) or 0.0))
    previous_emotion_vector = last_state.get("emotion_vector") or {}
    emotion_inputs: list[tuple[dict[str, Any], float]] = [(emotion_vector, weight_schedule["screen_weight"])]
    if profile_prior:
        emotion_inputs.append((profile_prior, min(profile_prior_weight, weight_schedule["prior_weight"])))
    if llm_semantic.get("emotion_vector"):
        emotion_inputs.append((llm_semantic["emotion_vector"], weight_schedule["screen_semantic_weight"] * llm_confidence))
    if review_semantic.get("emotion_vector"):
        emotion_inputs.append((review_semantic["emotion_vector"], weight_schedule["posthoc_weight"] * max(posthoc_confidence, 0.55)))
    if previous_emotion_vector:
        emotion_inputs.append((previous_emotion_vector, prev_weight))
    emotion_vector = combine_named_vectors(emotion_inputs, EMOTION_DIMS)
    labels = infer_labels(emotion_vector, features)
    if llm_semantic.get("labels"):
        for label in llm_semantic["labels"]:
            if label not in labels:
                labels.append(label)
    if review_semantic.get("labels"):
        for label in review_semantic["labels"]:
            if label not in labels:
                labels.append(label)
    mode_scores = build_mode_scores(emotion_vector, features)
    mode = dominant_mode(emotion_vector, features, mode_scores)
    if mode != "neutral" and mode not in labels:
        labels = [mode] if labels == ["neutral"] else labels + [mode]
    if mode in {"urgent", "frustrated"}:
        ttl = 1800
    elif mode == "cautious":
        ttl = 1500
    elif mode == "confused":
        ttl = 1200
    else:
        ttl = 900
    confidence = clamp(
        screen["confidence"] * 0.56
        + llm_confidence * 0.16
        + posthoc_confidence * 0.22
        + 0.03 * features["surface_signal_reliability"]
        - 0.05 * features["surface_uncertainty"]
        + 0.04 * abs(vector["urgency"] - vector["frustration"])
    )
    return {
        "dominant_mode": mode,
        "labels": canonicalize_labels(labels),
        "confidence": round(confidence, 4),
        "ttl_seconds": ttl,
        "vector": {dim: round(clamp(vector[dim]), 4) for dim in DIMS},
        "state_vector": {dim: round(clamp(vector[dim]), 4) for dim in DIMS},
        "interaction_state": build_interaction_state(vector),
        "emotion_vector": {dim: round(clamp(emotion_vector[dim]), 4) for dim in EMOTION_DIMS},
        "emotion_intensity": build_intensity_profile(emotion_vector),
        "emotionality_metrics": build_emotionality_metrics(emotion_vector, features),
        "mode_scores": mode_scores,
        "weight_schedule": weight_schedule,
        "evidence": screen["evidence"],
    }


def build_consistency_snapshot(payload: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    review_semantic = load_review_semantic(payload)
    if not review_semantic:
        return {
            "available": False,
            "consistency_rate": 0.0,
            "label_overlap": 0.0,
            "vector_alignment": 0.0,
            "axis_overlap": 0.0,
            "screen_labels": canonicalize_labels(screen.get("labels", [])),
            "posthoc_labels": [],
        }
    screen_vector = clamp_dict(screen.get("emotion_vector"), EMOTION_DIMS)
    posthoc_vector = clamp_dict(review_semantic.get("emotion_vector"), EMOTION_DIMS)
    screen_labels = canonicalize_labels(screen.get("labels", []))
    posthoc_labels = canonicalize_labels(list(review_semantic.get("labels") or []))
    label_overlap = label_overlap_score(screen_labels, posthoc_labels)
    vector_alignment = vector_alignment_score(screen_vector, posthoc_vector, EMOTION_DIMS)
    axis_overlap = axis_overlap_score(screen_vector, posthoc_vector, EMOTION_DIMS)
    consistency_rate = round(clamp(0.44 * label_overlap + 0.36 * vector_alignment + 0.2 * axis_overlap), 4)
    return {
        "available": True,
        "consistency_rate": consistency_rate,
        "label_overlap": label_overlap,
        "vector_alignment": vector_alignment,
        "axis_overlap": axis_overlap,
        "screen_labels": screen_labels,
        "posthoc_labels": posthoc_labels,
    }


def predict_state(features: dict[str, Any], confirmed: dict[str, Any]) -> dict[str, Any]:
    vector = confirmed["vector"]
    emotion_vector = confirmed["emotion_vector"]
    mode = confirmed["dominant_mode"]
    complexity_score = clamp(
        0.14 * clamp(features["chars"] / 280.0)
        + 0.14 * features["technical_ratio"]
        + 0.1 * clamp(features["file_refs"] / 3.0)
        + 0.1 * clamp(features["list_markers"] / 4.0)
        + 0.08 * clamp(features["questions"] / 3.0)
        + 0.18 * clamp(features["unresolved_turns"] / 5.0)
        + 0.12 * clamp(features["bug_retries"] / 3.0)
        + 0.08 * clamp(features["task_age_minutes"] / 60.0)
        + 0.06 * clamp(features["same_issue_mentions"] / 3.0)
        + 0.08 * features["stall_ratio"]
        + 0.06 * clamp(features["code_markers"])
    )
    complexity_level = "high" if complexity_score >= 0.68 else "medium" if complexity_score >= 0.4 else "low"
    frustration_risk = clamp(0.3 * emotion_vector["frustration"] + 0.18 * emotion_vector["urgency"] + 0.18 * features["delay_pressure"] + 0.14 * features["stuck_pressure"] + 0.1 * features["stall_ratio"] + 0.06 * features["resolution_mismatch"] + 0.08 * complexity_score - 0.08 * emotion_vector["satisfaction"])
    stall_risk = clamp(0.26 * complexity_score + 0.18 * features["delay_pressure"] + 0.16 * features["background_pressure"] + 0.2 * features["stuck_pressure"] + 0.1 * features["stall_ratio"] + 0.1 * emotion_vector["confusion"])
    if emotion_vector["urgency"] >= 0.78 or frustration_risk >= 0.78:
        patience_window_sec = 15
    elif frustration_risk >= 0.65:
        patience_window_sec = 25
    elif complexity_score >= 0.6:
        patience_window_sec = 45
    else:
        patience_window_sec = 60
    if frustration_risk >= 0.75:
        next_update_deadline_sec = 10
    elif stall_risk >= 0.7 or mode in {"urgent", "frustrated"}:
        next_update_deadline_sec = 15
    elif mode == "skeptical":
        next_update_deadline_sec = 20
    elif complexity_score >= 0.65:
        next_update_deadline_sec = 25
    else:
        next_update_deadline_sec = 40
    low_clarity = emotion_vector["confusion"] >= 0.58 and features["goal_specificity"] < 0.42
    probe_needed = bool(low_clarity or (mode == "confused" and features["questions"] >= 1) or (frustration_risk >= 0.72 and features["anger_hits"] == 0 and features["goal_specificity"] < 0.34))
    if mode in {"urgent", "frustrated", "skeptical"} and features["goal_specificity"] >= 0.34:
        probe_needed = False
    if features["evidence_request"] >= 1.0 or features["comparison_request"] >= 1.0 or features["guardrail_request"] >= 1.0:
        probe_needed = False
    reasons: list[str] = []
    if features["technical_hits"]:
        reasons.append("technical density")
    if features["file_refs"]:
        reasons.append("file or API references")
    if features["unresolved_turns"] >= 2:
        reasons.append("multiple unresolved turns")
    if features["bug_retries"] >= 1:
        reasons.append("repeat bug retries")
    if features["stall_hits"] >= 1:
        reasons.append("stall or hang wording")
    return {
        "task_complexity": {"score": round(complexity_score, 4), "level": complexity_level, "reasons": reasons},
        "frustration_risk": round(frustration_risk, 4),
        "stall_risk": round(stall_risk, 4),
        "patience_window_sec": patience_window_sec,
        "next_update_deadline_sec": next_update_deadline_sec,
        "probe_needed": probe_needed,
        "guard_needed": bool((vector["satisfaction"] >= 0.62 and vector["frustration"] <= 0.4) or features["guard_ratio"] >= 0.34),
    }


def build_analysis_plan(features: dict[str, Any], screen: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    ambiguity = clamp((1.0 - confirmed["vector"]["clarity"]) * 0.48 + 0.2 * features["vague_ratio"] + 0.16 * features["question_density"] + 0.12 * features["contradiction_signal"] - 0.14 * features["goal_specificity"] - 0.1 * screen["confidence"] - 0.08 * features["evidence_request"] - 0.08 * features["comparison_request"] - 0.08 * features["guardrail_request"])
    strong_state = screen["confidence"] >= 0.62 and ambiguity <= 0.22 and len([label for label in confirmed["labels"] if label != "neutral"]) <= 2
    semantic_pass = "fast" if mode in {"cautious", "confused", "skeptical"} or not strong_state else "skip"
    if semantic_pass == "skip":
        target_ms, max_response_tokens, max_prompt_chars = 0, 0, 260
    elif mode in {"urgent", "frustrated"}:
        target_ms, max_response_tokens, max_prompt_chars = 350, 90, 420
    else:
        target_ms, max_response_tokens, max_prompt_chars = 500, 120, 520
    return {
        "semantic_pass": semantic_pass,
        "ambiguity": round(ambiguity, 4),
        "target_ms": target_ms,
        "max_prompt_chars": max_prompt_chars,
        "max_response_tokens": max_response_tokens,
        "compact_overlay_chars": 220,
        "state_prompt_mode": "compact",
        "skip_probe": bool(mode in {"urgent", "frustrated", "skeptical"} and features["goal_specificity"] >= 0.34),
        "priority_reason": screen["evidence"][:3],
    }


def build_profile_state(features: dict[str, Any]) -> dict[str, Any]:
    profile = features["user_profile"]
    return {
        "id": profile["id"],
        "timezone": profile["timezone"],
        "local_hour": profile["local_hour"],
        "in_work_window": profile["in_work_window"],
        "work_hours_local": profile["work_hours_local"],
        "baseline": profile["baseline"],
        "persona_traits": profile["persona_traits"],
        "persona_source": profile["persona_source"],
        "affective_prior": profile["affective_prior"],
        "affective_prior_source": profile["affective_prior_source"],
        "affective_prior_weight": profile["affective_prior_weight"],
        "effective_delay_budget_seconds": features["effective_delay_budget_seconds"],
        "style_shift": {
            "politeness_delta": features["politeness_delta"],
            "terseness_delta": features["terseness_delta"],
            "punctuation_delta": features["punctuation_delta"],
            "directness_delta": features["directness_delta"],
        },
    }


def build_memory_update(payload: dict[str, Any], features: dict[str, Any], confirmed: dict[str, Any], weight_schedule: dict[str, Any], consistency_snapshot: dict[str, Any]) -> dict[str, Any]:
    baseline = features["user_profile"]["baseline"]
    persona_traits = features["user_profile"]["persona_traits"]
    affective_prior = features["user_profile"]["affective_prior"]
    emotion_vector = confirmed["emotion_vector"]
    calibration = payload.get("calibration_state") or {}
    calm_factor = clamp(1.0 - max(emotion_vector["urgency"], emotion_vector["frustration"]))
    learning_rate = round(clamp(0.03 + 0.11 * confirmed["confidence"] * calm_factor, 0.03, 0.12), 4)
    observed_delay = baseline["response_delay_seconds"]
    if features["response_delay_seconds"] > 0:
        if emotion_vector["urgency"] >= 0.55 or emotion_vector["frustration"] >= 0.55:
            observed_delay = max(8.0, min(baseline["response_delay_seconds"], features["response_delay_seconds"]))
        elif emotion_vector["satisfaction"] >= 0.45 or emotion_vector["confusion"] <= 0.4:
            observed_delay = min(120.0, max(baseline["response_delay_seconds"], features["response_delay_seconds"]))
    observed_style = {
        "response_delay_seconds": round(float(observed_delay), 2),
        "politeness": round(features["polite_ratio"], 4),
        "terseness": round(features["short_burst"], 4),
        "punctuation": round(features["punctuation_pressure"], 4),
        "directness": round(features["command_ratio"], 4),
    }
    proposed_baseline = {
        key: round((1.0 - learning_rate) * float(baseline[key]) + learning_rate * float(observed_style[key]), 4)
        for key in observed_style
    }
    observed_persona = {
        "patience": round(clamp(1.0 - max(emotion_vector["urgency"], emotion_vector["frustration"])), 4),
        "skepticism": round(clamp(max(emotion_vector["skepticism"], features["skepticism_ratio"])), 4),
        "caution": round(clamp(max(emotion_vector["cautiousness"], features["assurance_ratio"])), 4),
        "openness": round(clamp(emotion_vector["openness"]), 4),
        "assertiveness": round(clamp(features["command_ratio"]), 4),
    }
    persona_learning_rate = round(clamp(learning_rate * 0.55, 0.02, 0.07), 4)
    proposed_persona_traits = {
        key: round((1.0 - persona_learning_rate) * float(persona_traits[key]) + persona_learning_rate * float(observed_persona[key]), 4)
        for key in observed_persona
    }
    prior_learning_rate = round(clamp(persona_learning_rate * 0.6, 0.015, 0.045), 4)
    proposed_affective_prior = {
        key: round((1.0 - prior_learning_rate) * float(affective_prior.get(key, 0.0)) + prior_learning_rate * float(emotion_vector[key]), 4)
        for key in EMOTION_DIMS
    }
    calibration_learning_rate = round(clamp(0.05 + 0.08 * confirmed["confidence"], 0.05, 0.12), 4)
    prior_consistency = clamp(float(calibration.get("consistency_rate", weight_schedule["effective_consistency"]) or weight_schedule["effective_consistency"]))
    prior_prediction_agreement = clamp(float(calibration.get("prediction_agreement", weight_schedule["effective_consistency"]) or weight_schedule["effective_consistency"]))
    prior_observed_turns = int(calibration.get("observed_turns", 0) or 0)
    prior_posthoc_samples = int(calibration.get("posthoc_samples", 0) or 0)
    prior_consistency_samples = int(calibration.get("consistency_samples", prior_posthoc_samples) or prior_posthoc_samples)
    prior_stable_hits = int(calibration.get("stable_prediction_hits", 0) or 0)
    if consistency_snapshot["available"]:
        proposed_consistency_rate = round((1.0 - calibration_learning_rate) * prior_consistency + calibration_learning_rate * consistency_snapshot["consistency_rate"], 4)
        proposed_prediction_agreement = round((1.0 - calibration_learning_rate) * prior_prediction_agreement + calibration_learning_rate * consistency_snapshot["vector_alignment"], 4)
    else:
        proposed_consistency_rate = round(prior_consistency, 4)
        proposed_prediction_agreement = round((1.0 - calibration_learning_rate) * prior_prediction_agreement + calibration_learning_rate * confirmed["confidence"], 4)
    stable_hit_increment = 1 if consistency_snapshot["available"] and consistency_snapshot["consistency_rate"] >= 0.72 else 0
    proposed_calibration_state = {
        "observed_turns": prior_observed_turns + 1,
        "posthoc_samples": prior_posthoc_samples + (1 if consistency_snapshot["available"] else 0),
        "consistency_samples": prior_consistency_samples + (1 if consistency_snapshot["available"] else 0),
        "stable_prediction_hits": prior_stable_hits + stable_hit_increment,
        "prediction_agreement": proposed_prediction_agreement,
        "consistency_rate": proposed_consistency_rate,
    }
    return {
        "host_profile_update_recommended": bool(confirmed["confidence"] >= 0.58),
        "should_persist": bool(confirmed["confidence"] >= 0.58),
        "learning_rate": learning_rate,
        "persona_learning_rate": persona_learning_rate,
        "prior_learning_rate": prior_learning_rate,
        "calibration_learning_rate": calibration_learning_rate,
        "observed_style": observed_style,
        "observed_persona": observed_persona,
        "proposed_baseline": proposed_baseline,
        "proposed_persona_traits": proposed_persona_traits,
        "proposed_affective_prior": proposed_affective_prior,
        "proposed_calibration_state": proposed_calibration_state,
        "notes": [
            "use EMA merge into the host-owned baseline profile",
            "merge persona traits with a smaller EMA weight",
            "keep affective prior slower than persona traits",
            "keep front or review-pass trust tied to long-run consistency",
            "high-pressure turns keep a lower learning weight",
        ],
    }


def build_routing(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    vector = confirmed["vector"]
    emotion_vector = confirmed["emotion_vector"]
    labels = set(confirmed.get("labels") or [])
    frustration_risk = prediction["frustration_risk"]
    stall_risk = prediction["stall_risk"]
    complexity = prediction["task_complexity"]["score"]
    skeptical_priority = bool(
        (mode == "skeptical" or "skeptical" in labels)
        and (
            emotion_vector["skepticism"] >= 0.32
            or features["speculation_ratio"] >= 0.25
            or features["skepticism_ratio"] >= 0.25
            or features["context_loss_ratio"] >= 0.25
            or features["execution_plumbing_ratio"] >= 0.25
        )
        and (
            features["contradiction_signal"] >= 0.24
            or features["resolution_mismatch"] >= 0.28
            or features["speculation_ratio"] >= 0.25
            or features["context_loss_ratio"] >= 0.25
            or features["execution_plumbing_ratio"] >= 0.25
            or features["same_issue_mentions"] >= 1
            or features["assurance_ratio"] >= 0.25
            or features["stuck_pressure"] >= 0.72
            or features["delay_pressure"] >= 0.42
        )
    )
    if emotion_vector["urgency"] >= 0.88 and emotion_vector["frustration"] >= 0.74:
        queue_mode = "interrupt"
    elif mode in {"urgent", "frustrated"} or skeptical_priority or emotion_vector["urgency"] >= 0.64 or emotion_vector["frustration"] >= 0.62 or stall_risk >= 0.68:
        queue_mode = "steer"
    else:
        queue_mode = "collect"
    prefer_main_thread = bool(mode in {"urgent", "frustrated"} or skeptical_priority or emotion_vector["urgency"] >= 0.56 or emotion_vector["frustration"] >= 0.54 or emotion_vector["confusion"] >= 0.62 or emotion_vector["skepticism"] >= 0.58 or vector["clarity"] <= 0.4 or stall_risk >= 0.62 or features["delay_pressure"] >= 0.6)
    defer_heartbeat = bool(prefer_main_thread or mode in {"urgent", "frustrated"} or frustration_risk >= 0.62 or stall_risk >= 0.62)
    allow_parallel = bool(complexity >= 0.72 and not prefer_main_thread and mode in {"exploratory", "neutral"})
    progress_interval = 10 if frustration_risk >= 0.75 else 15 if mode in {"urgent", "frustrated"} or skeptical_priority or stall_risk >= 0.68 else 20 if complexity >= 0.62 or mode in {"skeptical", "cautious"} or features["guardrail_request"] >= 1.0 else 35
    if mode == "urgent":
        reply_style, verification_level, hermes_personality = "act_then_brief", "high", "concise"
    elif mode == "frustrated":
        reply_style, verification_level, hermes_personality = "repair_then_explain", "high", "concise"
    elif mode == "confused":
        reply_style, verification_level, hermes_personality = "explain_then_act", "high" if features["evidence_request"] >= 1.0 or features["unresolved_turns"] >= 2 or features["same_issue_mentions"] >= 1 else "medium", "teacher"
    elif mode == "skeptical":
        reply_style, verification_level, hermes_personality = "evidence_then_act", "very_high" if skeptical_priority else "high", "analytical"
    elif mode == "satisfied":
        reply_style, verification_level, hermes_personality = "guard_then_close", "high", "helpful"
    elif mode == "cautious":
        reply_style, verification_level, hermes_personality = "verify_then_act", "very_high", "careful"
    else:
        reply_style, verification_level, hermes_personality = "synthesize_then_recommend", "medium", "helpful"
    return {
        "reply_style": reply_style,
        "verification_level": verification_level,
        "thread_interface": {
            "queue_mode": queue_mode,
            "prefer_main_thread": prefer_main_thread,
            "defer_heartbeat": defer_heartbeat,
            "allow_parallel_subagents": allow_parallel,
            "max_parallel_subagents": 2 if allow_parallel else 0 if prefer_main_thread else 1,
            "progress_update_interval_sec": progress_interval,
            "openclaw": {
                "queue_mode": queue_mode,
                "prefer_lane": "main",
                "defer_heartbeat": defer_heartbeat,
                "allow_sessions_spawn": bool(allow_parallel or (complexity >= 0.58 and not prefer_main_thread)),
                "use_sessions_yield": bool(allow_parallel and complexity >= 0.78),
            },
            "hermes": {
                "personality": hermes_personality,
                "busy_input_mode": "interrupt" if mode in {"urgent", "frustrated"} or queue_mode in {"interrupt", "steer"} else "queue",
                "suggested_overlay_scope": "turn-local",
            },
        },
    }


def has_vector_signal(raw: Any, dims: tuple[str, ...]) -> bool:
    return isinstance(raw, dict) and any(dim in raw and raw.get(dim) is not None for dim in dims)


def significant_vector_delta(current: dict[str, Any], previous: dict[str, Any], dims: tuple[str, ...], floor: float = 0.05) -> dict[str, float]:
    deltas: dict[str, float] = {}
    for dim in dims:
        try:
            delta = float(current.get(dim, 0.0)) - float(previous.get(dim, 0.0))
        except (TypeError, ValueError):
            continue
        rounded = round(delta, 4)
        if abs(rounded) >= floor:
            deltas[dim] = rounded
    return deltas


def build_state_delta(payload: dict[str, Any], confirmed: dict[str, Any]) -> dict[str, Any]:
    last_state = payload.get("last_state") or {}
    previous_vector_raw = last_state.get("vector") if isinstance(last_state, dict) else {}
    previous_emotion_raw = last_state.get("emotion_vector") if isinstance(last_state, dict) else {}
    has_interaction = has_vector_signal(previous_vector_raw, STATE_DIMS)
    has_emotion = has_vector_signal(previous_emotion_raw, EMOTION_DIMS)
    if not has_interaction and not has_emotion:
        return {
            "available": False,
            "dominant_shift": "new_turn",
            "emotion": {},
            "interaction": {},
        }

    previous_vector = clamp_dict(previous_vector_raw, STATE_DIMS)
    previous_emotion = clamp_dict(previous_emotion_raw, EMOTION_DIMS)
    interaction_delta = significant_vector_delta(confirmed["vector"], previous_vector, INTERACTION_DIMS)
    emotion_delta = significant_vector_delta(confirmed["emotion_vector"], previous_emotion, EMOTION_DIMS)
    if emotion_delta.get("frustration", 0.0) >= 0.12:
        dominant_shift = "needs_concrete_unblock"
    elif emotion_delta.get("urgency", 0.0) >= 0.12:
        dominant_shift = "needs_priority_action"
    elif emotion_delta.get("skepticism", 0.0) >= 0.12 or interaction_delta.get("trust", 0.0) <= -0.12:
        dominant_shift = "needs_evidence_first"
    elif emotion_delta.get("confusion", 0.0) >= 0.12 or interaction_delta.get("clarity", 0.0) <= -0.12:
        dominant_shift = "needs_alignment_check"
    elif emotion_delta.get("satisfaction", 0.0) >= 0.12:
        dominant_shift = "ready_for_closeout"
    elif emotion_delta.get("satisfaction", 0.0) <= -0.12:
        dominant_shift = "needs_stabilization"
    elif not interaction_delta and not emotion_delta:
        dominant_shift = "stable"
    else:
        dominant_shift = "changed"
    return {
        "available": True,
        "dominant_shift": dominant_shift,
        "emotion": emotion_delta,
        "interaction": interaction_delta,
    }


def validate_route_reasons(reasons: list[str]) -> list[str]:
    valid: list[str] = []
    for reason in unique_labels(reasons):
        if reason in ROUTE_REASON_ENUM:
            valid.append(reason)
    return valid[:6]


def build_route_reasons(
    features: dict[str, Any],
    confirmed: dict[str, Any],
    prediction: dict[str, Any],
    routing: dict[str, Any],
    state_delta: dict[str, Any],
) -> list[str]:
    mode = confirmed["dominant_mode"]
    labels = set(confirmed.get("labels") or [])
    emotion_vector = confirmed["emotion_vector"]
    reasons: list[str] = []
    if routing["thread_interface"]["queue_mode"] in {"steer", "interrupt"}:
        reasons.append("runtime_priority")
    if mode == "urgent" or emotion_vector["urgency"] >= 0.64 or features.get("delay_pressure", 0.0) >= 0.42:
        reasons.append("urgent_pressure")
    if mode == "frustrated" or prediction["frustration_risk"] >= 0.62 or features.get("bug_retries", 0.0) >= 1:
        reasons.append("repeat_failure_pressure")
    if mode == "skeptical" or "skeptical" in labels or features.get("evidence_request", 0.0) >= 1.0:
        reasons.append("evidence_requested")
    if mode == "cautious" or "cautious" in labels or features.get("guardrail_request", 0.0) >= 1.0:
        reasons.append("scope_guard_requested")
    if mode == "confused" or emotion_vector["confusion"] >= 0.58:
        reasons.append("low_clarity")
    if mode == "satisfied" or prediction["guard_needed"]:
        reasons.append("post_success_guard")
    if prediction["stall_risk"] >= 0.62 or features.get("stall_ratio", 0.0) >= 0.25:
        reasons.append("stall_risk")
    if state_delta.get("dominant_shift") in {"needs_concrete_unblock", "needs_evidence_first", "needs_alignment_check", "needs_stabilization", "needs_priority_action"}:
        reasons.append(str(state_delta["dominant_shift"]))
    if features.get("goal_specificity", 0.0) >= 0.48:
        reasons.append("task_specific")
    return validate_route_reasons(reasons)


def build_satisfaction_lock(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    emotion_vector = confirmed["emotion_vector"]
    active = bool(mode == "satisfied" or prediction["guard_needed"] or features.get("success_ratio", 0.0) >= 0.34)
    if not active:
        return {
            "active": False,
            "reason": "inactive",
            "allowed_actions": [],
            "blocked_actions": [],
        }
    if features.get("guard_ratio", 0.0) >= 0.34:
        reason = "post_success_guard"
    elif emotion_vector["satisfaction"] >= 0.5:
        reason = "user_satisfied"
    elif features.get("resolution_claimed", 0.0) >= 1.0:
        reason = "resolution_claimed"
    else:
        reason = "guard_needed"
    return {
        "active": True,
        "reason": reason,
        "allowed_actions": ["summarize_result", "run_regression_check", "prepare_handoff"],
        "blocked_actions": ["expand_scope", "start_new_refactor", "change_config_without_request"],
    }


def build_response_constraints(
    confirmed: dict[str, Any],
    routing: dict[str, Any],
    prediction: dict[str, Any],
    satisfaction_lock: dict[str, Any],
) -> list[str]:
    mode = confirmed["dominant_mode"]
    constraints: list[str] = []
    if mode == "urgent":
        constraints.extend(["lead_with_action", "keep_first_reply_short", "progress_update_required"])
    elif mode == "frustrated":
        constraints.extend(["repair_before_explain", "avoid_repeating_failed_path", "progress_update_required"])
    elif mode == "skeptical":
        constraints.extend(["show_basis_first", "name_verification_steps", "avoid_guessing"])
    elif mode == "cautious":
        constraints.extend(["verify_before_editing", "keep_scope_tight", "protect_user_boundaries"])
    elif mode == "confused":
        constraints.extend(["explain_next_step", "ask_at_most_one_question"])
    elif mode == "satisfied":
        constraints.extend(["guard_mode", "avoid_scope_expansion", "close_with_regression_check"])
    else:
        constraints.extend(["state_recommendation_first", "expand_only_when_useful"])
    if routing["verification_level"] in {"high", "very_high"}:
        constraints.append("include_check_result")
    if prediction["next_update_deadline_sec"] <= 20:
        constraints.append("progress_update_required")
    if satisfaction_lock["active"]:
        constraints.extend(["avoid_scope_expansion", "close_with_regression_check"])
    return unique_labels(constraints)[:8]


def build_system_prompt_addendum(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> str:
    mode = confirmed["dominant_mode"]
    language = features["language"]
    if language == "zh":
        if mode in {"urgent", "frustrated"}:
            return "用户已经多次尝试。先确认当前障碍点的最小复现路径，再给出一个带明确成功判据的下一步。保持进度可见。"
        if mode == "skeptical":
            return "用户希望先看到依据。回复以校验点、命令或日志片段开头，再给结论和下一步。"
        if mode == "confused":
            return "用户需要目标对齐。先用一句话复述你理解的目标，再给一个可纠正的默认路径。"
        if mode == "cautious":
            return "默认保护现有可工作状态。任何变更前先说明范围、校验点和回滚路径。"
        if mode == "satisfied" or prediction["guard_needed"]:
            return "保留当前可工作状态。优先做回归检查、交付说明和收口，避免扩展 scope。"
        return "给出一个具体建议，说明下一步和验证方式。"
    if mode in {"urgent", "frustrated"}:
        return "The user has retried this path. Confirm the smallest reproducible blocking point, then give one next action with a clear success criterion. Keep progress visible."
    if mode == "skeptical":
        return "The user wants evidence before more changes. Start with a verification point, command, or log excerpt, then give the conclusion and next step."
    if mode == "confused":
        return "The user needs goal alignment. Restate the target in one sentence, then give one correctable default path."
    if mode == "cautious":
        return "Protect the current working state by default. Before any change, name the scope, verification point, and rollback path."
    if mode == "satisfied" or prediction["guard_needed"]:
        return "Preserve the working state. Prioritize regression checks, handoff notes, and closeout before adding scope."
    return "Give one concrete recommendation, the next step, and the verification method."


def guidance_tone(mode: str) -> str:
    if mode in {"urgent", "frustrated"}:
        return "concise_and_concrete"
    if mode == "skeptical":
        return "evidence_first"
    if mode == "cautious":
        return "careful_and_bounded"
    if mode == "confused":
        return "alignment_first"
    if mode == "satisfied":
        return "guarded_closeout"
    return "direct_and_useful"


def build_guidance(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    language = features["language"]
    system_prompt_addendum = build_system_prompt_addendum(features, confirmed, prediction)
    tone = guidance_tone(mode)
    should_probe = prediction["probe_needed"]
    allow_emotion_hook = bool(should_probe and mode not in {"urgent", "frustrated", "skeptical"} and prediction["frustration_risk"] < 0.7)
    if not should_probe:
        return {
            "should_probe": False,
            "allow_emotion_hook": False,
            "probe_style": "none",
            "hook_mode": "none",
            "tone": tone,
            "system_prompt_addendum": system_prompt_addendum,
            "soft_probe_seed": "",
            "question": "",
            "reason": "state already clear enough",
        }
    if language == "zh":
        if mode in {"urgent", "frustrated"}:
            question = "先给结果，还是先给报错定位？"
            probe_style = "priority_axis"
            hook_mode = "explicit"
            soft_probe_seed = ""
        elif mode == "confused":
            question = ""
            probe_style = "latent_preference_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首句加入可纠正默认项，例如“我先按一条可落地路径推进”，引导用户自然暴露偏好。"
        elif mode == "skeptical":
            question = ""
            probe_style = "latent_evidence_probe"
            hook_mode = "latent"
            soft_probe_seed = "首句先给依据和校验点，再给动作，让用户自然暴露证据偏好。"
        elif mode == "cautious":
            question = ""
            probe_style = "latent_boundary_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首句先复述安全边界并给出保守默认项，让用户自然补充禁止项。"
        elif prediction["guard_needed"]:
            question = ""
            probe_style = "latent_guard_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首句写成“我先按已达标进入收口检查”，让用户自然选择继续推进或结束。"
        else:
            question = ""
            probe_style = "latent_choice_probe"
            hook_mode = "latent"
            soft_probe_seed = "在首段同时放一个主建议和一个备选方向词，引导用户自然偏向其一。"
    else:
        if mode in {"urgent", "frustrated"}:
            question = "Fix first, or diagnosis first?"
            probe_style = "priority_axis"
            hook_mode = "explicit"
            soft_probe_seed = ""
        elif mode == "confused":
            question = ""
            probe_style = "latent_preference_probe"
            hook_mode = "latent"
            soft_probe_seed = "Open with a default path such as 'I will start with one concrete path' so the user can correct it naturally."
        elif mode == "skeptical":
            question = ""
            probe_style = "latent_evidence_probe"
            hook_mode = "latent"
            soft_probe_seed = "Lead with the basis and one concrete verification point before the action plan."
        elif mode == "cautious":
            question = ""
            probe_style = "latent_boundary_probe"
            hook_mode = "latent"
            soft_probe_seed = "State a conservative safety assumption in the first line so the user can refine boundaries without a hard stop."
        elif prediction["guard_needed"]:
            question = ""
            probe_style = "latent_guard_probe"
            hook_mode = "latent"
            soft_probe_seed = "Frame the next step as a guard-mode default so the user can continue or close naturally."
        else:
            question = ""
            probe_style = "latent_choice_probe"
            hook_mode = "latent"
            soft_probe_seed = "Lead with one recommendation and mention one soft alternative to invite natural preference disclosure."
    return {
        "should_probe": True,
        "allow_emotion_hook": allow_emotion_hook,
        "probe_style": probe_style,
        "hook_mode": hook_mode,
        "tone": tone,
        "system_prompt_addendum": system_prompt_addendum,
        "soft_probe_seed": soft_probe_seed if allow_emotion_hook else "",
        "question": question,
        "reason": "clarity is low or frustration risk is rising",
    }


def build_posthoc_plan(features: dict[str, Any], confirmed: dict[str, Any], analysis: dict[str, Any], weight_schedule: dict[str, Any]) -> dict[str, Any]:
    mode = confirmed["dominant_mode"]
    stage = weight_schedule["stage"]
    low_signal = confirmed["confidence"] < 0.64 or analysis["ambiguity"] >= 0.22
    weak_shift = bool(features["skepticism_ratio"] >= 0.25 or features["hedge_ratio"] >= 0.25 or features["assurance_ratio"] >= 0.25 or features["dismissive_pressure"] >= 0.26 or features["tempo_pause_pressure"] >= 0.28 or features["questions"] >= 1)
    low_consistency = weight_schedule["effective_consistency"] <= 0.58
    should_run = True
    if stage == "bootstrap" or weight_schedule["effective_consistency"] <= 0.38:
        style = "full_decompose"
        max_response_tokens = 180
        target_ms = 550
        reason = "bootstrap review pass stays enabled while consistency is still cold"
    elif stage == "calibrating" or low_consistency or low_signal or weak_shift or mode in {"confused", "skeptical"}:
        style = "compact_decompose"
        max_response_tokens = 110
        target_ms = 360
        reason = "calibration still benefits from a richer review pass"
    else:
        style = "micro_reflection"
        max_response_tokens = 56
        target_ms = 140
        reason = "front-versus-review agreement is stable so the review pass stays compact"
    return {
        "should_run": should_run,
        "execution_mode": "shadow_review",
        "surface": "runtime_internal",
        "style": style,
        "target_ms": target_ms,
        "max_response_tokens": max_response_tokens,
        "weight": weight_schedule["posthoc_weight"],
        "reason": reason,
    }


def render_overlay(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any], routing: dict[str, Any], analysis: dict[str, Any]) -> str:
    signal_alias = {
        "urgency_terms": "urg",
        "frustration_terms": "frus",
        "stall_terms": "stall",
        "repeated_user_emphasis": "repeat",
        "punctuation_intensity": "punct",
        "dismissive_cue": "dismiss",
        "tempo_pause_cue": "tempo",
        "textism_cue": "textism",
        "abrupt_short_reply": "abrupt",
        "task_object_anchor": "task",
        "delay_pressure": "delay",
        "stuck_issue_pressure": "stuck",
        "resolution_mismatch": "mismatch",
        "guard_terms": "guard",
        "boundary_terms": "bound",
        "skepticism_terms": "skept",
        "evidence_request": "proof",
        "structured_compare": "compare",
        "guardrail_request": "guardreq",
        "technical_context": "tech",
    }
    actions: list[str] = []
    mode = confirmed["dominant_mode"]
    if mode in {"urgent", "frustrated"}:
        actions.extend(["act-first", "short-first-reply"])
    elif mode == "confused":
        actions.extend(["stepwise", "one-clarifier-max"])
    elif mode == "skeptical":
        actions.extend(["show-basis", "light-proof"])
    elif mode == "satisfied":
        actions.extend(["guard-mode", "drift-check"])
    elif mode == "cautious":
        actions.extend(["verify-first", "keep-scope-tight"])
    else:
        actions.extend(["decisive", "expand-only-if-useful"])
    signals = ",".join(signal_alias.get(item, item) for item in analysis["priority_reason"][:2]) if analysis["priority_reason"] else mode
    return (
        f"<state mode={mode} route={routing['thread_interface']['queue_mode']} "
        f"main={1 if routing['thread_interface']['prefer_main_thread'] else 0} "
        f"hb={'defer' if routing['thread_interface']['defer_heartbeat'] else 'normal'} "
        f"parallel={1 if routing['thread_interface']['allow_parallel_subagents'] else 0} "
        f"style={routing['reply_style']} verify={routing['verification_level']} "
        f"upd={routing['thread_interface']['progress_update_interval_sec']}s "
        f"probe={1 if prediction['probe_needed'] else 0} "
        f"sem={analysis['semantic_pass']}>\n"
        f"signals:{signals}; actions:{','.join(actions)}\n"
        "</state>"
    )


def render_debug_overlay(features: dict[str, Any], confirmed: dict[str, Any], prediction: dict[str, Any], routing: dict[str, Any], analysis: dict[str, Any]) -> str:
    return (
        "<emotion_context>\n"
        f"mode: {confirmed['dominant_mode']}\n"
        f"labels: {', '.join(confirmed['labels'])}\n"
        f"emotion_vector: {json.dumps(confirmed['emotion_vector'], ensure_ascii=False, separators=(',', ':'))}\n"
        f"confidence: {confirmed['confidence']}\n"
        f"reply_style: {routing['reply_style']}\n"
        f"verification_level: {routing['verification_level']}\n"
        f"queue_mode: {routing['thread_interface']['queue_mode']}\n"
        f"prefer_main_thread: {str(routing['thread_interface']['prefer_main_thread']).lower()}\n"
        f"defer_heartbeat: {str(routing['thread_interface']['defer_heartbeat']).lower()}\n"
        f"progress_update_interval_sec: {routing['thread_interface']['progress_update_interval_sec']}\n"
        f"frustration_risk: {prediction['frustration_risk']}\n"
        f"task_complexity: {prediction['task_complexity']['level']}\n"
        f"semantic_pass: {analysis['semantic_pass']}\n"
        f"signals: {', '.join(analysis['priority_reason'])}\n"
        "</emotion_context>"
    )


def build_model_prompts(payload: dict[str, Any], screen: dict[str, Any], confirmed: dict[str, Any], routing: dict[str, Any], prediction: dict[str, Any], analysis: dict[str, Any], weight_schedule: dict[str, Any], posthoc_plan: dict[str, Any]) -> dict[str, str]:
    latest = str(payload.get("message") or "").strip()[:160]
    history = payload.get("history") or []
    runtime = payload.get("runtime") or {}
    user_profile = load_user_profile(payload, {"degraded": False, "degradation_reasons": []})
    history_excerpt = [{"r": item.get("role", ""), "t": str(item.get("text") or item.get("content") or "")[:80]} for item in history[-3:]]
    profile_hint = {
        "tz": user_profile["timezone"],
        "h": user_profile["local_hour"],
        "work": user_profile["in_work_window"],
        "delay": user_profile["baseline"]["response_delay_seconds"],
        "polite": user_profile["baseline"]["politeness"],
        "terse": user_profile["baseline"]["terseness"],
        "prior": user_profile["affective_prior"],
        "persona": user_profile["persona_traits"],
    }
    fast_screen_prompt = (
        "Classify current user work-state for an agent runtime.\n"
        "Prioritize delay against user baseline, same-issue pressure, hang/stuck wording, terse abrupt replies, dismissive short phrases, rhythmic pause cues, missed-expectation timing cues, success/guard signals, evidence-seeking skepticism, and anti-guesswork language.\n"
        "Return JSON only: {\"m\":\"urgent\",\"labels\":[\"urgent\"],\"vector\":{\"urgency\":0.0,\"frustration\":0.0,\"clarity\":0.0,\"satisfaction\":0.0,\"trust\":0.0,\"engagement\":0.0},\"emotion_vector\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},\"why\":[\"delay\"]}\n"
        f"latest={latest}\n"
        f"hist={json.dumps(history_excerpt, ensure_ascii=False, separators=(',', ':'))}\n"
        f"usr={json.dumps(profile_hint, ensure_ascii=False, separators=(',', ':'))}\n"
        f"rt={json.dumps(runtime, ensure_ascii=False, separators=(',', ':'))}"
    )
    fast_confirmation_prompt = (
        "Fuse the rule screen with runtime pressure.\n"
        "Treat nonstandard punctuation, textisms, and deliberate misspellings as weak cues unless runtime pressure, retries, or contradiction support them.\n"
        "Return JSON only: {\"m\":\"urgent\",\"labels\":[\"urgent\"],\"conf\":0.0,\"vector\":{\"urgency\":0.0,\"frustration\":0.0,\"clarity\":0.0,\"satisfaction\":0.0,\"trust\":0.0,\"engagement\":0.0},\"emotion_vector\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},\"acts\":[\"act-first\"]}\n"
        f"screen={json.dumps(screen, ensure_ascii=False, separators=(',', ':'))}\n"
        f"usr={json.dumps(profile_hint, ensure_ascii=False, separators=(',', ':'))}\n"
        f"rt={json.dumps(runtime, ensure_ascii=False, separators=(',', ':'))}"
    )
    review_pass_prompt = (
        "Run a runtime-only follow-up review for the latest user message.\n"
        "Decompose latent affect and stance cues for bounded calibration.\n"
        "Extract the exact wording, hedge, correction, punctuation, tempo clue, textism, deliberate typo, nonstandard spelling, or stance marker that carries emotion.\n"
        "Focus on weak shifts such as hedging, correction, doubt, evidence-seeking, anti-guesswork language, scope protection, frustration, urgency, satisfaction, openness, dismissive short replies, rhythmic pauses, and missed-expectation timing language.\n"
        "Return JSON only: "
        "{\"emotion_vector\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},"
        "\"labels\":[\"skeptical\"],\"confidence\":0.0,\"emotionality\":0.0,"
        "\"composition\":{\"urgency\":0.0,\"frustration\":0.0,\"confusion\":0.0,\"skepticism\":0.0,\"satisfaction\":0.0,\"cautiousness\":0.0,\"openness\":0.0},"
        "\"cue_spans\":[{\"text\":\"不一定\",\"signal\":\"skepticism\",\"kind\":\"hedge\",\"strength\":0.4}],"
        "\"notes\":[\"light hedge\"]}\n"
        f"stage={weight_schedule['stage']}\n"
        f"front_weight={weight_schedule['screen_weight']}\n"
        f"posthoc_weight={weight_schedule['posthoc_weight']}\n"
        f"front_consistency={weight_schedule['effective_consistency']}\n"
        f"execution_mode={posthoc_plan['execution_mode']}\n"
        f"latest={latest}\n"
        f"hist={json.dumps(history_excerpt, ensure_ascii=False, separators=(',', ':'))}\n"
        f"usr={json.dumps(profile_hint, ensure_ascii=False, separators=(',', ':'))}\n"
        f"screen_labels={json.dumps(screen['labels'], ensure_ascii=False, separators=(',', ':'))}\n"
        f"posthoc_style={posthoc_plan['style']}"
    )
    return {
        "fast_screen_prompt": fast_screen_prompt,
        "fast_confirmation_prompt": fast_confirmation_prompt,
        "review_pass_prompt": review_pass_prompt,
        "posthoc_reflection_prompt": review_pass_prompt,
        "overlay_prompt": render_overlay({}, confirmed, prediction, routing, analysis),
    }


def run_pipeline(payload: dict[str, Any]) -> dict[str, Any]:
    normalized_payload, diagnostics = normalize_payload(payload)
    features = build_features(normalized_payload, diagnostics)
    profile_state = build_profile_state(features)
    constraint_signals = build_constraint_signals(features)
    weight_schedule = build_weight_schedule(normalized_payload, features)
    screen = initial_screen(features)
    confirmed = confirm_state(normalized_payload, features, screen, weight_schedule)
    consistency_snapshot = build_consistency_snapshot(normalized_payload, screen)
    memory_update = build_memory_update(normalized_payload, features, confirmed, weight_schedule, consistency_snapshot)
    prediction = predict_state(features, confirmed)
    analysis = build_analysis_plan(features, screen, confirmed, prediction)
    routing = build_routing(features, confirmed, prediction)
    state_delta = build_state_delta(normalized_payload, confirmed)
    route_reasons = build_route_reasons(features, confirmed, prediction, routing, state_delta)
    satisfaction_lock = build_satisfaction_lock(features, confirmed, prediction)
    response_constraints = build_response_constraints(confirmed, routing, prediction, satisfaction_lock)
    guidance = build_guidance(features, confirmed, prediction)
    posthoc_plan = build_posthoc_plan(features, confirmed, analysis, weight_schedule)
    posthoc_shadow = build_posthoc_shadow(normalized_payload, features, confirmed, analysis, posthoc_plan)
    collection_stack = build_collection_stack(weight_schedule, features, posthoc_plan)
    overlay_prompt = render_overlay(features, confirmed, prediction, routing, analysis)
    debug_overlay_prompt = render_debug_overlay(features, confirmed, prediction, routing, analysis)
    prompts = build_model_prompts(normalized_payload, screen, confirmed, routing, prediction, analysis, weight_schedule, posthoc_plan)
    prompts["overlay_prompt"] = overlay_prompt
    prompts["debug_overlay_prompt"] = debug_overlay_prompt
    degradation_reasons = finalize_degradation_reasons(diagnostics)
    return {
        "schema_version": SCHEMA_VERSION,
        "degraded": bool(diagnostics["degraded"]),
        "degradation_reasons": degradation_reasons,
        "host_capabilities": normalized_payload.get("host_capabilities", {}),
        "profile_state": profile_state,
        "memory_update": memory_update,
        "constraint_signals": constraint_signals,
        "weight_schedule": weight_schedule,
        "collection_stack": collection_stack,
        "consistency_snapshot": consistency_snapshot,
        "review_plan": posthoc_plan,
        "posthoc_plan": posthoc_plan,
        "review_shadow": posthoc_shadow,
        "posthoc_shadow": posthoc_shadow,
        "features": features,
        "initial_screen": screen,
        "confirmed_state": confirmed,
        "prediction": prediction,
        "analysis": analysis,
        "routing": routing,
        "route_reasons": route_reasons,
        "response_constraints": response_constraints,
        "state_delta": state_delta,
        "satisfaction_lock": satisfaction_lock,
        "guidance": guidance,
        "overlay_prompt": overlay_prompt,
        "debug_overlay_prompt": debug_overlay_prompt,
        "prompts": prompts,
    }


def parse_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if args.input:
        payload.update(require_json_object(load_json_file(args.input) or {}, f"--input {args.input}"))
    elif not sys.stdin.isatty():
        stdin_text = sys.stdin.read().strip()
        if stdin_text:
            payload.update(require_json_object(json.loads(stdin_text), "stdin"))
    if args.message:
        payload["message"] = args.message
    if args.history_file:
        payload["history"] = load_json_file(args.history_file)
    if args.runtime_file:
        payload["runtime"] = load_json_file(args.runtime_file)
    if args.state_file:
        payload["last_state"] = load_json_file(args.state_file)
    if args.llm_file:
        payload["llm_semantic"] = load_json_file(args.llm_file)
    if getattr(args, "review_file", None):
        payload["review_semantic"] = load_json_file(args.review_file)
    if getattr(args, "posthoc_file", None):
        legacy_review = load_json_file(args.posthoc_file)
        payload["posthoc_semantic"] = legacy_review
        payload.setdefault("review_semantic", legacy_review)
    if getattr(args, "calibration_file", None):
        payload["calibration_state"] = load_json_file(args.calibration_file)
    if getattr(args, "include_raw_emotion", False):
        host_capabilities = dict(payload.get("host_capabilities") or {})
        host_capabilities["include_raw_emotion"] = True
        payload["host_capabilities"] = host_capabilities
    return payload


def select_output(command: str, full: dict[str, Any]) -> Any:
    contract = {
        "schema_version": full["schema_version"],
        "degraded": full["degraded"],
        "degradation_reasons": full["degradation_reasons"],
    }
    if command == "host":
        return build_host_output(full)
    if command == "screen":
        return {**contract, "features": full["features"], "initial_screen": full["initial_screen"]}
    if command == "confirm":
        return {**contract, "confirmed_state": full["confirmed_state"], "weight_schedule": full["weight_schedule"], "consistency_snapshot": full["consistency_snapshot"]}
    if command == "predict":
        return {**contract, "prediction": full["prediction"], "analysis": full["analysis"]}
    if command == "route":
        return {**contract, "routing": full["routing"]}
    if command == "guide":
        return {**contract, "guidance": full["guidance"]}
    if command == "posthoc":
        return {
            **contract,
            "collection_stack": full["collection_stack"],
            "review_plan": full["review_plan"],
            "posthoc_plan": full["posthoc_plan"],
            "review_shadow": full["review_shadow"],
            "posthoc_shadow": full["posthoc_shadow"],
            "weight_schedule": full["weight_schedule"],
            "consistency_snapshot": full["consistency_snapshot"],
            "review_pass_prompt": full["prompts"]["review_pass_prompt"],
            "posthoc_reflection_prompt": full["prompts"]["posthoc_reflection_prompt"],
        }
    if command == "overlay":
        return {**contract, "overlay_prompt": full["overlay_prompt"], "debug_overlay_prompt": full["debug_overlay_prompt"]}
    return full


def raw_emotion_requested(full: dict[str, Any]) -> bool:
    capabilities = full.get("host_capabilities") or {}
    return any(bool(capabilities.get(key)) for key in RAW_HOST_CAPABILITY_KEYS)


def build_host_state_delta(state_delta: dict[str, Any]) -> dict[str, Any]:
    dominant_shift = str(state_delta.get("dominant_shift", "changed"))
    interaction_delta = dict(state_delta.get("interaction") or {})
    interaction_needs: list[str] = []
    if interaction_delta.get("clarity", 0.0) <= -0.05:
        interaction_needs.append("alignment_check")
    if interaction_delta.get("trust", 0.0) <= -0.05:
        interaction_needs.append("evidence_first")
    if interaction_delta.get("engagement", 0.0) <= -0.05:
        interaction_needs.append("keep_progress_visible")
    return {
        "available": bool(state_delta.get("available")),
        "dominant_shift": STATE_SHIFT_ALIASES.get(dominant_shift, dominant_shift),
        "interaction": {
            "changed": bool(interaction_delta),
            "needs": unique_labels(interaction_needs),
        },
    }


def build_host_output(full: dict[str, Any]) -> dict[str, Any]:
    confirmed = full["confirmed_state"]
    routing = full["routing"]
    thread_interface = routing["thread_interface"]
    memory_update = full["memory_update"]
    emotion_vector = clamp_dict(confirmed.get("emotion_vector"), EMOTION_DIMS)
    interaction_state = clamp_dict(confirmed.get("interaction_state"), INTERACTION_DIMS)
    output = {
        "schema_version": full["schema_version"],
        "degraded": full["degraded"],
        "degradation_reasons": full["degradation_reasons"],
        "mode": confirmed["dominant_mode"],
        "confidence": confirmed["confidence"],
        "overlay_prompt": full["overlay_prompt"],
        "route_reasons": full["route_reasons"],
        "response_constraints": full["response_constraints"],
        "satisfaction_lock": full["satisfaction_lock"],
        "interaction_state": interaction_state,
        "routing": {
            "reply_style": routing["reply_style"],
            "verification_level": routing["verification_level"],
            "queue_mode": thread_interface["queue_mode"],
            "prefer_main_thread": thread_interface["prefer_main_thread"],
            "defer_heartbeat": thread_interface["defer_heartbeat"],
            "allow_parallel_subagents": thread_interface["allow_parallel_subagents"],
            "max_parallel_subagents": thread_interface["max_parallel_subagents"],
            "progress_update_interval_sec": thread_interface["progress_update_interval_sec"],
        },
        "guidance": {
            "should_probe": full["guidance"]["should_probe"],
            "hook_mode": full["guidance"]["hook_mode"],
            "probe_style": full["guidance"]["probe_style"],
            "tone": full["guidance"]["tone"],
            "system_prompt_addendum": full["guidance"]["system_prompt_addendum"],
            "question": full["guidance"]["question"],
            "soft_probe_seed": full["guidance"]["soft_probe_seed"],
        },
        "state": {
            "interaction_state": interaction_state,
            "state_delta": build_host_state_delta(full["state_delta"]),
        },
        "memory": {
            "should_persist": memory_update["should_persist"],
            "host_profile_update_recommended": memory_update["host_profile_update_recommended"],
            "proposed_calibration_state": memory_update["proposed_calibration_state"],
        },
    }
    if raw_emotion_requested(full):
        output["diagnostics"] = {
            "internal": {
                "labels": confirmed["labels"],
                "emotion_vector": emotion_vector,
                "state_delta": full["state_delta"],
                "mode_scores": confirmed.get("mode_scores", {}),
            }
        }
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emotion-aware routing and prompt overlay engine.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("host", "screen", "confirm", "predict", "route", "guide", "posthoc", "overlay", "run"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--input", help="Path to a JSON payload.")
        sub.add_argument("--message", help="Latest user message.")
        sub.add_argument("--history-file", help="Path to history JSON.")
        sub.add_argument("--runtime-file", help="Path to runtime JSON.")
        sub.add_argument("--state-file", help="Path to last_state JSON.")
        sub.add_argument("--llm-file", help="Path to llm_semantic JSON.")
        sub.add_argument("--review-file", help="Path to review_semantic JSON.")
        sub.add_argument("--posthoc-file", help="Path to posthoc_semantic JSON.")
        sub.add_argument("--calibration-file", help="Path to calibration_state JSON.")
        sub.add_argument("--include-raw-emotion", action="store_true", help="Include internal raw affect diagnostics in host output.")
        sub.add_argument("--output", help="Path to write JSON output.")
        sub.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        payload = parse_payload(args)
    except FileNotFoundError as exc:
        parser.exit(2, f"{exc}\n")
    except json.JSONDecodeError as exc:
        parser.exit(2, f"Invalid JSON input: {exc}\n")
    except ValueError as exc:
        parser.exit(2, f"{exc}\n")
    if not payload.get("message"):
        parser.error("A message is required via --message, --input, or stdin JSON.")
    full = run_pipeline(payload)
    selected = select_output(args.command, full)
    rendered = dump_json(selected, args.pretty)
    if args.output:
        try:
            atomic_write_text(Path(args.output), rendered)
        except OSError as exc:
            parser.exit(2, f"Could not write output {args.output}: {exc}\n")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
