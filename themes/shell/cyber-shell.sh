case $- in
    *i*) ;;
    *) return ;;
esac

__cyber_deck_mode() {
    if [[ "${HYPRLAND_CONFIG:-}" == *"gaming"* || "${HYPRLAND_CONFIG:-}" == *"hyprgame"* ]]; then
        printf "GAME"
    else
        printf "WORK"
    fi
}

__cyber_print_hud_rail() {
    local ec=$?
    local cols=$(( ${COLUMNS:-$(tput cols 2>/dev/null || echo 80)} - 1 ))
    [ "$cols" -lt 44 ] && cols=44

    local mode
    mode=$(__cyber_deck_mode)
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

    local left_plain="╭─◈ [CYBER//${mode} ∷ ${USER}]─[${dir}]"
    [ -n "$git_b" ] && left_plain="${left_plain}─[⎇ ${git_b}]"
    local right_plain="[${st_plain} • ${t_now}]─╮"

    local fill_len=$(( cols - ${#left_plain} - ${#right_plain} ))
    [ "$fill_len" -lt 2 ] && fill_len=2

    local C_IND="\e[38;2;76;110;245m"
    local C_DIM="\e[38;2;36;50;82m"
    local C_CYN="\e[1;38;2;34;184;207m"
    local C_TXT="\e[1;38;2;229;236;255m"
    local C_PTH="\e[1;38;2;145;167;255m"
    local C_GRN="\e[1;38;2;99;230;190m"
    local C_RED="\e[1;38;2;255;107;107m"
    local C_RST="\e[0m"

    local middle=""
    if [ "$fill_len" -ge 12 ]; then
        local l_pad=$(( (fill_len - 8) / 2 ))
        local r_pad=$(( fill_len - 8 - l_pad ))
        local seg_l seg_r
        printf -v seg_l '%*s' "$l_pad" ''; seg_l="${seg_l// /─}"
        printf -v seg_r '%*s' "$r_pad" ''; seg_r="${seg_r// /─}"
        middle="${C_DIM}${seg_l}${C_CYN} ////// ${C_DIM}${seg_r}"
    else
        printf -v middle '%*s' "$fill_len" ''; middle="${C_DIM}${middle// /─}"
    fi

    local git_col=""
    [ -n "$git_b" ] && git_col="${C_IND}─[${C_GRN}⎇ ${git_b}${C_IND}]"

    local st_col="${C_GRN}OK"
    [ "$ec" -ne 0 ] && st_col="${C_RED}ERR:${ec}"

    printf "\n${C_IND}╭─${C_CYN}◈${C_IND} [${C_CYN}CYBER//${mode}${C_IND} ∷ ${C_TXT}${USER}${C_IND}]─[${C_PTH}${dir}${C_IND}]${git_col}${middle}${C_IND}[${st_col}${C_IND} • ${C_TXT}${t_now}${C_IND}]─╮${C_RST}\n"
    return "$ec"
}

if [ -n "${BASH_VERSION:-}" ]; then
    __cyber_prompt_cmd() {
        local ec=$?
        (exit "$ec")
        __cyber_print_hud_rail
        if [ "$ec" -eq 0 ]; then
            PS1="\[\e[38;2;76;110;245m\]╰─\[\e[1;38;2;34;184;207m\]◈ ⟫\[\e[0m\] "
        else
            PS1="\[\e[38;2;76;110;245m\]╰─\[\e[1;38;2;255;107;107m\]✘ ⟫\[\e[0m\] "
        fi
    }
    PROMPT_COMMAND="__cyber_prompt_cmd"
elif [ -n "${ZSH_VERSION:-}" ]; then
    precmd() { __cyber_print_hud_rail; }
    setopt PROMPT_SUBST
    PROMPT='%F{#4c6ef5}╰─%(?.%B%F{#22b8cf}◈ ⟫.%B%F{#ff6b6b}✘ ⟫)%b%f '
fi

if [ -z "${CYBER_BANNER_SHOWN:-}" ] && [ "${SHLVL:-1}" -le 2 ]; then
    export CYBER_BANNER_SHOWN=1
    printf "\e[38;2;36;50;82m┏━━\e[1;38;2;34;184;207m◈ CYBER DECK CONSOLE\e[0m\e[38;2;36;50;82m━━┫ \e[38;2;145;167;255mSYS.NODE // %s\e[38;2;36;50;82m ┣━━\e[38;2;34;184;207m//////\e[38;2;36;50;82m━━┓\e[0m\n" "$(uname -r)"
    if command -v fastfetch >/dev/null 2>&1 && [ "$(tput cols 2>/dev/null || echo 80)" -ge 72 ]; then
        fastfetch
    fi
fi
