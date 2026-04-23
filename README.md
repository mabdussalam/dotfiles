# Dotfiles

Personal configuration files for macOS and Linux environments.

## Structure

```
dotfiles/
├── Brewfile          # Homebrew dependencies
├── bootstrap.zsh     # One-command setup script
├── vscode/           # VS Code settings, keybindings, and extensions
└── zsh/              # Zsh shell configuration and plugins
```

## Quick Start

```bash
git clone <repo-url> ~/dotfiles
cd ~/dotfiles
chmod +x bootstrap.zsh
./bootstrap.zsh
```

The bootstrap script will:

1. Install [Homebrew](https://brew.sh/) if it isn't already installed
2. Install all CLI tools listed in the `Brewfile`

After bootstrapping, follow the setup instructions in each module's README to symlink the configuration files:

- [Zsh Setup](zsh/README.md)
- [VS Code Setup](vscode/README.md)

## What's Included

### CLI Tools ([Brewfile](Brewfile))

| Tool | Description |
|------|-------------|
| [antidote](https://getantidote.github.io/) | Fast Zsh plugin manager |
| [bat](https://github.com/sharkdp/bat) | `cat` with syntax highlighting |
| [dust](https://github.com/bootandy/dust) | Intuitive disk usage viewer |
| [eza](https://github.com/eza-community/eza) | Modern replacement for `ls` |
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

### [Zsh](zsh/)

Shell configuration using Antidote for plugin management, Powerlevel10k for the prompt, and Zephyr for sensible defaults. See the [Zsh README](zsh/README.md) for details.

### [VS Code](vscode/)

Editor settings, keybindings, and a managed extensions list with install/save scripts. See the [VS Code README](vscode/README.md) for details.
