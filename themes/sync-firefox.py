#!/usr/bin/python3
import os, sys, glob, base64, configparser

HOME = os.path.expanduser("~")

# Верхняя панель Firefox в стиле тулбара игрового движка (координатная линейка, сетка 16px, оси X/Y)
TABBAR_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
  <defs>
    <linearGradient id="tbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0b0f14"/>
      <stop offset="100%" stop-color="#131922"/>
    </linearGradient>
    <pattern id="g16" width="16" height="16" patternUnits="userSpaceOnUse">
      <path d="M 16 0 L 0 0 0 16" fill="none" stroke="#478cbf" stroke-width="0.5" stroke-opacity="0.09"/>
    </pattern>
    <pattern id="Ruler" width="64" height="12" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="7" stroke="#478cbf" stroke-width="1.2" stroke-opacity="0.45"/>
      <line x1="16" y1="0" x2="16" y2="4" stroke="#478cbf" stroke-width="0.8" stroke-opacity="0.25"/>
      <line x1="32" y1="0" x2="32" y2="5" stroke="#478cbf" stroke-width="0.8" stroke-opacity="0.35"/>
      <line x1="48" y1="0" x2="48" y2="4" stroke="#478cbf" stroke-width="0.8" stroke-opacity="0.25"/>
    </pattern>
  </defs>
  <rect width="1920" height="96" fill="url(#tbg)"/>
  <rect width="1920" height="96" fill="url(#g16)"/>
  <rect width="1920" height="12" fill="url(#Ruler)"/>

  <line x1="0" y1="1" x2="1920" y2="1" stroke="#478cbf" stroke-width="1.5" stroke-opacity="0.65"/>
  <path d="M 8 28 L 8 5 L 36 5" fill="none" stroke="#63d994" stroke-width="2" stroke-opacity="0.85"/>
  <path d="M 1912 28 L 1912 5 L 1884 5" fill="none" stroke="#478cbf" stroke-width="2" stroke-opacity="0.85"/>

  <g stroke="#478cbf" stroke-width="1.3" stroke-opacity="0.35" fill="none">
    <polyline points="54,7 210,7 224,20 420,20"/>
    <polyline points="1320,20 1510,20 1526,8 1680,8"/>
  </g>
  <circle cx="54" cy="7" r="2.5" fill="#63d994"/>
  <circle cx="420" cy="20" r="2.5" fill="#478cbf"/>
  <circle cx="1680" cy="8" r="2.5" fill="#63d994"/>
  <text x="1700" y="16" font-family="monospace" font-size="9.5" font-weight="bold" fill="#63d994" fill-opacity="0.78">🎮 ENGINE // WEB_VIEWPORT 4.3</text>
