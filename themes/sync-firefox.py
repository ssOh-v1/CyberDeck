#!/usr/bin/python3
import os, glob, shutil, base64

HOME = os.path.expanduser("~")

# Чистый минималистичный матово-серый фон стартовой страницы Firefox
NEWTAB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <radialGradient id="g" cx="50%" cy="42%" r="55%">
      <stop offset="0%" stop-color="#1b1d22"/>
      <stop offset="100%" stop-color="#111215"/>
    </radialGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#g)"/>
  <g transform="translate(960, 210)" fill="none" stroke="#2c3038" stroke-width="1.5">
    <rect x="-220" y="-26" width="440" height="44" rx="22" fill="#16181c"/>
    <text x="0" y="1" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#8c939e" stroke="none">▣ STUDIO BROWSER // GAMEDEV &amp; AI WORKSPACE</text>
  </g>
</svg>"""

NT_B64 = base64.b64encode(NEWTAB_SVG.encode("utf-8")).decode("ascii")

USER_CHROME = """/* Studio Matte Grey — Clean Modern Firefox UI */
:root, #main-window, #navigator-toolbox, #TabsToolbar, #nav-bar, #PersonalToolbar {
    --lwt-accent-color: #111215 !important;
    --toolbox-bgcolor: #111215 !important;
    --toolbar-bgcolor: #16181c !important;
    --toolbar-color: #d4d8de !important;
    --lwt-text-color: #d4d8de !important;
    --tab-selected-bgcolor: #24272e !important;
    --tab-selected-textcolor: #ffffff !important;
    --tab-loading-fill: #9ea4b0 !important;
    --urlbar-box-bgcolor: #111215 !important;
    --urlbar-box-focus-bgcolor: #111215 !important;
    --toolbar-field-background-color: #111215 !important;
    --toolbar-field-color: #d4d8de !important;
    --toolbar-field-border-color: #282b32 !important;
    --toolbar-field-focus-background-color: #14161a !important;
    --toolbar-field-focus-color: #ffffff !important;
    --toolbar-field-focus-border-color: #6c727d !important;
    --tab-border-radius: 8px !important;
}

#navigator-toolbox {
    background-color: #111215 !important;
    background-image: none !important;
    border-bottom: 1px solid #24272e !important;
}

#TabsToolbar, #titlebar {
    background-color: #111215 !important;
    background-image: none !important;
    padding: 4px 8px 2px 8px !important;
}

#nav-bar {
    background-color: #16181c !important;
    background-image: none !important;
    border-top: 1px solid #22252b !important;
    box-shadow: none !important;
    padding: 4px 10px !important;
}

/* Аккуратные закруглённые вкладки-капсулы */
.tabbrowser-tab .tab-background {
    background-color: #16181c !important;
    background-image: none !important;
    border: 1px solid #23262c !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    margin-block: 2px !important;
}

.tabbrowser-tab:hover .tab-background:not([selected]) {
    background-color: #1d2026 !important;
    border-color: #363a42 !important;
}

.tabbrowser-tab .tab-background:is([selected], [multiselected]) {
    background-color: #252830 !important;
    background-image: none !important;
    border: 1px solid #525761 !important;
    box-shadow: none !important;
    outline: none !important;
}

.tabbrowser-tab[selected="true"] .tab-label {
    color: #ffffff !important;
    font-weight: 700 !important;
}

#urlbar-background, .urlbar-background, #searchbar {
    background-color: #111215 !important;
    background-image: none !important;
    border: 1px solid #2a2d34 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}

#urlbar[focused="true"] > #urlbar-background {
    background-color: #14161a !important;
    border: 1px solid #6c727d !important;
    box-shadow: none !important;
}

#PersonalToolbar {
    background-color: #14161a !important;
    border-top: 1px solid #202329 !important;
}
"""

USER_CONTENT = f"""/* Studio Matte Grey — Firefox NewTab & Home */
@-moz-document url("about:newtab"), url("about:home"), url("about:blank"), url("about:privatebrowsing") {{
    html, body {{
        background-color: #111215 !important;
        background-image: url("data:image/svg+xml;base64,{NT_B64}") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        color: #d4d8de !important;
    }}
    .outer-wrapper {{ background: transparent !important; }}
    .search-wrapper .search-handoff-button, .search-wrapper input {{
        background-color: #181a1f !important;
        border: 1px solid #32363e !important;
        border-radius: 10px !important;
        color: #d4d8de !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35) !important;
    }}
    .top-site-outer .tile {{
        background-color: #181a1f !important;
        border: 1px solid #2a2e36 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.28) !important;
    }}
    .top-site-outer:hover .tile {{
        background-color: #23262e !important;
        border-color: #6c727d !important;
    }}
    .top-site-outer .title span {{ color: #c8ccd2 !important; font-weight: 600 !important; }}
}}
"""

PREFS = {
    "toolkit.legacyUserProfileCustomizations.stylesheets": "true",
    "svg.context-properties.content.enabled": "true",
    "layout.css.has-selector.enabled": "true",
    "extensions.activeThemeID": '"firefox-compact-dark@mozilla.org"',
    "ui.systemUsesDarkTheme": "1",
    "layout.css.prefers-color-scheme.content-override": "0",
    "browser.theme.content-theme": "0",
    "browser.theme.toolbar-theme": "0",
    "browser.in-content.dark-mode": "true",
    "browser.startup.page": "3",
}

def apply_to_profile(pd):
    cdir = os.path.join(pd, "chrome")
    os.makedirs(cdir, exist_ok=True)
    open(os.path.join(cdir, "userChrome.css"), "w", encoding="utf-8").write(USER_CHROME)
    open(os.path.join(cdir, "userContent.css"), "w", encoding="utf-8").write(USER_CONTENT)

    # Очищаем кэш startupCache, чтобы Firefox гарантированно перечитал userChrome.css!
    shutil.rmtree(os.path.join(pd, "startupCache"), ignore_errors=True)

    for fname in ("user.js", "prefs.js"):
        fpath = os.path.join(pd, fname)
        existing = open(fpath, "r", encoding="utf-8", errors="ignore").readlines() if os.path.isfile(fpath) else []
        filtered = [ln for ln in existing if not any(f'"{k}"' in ln for k in PREFS)]
        for k, v in PREFS.items():
            filtered.append(f'user_pref("{k}", {v});\n')
        open(fpath, "w", encoding="utf-8").writelines(filtered)

prof_dirs = set()
search_roots = [
    os.path.join(HOME, ".mozilla/firefox"),
    os.path.join(HOME, ".config/mozilla/firefox"),
    os.path.join(HOME, ".var/app/org.mozilla.firefox/.mozilla/firefox"),
]
for r in search_roots:
    if not os.path.isdir(r): continue
    for sub in glob.glob(os.path.join(r, "*")):
        if os.path.isdir(sub) and (os.path.isfile(os.path.join(sub, "prefs.js")) or sub.endswith((".default", ".default-release"))):
            prof_dirs.add(os.path.realpath(sub))

for pd in sorted(prof_dirs):
    apply_to_profile(pd)
