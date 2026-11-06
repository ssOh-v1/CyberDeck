#!/usr/bin/env python3
import os, glob, configparser

HOME = os.path.expanduser("~")

USER_CHROME = """/* Alpora Cyber Deck — HUD Decorated Firefox UI */
:root, #main-window, #navigator-toolbox {
    --lwt-accent-color: #07090f !important;
    --lwt-accent-color-inactive: #07090f !important;
    --toolbox-bgcolor: #07090f !important;
    --toolbox-bgcolor-inactive: #07090f !important;
    --toolbar-bgcolor: #0a0e19 !important;
    --toolbar-color: #dce3f5 !important;
    --lwt-text-color: #dce3f5 !important;
    --tab-selected-bgcolor: #111a2e !important;
    --tab-selected-textcolor: #f0f4ff !important;
    --tab-loading-fill: #22b8cf !important;
    --urlbar-box-bgcolor: #0c1222 !important;
    --urlbar-box-focus-bgcolor: #10192e !important;
    --urlbar-box-hover-bgcolor: #10192e !important;
    --toolbar-field-background-color: #0c1222 !important;
    --toolbar-field-color: #e5ecff !important;
    --toolbar-field-border-color: #233252 !important;
    --toolbar-field-focus-background-color: #10192e !important;
    --toolbar-field-focus-color: #f0f4ff !important;
    --toolbar-field-focus-border-color: #22b8cf !important;
    --arrowpanel-background: #0b101d !important;
    --arrowpanel-color: #dce3f5 !important;
    --arrowpanel-border-color: #283a61 !important;
    --sidebar-background-color: #080c15 !important;
    --sidebar-text-color: #c5d0ea !important;
    --tab-border-radius: 8px !important;
}

/* Тактическая микросетка на шапке браузера + неоновая линия сканера */
#navigator-toolbox {
    background-color: #07090f !important;
    background-image:
        linear-gradient(90deg, transparent 0%, rgba(76, 110, 245, 0.45) 25%, rgba(34, 184, 207, 0.85) 50%, rgba(76, 110, 245, 0.45) 75%, transparent 100%),
        repeating-linear-gradient(90deg, rgba(76, 110, 245, 0.05) 0px, rgba(76, 110, 245, 0.05) 1px, transparent 1px, transparent 48px) !important;
    background-size: 100% 1px, 48px 100% !important;
    background-position: bottom center, top left !important;
    background-repeat: no-repeat, repeat !important;
    border-bottom: 1px solid #1e2b48 !important;
}

#TabsToolbar, #titlebar {
    background-color: transparent !important;
    background-image:
        repeating-linear-gradient(-55deg, rgba(34, 184, 207, 0.14) 0px, rgba(34, 184, 207, 0.14) 2px, transparent 2px, transparent 9px) !important;
    background-size: 110px 6px !important;
    background-repeat: no-repeat !important;
    background-position: right 140px top 4px !important;
}

#nav-bar, #PersonalToolbar {
    background-color: rgba(10, 14, 25, 0.94) !important;
    background-image: none !important;
    box-shadow: none !important;
}

/* Угловые кибер-скобы HUD на активной вкладке */
.tab-background {
    border-radius: 8px !important;
    box-shadow: none !important;
    border: 1px solid rgba(35, 48, 77, 0.45) !important;
    background-color: rgba(12, 17, 30, 0.65) !important;
}

.tab-background:is([selected], [multiselected]) {
    background-color: #111a2e !important;
    background-image:
        linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#4c6ef5, #4c6ef5),
        linear-gradient(#4c6ef5, #4c6ef5) !important;
    background-repeat: no-repeat !important;
    background-size: 10px 2px, 2px 10px, 10px 2px, 2px 10px !important;
    background-position: top left, top left, bottom right, bottom right !important;
    border: 1px solid #2d4270 !important;
    outline: none !important;
}

/* Адресная строка с HUD-уголками при фокусе */
#urlbar-background, .urlbar-background, #searchbar {
    background-color: #0c1222 !important;
    background-image:
        linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#22b8cf, #22b8cf) !important;
    background-repeat: no-repeat !important;
    background-size: 8px 2px, 2px 8px !important;
    background-position: top left, top left !important;
    border: 1px solid #233252 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}

#urlbar:is([focused="true"], [focused], [open]) > :is(#urlbar-background, .urlbar-background) {
    background-color: #10192e !important;
    background-image:
        linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#4c6ef5, #4c6ef5),
        linear-gradient(#4c6ef5, #4c6ef5),
        linear-gradient(#4c6ef5, #4c6ef5),
        linear-gradient(#4c6ef5, #4c6ef5) !important;
    background-repeat: no-repeat !important;
    background-size: 10px 2px, 2px 10px, 10px 2px, 2px 10px, 10px 2px, 2px 10px, 10px 2px, 2px 10px !important;
    background-position: top left, top left, top right, top right, bottom left, bottom left, bottom right, bottom right !important;
    border-color: #2f4b7c !important;
    outline: none !important;
}
"""

