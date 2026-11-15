#!/usr/bin/python3
import os, glob

HOME = os.path.expanduser("~")

DISCORD_CSS = """/**
 * @name Studio Matte Grey
 * @description Monochrome Matte-Grey Studio Theme for Discord
 * @version 2.0.0
 */
:root, .theme-dark, .theme-light, html.theme-dark, html.platform-linux {
    --background-primary: #121316 !important;
    --background-secondary: #16181c !important;
    --background-secondary-alt: #14161a !important;
    --background-tertiary: #0e1013 !important;
    --background-accent: #262930 !important;
    --background-floating: #17191e !important;
    --background-modifier-hover: rgba(140, 147, 158, 0.10) !important;
    --background-modifier-active: rgba(140, 147, 158, 0.16) !important;
    --background-modifier-selected: rgba(140, 147, 158, 0.20) !important;
    --bg-overlay-2: #16181c !important;
    --bg-overlay-3: #1b1e24 !important;
    --bg-base-primary: #121316 !important;
    --bg-base-secondary: #16181c !important;
    --bg-base-tertiary: #0e1013 !important;
    --bg-surface-overlay: #17191e !important;
    --channeltextarea-background: #181a20 !important;
    --chat-background: #121316 !important;
    --home-background: #121316 !important;
    --modal-background: #16181c !important;
    --modal-footer-background: #14161a !important;
    --scrollbar-thin-thumb: #2c3038 !important;
    --scrollbar-auto-thumb: #2c3038 !important;
    --scrollbar-auto-track: #121316 !important;
    --brand-experiment: #5c626d !important;
    --brand-500: #5c626d !important;
    --brand-560: #6c727d !important;
    --text-normal: #d4d8de !important;
    --text-muted: #828894 !important;
    --header-primary: #e6e9ef !important;
    --header-secondary: #9ea4b0 !important;
    --interactive-normal: #b0b6c0 !important;
    --interactive-hover: #e6e9ef !important;
    --interactive-active: #ffffff !important;
    --font-primary: "Inter", sans-serif !important;
    --font-display: "Inter", sans-serif !important;
    --font-code: "JetBrainsMono Nerd Font", monospace !important;
}

/* Поле ввода сообщения */
div[class*="scrollableContainer_"] {
    background-color: #181a20 !important;
    border: 1px solid #2b2f38 !important;
    border-radius: 7px !important;
}

/* Боковая панель серверов и каналов */
nav[class*="guilds_"], div[class*="sidebar_"], section[class*="panels_"] {
    background-color: #14161a !important;
    border-right: 1px solid #22252b !important;
}
"""

# 1. Применяем для Vesktop, Vencord, Equibop, Legcord, BetterDiscord
mod_dirs = [
    os.path.join(HOME, ".config/vesktop"),
    os.path.join(HOME, ".config/Vencord"),
    os.path.join(HOME, ".config/equibop"),
    os.path.join(HOME, ".config/legcord"),
    os.path.join(HOME, ".config/BetterDiscord"),
    os.path.join(HOME, ".var/app/dev.vencord.Vesktop/config/vesktop"),
]
for mdir in mod_dirs:
    os.makedirs(os.path.join(mdir, "themes"), exist_ok=True)
    os.makedirs(os.path.join(mdir, "settings"), exist_ok=True)
    open(os.path.join(mdir, "themes/studio-grey.theme.css"), "w", encoding="utf-8").write(DISCORD_CSS)
    open(os.path.join(mdir, "settings/quickCss.css"), "w", encoding="utf-8").write(DISCORD_CSS)

# 2. Сохраняем CSS в ~/.config/cyberdeck/discord-studio.css и внедряем автозагрузчик в стандартный клиент Discord
css_file = os.path.join(HOME, ".config/cyberdeck/discord-studio.css")
open(css_file, "w", encoding="utf-8").write(DISCORD_CSS)

HOOK_JS = f"""// Studio Grey Auto-CSS Hook
const fs = require('fs');
const electron = require('electron');
electron.app.on('browser-window-created', (_e, win) => {{
    win.webContents.on('dom-ready', () => {{
        try {{
            const css = fs.readFileSync('{css_file}', 'utf8');
            win.webContents.insertCSS(css);
        }} catch (err) {{}}
    }});
}});
module.exports = require('./core.asar');
"""

for core_idx in glob.glob(os.path.join(HOME, ".config/discord*/*/modules/discord_desktop_core/index.js")):
    try:
        cur_js = open(core_idx, "r", encoding="utf-8", errors="ignore").read()
        if "core.asar" in cur_js and "Studio Grey Auto-CSS" not in cur_js:
            open(core_idx, "w", encoding="utf-8").write(HOOK_JS)
    except Exception:
        pass
