# Zsh Configuration

This directory contains my Zsh shell configuration, designed to be fast, modular, and easy to maintain.

## Overview

The setup uses [Zim](https://zimfw.sh/) as the plugin manager. Zim is bootstrapped inline from `.zshrc` (no Homebrew dependency) and pre-compiles every module into a single `init.zsh` for fast shell startup. The prompt is [Powerlevel10k](https://github.com/romkatv/powerlevel10k) with instant prompt enabled.

### Files

- **`.zshrc`** — main interactive-shell config. Bootstraps Zim, sets shell options, aliases, keybindings, and tool integrations (NVM, uv, Python `PATH`).
- **`.zimrc`** — declarative list of Zim modules. Editing it and starting a new shell automatically installs/removes modules and rebuilds `init.zsh`.
- **`.zshenv`** — loaded for every shell. Sets `skip_global_compinit=1` so Debian/Ubuntu's pre-emptive `compinit` doesn't fight Zim's `completion` module.

## Modules Used

All modules are installed via [degit](https://zimfw.sh/docs/install/#degit) (set globally with `zstyle ':zim:zmodule' use 'degit'` at the top of `.zimrc`), which fetches a tarball of the latest release instead of doing a full `git clone` — faster, and no `.git` directory left behind.

- **`environment`, `input`, `termtitle`, `utility`** — Zim's built-in baseline (history options, keybindings, terminal title, colored `ls`/`grep`/`less`).
- **`git`** — git aliases and helpers.
- **`zimfw/fzf`** — wires up fzf's shell integration (CTRL-R history search, CTRL-T file finder, ALT-C cd) and completion using the Homebrew-installed `fzf` binary.
- **`romkatv/powerlevel10k`** — prompt theme. Keeps an explicit `--use degit` flag in `.zimrc` as a belt-and-braces marker, even though degit is the global default.
- **`zsh-users/zsh-completions`** — extra completion definitions, registered into `fpath` before `compinit`.
- **`completion`** — Zim's `compinit` runner; must come after any module that adds to `fpath`.
- **`zdharma-continuum/fast-syntax-highlighting`** — syntax highlighting.
- **`zsh-users/zsh-history-substring-search`** — Fish-style history search bound to up/down arrows.
- **`zsh-users/zsh-autosuggestions`** — Fish-style autosuggestions from history.

The last three must remain in that order (highlighting → substring-search → autosuggestions) — see comments in `.zimrc`.

## Prerequisites

- **Zsh**
- **git** and **curl** (for Zim to self-install)
- **Homebrew** (for the CLI tools in `Brewfile`)

## Setup

1. **Set Zsh as default shell**:
   ```bash
   chsh -s $(which zsh)
   ```

2. **Install CLI tools** via Homebrew:
   ```bash
   brew bundle --file=/path/to/dotfiles/Brewfile
   ```

3. **Symlink the dotfiles** to `$HOME`:
   ```bash
   ln -sf /path/to/dotfiles/zsh/.zshrc        ~/.zshrc
   ln -sf /path/to/dotfiles/zsh/.zimrc        ~/.zimrc
   ln -sf /path/to/dotfiles/zsh/.zshenv       ~/.zshenv
   ```

4. **Start Zsh**:
   ```bash
   exec zsh
   ```
   On first run, `.zshrc` downloads `zimfw.zsh` and installs every module declared in `.zimrc`.

## Day-to-day Zim commands

| Command | When to use |
|---|---|
| `zimfw update` | Pull latest module versions (run periodically). |
| `zimfw upgrade` | Upgrade Zim itself. |
| `zimfw build` | Rebuild `init.zsh` after editing module files directly. |
| `zimfw compile` | Re-`zcompile` everything for max startup speed. |
| `zimfw info` | Dump environment info for bug reports. |

After editing `.zimrc`, just open a new shell — Zim detects that `.zimrc` is newer than `init.zsh` and rebuilds automatically. Use `exec zsh` to reload, never `source ~/.zshrc` (that re-runs `compinit` and causes warnings).
