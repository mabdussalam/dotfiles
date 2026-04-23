# Zsh Configuration

This directory contains my Zsh shell configuration, designed to be fast, modular, and easy to maintain.

## Overview

The setup relies on [Antidote](https://getantidote.github.io/) as the plugin manager and uses [Zephyr](https://github.com/mattmc3/zephyr) for sensible Zsh defaults. The prompt is powered by [Powerlevel10k](https://github.com/romkatv/powerlevel10k).

### Files

- **`.zshrc`**: The main configuration file. It loads Antidote, applies custom overrides, defines tools and aliases (like `eza` and `batcat`), and exports necessary environment variables (like `PATH` for Python/Node).
- **`.zsh_plugins.txt`**: A declarative list of all Zsh plugins managed by Antidote.
- **`.zshenv`**: Environment configuration loaded for all shell sessions. Currently used to skip global `compinit` on Debian/Ubuntu systems for significantly faster startup times.

## Plugins Used

- **romkatv/powerlevel10k**: Extremely fast, highly customizable prompt theme.
- **mattmc3/zephyr**: Modular framework that provides robust defaults for directories, history, the editor, homebrew, and completions without cluttering the `.zshrc`.
- **zsh-users/zsh-completions**: Additional completion definitions.
- **zsh-users/zsh-autosuggestions**: Fish-like fast/unobtrusive autosuggestions based on command history.
- **zdharma-continuum/fast-syntax-highlighting**: Feature-rich, fast syntax highlighting.
- **zsh-users/zsh-history-substring-search**: Fish-like history search (type part of a command and use the Up/Down arrows to search).

## Prerequisites

Before starting, ensure you have the following installed:
- **Zsh**
- **Homebrew**

## Setup Instructions

1. **Set Zsh as default shell**:
   ```bash
   chsh -s $(which zsh)
   ```

2. **Install Dependencies**:
   Antidote and other CLI tools are managed via Homebrew. Install them using the `Brewfile` located in the root of the dotfiles:
   ```bash
   brew bundle --file=/path/to/dotfiles/Brewfile
   ```

3. **Symlink the dotfiles** to your home directory:
   ```bash
   ln -sf /path/to/dotfiles/zsh/.zshrc ~/.zshrc
   ln -sf /path/to/dotfiles/zsh/.zsh_plugins.txt ~/.zsh_plugins.txt
   ln -sf /path/to/dotfiles/zsh/.zshenv ~/.zshenv
   ```

4. **Start Zsh**:
   ```bash
   exec zsh
   ```
   *Antidote will automatically install all missing plugins from `.zsh_plugins.txt` on the first run.*
