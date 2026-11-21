# Claude Statusline

[English](README.md) | [繁體中文](README.zh-TW.md)

可自訂的 Claude Code 狀態列（Python 腳本），支援 **Windows、WSL、Linux 與 macOS**。欄位與版面和 [antigravity-statusline](https://github.com/yaochangyu/antigravity-statusline) 對齊，並加上**當前 session 的 token 用量**。

## 功能

- **目錄與分支**：目前目錄名稱、Git 分支、未提交變更標記（`*`），以及 ahead / behind 數量。
- **模型與額度**：模型名稱，以及 `5h` / `wk` 使用量進度條與重置倒數（Claude Code 提供 `rate_limits` 時顯示）。
- **用量**：今日與本月 token 用量（`↑` 輸入含快取、`↓` 輸出），透過 `ccusage` 取得並在背景快取；`ccusage` 無法執行時隱藏。
- **Session**：session 持續的分鐘數。
- **Context 與 Token**：context 使用率進度條，以及當前 session 的輸入（`↑`）與輸出（`↓`）token。
- **活動**：從 transcript 讀取目前使用的 skill、工具呼叫數、Artifacts（以 `Write` 工具寫入的不重複檔案數）與步驟數。
- **跨平台**：只使用 Python 標準函式庫。Windows 會自動啟用 ANSI 色彩並以 UTF-8 輸出。

輸出範例：

```
dir:my-project  branch:main*
  Model: Opus 5.5 | 5h:[##------]30%(~59m) wk:[#-------]10%(~1d0h) | today:↑8.4M ↓68.3k | month:↑1.2M ↓9.9k | session:12m
  skill:write-style | ctx:[####------]42% | tokens:↑152.3k ↓8.4k | Tools:2 | Steps:3
```

> [!NOTE]
> - `today` / `month` 需要能以 `npx --no-install ccusage` 執行 ccusage，否則隱藏該欄位。
> - `5h` / `wk` 只有在 Claude Code 的 statusline 輸入包含 `rate_limits` 時才會出現。

## 環境需求

- **Python 3.8+**
  - Windows：到 [python.org](https://www.python.org/downloads/) 安裝，並確認 `python` 已加入 `PATH`。
  - WSL / Linux：`sudo apt update && sudo apt install -y python3`
  - macOS：`brew install python`
- **Git**（選用，用於顯示分支）

## 安裝

clone 此專案後執行安裝程式：

```bash
git clone <repository-url> claude-statusline
cd claude-statusline
python install.py      # Windows（WSL / Linux / macOS 請用 python3 install.py）
```

安裝程式會做兩件事：

1. 把 `statusline.py` 複製到 `~/.claude/statusline/statusline.py`。
2. 在 `~/.claude/settings.json` 設定 `statusLine`，指向上述副本。其他設定會保留，原檔案會備份為 `settings.json.bak`。

重新啟動 Claude Code（或開新 session）即可看到狀態列。

> [!NOTE]
> - Windows 與 WSL 各自有獨立的 `~/.claude/settings.json`，在兩邊使用 Claude Code 都要各執行一次安裝程式。
> - 若已有 `statusLine` 設定，安裝程式會覆蓋它；舊值會保留在備份檔中。

### AI Agent 安裝提示詞

若你使用 AI 程式助手，可以貼上以下提示詞：

> 請在 claude-statusline 專案目錄中執行 `python install.py` 幫我安裝，完成後檢查我的 `~/.claude/settings.json` 中的 `statusLine` 設定。

## 更新

拉取最新版本後執行更新程式：

```bash
git pull origin main
python update.py       # 或 python3 update.py
```

`update.py` 會把本地的 `statusline.py` 複製到 `~/.claude/statusline/`，下一次狀態列重繪時即會使用新版。

若單獨執行 `update.py`（不在專案目錄中），它會從 `update.py` 內的 `REMOTE_URL` 下載最新版。

## 移除

在專案目錄中執行移除程式：

```bash
python uninstall.py    # 或 python3 uninstall.py
```

會執行以下動作：

1. 刪除 `~/.claude/statusline/statusline.py` 與執行時產生的檔案（`sessions.json`、`last_stdin.json`）。
2. 只有當 `statusLine` 指向本工具時，才從 `~/.claude/settings.json` 移除該設定；其他狀態列設定不會被動到。寫入前會先備份。

## 疑難排解

Claude Code 會把 session 資料以 JSON 經由 stdin 傳給狀態列。若要檢查內容，請加上傾印開關執行：

```bash
CLAUDE_STATUSLINE_DUMP=1 claude
```

然後查看 `~/.claude/statusline/last_stdin.json`。注意：只有在狀態列重繪時才會寫入。

## Token 資料來源

1. `context_window.total_input_tokens` 與 `context_window.total_output_tokens`（session 累計值）。
2. 若沒有上述欄位，則加總 `context_window.current_usage`（包含 cache 讀寫）。

## 手動設定

不使用安裝程式時，可在 `~/.claude/settings.json` 加入：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 \"/absolute/path/to/statusline.py\"",
    "padding": 0,
    "refreshInterval": 30
  }
}
```

Windows 請改用 `python`，路徑用正斜線，例如 `python "C:/Users/<你>/.claude/statusline/statusline.py"`。
