#!/usr/bin/env python3
# Copyright (c) 2026 WorkBuddy Skills. All rights reserved.
# Skill: skill-trend-analyzer | Version: 2.0.0
# Author: QQ 1817694478 | Q-Group: 972156177
"""
Safe I/O Module v2 - Anti-freeze, Anti-crash, Auto-fix for Windows
====================================================================
Solves ALL freeze/crash causes for multi-script Python skills on Windows:

Problem Chain (what happened before):
  Script A wraps stdout → Script B wraps same stream again
  → outer wrapper GC'd → buffer closed → all I/O frozen

Solution Stack (5 layers of defense):
  Layer 1: Shared marker - one process, one wrapper, no double-wrap
  Layer 2: Global print hook - intercept ALL print() calls, zero manual changes
  Layer 3: Stream health monitor - detect + auto-repair broken streams
  Layer 4: File read timeout - prevent big-file read() blocking forever
  Layer 5: Subprocess timeout - kill stuck npx/subprocess calls

Skill-specific optimizations for skill-trend-analyzer:
  - 23 skill dirs to scan → per-file read timeout (5s each)
  - 7 scripts that import each other → sys.path auto-fix
  - 152 print() calls → global hook replaces all, zero code changes
  - npx clawdhub subprocess → timeout + kill on hang

Usage (ONE line per script, replaces old 4-line encoding block):
  from safe_io import safe_print, safe_init, TimeoutGuard, safe_read_text
  safe_init()
"""

import sys
import io
import os
import json
import builtins
import threading
import subprocess
import traceback
from pathlib import Path
from datetime import datetime

# ============================================================
# Layer 0: sys.path Auto-Fix (before any other imports)
# ============================================================

