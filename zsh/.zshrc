# ~/.zshrc

# Homebrew =====================================================================
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"


# Zim ==========================================================================
ZIM_HOME=${ZDOTDIR:-${HOME}}/.zim

# Download zimfw plugin manager if missing.
if [[ ! -e ${ZIM_HOME}/zimfw.zsh ]]; then
  curl -fsSL --create-dirs -o ${ZIM_HOME}/zimfw.zsh \
      https://github.com/zimfw/zimfw/releases/latest/download/zimfw.zsh
fi
# Install missing modules and update ${ZIM_HOME}/init.zsh if .zimrc is newer.
if [[ ! ${ZIM_HOME}/init.zsh -nt ${ZIM_CONFIG_FILE:-${ZDOTDIR:-${HOME}}/.zimrc} ]]; then
  source ${ZIM_HOME}/zimfw.zsh init
fi
source ${ZIM_HOME}/init.zsh


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

# Key bindings
#   Only bind terminfo keys if they exist
bindkey "^H" backward-kill-word


# Tools ========================================================================
alias ls='eza --color=auto --group-directories-first --icons'
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
