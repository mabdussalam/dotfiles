#!/usr/bin/env bash
# Reads extensions.txt and installs each one

show_usage() {
    echo "Usage: $0 [code|antigravity] [-h|--help]"
    echo ""
    echo "Installs VS Code extensions listed in extensions.txt."
    echo ""
    echo "Arguments:"
    echo "  code|antigravity   The editor executable to use (default: code)"
    echo "  -h, --help         Show this help message"
}

EDITOR="code"

for arg in "$@"; do
    case $arg in
        code|antigravity)
            EDITOR="$arg"
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            show_usage
            exit 1
            ;;
    esac
done

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EXT_FILE="$DIR/../extensions.txt"

if [ -f "$EXT_FILE" ]; then
    while IFS= read -r ext || [ -n "$ext" ]; do
        if [ -n "$ext" ]; then
            echo "Installing $ext with $EDITOR..."
            $EDITOR --install-extension "$ext"
        fi
    done < "$EXT_FILE"
    echo "All extensions processed!"
else
    echo "extensions.txt not found!"
fi
