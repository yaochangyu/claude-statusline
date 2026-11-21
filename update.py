#!/usr/bin/env python3
"""更新已安裝的 Claude Statusline。

- 若在 clone 下來的專案目錄中執行：複製本地 statusline.py（建議先 git pull）
- 若單獨執行本檔案（沒有 statusline.py 在旁邊）：從 GitHub 下載最新版

支援 Windows / WSL / Linux / macOS。
"""

import shutil
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_FILE = HERE / "statusline.py"

TARGET_DIR = Path.home() / ".claude" / "statusline"
TARGET_FILE = TARGET_DIR / "statusline.py"

# 遠端來源：發布到 GitHub 後請填入該 statusline.py 的 raw URL
REMOTE_URL = ""


def main():
    print("Updating Claude Statusline to the latest version...")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    if SRC_FILE.exists():
        print(f"Copying local statusline.py to {TARGET_FILE}...")
        try:
            shutil.copy(SRC_FILE, TARGET_FILE)
        except OSError as e:
            print(f"Error copying file: {e}")
            sys.exit(1)
    else:
        if not REMOTE_URL:
            print("Local statusline.py not found and REMOTE_URL is not configured in update.py.")
            sys.exit(1)
        print(f"Local statusline.py not found. Downloading from {REMOTE_URL}...")
        try:
            with urllib.request.urlopen(REMOTE_URL, timeout=10) as response:
                content = response.read()
            TARGET_FILE.write_bytes(content)
        except Exception as e:
            print(f"Error downloading script: {e}")
            sys.exit(1)

    print("\033[0;32mUpdate successful!\033[0m")


if __name__ == "__main__":
    main()
