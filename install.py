#!/usr/bin/env python3
"""安裝 Claude Statusline。

1. 將 statusline.py 複製到 ~/.claude/statusline/statusline.py
2. 在 ~/.claude/settings.json 設定 statusLine 指向該檔案（寫入前會備份為 settings.json.bak）

支援 Windows / WSL / Linux / macOS。
"""

import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_FILE = HERE / "statusline.py"

CLAUDE_DIR = Path.home() / ".claude"
TARGET_DIR = CLAUDE_DIR / "statusline"
TARGET_FILE = TARGET_DIR / "statusline.py"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"


def build_command():
    # Windows 用 python；WSL / Linux / macOS 用 python3。路徑加引號以支援空白。
    interpreter = "python" if os.name == "nt" else "python3"
    return f'{interpreter} "{TARGET_FILE.as_posix()}"'


def main():
    print("Installing Claude Statusline...")

    if not SRC_FILE.exists():
        print(f"Error: {SRC_FILE} not found. Run this script from the cloned repository.")
        sys.exit(1)

    # 1. 複製腳本
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Copying statusline.py to {TARGET_FILE}...")
    try:
        shutil.copy(SRC_FILE, TARGET_FILE)
    except OSError as e:
        print(f"Error copying file: {e}")
        sys.exit(1)

    # 2. 設定 settings.json（保留其他設定）
    print(f"Configuring statusLine in {SETTINGS_FILE}...")
    settings = {}
    if SETTINGS_FILE.exists():
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except ValueError:
            print(f"Error: {SETTINGS_FILE} is not valid JSON. Please fix it manually and retry.")
            sys.exit(1)
        if not isinstance(settings, dict):
            print(f"Error: {SETTINGS_FILE} is not a JSON object. Please check it manually.")
            sys.exit(1)
        backup = SETTINGS_FILE.with_name("settings.json.bak")
        shutil.copy2(SETTINGS_FILE, backup)
        print(f"Backed up existing settings to {backup}")

    settings["statusLine"] = {
        "type": "command",
        "command": build_command(),
        "padding": 0,
    }

    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError as e:
        print(f"Error writing settings: {e}")
        sys.exit(1)

    print("\033[0;32mInstallation successful!\033[0m")
    print(f"statusLine.command = {settings['statusLine']['command']}")


if __name__ == "__main__":
    main()
