#!/usr/bin/env python3
"""write_notified.py — v4.6.3: 将 notified 状态写入 MD 文件，支持 status 更新，entry_id fallback"""
import json, sys, os, re

def update_md_file(file_path, entry_id, notified_val=None, nc_val=None, status_val=None):
    """更新 MD 文件中指定 entry 的 Notified / Notification-Count / Status 字段"""
    if not os.path.exists(file_path):
        return False

    with open(file_path) as f:
        content = f.read()

    # Find entry: ## [ENTRY_ID] ...
    entry_pattern = r"(## \[" + re.escape(entry_id) + r"\] .+?)(?=\n## \[|$)"
    m = re.search(entry_pattern, content, re.DOTALL)
    if not m:
        return False

    entry_start = m.start(1)
    entry_text = m.group(1)

    new_entry = entry_text

    # ── Status field (bold: **Status**) ──
    if status_val is not None:
        has_bold_status = bool(re.search(r"^\s*\*\*Status\*\*:", entry_text, re.MULTILINE))
        has_dash_status = bool(re.search(r"^\s*-\s*Status:", entry_text, re.MULTILINE))
        if has_bold_status:
            new_entry = re.sub(r"^\s*\*\*Status\*\*:.*$", f"**Status**: {status_val}", new_entry, flags=re.MULTILINE)
        elif has_dash_status:
            new_entry = re.sub(r"^\s*-\s*Status:.*$", f"  - Status: {status_val}", new_entry, flags=re.MULTILINE)
        else:
            # No Status field exists — insert after title; include Notified/N/C if also being set (single anchor insertion)
            notified_str = 'true' if notified_val == 1 else 'false' if notified_val is not None else None
            nc_insert = f"  - Notification-Count: {nc_val}\n" if nc_val is not None else ""
            notified_insert = f"  - Notified: {notified_str}\n" if notified_str is not None else ""
            status_line = f"**Status**: {status_val}"
            insert = status_line + ("\n" + notified_insert if notified_insert else "") + ("\n" + nc_insert if nc_insert else "")
            new_entry = re.sub(
                r"(## \[[^\]]+\][^\n]*\n)",
                r"\1" + insert + "\n",
                new_entry
            )
            # Skip individual Notified/N/C passes since we handled them above
            notified_val = None
            nc_val = None

    # ── Notified field (dash: - Notified) ──
    if notified_val is not None:
        has_notified = bool(re.search(r"^\s*-\s*Notified:", entry_text, re.MULTILINE))
        notified_str = 'true' if notified_val == 1 else 'false'
        if has_notified:
            new_entry = re.sub(r"^\s*-\s*Notified:.*$", f"  - Notified: {notified_str}", new_entry, flags=re.MULTILINE)
        else:
            # Anchor on bold **Status** (most common in this system) or dash - Status
            new_entry = re.sub(
                r"(\n\s*\*\*Status\*\*:[^\n]+\n)",
                r"\1  - Notified: " + notified_str + "\n",
                new_entry
            )
            if notified_str not in new_entry:  # bold anchor missed, try dash
                new_entry = re.sub(
                    r"(\n\s*-\s*Status:[^\n]+\n)",
                    r"\1  - Notified: " + notified_str + "\n",
                    new_entry
                )

    # ── Notification-Count field ──
    if nc_val is not None:
        has_nc = bool(re.search(r"^\s*-\s*Notification-Count:", entry_text, re.MULTILINE))
        if has_nc:
            new_entry = re.sub(r"^\s*-\s*Notification-Count:.*$", f"  - Notification-Count: {nc_val}", new_entry, flags=re.MULTILINE)
        else:
            # Anchor on bold **Status**
            new_entry = re.sub(
                r"(\n\s*\*\*Status\*\*:[^\n]+\n)",
                r"\1  - Notification-Count: " + str(nc_val) + "\n",
                new_entry
            )
            if str(nc_val) not in new_entry:  # bold anchor missed, try dash
                new_entry = re.sub(
                    r"(\n\s*-\s*Status:[^\n]+\n)",
                    r"\1  - Notification-Count: " + str(nc_val) + "\n",
                    new_entry
                )

    new_content = content[:entry_start] + new_entry + content[m.end():]

    with open(file_path, 'w') as f:
        f.write(new_content)
    return True

def _do_update(entry_id, learnings_dir, status_val=None, notified_val=None, nc_val=None):
    """Shared update logic for both old-mode and new-mode."""
    # Expand ~ in path
    learnings_dir = os.path.expanduser(learnings_dir)
    file_map = {
        "LEARNINGS.md": os.path.join(learnings_dir, "LEARNINGS.md"),
        "ERRORS.md": os.path.join(learnings_dir, "ERRORS.md"),
        "FEATURE_REQUESTS.md": os.path.join(learnings_dir, "FEATURE_REQUESTS.md"),
    }
    updated = 0
    for fname, fpath in file_map.items():
        if os.path.exists(fpath):
            if update_md_file(fpath, entry_id, notified_val, nc_val, status_val):
                print(f"Updated: {entry_id} in {fname} (status={status_val}, notified={notified_val}, nc={nc_val})", file=sys.stderr)
                updated += 1
    print(f"write-notified: {updated} entries updated", file=sys.stderr)
    return updated


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: write_notified.py [--status VAL] [--notified VAL] [--nc VAL] <entry_id> <learnings_dir>", file=sys.stderr)
        print("       write_notified.py <json_file> <learnings_dir>   [legacy: called by archive.sh]", file=sys.stderr)
        sys.exit(1)

    # ── Old mode: first positional is a .json file (archive.sh calling convention) ──
    # Detect: endswith .json OR is an existing file with .json content
    if args[0].endswith('.json') or (os.path.isfile(args[0]) and not args[0].startswith('--')):
        json_file = args[0]
        learnings_dir = args[1] if len(args) > 1 else None
        if not learnings_dir:
            print("Usage: write_notified.py <json_file> <learnings_dir>", file=sys.stderr)
            sys.exit(1)
        with open(json_file) as f:
            data = json.load(f)
        # Entry ID from entry_id field (new format) or pattern_name field (legacy format)
        entry_id = data.get('entry_id') or data.get('pattern_name')
        if not entry_id:
            print(f"Error: JSON has no 'pattern_name' field: {json_file}", file=sys.stderr)
            sys.exit(1)
        # archive.sh calls to mark notified; use notification_count from JSON if present
        nc_from_json = data.get('notification_count', 1)  # v4.6.8: read nc from JSON
        updated = _do_update(entry_id, learnings_dir, status_val=None, notified_val=1, nc_val=nc_from_json)
        sys.exit(0)

    # ── New mode: --flags + positionals ──
    status_val = None
    notified_val = None
    nc_val = None
    entry_id = None
    learnings_dir = None

    i = 0
    while i < len(args):
        if args[i] == '--status' and i + 1 < len(args):
            status_val = args[i + 1]
            i += 2
        elif args[i] == '--notified' and i + 1 < len(args):
            notified_val = int(args[i + 1])
            i += 2
        elif args[i] == '--nc' and i + 1 < len(args):
            nc_val = int(args[i + 1])
            i += 2
        else:
            entry_id = args[i]
            learnings_dir = args[i + 1] if i + 1 < len(args) else None
            i += 2 if learnings_dir else 1

    if not entry_id or not learnings_dir:
        print("Usage: write_notified.py [--status VAL] [--notified VAL] [--nc VAL] <entry_id> <learnings_dir>", file=sys.stderr)
        sys.exit(1)

    updated = _do_update(entry_id, learnings_dir, status_val, notified_val, nc_val)
    sys.exit(0)
