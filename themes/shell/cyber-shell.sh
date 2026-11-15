unset LD_PRELOAD
case $- in
    *i*) ;;
    *) return ;;
esac

__studio_pill_prompt() {
    local ec=$?
    local dir="${PWD/#$HOME/\~}"
    [ "${#dir}" -gt 34 ] && dir="…${dir: -33}"

    local BG_U="\e[48;2;42;46;54m\e[1;38;2;230;233;238m"
    local BG_D="\e[48;2;28;31;36m\e[38;2;190;196;206m"
    local BG_G="\e[48;2;35;38;45m\e[1;38;2;165;172;184m"
    local FG_M="\e[38;2;120;126;136m"
    local RST="\e[0m"

    local git_seg=""
    if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
        local br
        br=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
        if [ -n "$br" ]; then
            local dirty=""
            [ -n "$(git status --porcelain 2>/dev/null | head -n1)" ] && dirty=" •"
            git_seg=" ${BG_G} ⎇ ${br}${dirty} ${RST}"
        fi
    fi

    local venv_seg=""
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        venv_seg=" ${BG_G} py:$(basename "$VIRTUAL_ENV") ${RST}"
    fi

    local st_seg=""
    if [ "$ec" -ne 0 ]; then
        st_seg=" \e[48;2;68;38;42m\e[1;38;2;235;190;190m ✗ ${ec} ${RST}"
    fi

    printf "\n${BG_U} ▣ ${USER} ${RST}${BG_D}  ${dir}  ${RST}${git_seg}${venv_seg}${st_seg} ${FG_M}$(date +%H:%M)${RST}\n"
    return "$ec"
}

if [ -n "${BASH_VERSION:-}" ]; then
    __studio_bash_hook() {
        local ec=$?
        (exit "$ec")
        __studio_pill_prompt
        PS1="\[\e[1;38;2;165;172;184m\] ❯ \[\e[0m\]"
    }
    PROMPT_COMMAND="__studio_bash_hook"
elif [ -n "${ZSH_VERSION:-}" ]; then
    precmd() { __studio_pill_prompt; }
    setopt PROMPT_SUBST
    PROMPT='%B%F{#a5acb8} ❯ %f%b'
fi

if [ -z "${CYBER_BANNER_SHOWN:-}" ] && [ "${SHLVL:-1}" -le 2 ]; then
    export CYBER_BANNER_SHOWN=1
    if command -v fastfetch >/dev/null 2>&1 && [ "$(tput cols 2>/dev/null || echo 80)" -ge 68 ]; then
        fastfetch
    fi
fi
