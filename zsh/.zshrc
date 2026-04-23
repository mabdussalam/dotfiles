# ~/.zshrc

# Homebrew =====================================================================
# Add Homebrew to PATH
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"


# Antidote =====================================================================
source $(brew --prefix)/opt/antidote/share/antidote/antidote.zsh
antidote load


# ZSH Overrides & Additions ====================================================
# Directory
setopt AUTO_CD
setopt CD_SILENT
setopt PUSHD_IGNORE_DUPS

# Miscellaneous
setopt INTERACTIVE_COMMENTS
WORDCHARS=${WORDCHARS//[\/]}
ZSH_AUTOSUGGEST_MANUAL_REBIND=1
ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# Key bindings (zsh-history-substring-search)
bindkey "^[[A" history-substring-search-up
bindkey "^[[B" history-substring-search-down
# Only bind terminfo keys if they exist
[[ -n "$terminfo[kcuu1]" ]] && bindkey "$terminfo[kcuu1]" history-substring-search-up
[[ -n "$terminfo[kcud1]" ]] && bindkey "$terminfo[kcud1]" history-substring-search-down


# Tools ========================================================================
alias ls='eza --color=auto --group-directories-first'
alias l='ls -al'
alias ll='ls -l'
alias la='ls -a'
alias cl='clear'
alias cll='clear && exec zsh'
alias cat='bat'


# Python =======================================================================
export PATH="${HOME}/.local/bin:${PATH}"  # pip packages binaries are installed here
typeset -U PATH


# NVM ==========================================================================
export NVM_DIR="${HOME}/.nvm"
[ -s "${NVM_DIR}/nvm.sh" ] && \. "${NVM_DIR}/nvm.sh"


# uv ===========================================================================
eval "$(uv generate-shell-completion zsh)" || true
eval "$(uvx --generate-shell-completion zsh)" || true


# p10k theme ===================================================================
[[ ! -f ${HOME}/.p10k.zsh ]] || source ${HOME}/.p10k.zsh
