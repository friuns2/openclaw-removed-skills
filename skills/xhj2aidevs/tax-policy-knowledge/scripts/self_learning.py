#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财税政策知识库 - 自主学习脚本
self_learning.py

功能：
  1. 记录用户交互过程中产生的知识增量
  2. 分析高频问题，补充到FAQ章节
  3. 记录用户的纠正和补充信息
  4. 定期（每月）将已验证的学习内容合并到主知识库
  5. 维护学习日志（references/learning_log.md）

调用时机：
  - 用户说"正确"、"不对"、"补充"时触发纠正学习
  - 用户说"有用"或"谢谢"时记录最佳实践
  - 每月末自动触发知识合并

用法：
  python self_learning.py --learn "用户说..." --content "正确内容"
  python self_learning.py --merge           # 执行知识合并
  python self_learning.py --stats          # 查看学习统计
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
from typing import Optional

# ─────────────────────────────────────────
# 配置区
# ─────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent.resolve()
LEARNING_LOG = SKILL_DIR / "references" / "learning_log.md"
DATABASE_FILE = SKILL_DIR / "references" / "tax-policy-database.md"
FAQ_FILE = SKILL_DIR / "references" / "faq.md"
SELF_LEARNING_SCRIPT_DIR = Path(__file__).parent

LEARNING_VERSION = "v1.0.0"
LEARNING_DATE = datetime.now().strftime("%Y-%m-%d")

# ─────────────────────────────────────────
# 触发关键词配置
# ─────────────────────────────────────────
TRIGGER_CORRECTION = ["正确", "不对", "错了", "纠正", "修正", "更正", "实际上", "其实", "应该", "不是这样", "No,", "actually"]
TRIGGER_POSITIVE = ["有用", "谢谢", "太好了", "很有帮助", "对的", "好的", "清楚了", "明白了", "满意", "帮了大忙"]
TRIGGER_SUPPLEMENT = ["补充", "还有", "另外", "补充一下", "再补充", "顺便说一下", "另外补充"]
TRIGGER_FREQUENT = ["高频", "经常问", "重复问", "常见问题", "FAQ"]

# ─────────────────────────────────────────
# 学习记录模板
# ─────────────────────────────────────────
LEARNING_LOG_TEMPLATE = """# 学习日志 (Learning Log)

> 版本：{version} | 创建日期：{create_date}
> 本文件记录知识库在用户交互过程中的增量学习内容。
> 已验证的内容会在每月末自动合并到主知识库。

---

## 一、使用说明

### 1.1 如何触发学习记录
| 触发场景 | 触发关键词 | 说明 |
|---------|---------|------|
| 用户纠正答案 | 正确、不对、错了、纠正... | 将正确信息记录到"纠正记录"章节 |
| 用户补充信息 | 补充、还有、另外... | 将补充内容追加到对应章节 |
| 用户正向反馈 | 有用、谢谢、太好了... | 记录最佳实践问答模式 |
| 高频问题 | 3次以上重复问同一问题 | 补充到"高频问题"章节 |

### 1.2 记录格式
每条记录格式：
```markdown
### [ID] {时间} - {类型}
- 触发场景：{具体场景描述}
- 学习内容：{从用户交互中学到的内容}
- 来源：用户反馈 / 自动学习 / 知识合并
- 验证状态：[OK] 已验证 / ⏳ 待验证 / [FAIL] 已废弃
- 合并状态：[OK] 已合并 / ⏳ 待合并
```

---

## 二、学习记录

"""

