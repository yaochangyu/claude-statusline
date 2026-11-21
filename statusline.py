#!/usr/bin/env python3
"""Claude Code statusline — 欄位與 antigravity-statusline 對齊，支援 Windows / WSL / Linux / macOS。

Claude Code 會把 session 資訊以 JSON 經由 stdin 傳入，本腳本讀取後輸出多行狀態列：

  第 1 行：branch:<分支>*  ⇡ahead ⇣behind
  第 2 行：Model | 5h | wk | today | month | session
  第 3 行：skill | ctx | tokens | Tools | Steps

  - 5h / wk：Claude Code 提供 rate_limits 時才顯示（缺少時省略）
  - today / month：與 antigravity 相同，透過 `npx ccusage` 取得（背景更新快取）
  - tokens：當前 session 的輸入 ↑ / 輸出 ↓ token 累計

除錯：設定環境變數 CLAUDE_STATUSLINE_DUMP=1，會把收到的 stdin 存到
      ~/.claude/statusline/last_stdin.json。
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"

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
CACHE_FILE = DATA_DIR / "cache.json"
LOCK_FILE = DATA_DIR / "statusline.lock"
LAST_STDIN = DATA_DIR / "last_stdin.json"
CACHE_TTL = 30  # 秒
LOCK_TTL = 60  # 秒


# ---------------------------------------------------------------- I/O

def setup_io():
    """Windows 終端需要啟用 ANSI 跳脫序列，並以 UTF-8 輸出。"""
    if os.name == "nt":
        os.system("")
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
    if not isinstance(data, dict):
        return {}
    if os.environ.get("CLAUDE_STATUSLINE_DUMP"):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            LAST_STDIN.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return data


def read_json_file(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def write_json_file(path, value):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
    except OSError:
        pass


def as_dict(value):
    return value if isinstance(value, dict) else {}


def as_number(value, default=0.0):
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- formatting (對齊 antigravity)

def make_colored_bar(fraction, width=8):
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(fraction * width))
    empty = width - filled
    if fraction >= 1.0:
        bar = f"{RED}" + "#" * filled + f"{RESET}"
    else:
        bar = f"{GREEN}" + "#" * filled + f"{RESET}{DIM}" + "-" * empty + f"{RESET}"
    return f"{DIM}[{RESET}{bar}{DIM}]{RESET}"


def make_percentage_str(fraction):
    pct = int(round(fraction * 100))
    color = RED if fraction >= 1.0 else GREEN
    return f"{color}{pct}%{RESET}"


def format_time(sec):
    sec = int(as_number(sec))
    if sec <= 0:
        return "0m"
    days = sec // 86400
    hours = (sec % 86400) // 3600
    mins = (sec % 3600) // 60
    if days > 0:
        return f"~{days}d{hours}h"
    if hours > 0:
        return f"~{hours}h{mins}m"
    return f"~{mins}m"


def format_tokens(n):
    n = int(as_number(n))
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


# ---------------------------------------------------------------- git

def get_git_status_str(cwd):
    if not cwd or not os.path.isdir(cwd):
        return ""
    kwargs = dict(capture_output=True, text=True, timeout=1)
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        res = subprocess.run(["git", "--no-optional-locks", "-C", cwd, "status", "-b", "--porcelain"], **kwargs)
        if res.returncode != 0:
            return ""
        lines = res.stdout.strip().splitlines()
        if not lines or not lines[0].startswith("##"):
            return ""

        status_part = lines[0][2:].strip()
        ahead = behind = 0
        bracket = re.search(r"\[([^\]]+)\]", status_part)
        if bracket:
            content = bracket.group(1)
            m = re.search(r"ahead (\d+)", content)
            if m:
                ahead = int(m.group(1))
            m = re.search(r"behind (\d+)", content)
            if m:
                behind = int(m.group(1))
            status_part = status_part[:bracket.start()].strip()

        # 尚未有 commit 時輸出為 "## No commits yet on main"
        if status_part.startswith("No commits yet on "):
            branch = status_part[len("No commits yet on "):]
        else:
            branch = status_part.split("...")[0].strip()

        dirty_str = f"{RED}*{RESET}" if len(lines) > 1 else ""
        ab_parts = []
        if ahead > 0:
            ab_parts.append(f"{CYAN}⇡{ahead}{RESET}")
        if behind > 0:
            ab_parts.append(f"{RED}⇣{behind}{RESET}")
        ahead_behind = f" {DIM}|{RESET} " + " ".join(ab_parts) if ab_parts else ""
        return f"{DIM}branch:{RESET}{CYAN}{branch}{RESET}{dirty_str}{ahead_behind}"
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- transcript

def parse_transcript(transcript_path):
    """回傳 (tool_calls, steps, active_skill)。

    Claude Code 的 transcript 為 JSONL：每行一則訊息，assistant 訊息的 content 內含 tool_use 區塊。
    """
    tool_calls = 0
    steps = 0
    active_skill = None
    if not transcript_path or not os.path.exists(transcript_path):
        return tool_calls, steps, active_skill
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.startswith("{"):
                    continue
                steps += 1
                if '"tool_use"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = as_dict(entry.get("message"))
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    tool_calls += 1
                    if block.get("name") == "Skill":
                        skill = as_dict(block.get("input")).get("skill")
                        if skill:
                            active_skill = str(skill)
    except OSError:
        pass
    return tool_calls, steps, active_skill


def session_token_totals(data):
    """當前 session 的輸入 / 輸出 token 累計（優先 context_window.total_*，否則加總 current_usage）。"""
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


def session_minutes(data):
    """session 已進行的分鐘數（antigravity 格式：Nm）。"""
    cost = as_dict(data.get("cost"))
    if "total_duration_ms" in cost:
        return int(as_number(cost["total_duration_ms"]) // 60000)
    session_id = str(data.get("session_id") or "default")
    sessions = read_json_file(SESSION_FILE, {})
    now = time.time()
    if session_id not in sessions:
        sessions[session_id] = now
        recent = sorted(sessions.items(), key=lambda kv: kv[1])[-20:]
        write_json_file(SESSION_FILE, dict(recent))
    return int((now - sessions[session_id]) // 60)


# ---------------------------------------------------------------- ccusage 快取（today / month）

def run_ccusage(kind):
    cmd = ["npx", "--no-install", "ccusage", kind, "--json"]
    kwargs = dict(capture_output=True, text=True, timeout=20, shell=(os.name == "nt"))
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    res = subprocess.run(cmd, **kwargs)
    if res.returncode != 0:
        return []
    try:
        payload = json.loads(res.stdout)
    except ValueError:
        return []
    rows = payload.get(kind, []) if isinstance(payload, dict) else []
    return [r for r in rows if isinstance(r, dict)]


def period_cost(rows, period):
    """加總指定期間的花費；若資料含 agent 欄位，只取 agent == 'all' 的列。"""
    matched = [r for r in rows if (r.get("date") or r.get("period")) == period]
    if any("agent" in r for r in matched):
        matched = [r for r in matched if r.get("agent") == "all"]
    return sum(as_number(r.get("totalCost")) for r in matched)


def update_cache():
    """背景執行：更新 today / month 花費快取。"""
    try:
        if LOCK_FILE.exists() and time.time() - LOCK_FILE.stat().st_mtime < LOCK_TTL:
            return
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        return
    try:
        now = datetime.now()
        today_cost = period_cost(run_ccusage("daily"), now.strftime("%Y-%m-%d"))
        month_cost = period_cost(run_ccusage("monthly"), now.strftime("%Y-%m"))
        write_json_file(CACHE_FILE, {
            "today_cost": today_cost,
            "month_cost": month_cost,
            "updated_at": time.time(),
        })
    except (OSError, subprocess.SubprocessError):
        pass
    finally:
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass


def spawn_update():
    kwargs = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--update-cache"], **kwargs)
    except OSError:
        pass


# ---------------------------------------------------------------- render

def quota_segments(data):
    """5h / wk 額度（Claude Code 提供 rate_limits 時才顯示）。"""
    limits = as_dict(data.get("rate_limits"))
    now = time.time()
    parts = []
    for label, key in (("5h", "five_hour"), ("wk", "seven_day")):
        window = as_dict(limits.get(key))
        if "used_percentage" not in window:
            continue
        frac = as_number(window.get("used_percentage")) / 100.0
        reset_in = as_number(window.get("resets_at")) - now
        f_bar = make_colored_bar(frac, 8)
        f_pct = make_percentage_str(frac)
        star = "*" if frac >= 1.0 else ""
        parts.append(f"{DIM}{label}:{RESET}{f_bar}{f_pct}{star}{DIM}({format_time(reset_in)}){RESET}")
    return " ".join(parts)


def build_lines(data):
    cache = read_json_file(CACHE_FILE, {})
    if time.time() - as_number(cache.get("updated_at")) > CACHE_TTL:
        cache["updated_at"] = time.time()
        write_json_file(CACHE_FILE, cache)  # 先更新時間戳，避免短時間內重複啟動
        spawn_update()

    cwd = as_dict(data.get("workspace")).get("current_dir") or data.get("cwd") or os.getcwd()
    line1 = get_git_status_str(cwd)

    model = as_dict(data.get("model"))
    model_name = model.get("display_name") or model.get("id") or "Unknown"

    sep = f" {DIM}|{RESET} "
    segs = [f"{DIM}Model:{RESET} {CYAN}{model_name}{RESET}"]
    quota = quota_segments(data)
    if quota:
        segs.append(quota)
    segs.append(f"{DIM}today:{RESET}{GREEN}${as_number(cache.get('today_cost')):.2f}{RESET}")
    segs.append(f"{DIM}month:{RESET}{GREEN}${as_number(cache.get('month_cost')):.2f}{RESET}")
    segs.append(f"{DIM}session:{RESET}{GREEN}{session_minutes(data)}m{RESET}")
    line2 = "  " + sep.join(segs)

    ctx = as_dict(data.get("context_window"))
    ctx_frac = as_number(ctx.get("used_percentage")) / 100.0
    f_ctx = f"{DIM}ctx:{RESET}{make_colored_bar(ctx_frac, 10)}{make_percentage_str(ctx_frac)}"
    tin, tout = session_token_totals(data)
    f_tokens = f"{DIM}tokens:{RESET}{YELLOW}↑{format_tokens(tin)} ↓{format_tokens(tout)}{RESET}"
    tool_calls, steps, active_skill = parse_transcript(data.get("transcript_path", ""))
    f_stats = (
        f"{DIM}Tools:{RESET}{MAGENTA}{tool_calls}{RESET}"
        f"{sep}{DIM}Steps:{RESET}{MAGENTA}{steps}{RESET}"
    )
    parts = []
    if active_skill:
        parts.append(f"{DIM}skill:{RESET}{CYAN}{active_skill}{RESET}")
    parts += [f_ctx, f_tokens, f_stats]
    line3 = "  " + sep.join(parts)

    return [line for line in (line1, line2, line3) if line]


def main():
    if "--update-cache" in sys.argv[1:]:
        update_cache()
        return
    setup_io()
    data = read_stdin()
    try:
        lines = build_lines(data)
    except Exception as exc:  # 狀態列失敗時仍輸出訊息，不讓 Claude Code 出錯
        lines = [f"statusline error: {exc}"]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