def _fix_sys_path():
    """
    Ensure this script's directory is in sys.path so sibling imports work.
    Problem: when script A calls script B via subprocess or import,
    B's directory may not be in sys.path → ImportError.
    Fix: add SCRIPT_DIR to sys.path[0] (highest priority).
    """
    script_dir = str(Path(__file__).parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

_fix_sys_path()

# ============================================================
# Layer 1: Shared Encoding Initialization
# ============================================================

def safe_init():
    """
    One-time safe encoding setup for Windows.
    Key improvements over old pattern:
      - Shared marker _workbuddy_utf8_set (all scripts, one wrapper)
      - Detect already-utf-8 streams (skip re-wrap)
      - Verify buffer not closed before wrapping
      - Store originals for 3-level fallback recovery
      - Auto-fix sys.path for cross-script imports
      - Install global print() hook (replaces ALL 152 print calls)
    """
    # Already initialized by another script
    if getattr(sys, '_workbuddy_utf8_set', False):
        return True

    # Ensure sys.path includes our directory
    _fix_sys_path()

    try:
        # Check if current stdout already supports utf-8
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
            try:
                enc = sys.stdout.encoding.lower()
                # Strict check: only match 'utf-8' or 'utf8', NOT utf-16/utf-32
                if enc in ('utf-8', 'utf8', 'utf_8'):
                    sys._workbuddy_utf8_set = True
                    _install_print_hook()
                    return True
            except (ValueError, AttributeError):
                pass

        # Check buffer health before wrapping
        for stream_name in ['stdout', 'stderr']:
            stream = getattr(sys, stream_name)
            if hasattr(stream, 'buffer'):
                buf = stream.buffer
                if hasattr(buf, 'closed') and buf.closed:
                    continue
                if hasattr(buf, 'writable') and not buf.writable():
                    continue
                # Store original for fallback
                if not hasattr(sys, f'_workbuddy_orig_{stream_name}'):
                    setattr(sys, f'_workbuddy_orig_{stream_name}', stream)
                # Wrap with utf-8
                new_stream = io.TextIOWrapper(
                    buf, encoding='utf-8', errors='replace',
                    line_buffering=True  # per-line flush for real-time output
                )
                setattr(sys, stream_name, new_stream)

        sys._workbuddy_utf8_set = True
        # Install global print() hook - intercepts ALL print() calls
        _install_print_hook()
        return True

    except Exception as e:
        # Mark as attempted so we don't retry forever
        sys._workbuddy_utf8_set = True
        return False


# ============================================================
# Layer 2: Global Print Hook (replaces ALL print() calls)
# ============================================================

_orig_print = builtins.print  # Save original print before we hook it

def _safe_print_hook(*args, **kwargs):
    """
    Global replacement for builtins.print.
    Every print() in EVERY script goes through this hook automatically.
    No need to replace 152 individual print() calls manually.

    Fallback chain:
      1. sys.stdout.write (wrapped utf-8 stream)
      2. sys._workbuddy_orig_stdout (original stream before wrapping)
      3. os.write(1, ...) (direct kernel write, bypasses all wrappers)
      4. Silent drop (if ALL I/O is broken, at least don't crash)
    """
    # Build output string the same way print() does
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    file = kwargs.get('file', None)  # If user specified file=, honor it
    flush = kwargs.get('flush', False)

    # If target is not stdout/stderr, use original print (e.g. file=open('log'))
    if file is not None:
        try:
            _orig_print(*args, sep=sep, end=end, file=file, flush=flush)
        except (ValueError, OSError, IOError):
            pass
        return

    # Build output for stdout
    message = sep.join(str(a) for a in args) + end
    written = False

    # Level 1: Try wrapped stdout
    try:
        sys.stdout.write(message)
        if flush:
            sys.stdout.flush()
        written = True
        return
    except (ValueError, OSError, AttributeError, IOError):
        pass

    # Level 2: Try original stdout (before wrapping)
    orig_out = getattr(sys, '_workbuddy_orig_stdout', None)
    if orig_out:
        try:
            orig_out.write(message)
            if flush:
                orig_out.flush()
            written = True
            return
        except (ValueError, OSError, AttributeError, IOError):
            pass

    # Level 3: Direct kernel write (bypasses ALL Python wrappers)
    try:
        os.write(1, message.encode('utf-8', errors='replace'))
        written = True
        return
    except (OSError, IOError):
        pass

    # Level 4: Silent drop - better than crash


def _install_print_hook():
    """
    Replace builtins.print with our safe version.
    This affects ALL scripts in the entire process - no manual changes needed.
    Only install once (check marker).
    """
    if getattr(sys, '_workbuddy_print_hooked', False):
        return
    builtins.print = _safe_print_hook
    sys._workbuddy_print_hooked = True


def safe_print(*args, **kwargs):
    """
    Explicit safe print for critical messages.
    Uses the same hook mechanism but can be called explicitly
    when you want to be extra sure.
    """
    _safe_print_hook(*args, **kwargs)


# ============================================================
# Layer 3: Stream Health Monitor + Auto-Repair
# ============================================================

def check_stream_health():
    """Check if stdout/stderr are healthy. Returns (ok, details)."""
    issues = []
    for name in ['stdout', 'stderr']:
        stream = getattr(sys, name)
        if stream is None:
            issues.append(f"{name} is None")
            continue
        if hasattr(stream, 'closed') and stream.closed:
            issues.append(f"{name} is closed")
        if hasattr(stream, 'buffer'):
            buf = stream.buffer
            if hasattr(buf, 'closed') and buf.closed:
                issues.append(f"{name}.buffer is closed")
            if hasattr(buf, 'writable') and not buf.writable():
                issues.append(f"{name}.buffer not writable")
    return (len(issues) == 0, issues if issues else ["All healthy"])


def repair_streams():
    """Auto-repair broken stdout/stderr. Returns repair log."""
    repaired = []
    for name in ['stdout', 'stderr']:
        stream = getattr(sys, name)
        is_broken = False
        if stream is None:
            is_broken = True
        elif hasattr(stream, 'closed') and stream.closed:
            is_broken = True
        elif hasattr(stream, 'buffer'):
            buf = stream.buffer
            if hasattr(buf, 'closed') and buf.closed:
                is_broken = True
        if is_broken:
            orig = getattr(sys, f'_workbuddy_orig_{name}', None)
            if orig and not (hasattr(orig, 'closed') and orig.closed):
                setattr(sys, name, orig)
                repaired.append(f"{name}: restored from original")
            else:
                try:
                    fd = 1 if name == 'stdout' else 2
                    new_stream = io.TextIOWrapper(
                        io.open(fd, 'wb', closefd=False),
                        encoding='utf-8', errors='replace', line_buffering=True
                    )
                    setattr(sys, name, new_stream)
                    repaired.append(f"{name}: recreated from fd={fd}")
                except Exception as e:
                    repaired.append(f"{name}: UNREPAIRABLE ({e})")
    return repaired


# ============================================================
# Layer 4: File Read Timeout (prevent big-file blocking)
# ============================================================

def safe_read_text(path, timeout=5, encoding='utf-8', max_size_mb=10):
    """
    Read file content with size limit and timeout protection.
    Prevents: read() on huge files → blocks forever → process frozen.

    Args:
        path: file path (str or Path)
        timeout: max seconds to attempt read (default 5s per file)
        encoding: file encoding (default utf-8)
        max_size_mb: max file size to read (default 10MB, skip larger)

    Returns:
        str: file content, or '' on error/timeout/oversized
    """
    path = Path(path) if not isinstance(path, Path) else path

    # Size check: skip files larger than limit
    try:
        size = path.stat().st_size
        if size > max_size_mb * 1024 * 1024:
            _safe_print_hook(f"[SKIP] {path.name}: {size/1024/1024:.1f}MB exceeds {max_size_mb}MB limit")
            return ''
    except OSError:
        return ''

    # Read with timeout via threading
    result_container = {'content': '', 'done': False, 'error': None}

    def _reader():
        try:
            result_container['content'] = path.read_text(encoding=encoding, errors='replace')
            result_container['done'] = True
        except Exception as e:
            result_container['error'] = str(e)

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if result_container['done']:
        return result_container['content']
    elif result_container['error']:
        _safe_print_hook(f"[WARNING] Read error {path.name}: {result_container['error']}")
        return ''
    else:
        # Thread still running → file read stuck, skip it
        _safe_print_hook(f"[TIMEOUT] Read {path.name} stuck (> {timeout}s), skipping")
        return ''


def safe_read_json(path, timeout=5, max_size_mb=5):
    """
    Read and parse JSON file with timeout + size protection.
    Returns parsed dict/list, or {} on any error.
    """
    content = safe_read_text(path, timeout=timeout, max_size_mb=max_size_mb)
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        _safe_print_hook(f"[WARNING] JSON parse error {Path(path).name}: {e}")
        return {}


# ============================================================
# Layer 5: Timeout Guard (for code blocks, not just file reads)
# ============================================================

class TimeoutGuard:
    """
    Context manager with timeout protection.
    When timeout expires:
      - Sets self.timed_out = True
      - Prints timeout message
      - Suppresses any exception from the timed-out block
      - Code continues after the context manager exits

    Note: On Windows, threading.Timer CANNOT force-kill the blocked thread.
    The thread continues running in background but the main flow proceeds.
    For truly stuck operations, use safe_subprocess() instead (which CAN kill).

    Usage:
        with TimeoutGuard(seconds=30, message="Scan stuck"):
            scan_skill(dir)  # if this takes >30s, we skip and continue
    """

    def __init__(self, seconds=60, message="Operation timed out"):
        self.seconds = seconds
        self.message = message
        self._timer = None
        self._timed_out = False

    def _timeout_handler(self):
        self._timed_out = True
        _safe_print_hook(f"\n[TIMEOUT] {self.message} (exceeded {self.seconds}s)")
        # Try stream health check + repair on timeout (I/O may be broken)
        try:
            ok, _ = check_stream_health()
            if not ok:
                repair_streams()
        except Exception:
            pass

    def __enter__(self):
        self._timed_out = False
        self._timer = threading.Timer(self.seconds, self._timeout_handler)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._timer:
            self._timer.cancel()
        if self._timed_out:
            _safe_print_hook(f"[TIMEOUT] Skipping remaining work due to timeout")
            return True  # Suppress exception, continue execution
        return False

    @property
    def timed_out(self):
        return self._timed_out


# ============================================================
# Layer 5b: Safe Subprocess (CAN truly kill stuck processes)
# ============================================================

def safe_subprocess(cmd, timeout=30, cwd=None, capture_output=True):
    """
    Run subprocess with TRUE timeout + kill capability.
    Unlike TimeoutGuard (threading, cannot kill), subprocess.run CAN kill.

    Args:
        cmd: command list (e.g. ["npx", "clawdhub", "search", ...])
        timeout: max seconds (default 30s)
        cwd: working directory
        capture_output: capture stdout/stderr

    Returns:
        dict: {'success': bool, 'stdout': str, 'stderr': str, 'timed_out': bool}
    """
    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout or '',
            'stderr': result.stderr or '',
            'timed_out': False,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired as e:
        _safe_print_hook(f"[TIMEOUT] Subprocess {cmd[0]} exceeded {timeout}s, killed")
        return {
            'success': False,
            'stdout': e.stdout or '' if hasattr(e, 'stdout') and e.stdout else '',
            'stderr': '',
            'timed_out': True,
            'returncode': -1
        }
    except FileNotFoundError:
        _safe_print_hook(f"[ERROR] Command not found: {cmd[0]}")
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Command not found: {cmd[0]}',
            'timed_out': False,
            'returncode': -1
        }
    except Exception as e:
        _safe_print_hook(f"[ERROR] Subprocess failed: {e}")
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'timed_out': False,
            'returncode': -1
        }


# ============================================================
# Auto-initialize on import
# ============================================================

safe_init()

# Health check on import
_health_ok, _health_details = check_stream_health()
if not _health_ok:
    repair_streams()

# ============================================================
# Fixed Footer - Contact Author Info (ClawHub Compliance)
# ============================================================

def print_footer():
    """
    Print fixed ending footer with author contact info.
    Must be called at the end of every CLI script's main().
    Uses sys.stdout.buffer.write() to avoid Windows GBK encoding issues.
    """
    import sys
    footer_text = "\n[AUTHOR]有问题、建议、需求可[EMAIL] 联系作者QQ：1817694478[QGROUP]加Q群：972156177交流分享更多...\n"
    sys.stdout.buffer.write(footer_text.encode("utf-8", errors="replace"))


