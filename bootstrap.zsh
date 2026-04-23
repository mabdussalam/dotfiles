#!/usr/bin/env zsh

echo "=> Starting bootstrap process..."

# 1. Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "=> Homebrew not found. Installing Homebrew..."
    # The NONINTERACTIVE=1 flag prevents the installer from pausing for user input
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Configure Homebrew in the current shell session so the subsequent 'brew' commands work
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ "$(uname -m)" == "arm64" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    else
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    fi
else
    echo "=> Homebrew is already installed. Updating..."
    brew update
fi

# 2. Get the directory of this script to locate the Brewfile
DOTFILES_DIR=$(cd "$(dirname "$0")" && pwd)
BREWFILE="$DOTFILES_DIR/Brewfile"

# 3. Install packages using Brewfile
if [[ -f "$BREWFILE" ]]; then
    echo "=> Installing dependencies from Brewfile..."
    brew bundle --file="$BREWFILE"
else
    echo "=> Error: Brewfile not found at $BREWFILE"
    exit 1
fi

echo "=> Bootstrap complete!"