USER_CONTENT = """/* Alpora Cyber Deck — HUD Матрица Новой Вкладки Firefox */
@-moz-document url("about:newtab"), url("about:home"), url("about:blank"), url("about:privatebrowsing") {
    html, body {
        background-color: #07090f !important;
        background-image:
            radial-gradient(circle at 15% 15%, rgba(76, 110, 245, 0.11) 0%, transparent 42%),
            radial-gradient(circle at 85% 85%, rgba(34, 184, 207, 0.09) 0%, transparent 42%),
            linear-gradient(rgba(76, 110, 245, 0.055) 1px, transparent 1px),
            linear-gradient(90deg, rgba(76, 110, 245, 0.055) 1px, transparent 1px) !important;
        background-size: 100% 100%, 100% 100%, 64px 64px, 64px 64px !important;
        background-attachment: fixed !important;
        color: #dce3f5 !important;
    }

    /* Угловые периметральные HUD-скобы экрана внутри стартовой страницы */
    body::before {
        content: "" !important;
        position: fixed !important;
        inset: 16px !important;
        pointer-events: none !important;
        z-index: 9998 !important;
        background-image:
            linear-gradient(#22b8cf, #22b8cf), linear-gradient(#22b8cf, #22b8cf),
            linear-gradient(#22b8cf, #22b8cf), linear-gradient(#22b8cf, #22b8cf),
            linear-gradient(#4c6ef5, #4c6ef5), linear-gradient(#4c6ef5, #4c6ef5),
            linear-gradient(#4c6ef5, #4c6ef5), linear-gradient(#4c6ef5, #4c6ef5) !important;
        background-repeat: no-repeat !important;
        background-size: 36px 2px, 2px 36px, 36px 2px, 2px 36px, 36px 2px, 2px 36px, 36px 2px, 2px 36px !important;
        background-position: top left, top left, top right, top right, bottom left, bottom left, bottom right, bottom right !important;
        opacity: 0.75 !important;
    }

    /* Верхняя телеметрическая плашка Cyber Deck */
    body::after {
        content: "◈ CYBER DECK // WEB MATRIX   •   WAYLAND ENGINE" !important;
        position: fixed !important;
        top: 16px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        background-color: rgba(11, 16, 29, 0.92) !important;
        color: #66d9e8 !important;
        border: 1px solid #243354 !important;
        border-radius: 8px !important;
        padding: 4px 16px !important;
        font-family: "Noto Sans", sans-serif !important;
        font-size: 10px !important;
        font-weight: 700 !important;
        letter-spacing: 0.8px !important;
        pointer-events: none !important;
        z-index: 9999 !important;
    }

    .search-wrapper .search-handoff-button,
    .search-wrapper input {
        background-color: rgba(12, 18, 34, 0.95) !important;
        border: 1px solid #283a61 !important;
        border-left: 3px solid #22b8cf !important;
        border-radius: 10px !important;
        color: #e5ecff !important;
        box-shadow: none !important;
    }

    /* Плитки сайтов в стиле карточек Work Deck */
    .top-site-outer .tile {
        background-color: rgba(13, 18, 32, 0.95) !important;
        border: 1px solid #222f4d !important;
        border-left: 3px solid #4c6ef5 !important;
        border-radius: 11px !important;
        box-shadow: none !important;
    }
    .top-site-outer:hover .tile {
        background-color: rgba(20, 29, 50, 0.99) !important;
        border-color: #22b8cf !important;
        border-left: 3px solid #22b8cf !important;
    }
}
"""

