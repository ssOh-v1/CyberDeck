#!/usr/bin/python3
import os, sys, glob, json, base64, configparser

HOME = os.path.expanduser("~")
STATE_FILE = os.path.join(HOME, ".config/cyberdeck/theme.json")
WALL_DIR = os.path.join(HOME, ".config/cyberdeck/wallpapers")

def load_theme():
    try:
        if os.path.isfile(STATE_FILE):
            return json.load(open(STATE_FILE, encoding="utf-8"))
    except Exception:
        pass
    return {"id": "cyberdeck", "layout": "cyberdeck", "primary": "#478cbf", "accent": "#63d994", "bg": "#07090f", "bg_alt": "#0e1526", "fg": "#dce3f5", "radius": 10}

T = load_theme()
TID = T.get("id", "cyberdeck")
LAY = T.get("layout", "cyberdeck")
P   = T.get("primary", "#478cbf")
A   = T.get("accent", "#63d994")
BG  = T.get("bg", "#07090f")
BGA = T.get("bg_alt", "#0e1526")
FG  = T.get("fg", "#dce3f5")
RAD = int(T.get("radius", 10))

# Кодируем актуальные обои выбранного мира в Base64 для главной страницы Firefox (about:newtab / about:home)
wall_p = os.path.join(WALL_DIR, f"{TID}.png")
if not os.path.isfile(wall_p):
    wall_p = os.path.join(HOME, ".cache/cyberdeck/work_hud_bg.png")

WALL_B64 = ""
if os.path.isfile(wall_p):
    try:
        WALL_B64 = base64.b64encode(open(wall_p, "rb").read()).decode("ascii")
    except Exception:
        WALL_B64 = ""

# 5 уникальных SVG-шапок для панели вкладок Firefox под каждую тему
if LAY == "dungeon":
    TAB_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
      <rect width="1920" height="96" fill="#0d0708"/>
      <line x1="0" y1="95" x2="1920" y2="95" stroke="{A}" stroke-width="2" stroke-opacity="0.75"/>
      <path d="M 12 28 L 12 6 L 44 6 M 1908 28 L 1908 6 L 1876 6" fill="none" stroke="{A}" stroke-width="2.2"/>
      <text x="1720" y="18" font-family="serif" font-size="10" font-weight="bold" fill="{A}" fill-opacity="0.75">⚔ THE DUNGEON OF GOD</text>
    </svg>"""
elif LAY == "forest":
    TAB_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
      <defs><linearGradient id="fg" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#0a1912"/><stop offset="50%" stop-color="#122b20"/><stop offset="100%" stop-color="#0a1912"/></linearGradient></defs>
      <rect width="1920" height="96" fill="url(#fg)"/>
      <line x1="0" y1="95" x2="1920" y2="95" stroke="{A}" stroke-width="1.5" stroke-opacity="0.5"/>
    </svg>"""
elif LAY == "impasto":
    TAB_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
      <defs><linearGradient id="ig" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#181520"/><stop offset="50%" stop-color="#261f29"/><stop offset="100%" stop-color="#181520"/></linearGradient></defs>
      <rect width="1920" height="96" fill="url(#ig)"/>
      <line x1="0" y1="95" x2="1920" y2="95" stroke="{A}" stroke-width="2" stroke-opacity="0.7"/>
    </svg>"""
elif LAY == "gamedev":
    TAB_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
      <defs><pattern id="gg" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M 16 0 L 0 0 0 16" fill="none" stroke="{P}" stroke-width="0.6" stroke-opacity="0.12"/></pattern></defs>
      <rect width="1920" height="96" fill="#0d1117"/>
      <rect width="1920" height="96" fill="url(#gg)"/>
      <line x1="0" y1="95" x2="1920" y2="95" stroke="{P}" stroke-width="2"/>
      <text x="1730" y="17" font-family="monospace" font-size="9.5" font-weight="bold" fill="{A}" fill-opacity="0.7">🎮 ENGINE // WEB_VIEWPORT</text>
    </svg>"""
