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

`install.sh` is a thin orchestrator that runs every module under `install/[0-9]*.sh` in numeric order. Each module is **standalone-runnable** and **idempotent** — to run a single phase, invoke the file directly (e.g. `./install/10-docker.sh`).

| # | Module | What it does |
|---|--------|--------------|
| 00 | `00-apt-base.sh` | Base APT packages — build toolchain, zsh, and vendor-apt prereqs (Debian/Ubuntu only). Package list: `install/lists/apt-base.txt`. |
| 10 | `10-docker.sh` | Adds `download.docker.com` apt repo and installs Docker CE + Compose plugin; adds user to `docker` group. |
| 20 | `20-hashicorp.sh` | Adds `apt.releases.hashicorp.com` apt repo and installs `terraform-ls`. |
| 21 | `21-eza.sh` | Adds `deb.gierens.de` apt repo and installs `eza`. |
| 22 | `22-httpie.sh` | Adds `packages.httpie.io` apt repo and installs `httpie`. |
| 23 | `23-trippy.sh` | Adds the `ppa:fujiapple/trippy` PPA and installs `trippy`. |
| 30 | `30-homebrew.sh` | Installs Homebrew non-interactively if missing (else `brew update`), then runs `brew bundle` against the repo `Brewfile`. |
| 40 | `40-mise.sh` | Installs `mise` (runtime version manager) via the upstream installer. |
| 41 | `41-uv.sh` | Installs `uv` (Python package manager) via the upstream installer. |
| 42 | `42-marksman.sh` | Drops the `marksman` Markdown LSP binary into `~/.local/bin`. |
| 50 | `50-uv-tools.sh` | `uv tool install` for everything in `install/lists/uv-tools.txt` (`pyright`, `ruff`). |
| 60 | `60-copy-configs.sh` | Copies `zsh/*`, `vscode/{settings,keybindings}.json`, and everything under `claude_code/` (except READMEs) into `~/`. Skips any target that already exists so local tweaks survive re-runs; set `FORCE=1` to overwrite (existing target is moved to a timestamped backup dir under `~/.dotfiles-backups/` first). |
| 70 | `70-node.sh` | Installs `nvm` if missing, then installs the Node version from `.nvmrc` (`lts/*`) and aliases it as default. |
| 80 | `80-npm-globals.sh` | `npm install -g` for everything in `install/lists/npm-globals.txt` (TypeScript, `typescript-language-server`, OpenSpec). |
| 90 | `90-vscode.sh` | Delegates to `vscode/scripts/install-extensions.sh` if `code` is on PATH; otherwise prints a skip note. |
| 99 | `99-shell.sh` | Sets zsh as the default shell via `chsh`. If `chsh` fails (common in some WSL setups), prints clear manual fallback instructions instead of aborting. |

Shared helpers (logging, apt-repo registration, list parsing, brew shellenv) live in `install/_lib.sh` and are sourced by every module.

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

Tools split between Homebrew (no vendor apt repo) and vendor apt repos (fresh upstream releases via APT). See [Brewfile](Brewfile) for the brew set; the `install/[12]?-*.sh` modules for the vendor apt repos.

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

**Language servers** (for Claude Code's native LSP — `pyright-lsp` and `typescript-lsp` plugins are pre-enabled in `claude_code/settings.json`): `pyright` via `uv tool`; `typescript-language-server` via `npm -g`. `marksman` (Markdown) and `terraform-ls` are also on PATH for future plugin pairings.

**AI dev tools**: `@fission-ai/openspec` (npm) for spec-driven workflows.

> **WSL note**: `iputils` is installed with `link: false` so it doesn't override the system `ping`.

### [Zsh](zsh/)

Shell configuration using Zim for plugin management, Powerlevel10k for the prompt, and Zim's built-in modules (environment, input, termtitle, utility) for sensible defaults. See the [Zsh README](zsh/README.md) for details.

### [VS Code](vscode/)

Editor settings, keybindings, and a managed extensions list with install/save scripts. See the [VS Code README](vscode/README.md) for details.

## Advanced / Manual Setup

`install.sh` **copies** configs into place as a one-time bootstrap. If you'd rather treat this repo as your live config — edit once, `git diff` shows real drift — symlink the files yourself instead:

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
