unset LD_PRELOAD
case $- in
    *i*) ;;
    *) return ;;
esac

__cyber_print_hud_rail() {
    local ec=$?
    local cols=$(( ${COLUMNS:-$(tput cols 2>/dev/null || echo 80)} - 1 ))
    [ "$cols" -lt 44 ] && cols=44

    local dir="${PWD/#$HOME/\~}"
    [ "${#dir}" -gt 32 ] && dir="…${dir: -31}"

    local git_b=""
    if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
        git_b=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
    fi

    local t_now
    t_now=$(date +%H:%M)
    local st_plain="OK"
    [ "$ec" -ne 0 ] && st_plain="ERR:$ec"

    local left_plain="╭─◈ [STUDIO ∷ ${USER}]─[${dir}]"
    [ -n "$git_b" ] && left_plain="${left_plain}─[⎇ ${git_b}]"
    local right_plain="[${st_plain} • ${t_now}]─╮"

    local fill_len=$(( cols - ${#left_plain} - ${#right_plain} ))
    [ "$fill_len" -lt 2 ] && fill_len=2

    local C_MID="\e[38;2;92;98;109m"
    local C_DIM="\e[38;2;58;63;71m"
    local C_SIL="\e[1;38;2;158;164;176m"
    local C_TXT="\e[1;38;2;212;216;222m"
    local C_RST="\e[0m"

    local middle=""
    printf -v middle '%*s' "$fill_len" ''; middle="${C_DIM}${middle// /─}"

    local git_col=""
    [ -n "$git_b" ] && git_col="${C_MID}─[${C_SIL}⎇ ${git_b}${C_MID}]"

    printf "\n${C_MID}╭─${C_SIL}◈${C_MID} [${C_SIL}STUDIO${C_MID} ∷ ${C_TXT}${USER}${C_MID}]─[${C_SIL}${dir}${C_MID}]${git_col}${middle}${C_MID}[${C_SIL}${st_plain}${C_MID} • ${C_TXT}${t_now}${C_MID}]─╮${C_RST}\n"
    return "$ec"
}

if [ -n "${BASH_VERSION:-}" ]; then
    __cyber_prompt_cmd() {
        local ec=$?
        (exit "$ec")
        __cyber_print_hud_rail
        PS1="\[\e[38;2;92;98;109m\]╰─\[\e[1;38;2;158;164;176m\]◈ ⟫\[\e[0m\] "
    }
    PROMPT_COMMAND="__cyber_prompt_cmd"
elif [ -n "${ZSH_VERSION:-}" ]; then
    precmd() { __cyber_print_hud_rail; }
    setopt PROMPT_SUBST
    PROMPT='%F{#5c626d}╰─%B%F{#9ea4b0}◈ ⟫%b%f '
fi

if [ -z "${CYBER_BANNER_SHOWN:-}" ] && [ "${SHLVL:-1}" -le 2 ]; then
    export CYBER_BANNER_SHOWN=1
    if command -v fastfetch >/dev/null 2>&1 && [ "$(tput cols 2>/dev/null || echo 80)" -ge 72 ]; then
        fastfetch
    fi
fi