else:
    TAB_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
      <defs><pattern id="cg" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M 24 0 L 0 0 0 24" fill="none" stroke="{P}" stroke-width="0.6" stroke-opacity="0.09"/></pattern></defs>
      <rect width="1920" height="96" fill="{BG}"/>
      <rect width="1920" height="96" fill="url(#cg)"/>
      <line x1="0" y1="1" x2="1920" y2="1" stroke="{A}" stroke-width="1.5" stroke-opacity="0.55"/>
    </svg>"""

TAB_B64 = base64.b64encode(TAB_SVG.encode("utf-8")).decode("ascii")

USER_CHROME = f"""/* World-Adaptive Firefox Theme: {TID} */
:root, #main-window, #navigator-toolbox {{
    --lwt-accent-color: {BG} !important;
    --toolbox-bgcolor: {BG} !important;
    --toolbar-bgcolor: transparent !important;
    --toolbar-color: {FG} !important;
    --lwt-text-color: {FG} !important;
    --tab-selected-bgcolor: {BGA} !important;
    --tab-selected-textcolor: #ffffff !important;
    --tab-loading-fill: {A} !important;
    --urlbar-box-bgcolor: {BGA} !important;
    --urlbar-box-focus-bgcolor: {BGA} !important;
    --toolbar-field-background-color: {BGA} !important;
    --toolbar-field-color: {FG} !important;
    --toolbar-field-border-color: {P} !important;
    --toolbar-field-focus-background-color: {BGA} !important;
    --toolbar-field-focus-color: #ffffff !important;
    --toolbar-field-focus-border-color: {A} !important;
    --tab-border-radius: {RAD}px !important;
}}

#navigator-toolbox {{
    background-color: {BG} !important;
    background-image: url("data:image/svg+xml;base64,{TAB_B64}") !important;
    background-size: 1920px 96px !important;
    background-position: top left !important;
    background-repeat: repeat-x !important;
    border-bottom: 1px solid {P} !important;
}}

#TabsToolbar, #titlebar {{ background: transparent !important; padding: 3px 6px !important; }}
#nav-bar {{ background-color: {BG}e6 !important; border-top: 1px solid {P}44 !important; box-shadow: none !important; padding: 3px 8px !important; }}

.tabbrowser-tab .tab-background {{
    background-color: {BG}cc !important;
    border: 1px solid {P}66 !important;
    border-radius: {RAD}px !important;
    box-shadow: none !important;
    margin-block: 3px !important;
}}

.tabbrowser-tab .tab-background:is([selected], [multiselected]) {{
    background-color: {BGA} !important;
    border: 1px solid {A} !important;
    border-top: 2px solid {A} !important;
    outline: none !important;
}}

#urlbar-background, .urlbar-background, #searchbar {{
    background-color: {BGA} !important;
    border: 1px solid {P} !important;
    border-left: 3px solid {A} !important;
    border-radius: {RAD}px !important;
    box-shadow: none !important;
}}
"""

BG_IMG_RULE = f'background-image: url("data:image/png;base64,{WALL_B64}") !important;' if WALL_B64 else ""

USER_CONTENT = f"""/* World-Adaptive Firefox NewTab: {TID} */
@-moz-document url("about:newtab"), url("about:home"), url("about:blank"), url("about:privatebrowsing") {{
    html, body {{
        background-color: {BG} !important;
        {BG_IMG_RULE}
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
        color: {FG} !important;
    }}
    .outer-wrapper {{ background: transparent !important; }}
    .search-wrapper .search-handoff-button, .search-wrapper input {{
        background-color: {BG}e8 !important;
        border: 1px solid {P} !important;
        border-left: 4px solid {A} !important;
        border-radius: {RAD}px !important;
        color: {FG} !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55) !important;
    }}
    .top-site-outer .tile {{
        background-color: {BG}e6 !important;
        border: 1px solid {P} !important;
        border-top: 2px solid {A} !important;
        border-radius: {RAD}px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45) !important;
    }}
    .top-site-outer:hover .tile {{
        background-color: {BGA}f5 !important;
        border-color: {A} !important;
    }}
    .top-site-outer .title span {{ color: {FG} !important; font-weight: 600 !important; }}
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
}

def apply_to_profile(pd):
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

prof_dirs = set()
for r in [os.path.join(HOME, ".config/mozilla/firefox"), os.path.join(HOME, ".mozilla/firefox")]:
    if not os.path.isdir(r): continue
    for pjs in glob.glob(os.path.join(r, "*", "prefs.js")):
        prof_dirs.add(os.path.realpath(os.path.dirname(pjs)))

for pd in sorted(prof_dirs):
    apply_to_profile(pd)
