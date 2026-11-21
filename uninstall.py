#!/usr/bin/env python3
"""移除 Claude Statusline。

1. 刪除 ~/.claude/statusline/statusline.py 與執行時產生的快取檔
2. 從 ~/.claude/settings.json 移除 statusLine（只在它指向本工具時才移除；寫入前會備份）

支援 Windows / WSL / Linux / macOS。
"""

import json
import shutil
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
TARGET_DIR = CLAUDE_DIR / "statusline"
TARGET_FILE = TARGET_DIR / "statusline.py"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
RUNTIME_FILES = ["sessions.json", "last_stdin.json", "cache.json", "statusline.lock"]


def remove_script_and_state():
    if TARGET_FILE.exists():
        print(f"Removing {TARGET_FILE}...")
        TARGET_FILE.unlink()
    else:
        print("statusline.py is not installed at the target path.")

    for name in RUNTIME_FILES:
        path = TARGET_DIR / name
        if path.exists():
            path.unlink()

    # 目錄為空時才刪除，避免誤刪其他檔案
    if TARGET_DIR.exists() and not any(TARGET_DIR.iterdir()):
        TARGET_DIR.rmdir()


def remove_settings_entry():
    if not SETTINGS_FILE.exists():
        print("No settings.json found; nothing to clean up.")
        return

    try:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except ValueError:
        print(f"Warning: {SETTINGS_FILE} is not valid JSON; please remove statusLine manually.")
        return
    if not isinstance(settings, dict):
        print(f"Warning: {SETTINGS_FILE} is not a JSON object; please check it manually.")
        return

    status_line = settings.get("statusLine")
    if not isinstance(status_line, dict):
        print("No statusLine configuration found in settings.json.")
        return

    # 只移除指向本工具的設定，不動使用者其他的 statusLine
    command = str(status_line.get("command", ""))
    if "statusline" not in command or "claude" not in command.lower():
        print("statusLine in settings.json does not point to Claude Statusline; leaving it unchanged.")
        return

    print(f"Removing statusLine configuration from {SETTINGS_FILE}...")
    backup = SETTINGS_FILE.with_name("settings.json.bak")
    shutil.copy2(SETTINGS_FILE, backup)
    del settings["statusLine"]
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Configuration removed (backup: {backup}).")


def main():
    print("Uninstalling Claude Statusline...")
    remove_script_and_state()
    remove_settings_entry()
    print("\033[0;32mUninstallation successful!\033[0m")


if __name__ == "__main__":
    main()
