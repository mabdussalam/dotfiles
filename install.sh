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
    echo "=> [1/9] Installing APT prerequisites (build-essential, curl, git, zsh …)"
    sudo apt-get update -qq
    sudo apt-get install -y \
        build-essential procps curl wget file git zsh \
        ca-certificates gnupg lsb-release software-properties-common
    echo "   APT prerequisites installed."

    sudo install -m 0755 -d /etc/apt/keyrings
    UBUNTU_CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"
    DEB_ARCH="$(dpkg --print-architecture)"

    # --- Docker (https://docs.docker.com/engine/install/ubuntu/) ---
    if ! command -v docker &>/dev/null; then
        echo "   Installing Docker from official apt repo…"
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
            | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$DEB_ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $UBUNTU_CODENAME stable" \
            | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    fi

    # --- HashiCorp (terraform, terraform-ls — https://developer.hashicorp.com/terraform/install) ---
    if [[ ! -f /etc/apt/keyrings/hashicorp.gpg ]]; then
        echo "   Adding HashiCorp apt repo (terraform-ls)…"
        curl -fsSL https://apt.releases.hashicorp.com/gpg \
            | sudo gpg --dearmor -o /etc/apt/keyrings/hashicorp.gpg
        sudo chmod a+r /etc/apt/keyrings/hashicorp.gpg
        echo "deb [arch=$DEB_ARCH signed-by=/etc/apt/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $UBUNTU_CODENAME main" \
            | sudo tee /etc/apt/sources.list.d/hashicorp.list > /dev/null
    fi

    # --- eza (https://github.com/eza-community/eza/blob/main/INSTALL.md) ---
    if [[ ! -f /etc/apt/keyrings/gierens.gpg ]]; then
        echo "   Adding eza apt repo…"
        curl -fsSL https://raw.githubusercontent.com/eza-community/eza/main/deb.asc \
            | sudo gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
        sudo chmod a+r /etc/apt/keyrings/gierens.gpg
        echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" \
            | sudo tee /etc/apt/sources.list.d/gierens.list > /dev/null
    fi

    # --- HTTPie (https://httpie.io/docs/cli/debian-and-ubuntu) ---
    if [[ ! -f /etc/apt/keyrings/httpie.gpg ]]; then
        echo "   Adding HTTPie apt repo…"
        curl -fsSL https://packages.httpie.io/deb/KEY.gpg \
            | sudo gpg --dearmor -o /etc/apt/keyrings/httpie.gpg
        sudo chmod a+r /etc/apt/keyrings/httpie.gpg
        echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/httpie.gpg] https://packages.httpie.io/deb ./" \
            | sudo tee /etc/apt/sources.list.d/httpie.list > /dev/null
    fi

    # --- Trippy (https://github.com/fujiapple852/trippy — official PPA) ---
    if [[ ! -f /etc/apt/sources.list.d/fujiapple-ubuntu-trippy-${UBUNTU_CODENAME}.list \
       && ! -f /etc/apt/sources.list.d/fujiapple-ubuntu-trippy.list ]]; then
        echo "   Adding Trippy PPA (fujiapple/trippy)…"
        sudo add-apt-repository -y ppa:fujiapple/trippy
    fi

    # Single update + install everything we just added a repo for
    sudo apt-get update -qq
    sudo apt-get install -y \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin \
        terraform-ls eza httpie trippy

    if ! getent group docker | grep -q "\b$USER\b"; then
        sudo usermod -aG docker "$USER"
        echo "   Added $USER to docker group. Re-login or run 'newgrp docker'."
    fi
    echo "   APT repo packages installed (docker, terraform-ls, eza, httpie, trippy)."
else
    echo "=> [1/9] apt-get not found — skipping APT prerequisites (non-Debian system)."
fi

# ---------------------------------------------------------------------------
# 2. Homebrew
# ---------------------------------------------------------------------------
echo ""
echo "=> [2/9] Setting up Homebrew…"

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
echo "=> [3/9] Running brew bundle…"
brew bundle --file="$REPO/Brewfile"
echo "   brew bundle complete."

# ---------------------------------------------------------------------------
# 4. Standalone tool installers (mise, uv)
#    These tools ship self-update mechanisms that the Homebrew bottles bypass.
#    Official installers are the upstream-preferred path on Linux.
#    Both install to ~/.local/bin, which .zshrc already adds to PATH.
# ---------------------------------------------------------------------------
echo ""
echo "=> [4/9] Installing standalone tools (mise, uv, marksman)…"

