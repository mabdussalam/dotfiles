#!/usr/bin/env bash
# Full one-command setup for a fresh Ubuntu/Kubuntu machine (native or WSL).
# See README.md for usage. bootstrap.zsh is a brew-only convenience wrapper.
set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve repo root regardless of CWD
# ---------------------------------------------------------------------------
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "======================================================================"
echo "  Dotfiles installer — repo: $REPO"
echo "======================================================================"
echo ""

# ---------------------------------------------------------------------------
# 1. APT prerequisites (Debian/Ubuntu only)
# ---------------------------------------------------------------------------
if command -v apt-get &>/dev/null; then
    echo "=> [1/7] Installing APT prerequisites (build-essential, curl, git, zsh …)"
    sudo apt-get update -qq
    sudo apt-get install -y build-essential procps curl file git zsh
    echo "   APT prerequisites installed."
else
    echo "=> [1/7] apt-get not found — skipping APT prerequisites (non-Debian system)."
fi

# ---------------------------------------------------------------------------
# 2. Homebrew
# ---------------------------------------------------------------------------
echo ""
echo "=> [2/7] Setting up Homebrew…"

if ! command -v brew &>/dev/null; then
    echo "   Homebrew not found. Installing non-interactively…"
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "   Homebrew already installed. Updating…"
    brew update
fi

# Make brew available in this shell session
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ "$(uname -m)" == "arm64" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi
elif [[ -x "/home/linuxbrew/.linuxbrew/bin/brew" ]]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi

echo "   Homebrew ready: $(brew --version | head -1)"

# ---------------------------------------------------------------------------
# 3. brew bundle
# ---------------------------------------------------------------------------
echo ""
echo "=> [3/7] Running brew bundle…"
brew bundle --file="$REPO/Brewfile"
echo "   brew bundle complete."

# ---------------------------------------------------------------------------
# 4. Symlink configs
# ---------------------------------------------------------------------------
echo ""
echo "=> [4/7] Symlinking configs…"

# Helper: symlink $1 → $2, backing up an existing real file
_link() {
    local src="$1"
    local dst="$2"
    local dst_dir
    dst_dir="$(dirname "$dst")"

    mkdir -p "$dst_dir"

    # If dst already points to src exactly, nothing to do
    if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
        echo "   [skip] $dst already linked"
        return
    fi

    # Back up existing real file (not a symlink)
    if [[ -e "$dst" && ! -L "$dst" ]]; then
        echo "   [backup] $dst → ${dst}.bak"
        mv "$dst" "${dst}.bak"
    fi

    # Remove stale symlink pointing elsewhere
    if [[ -L "$dst" ]]; then
        rm "$dst"
    fi

    ln -sfn "$src" "$dst"
    echo "   [linked] $src → $dst"
}

# Zsh configs
_link "$REPO/zsh/.zshrc"  "$HOME/.zshrc"
_link "$REPO/zsh/.zimrc"  "$HOME/.zimrc"
_link "$REPO/zsh/.zshenv" "$HOME/.zshenv"

# VS Code (Linux path; directory is created by _link helper)
VSCODE_USER_DIR="$HOME/.config/Code/User"
_link "$REPO/vscode/settings.json"    "$VSCODE_USER_DIR/settings.json"
_link "$REPO/vscode/keybindings.json" "$VSCODE_USER_DIR/keybindings.json"

# Claude Code — link every file/dir present under claude_code/, skip README files
CLAUDE_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_DIR"
for item in "$REPO/claude_code/"*; do
    basename_item="$(basename "$item")"
    # Skip README files (any capitalisation)
    if [[ "${basename_item,,}" == readme* ]]; then
        echo "   [skip] claude_code/$basename_item (README)"
        continue
    fi
    _link "$item" "$CLAUDE_DIR/$basename_item"
done

echo "   Config symlinking complete."

# ---------------------------------------------------------------------------
# 5. nvm + Node
# ---------------------------------------------------------------------------
echo ""
echo "=> [5/7] Setting up nvm and Node…"

NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
    echo "   nvm not found. Installing latest nvm…"
    # Fetch the latest release tag and install
    NVM_INSTALL_URL="https://raw.githubusercontent.com/nvm-sh/nvm/HEAD/install.sh"
    curl -fsSL "$NVM_INSTALL_URL" | PROFILE=/dev/null bash
    echo "   nvm installed."
else
    echo "   nvm already installed."
fi

# Load nvm into this session (without modifying shell profile again).
# nvm.sh references unset vars and returns non-zero internally, so relax
# errexit/nounset/pipefail while sourcing and running it, then restore.
export NVM_DIR="$HOME/.nvm"
set +euo pipefail
# shellcheck source=/dev/null
\. "$NVM_DIR/nvm.sh"

echo "   nvm version: $(nvm --version)"

# Install Node version specified by .nvmrc (lts/*)
echo "   Installing Node from .nvmrc…"
nvm install
nvm alias default 'lts/*'
set -euo pipefail
echo "   Node ready: $(node --version), npm: $(npm --version)"

# ---------------------------------------------------------------------------
# 6. VS Code extensions
# ---------------------------------------------------------------------------
echo ""
echo "=> [6/7] VS Code extensions…"

if command -v code &>/dev/null; then
    bash "$REPO/vscode/scripts/install-extensions.sh"
else
    echo "   'code' CLI not on PATH — skipping extension install."
    echo "   Run '$REPO/vscode/scripts/install-extensions.sh' manually after VS Code is installed."
fi

# ---------------------------------------------------------------------------
# 7. Default shell → zsh
# ---------------------------------------------------------------------------
echo ""
echo "=> [7/7] Setting default shell to zsh…"

ZSH_PATH="$(command -v zsh)"

if [[ "$SHELL" == "$ZSH_PATH" ]]; then
    echo "   Default shell is already zsh ($ZSH_PATH). Nothing to do."
else
    # Ensure zsh is in /etc/shells
    if ! grep -qF "$ZSH_PATH" /etc/shells 2>/dev/null; then
        echo "   Adding $ZSH_PATH to /etc/shells…"
        echo "$ZSH_PATH" | sudo tee -a /etc/shells >/dev/null
    fi

    echo "   Running: chsh -s $ZSH_PATH"
    if chsh -s "$ZSH_PATH" 2>/dev/null; then
        echo "   Default shell changed to zsh. Re-login or open a new terminal for it to take effect."
    else
        echo ""
        echo "   WARNING: chsh failed (common in some WSL setups or containers)."
        echo "   To switch to zsh manually, add the following to the end of your ~/.bashrc:"
        echo ""
        echo "       export SHELL=$(command -v zsh)"
        echo "       exec \$(command -v zsh) -l"
        echo ""
    fi
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  Installation complete!"
echo "======================================================================"
echo ""
echo "  Next steps:"
echo "   1. Open a NEW terminal (or run 'exec zsh') — Zim will bootstrap"
echo "      itself and install plugins on first launch."
echo "   2. If you use Powerlevel10k, run 'p10k configure' to set up the"
echo "      prompt, or copy your existing ~/.p10k.zsh into place."
echo "   3. If VS Code extensions were skipped, run:"
echo "      $REPO/vscode/scripts/install-extensions.sh"
echo ""
