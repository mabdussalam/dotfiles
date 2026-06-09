# Shared helpers for install/* modules.
# Sourced (not executed) by every install/[0-9]*-*.sh.

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LISTS="$REPO/install/lists"

# --- logging ---------------------------------------------------------------
log()  { printf '   %s\n' "$*"; }
warn() { printf '   WARN: %s\n' "$*" >&2; }
die()  { printf '   ERROR: %s\n' "$*" >&2; exit 1; }

# --- platform probes -------------------------------------------------------
is_debian()       { command -v apt-get &>/dev/null; }
ubuntu_codename() { ( . /etc/os-release && printf '%s' "${VERSION_CODENAME:-}" ); }
deb_arch()        { dpkg --print-architecture; }

# --- apt repo helpers ------------------------------------------------------
ensure_keyring_dir() { sudo install -m 0755 -d /etc/apt/keyrings; }

# add_apt_repo NAME KEY_URL LIST_LINE — idempotent (skip if keyring already
# exists AND is non-empty; a zero-byte file from a previously aborted run is
# rewritten). Writes the keyring atomically via a .tmp file + mv.
add_apt_repo() {
    local name="$1" key_url="$2" list_line="$3"
    local key="/etc/apt/keyrings/$name.gpg"
    if [[ -s "$key" ]]; then
        return 0
    fi
    ensure_keyring_dir
    curl -fsSL "$key_url" | sudo gpg --dearmor -o "$key.tmp"
    sudo chmod a+r "$key.tmp"
    sudo mv "$key.tmp" "$key"
    printf '%s\n' "$list_line" | sudo tee "/etc/apt/sources.list.d/$name.list" > /dev/null
}

# --- homebrew --------------------------------------------------------------
# load_brew_shellenv — set PATH so `brew` works in the current subshell.
# Mirrors install.sh's original brew-discovery block: macOS arm64 / x86_64,
# else Linuxbrew. No-op if none are present (callers should have installed
# brew first, otherwise downstream calls will fail loudly).
load_brew_shellenv() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ "$(uname -m)" == "arm64" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    elif [[ -x "/home/linuxbrew/.linuxbrew/bin/brew" ]]; then
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    fi
}

# --- file copy -------------------------------------------------------------
# _copy SRC DST — copy SRC → DST with bootstrap semantics.
# If DST exists, skip (preserve local edits). With FORCE=1, back DST up to
# <DST>.bak and overwrite. Legacy symlinks from the previous symlink-based
# installer are removed before copying. Creates DST's parent dir if needed.
_copy() {
    local src="$1"
    local dst="$2"
    local dst_dir
    dst_dir="$(dirname "$dst")"
    mkdir -p "$dst_dir"

    if [[ -L "$dst" ]]; then
        log "[migrate] removing symlink $dst"
        rm "$dst"
    fi

    if [[ -e "$dst" ]]; then
        if [[ "${FORCE:-0}" == "1" ]]; then
            log "[backup] $dst → ${dst}.bak"
            rm -rf "${dst}.bak"
            mv "$dst" "${dst}.bak"
        else
            log "[skip] $dst exists (FORCE=1 to overwrite)"
            return
        fi
    fi

    if [[ -d "$src" ]]; then
        cp -R "$src" "$dst"
    else
        cp "$src" "$dst"
    fi
    log "[copied] $src → $dst"
}

# --- list files ------------------------------------------------------------
# read_list NAME — print non-comment, non-blank items from lists/NAME.txt.
# Strips inline "# comment" tails and surrounding whitespace.
read_list() {
    local file="$LISTS/$1.txt"
    [[ -f "$file" ]] || die "list not found: $file"
    # Drop comments and blank lines; strip inline comments; trim whitespace.
    sed -e 's/#.*$//' -e 's/^[[:space:]]\+//' -e 's/[[:space:]]\+$//' "$file" \
        | grep -vE '^$'
}