# ─────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────
def log(msg: str):
    """带时间戳的日志输出（兼容Windows GBK控制台）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 移除emoji以兼容Windows GBK控制台
    clean_msg = re.sub(r'[\U00010000-\U0010ffff]', '', msg)
    print(f"[{timestamp}] {clean_msg}", flush=True)


def read_file_content(filepath: Path) -> str:
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def write_file_content(filepath: Path, content: str):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    log(f"[OK] 文件已保存：{filepath}")


def get_log_id(existing_content: str) -> int:
    """从现有日志中提取最大ID，+1后返回"""
    ids = re.findall(r"### \[(\d+)\]", existing_content)
    if ids:
        return max(int(i) for i in ids) + 1
    return 1


def detect_learning_type(user_input: str) -> str:
    """根据用户输入内容自动判断学习类型"""
    for kw in TRIGGER_CORRECTION:
        if kw in user_input:
            return "纠正"
    for kw in TRIGGER_SUPPLEMENT:
        if kw in user_input:
            return "补充"
    for kw in TRIGGER_POSITIVE:
        if kw in user_input:
            return "正向反馈"
    return "其他"


def build_learning_entry(
    log_id: int,
    learning_type: str,
    trigger_scene: str,
    content: str,
    source: str = "用户反馈",
) -> str:
    """构建一条学习记录"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""
### [{log_id}] {timestamp} - {learning_type}
- **触发场景**：{trigger_scene}
- **学习内容**：{content}
- **来源**：{source}
- **验证状态**：⏳ 待验证
- **合并状态**：⏳ 待合并
"""
    return entry


def update_learning_log(entry: str, log_id: int):
    """追加学习记录到日志文件"""
    existing = read_file_content(LEARNING_LOG)

    if not existing or existing.strip() == "":
        # 创建新文件
        new_content = LEARNING_LOG_TEMPLATE.format(
            version=LEARNING_VERSION,
            create_date=LEARNING_DATE,
        ) + "\n" + entry
    else:
        # 在"## 二、学习记录" 之后插入
        marker = "## 二、学习记录"
        if marker in existing:
            parts = existing.split(marker)
            new_content = parts[0] + marker + entry + "\n" + parts[1]
        else:
            new_content = existing + "\n" + entry

    write_file_content(LEARNING_LOG, new_content)


def merge_verified_learning() -> dict:
    """将已验证的学习内容合并到主知识库"""
    log(" 开始执行知识合并...")

    log_content = read_file_content(LEARNING_LOG)
    if not log_content:
        return {"merged": 0, "message": "学习日志为空，无需合并。"}

    # 提取所有"待合并"且"已验证"的记录
    pending_records = []
    # 匹配记录块
    pattern = r"### \[\d+\].*?(?=\n### \[\d+\]|\n---\n## |\Z)"
    matches = re.findall(pattern, log_content, re.DOTALL)

    for match in matches:
        if "⏳ 待合并" in match and "[OK] 已验证" in match:
            # 提取学习内容
            content_match = re.search(r"\*\*学习内容\*\*：(.+)", match)
            type_match = re.search(r"- \d{4}-\d{2}-\d{2} \d{2}:\d{2} - (.+)", match)
            if content_match and type_match:
                pending_records.append({
                    "content": content_match.group(1).strip(),
                    "type": type_match.group(1).strip(),
                    "raw": match.strip(),
                })

    if not pending_records:
        return {"merged": 0, "message": "没有需要合并的记录（待验证或待合并状态）。"}

    # 读取FAQ文件
    faq_content = read_file_content(FAQ_FILE)

    # 构建新的FAQ内容
    faq_entries = "\n".join([
        f"- **{r['type']}**：{r['content']}" for r in pending_records
    ])

    if faq_content:
        new_faq = faq_content + "\n\n### 自动学习补充\n" + faq_entries
    else:
        new_faq = f"""# 常见问题FAQ

> 版本：v1.0.0 | 更新日期：{datetime.now().strftime("%Y-%m-%d")}
> 本文件由自学习脚本自动生成，记录高频问题和最佳答案。