</svg>"""

# Главная страница Firefox в стиле 2D/3D Viewport среды разработки игр
NEWTAB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#090d12"/>
      <stop offset="50%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#080b10"/>
    </linearGradient>
    <radialGradient id="vpGlow" cx="50%" cy="48%" r="45%">
      <stop offset="0%" stop-color="#478cbf" stop-opacity="0.15"/>
      <stop offset="55%" stop-color="#63d994" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid32" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#478cbf" stroke-width="0.6" stroke-opacity="0.06"/>
    </pattern>
    <pattern id="grid128" width="128" height="128" patternUnits="userSpaceOnUse">
      <path d="M 128 0 L 0 0 0 128" fill="none" stroke="#478cbf" stroke-width="1.1" stroke-opacity="0.14"/>
      <path d="M 123 128 L 133 128 M 128 123 L 128 133" stroke="#63d994" stroke-width="1.3" stroke-opacity="0.42"/>
    </pattern>
  </defs>

  <rect width="1920" height="1080" fill="url(#bg)"/>
  <rect width="1920" height="1080" fill="url(#vpGlow)"/>
  <rect width="1920" height="1080" fill="url(#grid32)"/>
  <rect width="1920" height="1080" fill="url(#grid128)"/>

  <!-- Мировые оси координат X (Red) и Y (Green) -->
  <line x1="0" y1="540" x2="1920" y2="540" stroke="#ff6b6b" stroke-width="1.5" stroke-opacity="0.38"/>
  <line x1="960" y1="0" x2="960" y2="1080" stroke="#63d994" stroke-width="1.5" stroke-opacity="0.38"/>

  <!-- Рамка Camera2D и центральный Gizmo-компас -->
  <rect x="340" y="150" width="1240" height="760" fill="none" stroke="#478cbf" stroke-width="1.6" stroke-opacity="0.38" stroke-dasharray="10 6"/>
  <g transform="translate(960, 540)">
    <circle r="310" fill="none" stroke="#478cbf" stroke-width="1.2" stroke-opacity="0.24"/>
    <circle r="240" fill="none" stroke="#63d994" stroke-width="1.4" stroke-opacity="0.22" stroke-dasharray="6 4"/>
    <path d="M -325 -55 A 330 330 0 0 1 -230 -235" fill="none" stroke="#63d994" stroke-width="3" stroke-opacity="0.6"/>
    <path d="M 325 -55 A 330 330 0 0 0 230 -235" fill="none" stroke="#478cbf" stroke-width="3" stroke-opacity="0.6"/>
    <path d="M -325 55 A 330 330 0 0 0 -230 235" fill="none" stroke="#478cbf" stroke-width="3" stroke-opacity="0.6"/>
    <path d="M 325 55 A 330 330 0 0 1 230 235" fill="none" stroke="#63d994" stroke-width="3" stroke-opacity="0.6"/>
  </g>

  <!-- Левая панель SceneTree // Engine Nodes -->
  <g transform="translate(46, 350)">
    <rect width="265" height="230" rx="6" fill="#12171e" fill-opacity="0.92" stroke="#30363d" stroke-width="1.5"/>
    <rect x="0" y="0" width="265" height="3" fill="#478cbf"/>
    <text x="16" y="30" font-family="monospace" font-size="11" font-weight="bold" fill="#63d994">📂 SceneTree // WebViewport</text>
    <line x1="16" y1="42" x2="249" y2="42" stroke="#263242" stroke-width="1"/>
    <text x="16" y="70" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">├─ 🎮 Root_Viewport <tspan fill="#79c0ff">[2D]</tspan></text>
    <text x="16" y="100" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">├─ ⚡ WebRender_GPU <tspan fill="#63d994">[ON]</tspan></text>
    <text x="16" y="130" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">├─ 🐍 Python_Runtime <tspan fill="#f5b82e">[3.14]</tspan></text>
    <text x="16" y="160" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">└─ 🛡 Wayland_Socket <tspan fill="#63d994">[OK]</tspan></text>
    <rect x="16" y="190" width="233" height="8" rx="3" fill="#161b22" stroke="#30363d" stroke-width="1"/>
    <rect x="17" y="191" width="195" height="6" rx="2" fill="#63d994"/>
  </g>

  <!-- Правая панель Inspector // Frame Profiler -->
  <g transform="translate(1609, 350)">
    <rect width="265" height="230" rx="6" fill="#12171e" fill-opacity="0.92" stroke="#30363d" stroke-width="1.5"/>
    <rect x="0" y="0" width="265" height="3" fill="#63d994"/>
    <text x="16" y="30" font-family="monospace" font-size="11" font-weight="bold" fill="#79c0ff">🔍 Inspector // Profiler</text>
    <line x1="16" y1="42" x2="249" y2="42" stroke="#263242" stroke-width="1"/>
    <text x="16" y="70" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">FRAME_TIME // <tspan fill="#63d994">4.1 ms</tspan></text>
    <text x="16" y="100" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">RENDER_API // <tspan fill="#79c0ff">VULKAN DRM</tspan></text>
    <text x="16" y="130" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">SHADER_CACHE // <tspan fill="#63d994">10 GB</tspan></text>
    <text x="16" y="160" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">OPERATOR   // <tspan fill="#e6edf3">ssOh-v1</tspan></text>
    <rect x="16" y="190" width="233" height="8" rx="3" fill="#161b22" stroke="#30363d" stroke-width="1"/>
    <rect x="17" y="191" width="210" height="6" rx="2" fill="#478cbf"/>
  </g>

  <text x="960" y="28" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#79c0ff">🎮 GAMEDEV ENGINE STUDIO   •   VIEWPORT_2D [1920x1080]   •   X/Y GIZMO ACTIVE</text>
</svg>"""

