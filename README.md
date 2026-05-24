# Dotfiles

Personal configuration files for macOS and Linux environments.

## Quick Start — One-Command Install

Works on **Ubuntu / Kubuntu** (native and WSL). Installs all prerequisites, Homebrew, tools, configs, nvm/Node, and sets zsh as the default shell in a single run.

```bash
git clone <repo-url> ~/dotfiles
cd ~/dotfiles
./install.sh
```

Then open a new terminal — Zim will bootstrap itself and install plugins on first launch.

`install.sh` is idempotent: safe to re-run at any time.

## What `install.sh` Does

1. **APT prerequisites** (Ubuntu/Debian only): installs `build-essential`, `procps`, `curl`, `file`, `git`, `zsh` — the Homebrew-on-Linux requirements plus zsh itself.
2. **Homebrew**: installs Homebrew non-interactively if missing; otherwise updates.
3. **brew bundle**: installs everything listed in `Brewfile`.
4. **Symlinks** all configs into place (backing up existing real files to `<file>.bak`):
   - `zsh/.zshrc`, `zsh/.zimrc`, `zsh/.zshenv` → `~/.zshrc` etc.
   - `vscode/settings.json`, `vscode/keybindings.json` → `~/.config/Code/User/`
   - Everything under `claude_code/` (except READMEs) → `~/.claude/`
5. **nvm + Node**: installs nvm if missing, then installs the Node version from `.nvmrc` (`lts/*`).
6. **VS Code extensions**: runs `vscode/scripts/install-extensions.sh` if `code` is on PATH; otherwise prints a skip note.
7. **Default shell**: sets zsh via `chsh`. If `chsh` fails (common in some WSL setups), prints clear manual fallback instructions instead of aborting.

## Structure

```
dotfiles/
├── .nvmrc            # Node version (lts/*)
├── Brewfile          # Homebrew dependencies
├── install.sh        # Full one-command setup (start here)
├── bootstrap.zsh     # Brew-only convenience re-run
├── claude_code/      # Claude Code settings → ~/.claude/
├── vscode/           # VS Code settings, keybindings, and extensions
└── zsh/              # Zsh shell configuration and plugins
```

## What's Included

### CLI Tools ([Brewfile](Brewfile))

| Tool | Description |
|------|-------------|
| [bat](https://github.com/sharkdp/bat) | `cat` with syntax highlighting |
| [dust](https://github.com/bootandy/dust) | Intuitive disk usage viewer |
| [eza](https://github.com/eza-community/eza) | Modern replacement for `ls` |
| [fd](https://github.com/sharkdp/fd) | Simple, fast alternative to `find` |
| [fzf](https://github.com/junegunn/fzf) | Fuzzy finder |
| [gping](https://github.com/orf/gping) | Graphical ping |
| [htop](https://htop.dev/) | Interactive process viewer |
| [httpie](https://httpie.io/) | Human-friendly HTTP client |
| [jq](https://jqlang.github.io/jq/) | JSON processor |
| [mise](https://mise.jdx.dev/) | Polyglot runtime manager |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Fast recursive search |
| [tldr](https://tldr.sh/) | Simplified man pages |
| [trippy](https://trippy.cli.rs/) | Network diagnostic tool |
| [uv](https://docs.astral.sh/uv/) | Fast Python package manager |
| [yq](https://github.com/mikefarah/yq) | YAML processor |

> **WSL note**: `iputils` is installed with `link: false` so it doesn't override the system `ping`.

### [Zsh](zsh/)

Shell configuration using Zim for plugin management, Powerlevel10k for the prompt, and Zim's built-in modules (environment, input, termtitle, utility) for sensible defaults. See the [Zsh README](zsh/README.md) for details.

### [VS Code](vscode/)

Editor settings, keybindings, and a managed extensions list with install/save scripts. See the [VS Code README](vscode/README.md) for details.

## Advanced / Manual Setup

If you prefer to manage symlinks yourself instead of using `install.sh`:

```bash
# Zsh
ln -sfn ~/dotfiles/zsh/.zshrc   ~/.zshrc
ln -sfn ~/dotfiles/zsh/.zimrc   ~/.zimrc
ln -sfn ~/dotfiles/zsh/.zshenv  ~/.zshenv

# VS Code
mkdir -p ~/.config/Code/User
ln -sfn ~/dotfiles/vscode/settings.json    ~/.config/Code/User/settings.json
ln -sfn ~/dotfiles/vscode/keybindings.json ~/.config/Code/User/keybindings.json

# Claude Code
mkdir -p ~/.claude
ln -sfn ~/dotfiles/claude_code/settings.json ~/.claude/settings.json

# Homebrew packages
./bootstrap.zsh
```
