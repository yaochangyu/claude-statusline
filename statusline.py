#!/usr/bin/env python3
"""Claude Code statusline — 支援 Windows 與 WSL / Linux / macOS。

Claude Code 會把 session 資訊以 JSON 經由 stdin 傳入，本腳本讀取後輸出多行狀態列。
顯示內容：
  第 1 行：目錄 + Git 分支 (含 dirty 標記)
  第 2 行：模型 | context 使用率 | 當前 session token (↑ 輸入 / ↓ 輸出) | 費用 | session 時長

除錯：設定環境變數 CLAUDE_STATUSLINE_DUMP=1 會把收到的 stdin 存到
      ~/.claude/statusline/last_stdin.json，方便確認欄位。
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

VERSION = "1.0.0"

ESC = "\033["
RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
GRAY = "\033[37m"

DATA_DIR = Path.home() / ".claude" / "statusline"
SESSION_FILE = DATA_DIR / "sessions.json"


def setup_io():
    """Windows 終端需要啟用 ANSI 跳脫序列，並以 UTF-8 輸出。"""
    if os.name == "nt":
        os.system("")  # 觸發 Windows 10+ 的 VT 處理模式
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def read_stdin():
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        if not raw.strip():
            return {}
        data = json.loads(raw)
    except (OSError, ValueError):
        return {}
    if os.environ.get("CLAUDE_STATUSLINE_DUMP"):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            (DATA_DIR / "last_stdin.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass
    return data if isinstance(data, dict) else {}


def as_dict(value):
    return value if isinstance(value, dict) else {}


def as_number(value, default=0):
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_tokens(n):
    n = int(as_number(n))
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def make_bar(fraction, width=10):
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(fraction * width))
    color = RED if fraction >= 0.9 else YELLOW if fraction >= 0.7 else GREEN
    return f"{DIM}[{RESET}{color}{'#' * filled}{RESET}{DIM}{'-' * (width - filled)}]{RESET}"


def format_duration(ms):
    secs = int(as_number(ms) // 1000)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def git_info(cwd):
    """回傳 (branch, dirty)；不是 git repo 或沒有 git 時回傳 (None, False)。"""
    if not cwd or not os.path.isdir(cwd):
        return None, False
    kwargs = dict(cwd=cwd, capture_output=True, text=True, timeout=2)
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        # symbolic-ref 在尚未有 commit 的分支上也能運作（rev-parse 會失敗）
        branch = subprocess.run(["git", "symbolic-ref", "--short", "-q", "HEAD"], **kwargs)
        if branch.returncode != 0:
            return None, False
        status = subprocess.run(["git", "status", "--porcelain"], **kwargs)
        dirty = status.returncode == 0 and bool(status.stdout.strip())
        return branch.stdout.strip() or None, dirty
    except (OSError, subprocess.SubprocessError):
        return None, False


def session_token_totals(data):
    """取得當前 session 的 token 累計值。

    優先使用 context_window.total_input_tokens / total_output_tokens；
    若不存在，改以 current_usage 加總（cache 讀寫也計入輸入）。
    """
    ctx = as_dict(data.get("context_window"))
    if "total_input_tokens" in ctx or "total_output_tokens" in ctx:
        return as_number(ctx.get("total_input_tokens")), as_number(ctx.get("total_output_tokens"))

    usage = as_dict(ctx.get("current_usage"))
    tin = (
        as_number(usage.get("input_tokens"))
        + as_number(usage.get("cache_creation_input_tokens"))
        + as_number(usage.get("cache_read_input_tokens"))
    )
    return tin, as_number(usage.get("output_tokens"))


def session_elapsed_minutes(data, session_id):
    """以本地快取記錄 session 第一次出現的時間（資料中無時長時使用）。"""
    try:
        sessions = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        sessions = {}
    if not isinstance(sessions, dict):
        sessions = {}
    now = time.time()
    if session_id not in sessions:
        sessions[session_id] = now
        # 只保留最近 20 個 session 的紀錄
        recent = sorted(sessions.items(), key=lambda kv: kv[1])[-20:]
        sessions = dict(recent)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            SESSION_FILE.write_text(json.dumps(sessions), encoding="utf-8")
        except OSError:
            pass
    return int((now - sessions[session_id]) // 60)


def build_lines(data):
    model = as_dict(data.get("model"))
    model_name = model.get("display_name") or model.get("id") or "Unknown"

    workspace = as_dict(data.get("workspace"))
    cwd = workspace.get("current_dir") or data.get("cwd") or os.getcwd()
    dir_name = os.path.basename(os.path.normpath(cwd)) or cwd

    # 第 1 行：目錄 + Git
    branch, dirty = git_info(cwd)
    line1 = f"{DIM}dir:{RESET}{CYAN}{dir_name}{RESET}"
    if branch:
        star = f"{RED}*{RESET}" if dirty else ""
        line1 += f" {DIM}git:{RESET}{MAGENTA}{branch}{RESET}{star}"

    # 第 2 行：模型 / ctx / token / 費用 / 時長
    ctx = as_dict(data.get("context_window"))
    used = as_number(ctx.get("used_percentage"))
    frac = used / 100.0
    ctx_str = f"{DIM}ctx:{RESET}{make_bar(frac)}{GREEN if frac < 0.9 else RED}{int(round(used))}%{RESET}"

    tin, tout = session_token_totals(data)
    tok_str = f"{DIM}tokens:{RESET}{YELLOW}↑{format_tokens(tin)} ↓{format_tokens(tout)}{RESET}"
    total_tok = format_tokens(tin + tout)
    tok_str += f" {DIM}(Σ{total_tok}){RESET}"

    cost = as_dict(data.get("cost"))
    cost_str = ""
    if "total_cost_usd" in cost:
        cost_str = f" {DIM}|{RESET} {DIM}cost:{RESET}{GREEN}${as_number(cost['total_cost_usd']):.2f}{RESET}"

    if "total_duration_ms" in cost:
        dur = format_duration(cost["total_duration_ms"])
    else:
        dur = f"{session_elapsed_minutes(data, data.get('session_id', 'default'))}m"
    sep = f" {DIM}|{RESET} "
    line2 = (
        f"  {DIM}Model:{RESET} {CYAN}{model_name}{RESET}{sep}{ctx_str}{sep}{tok_str}"
        f"{cost_str}{sep}{DIM}session:{RESET}{GREEN}{dur}{RESET}"
    )
    return [line1, line2]


def main():
    setup_io()
    data = read_stdin()
    try:
        lines = build_lines(data)
    except Exception as exc:  # 狀態列失敗時仍輸出可讀訊息，不讓 Claude Code 出錯
        lines = [f"statusline error: {exc}"]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
