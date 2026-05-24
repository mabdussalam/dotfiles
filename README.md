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

1. **APT prerequisites + vendor apt repos** (Ubuntu/Debian only): installs build tools and zsh, then adds vendor apt repos for **Docker**, **HashiCorp** (`terraform-ls`), **eza**, **HTTPie**, and **Trippy** so those tools track upstream releases instead of stale Ubuntu defaults.
2. **Homebrew**: installs non-interactively if missing; otherwise updates.
3. **brew bundle**: installs everything listed in `Brewfile` (the CLI tools that don't have vendor apt repos).
4. **Standalone tools**: installs `mise` and `uv` via official installers, `marksman` (Markdown LSP) from GitHub releases, and `pyright` via `uv tool install`.
5. **Symlinks** all configs into place (backing up existing real files to `<file>.bak`):
   - `zsh/.zshrc`, `zsh/.zimrc`, `zsh/.zshenv` → `~/.zshrc` etc.
   - `vscode/settings.json`, `vscode/keybindings.json` → `~/.config/Code/User/`
   - Everything under `claude_code/` (except READMEs) → `~/.claude/`
6. **nvm + Node**: installs nvm if missing, then installs the Node version from `.nvmrc` (`lts/*`).
7. **npm global tools**: `typescript-language-server`, `bash-language-server` (Claude Code LSP plugins), plus `@fission-ai/openspec` for spec-driven workflows.
8. **VS Code extensions**: runs `vscode/scripts/install-extensions.sh` if `code` is on PATH; otherwise prints a skip note.
9. **Default shell**: sets zsh via `chsh`. If `chsh` fails (common in some WSL setups), prints clear manual fallback instructions instead of aborting.

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

### CLI Tools

Tools split between Homebrew (no vendor apt repo) and vendor apt repos (fresh upstream releases via APT). See [Brewfile](Brewfile) for the brew set; [install.sh](install.sh) section 1 for the apt repos.

| Tool | Source | Description |
|------|--------|-------------|
| [bat](https://github.com/sharkdp/bat) | brew | `cat` with syntax highlighting |
| [dust](https://github.com/bootandy/dust) | brew | Intuitive disk usage viewer |
| [eza](https://github.com/eza-community/eza) | apt (deb.gierens.de) | Modern `ls` replacement |
| [fd](https://github.com/sharkdp/fd) | brew | Fast `find` alternative |
| [fzf](https://github.com/junegunn/fzf) | brew | Fuzzy finder |
| [gping](https://github.com/orf/gping) | brew | Graphical ping |
| [htop](https://htop.dev/) | brew | Interactive process viewer |
| [httpie](https://httpie.io/) | apt (packages.httpie.io) | Human-friendly HTTP client |
| [jq](https://jqlang.github.io/jq/) | brew | JSON processor |
| [mise](https://mise.jdx.dev/) | upstream installer | Polyglot runtime manager |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | brew | Fast recursive search |
| [tldr](https://tldr.sh/) | brew | Simplified man pages |
| [trippy](https://trippy.cli.rs/) | apt (PPA: fujiapple/trippy) | Network diagnostic tool |
| [uv](https://docs.astral.sh/uv/) | upstream installer | Fast Python package manager |
| [yq](https://github.com/mikefarah/yq) | brew | YAML processor |
| [Docker](https://docs.docker.com/) | apt (download.docker.com) | Container runtime |
| [terraform-ls](https://github.com/hashicorp/terraform-ls) | apt (HashiCorp) | Terraform language server (LSP) |

**Language servers** (for Claude Code's native LSP — `pyright-lsp` and `typescript-lsp` plugins are pre-enabled in `claude_code/settings.json`): `pyright` via `uv tool`; `typescript-language-server`, `bash-language-server` via `npm -g`; `marksman` from GitHub releases; `terraform-ls` from the HashiCorp apt repo.

**AI dev tools**: `@fission-ai/openspec` (npm) for spec-driven workflows.

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
