#!/usr/bin/env bash
# Saves the list of currently installed extensions alphabetically and with UTF-8 encoding

show_usage() {
    echo "Usage: $0 [code|antigravity] [--overwrite|-o] [-h|--help]"
    echo ""
    echo "Saves currently installed extensions to extensions.txt."
    echo "By default, merges with the existing list."
    echo ""
    echo "Arguments:"
    echo "  code|antigravity   The editor executable to use (default: code)"
    echo "  -o, --overwrite    Overwrite extensions.txt instead of merging"
    echo "  -h, --help         Show this help message"
}

EDITOR="code"
OVERWRITE=0

for arg in "$@"; do
    case $arg in
        code|antigravity)
            EDITOR="$arg"
            ;;
        --overwrite|-o)
            OVERWRITE=1
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

if [ $OVERWRITE -eq 0 ] && [ -f "$EXT_FILE" ]; then
    # Merge existing and new
    { cat "$EXT_FILE"; $EDITOR --list-extensions; } | grep -v '^\s*$' | sort -u > "$EXT_FILE.tmp"
    mv "$EXT_FILE.tmp" "$EXT_FILE"
else
    # Overwrite
    $EDITOR --list-extensions | grep -v '^\s*$' | sort -u > "$EXT_FILE"
fi

echo "Extensions successfully saved to extensions.txt!"
