# Claude Statusline

[English](README.md) | [繁體中文](README.zh-TW.md)

A customizable Python statusline for Claude Code that works on **Windows, WSL, Linux and macOS**. Its fields and layout mirror [antigravity-statusline](https://github.com/yaochangyu/antigravity-statusline), with the **token usage of the current session** added.

## Features

- **Directory & Branch**: Current directory name, Git branch, dirty marker (`*`), and ahead/behind counts.
- **Model & Quota**: Model name, `5h` and `wk` usage bars with reset countdowns (shown when Claude Code provides `rate_limits`).
- **Usage**: Today's and this month's token usage (`↑` input incl. cache, `↓` output), from `ccusage` and cached in the background. Hidden when `ccusage` is unavailable.
- **Session**: Session duration in minutes.
- **Context & Tokens**: Context usage bar, plus the current session's input (`↑`) and output (`↓`) tokens.
- **Activity**: Active skill, tool call count, artifact count (unique files written via the `Write` tool), and step count from the transcript.
- **Cross-platform**: Uses only the Python standard library. Enables ANSI colors on Windows and forces UTF-8 output.

Example output:

```
dir:/home/you/projects/my-project  branch:main*
  Model: Opus 5.5 | 5h:[##------]30%(~59m) wk:[#-------]10%(~1d0h) | today:↑8.4M ↓68.3k | month:↑1.2M ↓9.9k | session:12m
  skill:write-style | ctx:[####------]42% | tokens:↑152.3k ↓8.4k | Tools:2 | Artifacts:1 | Steps:3
```

> [!NOTE]
> - `today` / `month` require `ccusage` to be runnable with `npx --no-install ccusage`. Without it they are hidden.
> - `5h` / `wk` appear only when Claude Code includes `rate_limits` in its statusline input.

## Prerequisites

- **Python 3.8+**: The statusline renderer requires Python 3. You can verify if it's installed by running `python3 --version` (Windows: `python --version`).
  - Windows: install from [python.org](https://www.python.org/downloads/) and make sure `python` is on your `PATH`.
  - WSL / Linux: `sudo apt update && sudo apt install -y python3`
  - macOS: `brew install python`
- **Git** (optional, for branch information)

## Installation

### AI Agent Installation Prompt

If you are using an AI coding assistant (like Antigravity or Claude Code), you can copy and paste the following prompt to let the agent do the installation for you:

> Please install the claude-statusline repository for me by running this remote Python installer:
> `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/yaochangyu/claude-statusline/main/install.py').read())"`
> After running, verify the statusLine settings in my `~/.claude/settings.json` file.

### 1. Remote Installation (Recommended)

You can run the installer directly using Python without cloning the repository:

```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/yaochangyu/claude-statusline/main/install.py').read())"
```

> [!TIP]
> - On Linux / macOS / WSL systems where the default command is `python3`, replace the beginning with `python3 -c ...`.

### 2. Local Installation (For Developers)

If you plan to customize the statusline, clone the repository and run the local installer:

```bash
git clone https://github.com/yaochangyu/claude-statusline.git
cd claude-statusline
python install.py      # or `python3 install.py` on WSL / Linux / macOS
```

> [!NOTE]
> - Windows and WSL keep **separate** `~/.claude/settings.json` files. Run the installer in each environment where you use Claude Code.
> - If you already have a `statusLine` entry, the installer replaces it. The previous file is backed up as `settings.json.bak`.
> - Restart Claude Code (or start a new session) to see the statusline.

## How It Works & Configuration

The installer does two things:

1. Copies `statusline.py` to `~/.claude/statusline/statusline.py` (from the local repository, or from GitHub when run remotely).
2. Sets the `statusLine` entry in `~/.claude/settings.json` to run that copy. Your other settings are kept.

The resulting configuration looks like this:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 \"/home/<you>/.claude/statusline/statusline.py\"",
    "padding": 0,
    "refreshInterval": 30
  }
}
```

> [!NOTE]
> - `refreshInterval` re-runs the statusline every 30 seconds, so `today` / `month` stay current while the session is idle. Claude Code also re-runs it on conversation events.
> - On Windows, `~` is not expanded in `settings.json`. The installer writes the absolute path in quotes (for example `python "C:/Users/<you>/.claude/statusline/statusline.py"`).

### Manual Configuration

Without the installer, add the block above to `~/.claude/settings.json`, replacing the path with the absolute path to `statusline.py`.

### Token Data Source

1. `context_window.total_input_tokens` and `context_window.total_output_tokens` (session totals).
2. If those fields are missing, the sum of `context_window.current_usage` (including cache reads and writes).

### Troubleshooting

Claude Code sends session data to the statusline as JSON on stdin. To inspect it, run Claude Code with the dump switch:

```bash
CLAUDE_STATUSLINE_DUMP=1 claude
```

Then open `~/.claude/statusline/last_stdin.json`. The dump is written only when the statusline is rendered.

## Update

### 1. Remote Update (Recommended)

Update without cloning the repository. This downloads the latest `statusline.py` from GitHub and overwrites the copy in `~/.claude/statusline/`, while keeping your `settings.json` intact:

```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/yaochangyu/claude-statusline/main/update.py').read())"
```

> [!TIP]
> - On Linux / macOS / WSL systems where the default command is `python3`, replace the beginning with `python3 -c ...`.

### 2. AI Agent Update Prompt

If you are using an AI coding assistant (like Antigravity or Claude Code), you can copy and paste the following prompt to let the agent update the statusline for you:

> Please update claude-statusline to the latest version by running this remote Python update script:
> `python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/yaochangyu/claude-statusline/main/update.py').read())"`
> Also verify the `statusLine` entry in my `~/.claude/settings.json` file.

### 3. Local Update (For Developers with a cloned repository)

If you previously cloned the repository, pull the latest changes and run the updater:

```bash
git pull origin main
python update.py       # or `python3 update.py`
```

## Uninstallation

### 1. Remote Uninstallation

You can run the uninstaller directly from GitHub:

```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/yaochangyu/claude-statusline/main/uninstall.py').read())"
```

This deletes `~/.claude/statusline/statusline.py` and its runtime files (`sessions.json`, `last_stdin.json`, `cache.json`, `statusline.lock`), and removes the `statusLine` entry from `~/.claude/settings.json` only if it points to this tool. A backup is written first.

### 2. Local Uninstallation

Run the uninstaller script in the cloned repository directory:

```bash
python uninstall.py    # or `python3 uninstall.py`
```
