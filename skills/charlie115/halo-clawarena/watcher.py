#!/usr/bin/env python3
"""ClawArena local turn watcher.

Keeps a lightweight watcher websocket open to ClawArena and launches one
local OpenClaw agent turn only when the fighter has an actionable turn.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import socket
import ssl
import struct
import json
import os
import re
import select
import subprocess
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request


CLAW_DIR = Path.home() / ".clawarena"
TOKEN_PATH = CLAW_DIR / "token"
DELIVERY_CONFIG_PATH = CLAW_DIR / "openclaw_delivery.json"
STATE_PATH = CLAW_DIR / "watcher_state.json"
LOCK_PATH = CLAW_DIR / "watcher.lock"

API_BASE = "https://clawarena.halochain.xyz/api/v1"
PUBLIC_BASE = API_BASE.rsplit("/api/v1", 1)[0]
WATCHER_WS_URL = (
    f"{PUBLIC_BASE.replace('https://', 'wss://').replace('http://', 'ws://')}/ws/watcher/"
)
GAME_URL = f"{API_BASE}/agents/game/"
WATCHER_URL = f"{API_BASE}/agents/watcher/"
HTTP_TIMEOUT_SECONDS = 70
TELEMETRY_HEARTBEAT_SECONDS = 30
PING_TIMEOUT_SECONDS = 10
MAX_MISSED_PONGS = 2
WS_STALE_RECONNECT_SECONDS = 45
WS_HANDSHAKE_TIMEOUT_SECONDS = 15

ERROR_RETRY_DELAY_SECONDS = 5.0
MAX_TRIGGER_ATTEMPTS = 3
TRIGGER_RETRY_DELAY_SECONDS = 2.0
WS_FAILURE_SELF_RESTART_THRESHOLD = 6
SELF_RESTART_COOLDOWN_SECONDS = 300


class WebSocketError(Exception):
    pass


class MinimalWebSocket:
    """Small stdlib-only WebSocket client for the watcher feed."""

    def __init__(self, url: str):
        parsed = parse.urlparse(url)
        is_tls = parsed.scheme == "wss"
        host = parsed.hostname
        port = parsed.port or (443 if is_tls else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        raw = socket.create_connection((host, port), timeout=30)
        if is_tls:
            ctx = ssl.create_default_context()
            self._sock = ctx.wrap_socket(raw, server_hostname=host)
        else:
            self._sock = raw
        self._sock.settimeout(WS_HANDSHAKE_TIMEOUT_SECONDS)

        origin_scheme = "https" if is_tls else "http"
        origin = f"{origin_scheme}://{host}"
        key = base64.b64encode(os.urandom(16)).decode()
        headers = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Origin: {origin}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        self._sock.sendall(headers.encode())

        resp = b""
        try:
            while b"\r\n\r\n" not in resp:
                chunk = self._sock.recv(4096)
                if not chunk:
                    raise WebSocketError("Connection closed during handshake")
                resp += chunk
        except socket.timeout as exc:
            raise WebSocketError("Watcher websocket handshake timed out") from exc
        status_line = resp.split(b"\r\n", 1)[0]
        if b"101" not in status_line:
            raise WebSocketError(f"Handshake failed: {status_line.decode(errors='replace')}")

        self._closed = False
        self._buffer = resp.split(b"\r\n\r\n", 1)[1]
        self._sock.settimeout(None)

    def _recv_exactly(self, n: int) -> bytes:
        while len(self._buffer) < n:
            chunk = self._sock.recv(max(4096, n - len(self._buffer)))
            if not chunk:
                raise WebSocketError("Connection closed")
            self._buffer += chunk
        data, self._buffer = self._buffer[:n], self._buffer[n:]
        return data

    def _send_frame(self, opcode: int, payload: bytes) -> None:
        header = bytes([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header += bytes([0x80 | length])
        elif length < 65536:
            header += bytes([0x80 | 126]) + struct.pack("!H", length)
        else:
            header += bytes([0x80 | 127]) + struct.pack("!Q", length)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(header + mask + masked)

    def _read_frame(self) -> tuple[int, bytes]:
        b0, b1 = self._recv_exactly(2)
        opcode = b0 & 0x0F
        masked = b1 & 0x80
        length = b1 & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exactly(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exactly(8))[0]
        if masked:
            mask = self._recv_exactly(4)
            raw = self._recv_exactly(length)
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(raw))
        else:
            payload = self._recv_exactly(length)
        return opcode, payload

    def send_json(self, payload: dict[str, Any]) -> None:
        if self._closed:
            raise WebSocketError("WebSocket is closed")
        self._send_frame(0x1, json.dumps(payload).encode("utf-8"))

    def recv_json(self, timeout: float | None = None) -> dict[str, Any]:
        if timeout is not None and not self._buffer:
            readable, _, _ = select.select([self._sock], [], [], timeout)
            if not readable:
                raise TimeoutError("WebSocket recv timed out")
        if timeout is not None:
            # Keep a socket-level timeout too so partial frame reads cannot block forever.
            self._sock.settimeout(timeout)
        try:
            while True:
                opcode, payload = self._read_frame()
                if opcode == 0x1:
                    return json.loads(payload.decode("utf-8"))
                if opcode == 0x9:
                    self._send_frame(0xA, payload)
                    continue
                if opcode == 0x8:
                    self._closed = True
                    raise WebSocketError("Server sent close frame")
        except socket.timeout as exc:
            raise TimeoutError("WebSocket recv timed out") from exc
        finally:
            if timeout is not None:
                self._sock.settimeout(None)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._sock.settimeout(0.2)
        except OSError:
            pass
        try:
            self._send_frame(0x8, b"")
        except OSError:
            pass
        except Exception:
            pass
        try:
            self._sock.close()
        except OSError:
            pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp_path.replace(path)


def read_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return dict(default or {})
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return dict(default or {})


class Watcher:
    def __init__(self, wait_seconds: int) -> None:
        self.wait_seconds = wait_seconds
        self.current_status = "idle"
        self.current_idle_reason = "Watcher connected and waiting for actionable turns."
        self.current_prefs: dict[str, Any] = {}
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._force_reconnect = threading.Event()
        self._ws_lock = threading.Lock()
        self._active_ws: MinimalWebSocket | None = None
        self.state = read_json(
            STATE_PATH,
            {
                "started_at": utc_now(),
                "last_poll_at": None,
                "last_status": None,
                "last_match_id": None,
                "last_seq": None,
                "last_trigger_key": None,
                "last_trigger_attempts": 0,
                "last_agent_at": None,
                "last_agent_status": None,
                "last_trigger_pending_retry": False,
                "last_bonus_attempt_at": None,
                "last_posted_status": None,
                "last_posted_idle_reason": None,
                "last_posted_error": None,
                "last_posted_at": None,
                "last_ws_message_at": None,
                "last_pong_at": None,
                "last_probe_ok_at": None,
                "last_probe_failed_at": None,
                "ws_probe_failures": 0,
                "last_error": None,
                "bootstrapped_sessions": {},
                "ws_consecutive_failures": 0,
                "last_self_restart_at": None,
            },
        )
        if not isinstance(self.state.get("bootstrapped_sessions"), dict):
            self.state["bootstrapped_sessions"] = {}

    def _derive_status_from_snapshot(self, snapshot: dict[str, Any]) -> tuple[str, str]:
        prefs = snapshot.get("agent_preferences") or self.current_prefs or {}
        status = str(snapshot.get("status") or "idle")
        message = str(snapshot.get("message") or "").strip()
        preferred_game = str(
            prefs.get("preferred_game_type")
            or prefs.get("current_game_type")
            or ""
        )
        autoplay_enabled = prefs.get("autoplay_enabled")

        if autoplay_enabled is False or "Autoplay is paused" in message:
            return "paused", "Paused by user."
        if status == "playing":
            return "in_match", "In a match, waiting for the next actionable turn."
        if status == "matched":
            return "matched", "Matched. Waiting for game start."
        if status == "waiting":
            return "idle", "Waiting for match assignment..."
        if status == "finished":
            return "idle", message or "Previous match finished."
        if "Choose a game in your dashboard" in message:
            return "idle", "No game selected in the dashboard."
        if not preferred_game:
            return "idle", "No game selected in the dashboard."
        return "idle", message or "Waiting to enter matchmaking."

    def sync_status_from_server(self) -> dict[str, Any]:
        snapshot = self.peek_game_state(consume_history=False)
        prefs = snapshot.get("agent_preferences") or {}
        if prefs:
            self.current_prefs = prefs
        self.current_status, self.current_idle_reason = self._derive_status_from_snapshot(snapshot)
        self.save_state(last_poll_at=utc_now())
        return snapshot

    def save_state(self, **updates: Any) -> None:
        with self._state_lock:
            self.state.update(updates)
            atomic_write_json(STATE_PATH, self.state)

    def load_connection_token(self) -> str:
        token = TOKEN_PATH.read_text().strip()
        if not token:
            raise RuntimeError(f"Missing connection token in {TOKEN_PATH}")
        return token

    def load_delivery_config(self) -> dict[str, Any]:
        config = read_json(DELIVERY_CONFIG_PATH)
        required = ["channel", "to"]
        missing = [key for key in required if not config.get(key)]
        if missing:
            raise RuntimeError(
                f"Missing delivery config keys {missing} in {DELIVERY_CONFIG_PATH}"
            )
        return config

    def decode_connection_token(self) -> tuple[int, str]:
        token = self.load_connection_token()
        padded = token + ("=" * ((4 - len(token) % 4) % 4))
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        return int(payload["a"]), str(payload["t"])

    def peek_game_state(self, *, consume_history: bool = False) -> dict[str, Any]:
        token = self.load_connection_token()
        consume_value = "1" if consume_history else "0"
        url = f"{GAME_URL}?wait=0&consume_history={consume_value}"
        req = request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        with request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)

    def post_status(self, *, status: str, idle_reason: str = "", error_message: str = "",
                    action_taken: bool = False, report_sent: bool = False,
                    restart_ack: bool = False) -> dict[str, Any]:
        last_posted_at = self.state.get("last_posted_at")
        should_send = action_taken or report_sent or restart_ack or bool(error_message)
        if (
            not should_send
            and self.state.get("last_posted_status") == status
            and self.state.get("last_posted_idle_reason") == idle_reason
            and self.state.get("last_posted_error") == error_message
            and last_posted_at
        ):
            try:
                last_ts = datetime.fromisoformat(str(last_posted_at)).timestamp()
                if (time.time() - last_ts) < TELEMETRY_HEARTBEAT_SECONDS:
                    return {}
            except ValueError:
                pass
        try:
            token = self.load_connection_token()
            feed_status = self._current_feed_status()
            body = json.dumps(
                {
                    "status": status,
                    "idle_reason": idle_reason,
                    "error": error_message,
                    "feed_status": feed_status,
                    "last_ws_message_at": self.state.get("last_ws_message_at"),
                    "last_pong_at": self.state.get("last_pong_at"),
                    "action_taken": action_taken,
                    "report_sent": report_sent,
                    "restart_ack": restart_ack,
                }
            ).encode("utf-8")
            req = request.Request(
                WATCHER_URL,
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            with request.urlopen(req, timeout=15) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            watcher = payload.get("watcher", {})
            self.current_prefs = payload.get("agent_preferences") or self.current_prefs
            self.save_state(
                last_server_status=watcher.get("status"),
                last_server_seen_at=watcher.get("last_seen_at"),
                last_posted_status=status,
                last_posted_idle_reason=idle_reason,
                last_posted_error=error_message,
                last_posted_at=utc_now(),
            )
            return payload
        except Exception:
            # Telemetry failure should never stop gameplay.
            return {}

    def connect_ws(self) -> MinimalWebSocket:
        ws = MinimalWebSocket(WATCHER_WS_URL)
        ws.send_json({"type": "auth", "token": self.load_connection_token()})
        resp = ws.recv_json(timeout=10)
        if resp.get("type") != "auth_ok":
            raise RuntimeError(f"Watcher auth failed: {resp}")
        now_iso = utc_now()
        self.current_prefs = resp.get("agent_preferences") or {}
        self.save_state(
            last_ws_message_at=now_iso,
            last_pong_at=now_iso,
            last_probe_ok_at=now_iso,
            last_probe_failed_at=None,
            ws_probe_failures=0,
            last_error=None,
            ws_consecutive_failures=0,
        )
        return ws

    def _maybe_self_restart_for_ws_failures(self, error_message: str) -> None:
        failures = int(self.state.get("ws_consecutive_failures") or 0)
        if failures < WS_FAILURE_SELF_RESTART_THRESHOLD:
            return

        last_restart_at = self.state.get("last_self_restart_at")
        if last_restart_at:
            try:
                age = time.time() - datetime.fromisoformat(str(last_restart_at)).timestamp()
            except ValueError:
                age = None
            if age is not None and age < SELF_RESTART_COOLDOWN_SECONDS:
                return

        self.save_state(last_self_restart_at=utc_now())
        self.post_status(
            status="error",
            idle_reason="Watcher is restarting itself after repeated live feed failures.",
            error_message=error_message[:500],
        )
        os.execv(
            sys.executable,
            [
                sys.executable,
                str(Path(__file__)),
                "--wait-seconds",
                str(self.wait_seconds),
            ],
        )

    def maybe_restart_if_requested(self, data: dict[str, Any]) -> None:
        prefs = data.get("agent_preferences") or data or {}
        requested = prefs.get("watcher_restart_requested_at")
        acked = prefs.get("watcher_restart_ack_at")
        if not requested:
            return
        if acked and acked >= requested:
            return

        os.execv(
            sys.executable,
            [
                sys.executable,
                str(Path(__file__)),
                "--wait-seconds",
                str(self.wait_seconds),
                "--ack-restart",
            ],
        )

    def _should_deliver(self, data: dict[str, Any]) -> bool:
        prefs = data.get("agent_preferences") or {}
        report_level = prefs.get("report_level", "every_turn")
        if report_level == "silent":
            return False
        if report_level == "every_turn":
            return True
        legal_actions = data.get("legal_actions") or []
        action_names = {str(action.get("action")) for action in legal_actions if isinstance(action, dict)}
        return "chat" not in action_names

    def _has_optional_player_message(self, data: dict[str, Any]) -> bool:
        for action in data.get("legal_actions") or []:
            if not isinstance(action, dict):
                continue
            params = action.get("params") or {}
            if not isinstance(params, dict):
                continue
            message_spec = params.get("message")
            if message_spec is None:
                continue
            if "optional" in str(message_spec).strip().lower():
                return True
        return False

    def _prompt_extras(self, data: dict[str, Any]) -> list[str]:
        prefs = data.get("agent_preferences") or {}
        extras = [
            "Use the single GET /agents/game result itself as the working state for this tick. Do not run extra inspection commands that pretty-print, truncate, or derive a second copy of the same payload.",
        ]
        risk = prefs.get("current_risk_profile") or prefs.get("risk_profile")
        if risk and risk != "balanced":
            extras.append(f"Play with a {risk} risk profile.")
        message_language = str(prefs.get("message_language") or "english").strip().lower()
        if message_language:
            extras.append(
                f"When sending in-game player-facing messages, write them in {message_language}."
            )
        strategy_hint = prefs.get("current_strategy_hint")
        if isinstance(strategy_hint, str):
            strategy_hint = " ".join(strategy_hint.split())
            if strategy_hint:
                extras.append(f"Extra player hint for this game: {strategy_hint}")
        if self._has_optional_player_message(data):
            extras.append(
                "When an action supports an optional player-facing message, usually send one. "
                "Do not just narrate your action or its result. Prefer short table talk that bluffs, taunts, bargains, reassures, accuses, or pressures other players. "
                "Only stay silent when silence is strategically better."
            )
        if str(prefs.get("result_report_style") or "").strip().lower() == "brief":
            extras.append(
                "Keep the result report very brief: one short sentence, or two short bullets at most. Do not use markdown tables. Mention only the action taken and the key reason."
            )
        return extras

    def _build_bootstrap_message(self, data: dict[str, Any]) -> str:
        extras = self._prompt_extras(data)
        skill_root = Path(__file__).resolve().parent
        gameloop_path = skill_root / "GAMELOOP.md"
        message = (
            "Use the installed halo-clawarena skill. "
            f"Read this exact file and no other gameplay docs: {gameloop_path}. "
            f"Read CONNECTION_TOKEN from {TOKEN_PATH}. "
            "Do not search for the skill directory, do not inspect unrelated files, "
            "and do not browse for extra docs. "
            "Use this session for this match only. "
            "This is a ClawArena gameplay session only; ignore workspace onboarding or persona setup files such as BOOTSTRAP.md, IDENTITY.md, and USER.md, and do not read, edit, or delete them. "
            "From now on, execute exactly one ClawArena game loop tick each time you are woken in this session, "
            "and report the result in this chat."
        )
        if extras:
            message = f"{message} {' '.join(extras)}"
        return message

    def _build_incremental_message(self, data: dict[str, Any]) -> str:
        extras = self._prompt_extras(data)
        message = (
            "Use the procedure already established in this session. "
            "Run exactly one ClawArena game loop tick for the current match and report the result in this chat. "
            "Do not reread GAMELOOP.md or search for gameplay docs unless this session has clearly lost context."
        )
        if extras:
            message = f"{message} {' '.join(extras)}"
        return message

    def _session_id_for_turn(self, wake: dict[str, Any], current: dict[str, Any]) -> str:
        game_type = str(current.get("game_type") or wake.get("game_type") or "game").strip().lower()
        match_id = str(current.get("match_id") or wake.get("match_id") or "match").strip()
        agent_id, _ = self.decode_connection_token()
        safe_game = re.sub(r"[^a-z0-9_-]+", "-", game_type).strip("-") or "game"
        safe_match = re.sub(r"[^a-zA-Z0-9_-]+", "-", match_id).strip("-") or "match"
        return f"clawarena-{safe_game}-agent-{agent_id}-match-{safe_match}"

    def _bootstrapped_sessions(self) -> dict[str, Any]:
        sessions = self.state.get("bootstrapped_sessions")
        return sessions if isinstance(sessions, dict) else {}

    def _is_session_bootstrapped(self, session_id: str) -> bool:
        return session_id in self._bootstrapped_sessions()

    def _mark_session_bootstrapped(self, session_id: str, current: dict[str, Any]) -> None:
        sessions = dict(self._bootstrapped_sessions())
        sessions[session_id] = {
            "at": utc_now(),
            "match_id": current.get("match_id"),
            "game_type": current.get("game_type"),
        }
        # Keep only the newest 32 entries to avoid unbounded watcher_state growth.
        if len(sessions) > 32:
            ordered = sorted(
                sessions.items(),
                key=lambda item: str(item[1].get("at") or ""),
            )
            sessions = dict(ordered[-32:])
        self.save_state(bootstrapped_sessions=sessions)

    def _last_ws_activity_age(self) -> float | None:
        last_activity = self.state.get("last_pong_at") or self.state.get("last_ws_message_at")
        if not last_activity:
            return None
        try:
            return time.time() - datetime.fromisoformat(str(last_activity)).timestamp()
        except ValueError:
            return None

    def _current_feed_status(self) -> str:
        with self._ws_lock:
            ws = self._active_ws
        if ws is not None:
            if int(self.state.get("ws_probe_failures") or 0) > 0:
                return "stale"
            return "connected"
        age = self._last_ws_activity_age()
        if age is None:
            return "unknown"
        return "disconnected"

    def _maybe_force_reconnect(self) -> None:
        if int(self.state.get("ws_probe_failures") or 0) >= MAX_MISSED_PONGS:
            self._force_reconnect.set()

    def _set_active_ws(self, ws: MinimalWebSocket | None) -> None:
        with self._ws_lock:
            self._active_ws = ws

    def _close_active_ws(self) -> None:
        with self._ws_lock:
            ws = self._active_ws
        if ws is None:
            return
        try:
            ws.close()
        except Exception:
            pass

    def should_trigger(self, wake: dict[str, Any]) -> bool:
        trigger_key = f"{wake.get('match_id')}:{wake.get('seq')}"
        last_key = self.state.get("last_trigger_key")
        if trigger_key != last_key:
            return True

        if not self.state.get("last_trigger_pending_retry"):
            return False

        attempts = int(self.state.get("last_trigger_attempts") or 0)
        if attempts >= MAX_TRIGGER_ATTEMPTS:
            return False

        last_agent_at = self.state.get("last_agent_at")
        if not last_agent_at:
            return True

        try:
            last_ts = datetime.fromisoformat(str(last_agent_at)).timestamp()
        except ValueError:
            return True

        return (time.time() - last_ts) >= TRIGGER_RETRY_DELAY_SECONDS

    def trigger(self, wake: dict[str, Any], ws: MinimalWebSocket | None = None) -> None:
        delivery = self.load_delivery_config()
        current = self.peek_game_state(consume_history=False)
        if not (
            current.get("status") == "playing"
            and current.get("match_id") == wake.get("match_id")
            and current.get("is_your_turn")
            and bool(current.get("legal_actions"))
        ):
            self.save_state(last_trigger_pending_retry=False)
            return
        should_deliver = self._should_deliver(current)
        session_id = self._session_id_for_turn(wake, current)
        is_bootstrapped = self._is_session_bootstrapped(session_id)
        cmd = [
            "openclaw",
            "agent",
            "--session-id",
            session_id,
            "--message",
            self._build_incremental_message(current) if is_bootstrapped else self._build_bootstrap_message(current),
            "--json",
        ]
        if should_deliver:
            cmd.extend([
                "--deliver",
                "--reply-channel",
                str(delivery["channel"]),
                "--reply-to",
                str(delivery["to"]),
            ])
        reply_account = delivery.get("reply_account")
        if reply_account and should_deliver:
            cmd.extend(["--reply-account", str(reply_account)])
        seq = str(wake.get("seq") or "")
        if ws is not None and seq:
            ws.send_json({"type": "wake_ack", "seq": seq})
        proc = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        trigger_key = f"{wake.get('match_id')}:{wake.get('seq')}"
        attempts = 1
        if trigger_key == self.state.get("last_trigger_key"):
            attempts = int(self.state.get("last_trigger_attempts") or 0) + 1
        retry_pending = proc.returncode != 0
        if proc.returncode == 0:
            time.sleep(0.5)
            try:
                latest = self.peek_game_state(consume_history=False)
                retry_pending = (
                    latest.get("status") == "playing"
                    and latest.get("match_id") == wake.get("match_id")
                    and latest.get("is_your_turn")
                    and bool(latest.get("legal_actions"))
                )
            except Exception:
                retry_pending = False
        self.save_state(
            last_trigger_key=trigger_key,
            last_trigger_attempts=attempts,
            last_trigger_pending_retry=retry_pending,
            last_agent_at=utc_now(),
            last_agent_status={
                "code": proc.returncode,
                "body": (proc.stdout or proc.stderr)[:500],
                "session_id": session_id,
                "bootstrapped": is_bootstrapped,
            },
            last_error=None,
        )
        if proc.returncode == 0 and not is_bootstrapped:
            self._mark_session_bootstrapped(session_id, current)
        self.post_status(
            status="acting" if proc.returncode == 0 else "delivery_blocked",
            idle_reason="Submitted a live turn to OpenClaw." if proc.returncode == 0 else "OpenClaw delivery failed.",
            error_message="" if proc.returncode == 0 else (proc.stderr or proc.stdout)[:500],
            action_taken=True,
            report_sent=should_deliver and proc.returncode == 0,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"openclaw agent failed with exit code {proc.returncode}: {(proc.stderr or proc.stdout)[:200]}"
            )

    def _retry_pending_wake(self) -> None:
        if not self.state.get("last_trigger_pending_retry"):
            return
        trigger_key = self.state.get("last_trigger_key")
        if not trigger_key:
            return
        match_id, seq = trigger_key.split(":", 1)
        wake = {"match_id": int(match_id), "seq": seq}
        if self.should_trigger(wake):
            self.trigger(wake)

    def _handle_message(self, ws: MinimalWebSocket, message: dict[str, Any]) -> None:
        now_iso = utc_now()
        self.save_state(
            last_ws_message_at=now_iso,
            last_probe_ok_at=now_iso,
            last_probe_failed_at=None,
            ws_probe_failures=0,
        )
        msg_type = message.get("type")
        data = message.get("data", {})
        if msg_type == "watcher_status":
            self.current_prefs = data.get("agent_preferences") or self.current_prefs
            self.current_status = str(data.get("status") or "idle")
            self.current_idle_reason = str(data.get("idle_reason") or "Waiting.")
            payload = self.post_status(
                status=self.current_status,
                idle_reason=self.current_idle_reason,
            )
            if payload:
                self.maybe_restart_if_requested(payload)
        elif msg_type == "watcher_wake":
            self.current_status = "acting"
            self.current_idle_reason = "Submitted a live turn to OpenClaw."
            if self.should_trigger(data):
                self.trigger(data, ws=ws)
        elif msg_type == "pong":
            self.save_state(last_pong_at=utc_now())

    def _probe_connection(self, ws: MinimalWebSocket) -> bool:
        ws.send_json({"type": "ping"})
        try:
            message = ws.recv_json(timeout=PING_TIMEOUT_SECONDS)
        except TimeoutError:
            self.save_state(
                last_probe_failed_at=utc_now(),
                ws_probe_failures=int(self.state.get("ws_probe_failures") or 0) + 1,
            )
            return False
        self._handle_message(ws, message)
        return True

    def run_once(self) -> int:
        ws = None
        try:
            ws = self.connect_ws()
            self._set_active_ws(ws)
            self.sync_status_from_server()
            payload = self.post_status(
                status=self.current_status,
                idle_reason=self.current_idle_reason,
            )
            if payload:
                self.maybe_restart_if_requested(payload)
            self._probe_connection(ws)
            return 0
        finally:
            self._set_active_ws(None)
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

    def loop(self) -> int:
        heartbeat_thread = threading.Thread(
            target=self._background_heartbeat_loop,
            name="clawarena-watcher-heartbeat",
            daemon=True,
        )
        heartbeat_thread.start()
        while True:
            ws = None
            missed_pongs = 0
            try:
                ws = self.connect_ws()
                self._set_active_ws(ws)
                self._force_reconnect.clear()
                self.sync_status_from_server()
                payload = self.post_status(
                    status=self.current_status,
                    idle_reason=self.current_idle_reason,
                )
                if payload:
                    self.maybe_restart_if_requested(payload)
                while True:
                    if self._force_reconnect.is_set():
                        self._force_reconnect.clear()
                        raise WebSocketError("Watcher websocket feed is stale; reconnecting")
                    try:
                        message = ws.recv_json(timeout=TELEMETRY_HEARTBEAT_SECONDS)
                    except TimeoutError:
                        self.sync_status_from_server()
                        payload = self.post_status(
                            status=self.current_status,
                            idle_reason=self.current_idle_reason,
                        )
                        if payload:
                            self.maybe_restart_if_requested(payload)
                        self._retry_pending_wake()
                        if self._probe_connection(ws):
                            missed_pongs = 0
                            self._maybe_force_reconnect()
                            continue
                        missed_pongs += 1
                        if missed_pongs >= MAX_MISSED_PONGS:
                            raise WebSocketError("Watcher websocket ping timed out")
                        continue

                    missed_pongs = 0
                    self._handle_message(ws, message)
            except Exception as exc:  # noqa: BLE001
                failures = int(self.state.get("ws_consecutive_failures") or 0) + 1
                controlled_reconnect = isinstance(exc, WebSocketError) and (
                    "reconnecting" in str(exc).lower()
                    or "timed out" in str(exc).lower()
                )
                self.save_state(
                    ws_consecutive_failures=failures,
                    last_error={"kind": "exception", "message": str(exc), "at": utc_now()},
                )
                if not controlled_reconnect:
                    self.post_status(
                        status="error",
                        idle_reason="Watcher lost the live turn feed and is reconnecting.",
                        error_message=str(exc)[:500],
                    )
                self._maybe_self_restart_for_ws_failures(str(exc))
                time.sleep(ERROR_RETRY_DELAY_SECONDS)
            finally:
                self._set_active_ws(None)
                if ws is not None:
                    try:
                        ws.close()
                    except Exception:
                        pass

    def _background_heartbeat_loop(self) -> None:
        while not self._stop_event.wait(TELEMETRY_HEARTBEAT_SECONDS):
            try:
                self.sync_status_from_server()
                payload = self.post_status(
                    status=self.current_status,
                    idle_reason=self.current_idle_reason,
                )
                if payload:
                    self.maybe_restart_if_requested(payload)
                self._maybe_force_reconnect()
            except Exception:
                continue


def acquire_lock() -> Any:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK_PATH.open("w")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Another ClawArena watcher is already running.", file=sys.stderr)
        sys.exit(1)
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClawArena local turn watcher")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Poll once and exit",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=0,
        help="Legacy no-op flag kept for compatibility.",
    )
    parser.add_argument(
        "--ack-restart",
        action="store_true",
        help="Acknowledge a dashboard-triggered watcher restart on startup",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _lock = acquire_lock()
    watcher = Watcher(wait_seconds=args.wait_seconds)
    watcher.save_state(pid=os.getpid(), started_at=watcher.state.get("started_at") or utc_now())
    if args.ack_restart:
        watcher.post_status(
            status="idle",
            idle_reason="Watcher restarted from dashboard request.",
            restart_ack=True,
        )
    if args.once:
        return watcher.run_once()
    return watcher.loop()


if __name__ == "__main__":
    raise SystemExit(main())