TAB_B64 = base64.b64encode(TABBAR_SVG.encode("utf-8")).decode("ascii")
NT_B64  = base64.b64encode(NEWTAB_SVG.encode("utf-8")).decode("ascii")

USER_CHROME = f"""/* GameDev Engine Studio — Firefox IDE Theme */
:root, #main-window, #navigator-toolbox {{
    --lwt-accent-color: #0b0f14 !important;
    --toolbox-bgcolor: #0b0f14 !important;
    --toolbar-bgcolor: transparent !important;
    --toolbar-color: #e6edf3 !important;
    --lwt-text-color: #e6edf3 !important;
    --tab-selected-bgcolor: #161b22 !important;
    --tab-selected-textcolor: #ffffff !important;
    --tab-loading-fill: #63d994 !important;
    --urlbar-box-bgcolor: #0d1117 !important;
    --urlbar-box-focus-bgcolor: #121820 !important;
    --toolbar-field-background-color: #0d1117 !important;
    --toolbar-field-color: #e6edf3 !important;
    --toolbar-field-border-color: #30363d !important;
    --toolbar-field-focus-background-color: #121820 !important;
    --toolbar-field-focus-color: #ffffff !important;
    --toolbar-field-focus-border-color: #63d994 !important;
    --tab-border-radius: 6px !important;
}}

#navigator-toolbox {{
    background-color: #0b0f14 !important;
    background-image:
        linear-gradient(90deg, transparent 0%, #478cbf 25%, #63d994 50%, #478cbf 75%, transparent 100%),
        url("data:image/svg+xml;base64,{TAB_B64}") !important;
    background-size: 100% 2px, 1920px 96px !important;
    background-position: bottom center, top left !important;
    background-repeat: no-repeat, repeat-x !important;
    border-bottom: 1px solid #30363d !important;
}}

#TabsToolbar, #titlebar {{ background: transparent !important; padding: 3px 6px !important; }}
#nav-bar {{ background-color: rgba(13, 17, 23, 0.90) !important; border-top: 1px solid #263242 !important; box-shadow: none !important; padding: 3px 8px !important; }}

/* Вкладки в стиле открытых скриптов игрового движка */
.tabbrowser-tab .tab-background {{
    background-color: rgba(18, 23, 30, 0.82) !important;
    border: 1px solid #263242 !important;
    border-left: 3px solid #478cbf !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    margin-block: 3px !important;
}}

.tabbrowser-tab .tab-background:is([selected], [multiselected]) {{
    background-color: #161b22 !important;
    border: 1px solid #478cbf !important;
    border-top: 2px solid #63d994 !important;
    border-left: 3px solid #63d994 !important;
    outline: none !important;
}}

#urlbar-background, .urlbar-background, #searchbar {{
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-left: 3px solid #63d994 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}}
"""

USER_CONTENT = f"""/* GameDev Engine Studio — Firefox NewTab Viewport */
@-moz-document url("about:newtab"), url("about:home"), url("about:blank"), url("about:privatebrowsing") {{
    html, body {{
        background-color: #0d1117 !important;
        background-image: url("data:image/svg+xml;base64,{NT_B64}") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
        color: #e6edf3 !important;
    }}
    .outer-wrapper {{ background: transparent !important; }}
    .search-wrapper .search-handoff-button, .search-wrapper input {{
        background-color: rgba(18, 23, 30, 0.95) !important;
        border: 1px solid #478cbf !important;
        border-left: 4px solid #63d994 !important;
        border-radius: 6px !important;
        color: #e6edf3 !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55) !important;
    }}
    .top-site-outer .tile {{
        background-color: rgba(22, 27, 34, 0.94) !important;
        border: 1px solid #30363d !important;
        border-top: 2px solid #478cbf !important;
        border-radius: 6px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45) !important;
    }}
    .top-site-outer:hover .tile {{
        background-color: #1f2937 !important;
        border-color: #63d994 !important;
        border-top: 2px solid #63d994 !important;
    }}
    .top-site-outer .title span {{ color: #e6edf3 !important; font-family: monospace !important; font-weight: bold !important; }}
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