PREFS = {
    "toolkit.legacyUserProfileCustomizations.stylesheets": "true",
    "svg.context-properties.content.enabled": "true",
    "layout.css.has-selector.enabled": "true",
    "extensions.activeThemeID": '"firefox-compact-dark@mozilla.org"',
    "ui.systemUsesDarkTheme": "1",
    "browser.theme.content-theme": "0",
    "browser.theme.toolbar-theme": "0",
    "browser.in-content.dark-mode": "true",
}

prof_dirs = set()
roots = [
    os.path.join(HOME, ".config/mozilla/firefox"),
    os.path.join(HOME, ".mozilla/firefox"),
    os.path.join(HOME, ".var/app/org.mozilla.firefox/.mozilla/firefox"),
    os.path.join(HOME, ".var/app/org.mozilla.firefox/config/mozilla/firefox"),
    os.path.join(HOME, ".librewolf"),
    os.path.join(HOME, ".zen"),
]

for r in roots:
    if not os.path.isdir(r):
        continue
    ini = os.path.join(r, "profiles.ini")
    if os.path.isfile(ini):
        cp = configparser.ConfigParser()
        try:
            cp.read(ini, encoding="utf-8")
            for sec in cp.sections():
                for key in ("Path", "Default"):
                    if cp.has_option(sec, key):
                        p = cp.get(sec, key).strip()
                        if p:
                            full = p if p.startswith("/") else os.path.join(r, p)
                            if os.path.isdir(full):
                                prof_dirs.add(os.path.realpath(full))
        except Exception:
            pass
    for pjs in glob.glob(os.path.join(r, "*", "prefs.js")):
        prof_dirs.add(os.path.realpath(os.path.dirname(pjs)))

for pid in os.listdir("/proc"):
    if pid.isdigit():
        try:
            if "firefox" in open(f"/proc/{pid}/comm").read().strip().lower():
                for fd in os.listdir(f"/proc/{pid}/fd"):
                    target = os.readlink(f"/proc/{pid}/fd/{fd}")
                    if target.endswith(("places.sqlite", "cookies.sqlite", "prefs.js")):
                        prof_dirs.add(os.path.realpath(os.path.dirname(target)))
        except Exception:
            pass

for pd in sorted(prof_dirs):
    cdir = os.path.join(pd, "chrome")
    os.makedirs(cdir, exist_ok=True)
    open(os.path.join(cdir, "userChrome.css"), "w", encoding="utf-8").write(USER_CHROME)
    open(os.path.join(cdir, "userContent.css"), "w", encoding="utf-8").write(USER_CONTENT)

    ujs = os.path.join(pd, "user.js")
    existing = open(ujs, "r", encoding="utf-8", errors="ignore").readlines() if os.path.isfile(ujs) else []
    filtered = [ln for ln in existing if not any(f'"{k}"' in ln for k in PREFS)]
    for k, v in PREFS.items():
        filtered.append(f'user_pref("{k}", {v});\n')
    open(ujs, "w", encoding="utf-8").writelines(filtered)
    print("HUD-тема Firefox записана в:", pd)