## 自动学习补充
{faq_entries}
"""

    write_file_content(FAQ_FILE, new_faq)

    # 更新学习日志，标记已合并
    for record in pending_records:
        log_content = log_content.replace(
            record["raw"],
            record["raw"].replace("⏳ 待合并", "[OK] 已合并")
        )
    write_file_content(LEARNING_LOG, log_content)

    return {
        "merged": len(pending_records),
        "message": f"成功合并 {len(pending_records)} 条已验证记录到 FAQ。"
    }


def get_learning_stats() -> dict:
    """获取学习统计信息"""
    log_content = read_file_content(LEARNING_LOG)

    if not log_content:
        return {
            "total": 0,
            "verified": 0,
            "pending": 0,
            "merged": 0,
            "by_type": {},
        }

    records = re.findall(r"### \[\d+\].*?(?=\n### \[\d+\]|\n---\n## |\Z)", log_content, re.DOTALL)

    stats = {
        "total": len(records),
        "verified": len([r for r in records if "[OK] 已验证" in r]),
        "pending": len([r for r in records if "⏳ 待验证" in r]),
        "merged": len([r for r in records if "[OK] 已合并" in r]),
        "by_type": {},
    }

    for record in records:
        type_match = re.search(r"- \d{4}-\d{2}-\d{2} \d{2}:\d{2} - (.+)", record)
        if type_match:
            t = type_match.group(1).strip()
            stats["by_type"][t] = stats["by_type"].get(t, 0) + 1

    return stats


def run_learn_from_user(
    user_input: str,
    skill_output: str = "",
    user_feedback: str = "",
    context: str = "",
) -> dict:
    """
    从用户输入中学习

    参数：
      user_input：用户原始输入
      skill_output：技能原始回答
      user_feedback：用户反馈内容
      context：对话上下文

    返回：{"learned": bool, "log_id": int, "message": str}
    """
    learning_type = detect_learning_type(user_input + " " + user_feedback)
    log(f" 检测到学习类型：{learning_type}")

    # 初始化日志文件
    existing = read_file_content(LEARNING_LOG)
    log_id = get_log_id(existing)

    # 构建学习内容
    if learning_type == "纠正":
        content = f"用户纠正：{user_feedback or user_input}。参考回答：{skill_output[:200]}"
    elif learning_type == "补充":
        content = f"用户补充：{user_feedback or user_input}"
    elif learning_type == "正向反馈":
        content = f"问答模式被标记为有用。问题：{user_input[:100]}，回答：{skill_output[:200]}"
    else:
        content = f"交互记录：{user_input[:100]}"

    entry = build_learning_entry(
        log_id=log_id,
        learning_type=learning_type,
        trigger_scene=context or user_input[:80],
        content=content,
    )

    update_learning_log(entry, log_id)

    return {
        "learned": True,
        "log_id": log_id,
        "learning_type": learning_type,
        "message": f"[OK] 已记录学习（类型：{learning_type}，ID：{log_id}）",
    }


def add_high_freq_question(question: str, answer: str, source: str = "自动统计"):
    """添加高频问题到FAQ"""
    log(f" 添加高频问题：{question[:50]}...")

    existing = read_file_content(LEARNING_LOG)
    log_id = get_log_id(existing)

    entry = build_learning_entry(
        log_id=log_id,
        learning_type="高频问题",
        trigger_scene=f"来源：{source}",
        content=f"Q：{question}\nA：{answer}",
    )

    update_learning_log(entry, log_id)
    return {"added": True, "log_id": log_id}


def auto_learn_from_conversation(conversation_history: list) -> dict:
    """
    从对话历史中自动分析并学习

    参数：conversation_history - 对话历史列表
         每个元素格式：{"role": "user/assistant", "content": "...", "feedback": "..."}

    返回：{"learned_count": int, "high_freq_questions": list}
    """
    log(f" 开始分析对话历史，共 {len(conversation_history)} 条记录...")

    # 统计用户问题频率
    user_questions = {}
    for msg in conversation_history:
        if msg.get("role") == "user":
            q = msg.get("content", "")[:100]
            user_questions[q] = user_questions.get(q, 0) + 1

    # 找出高频问题（出现3次以上）
    high_freq = {q: c for q, c in user_questions.items() if c >= 3}

    learned = []
    for q, count in high_freq.items():
        result = add_high_freq_question(
            question=q,
            answer="[待补充最佳答案]",
            source=f"自动统计（出现{count}次）",
        )
        learned.append(result)

    return {
        "learned_count": len(learned),
        "high_freq_questions": list(high_freq.keys()),
        "total_messages": len(conversation_history),
    }


# ─────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="财税政策知识库 - 自主学习脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python self_learning.py --learn "用户输入" --feedback "正确内容"
  python self_learning.py --input "用户输入" --output "原回答" --feedback "用户纠正内容"
  python self_learning.py --merge           # 执行知识合并（将已验证内容合入FAQ）
  python self_learning.py --stats           # 查看学习统计
  python self_learning.py --check           # 检查学习日志状态
        """
    )
    parser.add_argument("--learn", type=str, default="", help="用户原始输入或反馈内容")
    parser.add_argument("--feedback", type=str, default="", help="用户纠正/补充的具体内容")
    parser.add_argument("--input", type=str, default="", help="用户问题（原输入）")
    parser.add_argument("--output", type=str, default="", help="技能原回答")
    parser.add_argument("--context", type=str, default="", help="对话上下文")
    parser.add_argument("--merge", action="store_true", help="执行知识合并")
    parser.add_argument("--stats", action="store_true", help="查看学习统计")
    parser.add_argument("--check", action="store_true", help="检查学习日志状态")
    parser.add_argument("--source", type=str, default="manual", help="学习来源（manual/auto_update/conversation）")
    parser.add_argument("--count", type=str, default="0", help="学习条目数量")
    parser.add_argument("--version", action="version", version=f"%(prog)s {LEARNING_VERSION}")

    args = parser.parse_args()

    print("=" * 60)
    print("  财税政策知识库 - 自主学习脚本")
    print(f"  版本：{LEARNING_VERSION} | 日期：{LEARNING_DATE}")
    print("=" * 60)

    if args.merge:
        result = merge_verified_learning()
        print(f"\n{'[OK]' if result['merged'] > 0 else '[INFO]'} {result['message']}")

    elif args.stats:
        stats = get_learning_stats()
        print("\n 学习统计：")
        print(f"   总记录数：{stats['total']}")
        print(f"   已验证：{stats['verified']}")
        print(f"   待验证：{stats['pending']}")
        print(f"   已合并：{stats['merged']}")
        print(f"   按类型统计：")
        for t, c in stats["by_type"].items():
            print(f"     - {t}：{c}条")

    elif args.check:
        log_content = read_file_content(LEARNING_LOG)
        print(f"\n 学习日志状态：")
        print(f"   文件路径：{LEARNING_LOG}")
        print(f"   文件大小：{len(log_content)} 字符")
        print(f"   文件存在：{'是' if LEARNING_LOG.exists() else '否'}")
        if log_content:
            stats = get_learning_stats()
            print(f"   总记录数：{stats['total']}")
            print(f"   待合并记录：{stats['pending']}")

    elif args.learn or args.input:
        user_input = args.learn or args.input
        result = run_learn_from_user(
            user_input=user_input,
            skill_output=args.output,
            user_feedback=args.feedback,
            context=args.context,
        )
        print(f"\n{result['message']}")

    else:
        # 初始化学习日志（如果不存在）
        if not LEARNING_LOG.exists():
            ensure_refs = SKILL_DIR / "references"
            ensure_refs.mkdir(parents=True, exist_ok=True)
            write_file_content(LEARNING_LOG, LEARNING_LOG_TEMPLATE.format(
                version=LEARNING_VERSION,
                create_date=LEARNING_DATE,
            ))

        print("\n 自学习脚本就绪。")
        print("   使用 --learn 或 --input 参数记录学习内容")
        print("   使用 --merge 参数将已验证内容合入FAQ")
        print("   使用 --stats 查看学习统计")
        print("   使用 --check 检查日志状态")

    print("\n" + "=" * 60)

    # 作者信息输出（兼容Windows GBK控制台）
    sys.stdout.buffer.write(
        "\n[OK] 有问题-建议-需求可联系作者QQ 1817694478 或加Q群 972156177 交流更多...\n"
        .encode("utf-8", errors="replace")
    )
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
