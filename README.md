# Spotlight Launcher

Spotlight Launcher is a lightweight keyboard launcher for Windows.

It runs in the background, opens with a global hotkey, and lets you launch apps, shell commands, folders, and URLs from one search box.

## What This Tool Does

- Opens with `Ctrl + Alt + Space`
- Searches commands by name, alias, and fuzzy match
- Executes shell commands (for example: `notepad`, `code .`, `explorer D:\`)
- Opens URLs in your default browser
- Lets you manage commands in-app with a built-in editor

## System Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer

## Install Or Update

For both first-time install and future updates, run:

```powershell
.\installer.bat
```

The script will:

- find Python 3.10+ on your system or try to install it with `winget`
- create a dedicated `.venv` inside this repo
- install or update the app and dependencies in that virtual environment
- create `app.bat` in the repo root to launch the GUI
- create a `spotlight-sid.bat` shim in `%USERPROFILE%\spotlight-launcher-bin`
- add `%USERPROFILE%\spotlight-launcher-bin` to your user `PATH`

After the script finishes, open a new terminal and run:

```powershell
spotlight-sid
```

## Manual Setup (Fallback)

Run these steps once on Windows PowerShell:

1. Clone the repo.

```powershell
git clone <your-repo-url>
cd spotlight-launcher
```

2. Create and activate a virtual environment.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install the app.

```powershell
python -m pip install --upgrade pip
python -m pip install .
```

4. Start the launcher.

```powershell
spotlight-sid
```

After launch, the process detaches and keeps running in the background.

## First Run: Add Your Commands

1. Press `Ctrl + Alt + Space` to open the launcher.
2. Click the green top-left button (Manage).
3. Add entries with:
   - `name`: unique command name you will search
   - `target`: the URL or shell command to execute
   - `folder path`: used when `type` is `folder`
   - `type`: `url`, `command`, or `folder`
   - `aliases`: optional comma-separated shortcuts
4. Optional: tick `Start launcher when Windows signs in` to launch it automatically at login.
5. Click `Save Entry`, then `Done`.

Example entries:

```json
{
  "commands": [
    {
      "name": "google",
      "target": "https://google.com",
      "type": "url",
      "aliases": ["search"]
    },
    {
      "name": "vscode-here",
      "target": "code .",
      "type": "command",
      "aliases": ["code"]
    },
    {
      "name": "notes",
      "target": "notepad",
      "type": "command",
      "aliases": ["np"]
    },
    {
      "name": "inetpub",
      "target": "C:\\inetpub",
      "type": "folder",
      "aliases": ["iis"]
    }
  ]
}
```

## Everyday Usage

1. Open launcher: `Ctrl + Alt + Space`
2. Type a command name or alias
3. Press:
   - `Enter` to run
   - `Tab` to autocomplete
   - `Up/Down` to navigate results
   - `Esc` to hide

Top-left controls:

- Red: exit launcher completely
- Yellow: hide launcher
- Green: open command manager

In the manager dialog, you can also enable or disable Windows startup with a checkbox.

## Command Storage

By default, commands are stored at:

`%APPDATA%\SpotlightLauncher\commands.json`

You can override this path:

```powershell
$env:SPOTLIGHT_COMMANDS_FILE = "D:\path\to\commands.json"
spotlight-sid
```

## Developer Run (Without Installing Script)

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Update After Pulling Changes

Run the same script again:

```powershell
.\installer.bat
```

## Troubleshooting

### Hotkey does not open launcher

- Verify no other app is using `Ctrl + Alt + Space`
- Exit existing launcher instances, then run `spotlight-sid` again

### `spotlight-sid` command not found

- Ensure your virtual environment is activated
- Or run with module mode: `python -m main`

### Some commands fail to launch

- Confirm the command works in PowerShell first
- Use full paths when needed (for example: `"C:\Program Files\App\app.exe"`)
- For folders, use the `folder` type and enter the directory path directly (for example: `C:\inetpub`)
- For workspace commands like `code .`, ensure `code` is available in your PATH

## Project Structure

- `main.py`: app startup, background process behavior, global hotkey listener
- `launcher.py`: UI, command manager, suggestion ranking, command execution
- `style.py`: Apple-style Qt theme
- `pyproject.toml`: package metadata and CLI entry point
