# Claude Statusline

[English](README.md) | [繁體中文](README.zh-TW.md)

A customizable Python statusline for Claude Code that works on **Windows, WSL, Linux and macOS**. Its fields and layout mirror [antigravity-statusline](https://github.com/yaochangyu/antigravity-statusline), with the **token usage of the current session** added.

## Features

- **Branch**: Current Git branch, dirty marker (`*`), and ahead/behind counts.
- **Model & Quota**: Model name, `5h` and `wk` usage bars with reset countdowns (shown when Claude Code provides `rate_limits`).
- **Cost**: Today's and this month's API cost, from `ccusage` and cached in the background.
- **Session**: Session duration in minutes.
- **Context & Tokens**: Context usage bar, plus the current session's input (`↑`) and output (`↓`) tokens.
- **Activity**: Active skill, tool call count, and step count from the transcript.
- **Cross-platform**: Uses only the Python standard library. Enables ANSI colors on Windows and forces UTF-8 output.

Example output:

```
branch:main*
  Model: Opus 5.5 | 5h:[##------]30%(~59m) wk:[#-------]10%(~1d0h) | today:$4.21 | month:$87.50 | session:12m
  skill:write-style | ctx:[####------]42% | tokens:↑152.3k ↓8.4k | Tools:2 | Steps:3
```

> [!NOTE]
> - `today` / `month` require `ccusage` to be runnable with `npx --no-install ccusage`. Without it they show `$0.00`.
> - `5h` / `wk` appear only when Claude Code includes `rate_limits` in its statusline input.

## Prerequisites

- **Python 3.8+**
  - Windows: install from [python.org](https://www.python.org/downloads/) and make sure `python` is on your `PATH`.
  - WSL / Linux: `sudo apt update && sudo apt install -y python3`
  - macOS: `brew install python`
- **Git** (optional, for branch information)

## Installation

Clone the repository and run the installer:

```bash
git clone <repository-url> claude-statusline
cd claude-statusline
python install.py      # Windows (or `python3 install.py` on WSL / Linux / macOS)
```

The installer does two things:

1. Copies `statusline.py` to `~/.claude/statusline/statusline.py`.
2. Sets the `statusLine` entry in `~/.claude/settings.json` to run that copy. Your other settings are kept, and the previous file is backed up as `settings.json.bak`.

Restart Claude Code (or start a new session) to see the statusline.

> [!NOTE]
> - Windows and WSL keep **separate** `~/.claude/settings.json` files. Run the installer in each environment where you use Claude Code.
> - If you already have a `statusLine` entry, the installer replaces it. The backup keeps the old value.

### AI Agent Installation Prompt

If you use an AI coding assistant, you can paste this prompt:

> Please install the claude-statusline repository for me by running `python install.py` in the repository directory, then verify the `statusLine` entry in my `~/.claude/settings.json`.

## Update

Pull the latest changes and run the updater:

```bash
git pull origin main
python update.py       # or `python3 update.py`
```

`update.py` copies the local `statusline.py` to `~/.claude/statusline/`. Claude Code picks up the new version on the next statusline refresh.

If you run `update.py` on its own without the repository, it downloads the latest file from `REMOTE_URL` (set inside `update.py`).

## Uninstallation

Run the uninstaller from the repository directory:

```bash
python uninstall.py    # or `python3 uninstall.py`
```

This will:

1. Delete `~/.claude/statusline/statusline.py` and its runtime files (`sessions.json`, `last_stdin.json`).
2. Remove the `statusLine` entry from `~/.claude/settings.json`, but only if it points to this tool. Other statusline settings are left alone. A backup is written first.

## Troubleshooting

Claude Code sends session data to the statusline as JSON on stdin. To inspect it, run Claude Code with the dump switch:

```bash
CLAUDE_STATUSLINE_DUMP=1 claude
```

Then open `~/.claude/statusline/last_stdin.json`. Note that the dump is written only when the statusline is rendered.

## Where the token numbers come from

1. `context_window.total_input_tokens` and `context_window.total_output_tokens` (session totals).
2. If those fields are missing, the sum of `context_window.current_usage` (including cache reads and writes).

## Manual configuration

Without the installer, add this to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 \"/absolute/path/to/statusline.py\"",
    "padding": 0
  }
}
```

On Windows, use `python` and forward slashes, for example `python "C:/Users/<you>/.claude/statusline/statusline.py"`.