# Ensure ~/.local/bin is on PATH for the current session (it's in .zshrc for
# interactive shells, but we need it now while running this script)
export PATH="$HOME/.local/bin:$PATH"

# mise (runtime version manager — https://mise.jdx.dev)
if command -v mise &>/dev/null; then
    echo "   mise already installed: $(mise --version)"
else
    echo "   Installing mise via official installer…"
    curl -fsSL https://mise.run | sh
    echo "   mise installed."
fi

# uv (Python package/project manager — https://astral.sh/uv)
if command -v uv &>/dev/null; then
    echo "   uv already installed: $(uv --version)"
else
    echo "   Installing uv via official installer…"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "   uv installed."
fi

echo "   Run 'mise self-update' / 'uv self update' to update these tools later."

# marksman (Markdown language server — github.com/artempyanykh/marksman)
mkdir -p "$HOME/.local/bin"
if [[ -x "$HOME/.local/bin/marksman" ]]; then
    echo "   marksman already installed."
else
    echo "   Installing marksman (Markdown LSP)…"
    curl -fsSL -o "$HOME/.local/bin/marksman" \
        https://github.com/artempyanykh/marksman/releases/latest/download/marksman-linux-x64
    chmod +x "$HOME/.local/bin/marksman"
    echo "   marksman installed."
fi

# Python tools via 'uv tool install' (each gets its own isolated venv, on PATH).
#   - pyright: language server (used by the pyright-lsp Claude Code plugin)
UV_TOOLS=(pyright)
for tool in "${UV_TOOLS[@]}"; do
    if uv tool list 2>/dev/null | grep -q "^$tool "; then
        echo "   $tool already installed via uv."
    else
        echo "   Installing $tool via 'uv tool install'…"
        uv tool install "$tool" || echo "   WARN: uv tool install $tool failed (continuing)."
    fi
done

# ---------------------------------------------------------------------------
# 5. Symlink configs
# ---------------------------------------------------------------------------
echo ""
echo "=> [5/9] Symlinking configs…"

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
# 6. nvm + Node
# ---------------------------------------------------------------------------
echo ""
echo "=> [6/9] Setting up nvm and Node…"

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
# 7. npm global tools (LSP servers + OpenSpec)
# ---------------------------------------------------------------------------
echo ""
echo "=> [7/9] Installing npm global tools (LSP servers, OpenSpec)…"

# Language-server binaries — Claude Code's official LSP plugins
# (pyright-lsp, typescript-lsp, etc.) expect these on PATH. pyright is
# installed via uv (above). vtsls would require a custom local plugin; the
# official typescript-lsp plugin uses typescript-language-server.
NPM_GLOBALS=(
    typescript                    # tsc/tsserver (required by typescript-language-server)
    typescript-language-server    # TypeScript/JS LSP (typescript-lsp plugin)
    bash-language-server          # Bash LSP
    "@fission-ai/openspec"        # spec-driven dev workflow
)
for pkg in "${NPM_GLOBALS[@]}"; do
    if npm ls -g --depth=0 "$pkg" &>/dev/null; then
        echo "   $pkg already installed."
    else
        echo "   Installing $pkg…"
        npm install -g "$pkg"
    fi
done

# ---------------------------------------------------------------------------
# 8. VS Code extensions
# ---------------------------------------------------------------------------
echo ""
echo "=> [8/9] VS Code extensions…"

if command -v code &>/dev/null; then
    bash "$REPO/vscode/scripts/install-extensions.sh"
else
    echo "   'code' CLI not on PATH — skipping extension install."
    echo "   Run '$REPO/vscode/scripts/install-extensions.sh' manually after VS Code is installed."
fi

# ---------------------------------------------------------------------------
# 9. Default shell → zsh
# ---------------------------------------------------------------------------
echo ""
echo "=> [9/9] Setting default shell to zsh…"

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
echo "   4. Claude Code LSP plugins (pyright-lsp, typescript-lsp) are pre-enabled"
echo "      in claude_code/settings.json — they activate on next 'claude' launch."
echo "      For other languages, install plugins from the official marketplace:"
echo "        /plugin install <name>@claude-plugins-official"
echo "   5. Per-project bootstrap of OpenSpec (spec-driven workflow):"
echo "        cd your-project && openspec init --tools claude"
echo ""
