# VS Code Dotfiles

This directory contains Visual Studio Code configuration files and a list of installed extensions.

## Files

- `settings.json`: User settings preferences.
- `keybindings.json`: Custom keyboard shortcuts.
- `extensions.txt`: A plain text list of installed VS Code extensions.
- `scripts/install-extensions.ps1`: A PowerShell script to install all extensions listed in `extensions.txt`.
- `scripts/save-extensions.ps1`: A PowerShell script to save currently installed extensions to `extensions.txt`.
- `scripts/install-extensions.sh`: A Bash script to install all extensions listed in `extensions.txt`.
- `scripts/save-extensions.sh`: A Bash script to save currently installed extensions to `extensions.txt`.

## Installation

### 1. Apply Configuration Files

You need to copy or symlink the `settings.json` and `keybindings.json` files to your VS Code User data directory. 

**Windows:**
```powershell
# Copy files
Copy-Item .\settings.json $env:APPDATA\Code\User\settings.json -Force
Copy-Item .\keybindings.json $env:APPDATA\Code\User\keybindings.json -Force

# OR create symlinks (requires running PowerShell as Administrator)
New-Item -ItemType SymbolicLink -Path $env:APPDATA\Code\User\settings.json -Target .\settings.json -Force
New-Item -ItemType SymbolicLink -Path $env:APPDATA\Code\User\keybindings.json -Target .\keybindings.json -Force
```

**macOS:**
```bash
ln -sf $(pwd)/settings.json ~/Library/Application\ Support/Code/User/settings.json
ln -sf $(pwd)/keybindings.json ~/Library/Application\ Support/Code/User/keybindings.json
```

**Linux:**
```bash
ln -sf $(pwd)/settings.json ~/.config/Code/User/settings.json
ln -sf $(pwd)/keybindings.json ~/.config/Code/User/keybindings.json
```

### 2. Install Extensions

Run the included script to install all the extensions listed in `extensions.txt`. Make sure the `code` (or `antigravity`) CLI command is available in your PATH.

**Windows (PowerShell):**
```powershell
# Default (uses 'code')
.\scripts\install-extensions.ps1

# Specify the Antigravity editor
.\scripts\install-extensions.ps1 -Editor antigravity
```

*(Note: If you encounter an execution policy error on Windows, you might need to allow local scripts by running `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first.)*

**macOS / Linux (Bash):**
```bash
# Default (uses 'code')
./scripts/install-extensions.sh

# Specify the Antigravity editor
./scripts/install-extensions.sh antigravity
```

## Updating Extensions List

Whenever you install new extensions that you want to keep track of, you can update the `extensions.txt` file by running the save scripts. By default, these scripts will **merge** your currently installed extensions with the existing list in `extensions.txt` and sort them. You can optionally choose to completely **overwrite** the file instead.

**Windows (PowerShell):**
```powershell
# Default (uses 'code' and merges)
.\scripts\save-extensions.ps1

# Specify the Antigravity editor and merge
.\scripts\save-extensions.ps1 -Editor antigravity

# Overwrite instead of merge
.\scripts\save-extensions.ps1 -Overwrite
```

**macOS / Linux (Bash):**
```bash
# Default (uses 'code' and merges)
./scripts/save-extensions.sh

# Specify the Antigravity editor and merge
./scripts/save-extensions.sh antigravity

# Overwrite instead of merge
./scripts/save-extensions.sh --overwrite
```

## Script Usage and Help

All scripts come with built-in help. 

**Windows (PowerShell):**
Use `Get-Help` to see detailed documentation for any script.
```powershell
Get-Help .\scripts\install-extensions.ps1 -Detailed
Get-Help .\scripts\save-extensions.ps1 -Detailed
```

**macOS / Linux (Bash):**
Use the `-h` or `--help` flag to see the usage menu.
```bash
./scripts/install-extensions.sh --help
./scripts/save-extensions.sh --help
```
