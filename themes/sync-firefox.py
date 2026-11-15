#!/usr/bin/python3
import os, sys, glob, base64, configparser

HOME = os.path.expanduser("~")

# Верхняя панель Firefox в стиле тулбара игрового движка (координатная линейка, сетка 16px, оси X/Y)
TABBAR_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
  <defs>
    <linearGradient id="tbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#121316"/>
      <stop offset="100%" stop-color="#181a1f"/>
    </linearGradient>
    <pattern id="g16" width="16" height="16" patternUnits="userSpaceOnUse">
      <path d="M 16 0 L 0 0 0 16" fill="none" stroke="#454a52" stroke-width="0.5" stroke-opacity="0.09"/>
    </pattern>
    <pattern id="Ruler" width="64" height="12" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="0" y2="7" stroke="#454a52" stroke-width="1.2" stroke-opacity="0.45"/>
      <line x1="16" y1="0" x2="16" y2="4" stroke="#454a52" stroke-width="0.8" stroke-opacity="0.25"/>
      <line x1="32" y1="0" x2="32" y2="5" stroke="#454a52" stroke-width="0.8" stroke-opacity="0.35"/>
      <line x1="48" y1="0" x2="48" y2="4" stroke="#454a52" stroke-width="0.8" stroke-opacity="0.25"/>
    </pattern>
  </defs>
  <rect width="1920" height="96" fill="url(#tbg)"/>
  <rect width="1920" height="96" fill="url(#g16)"/>
  <rect width="1920" height="12" fill="url(#Ruler)"/>

  <line x1="0" y1="1" x2="1920" y2="1" stroke="#454a52" stroke-width="1.5" stroke-opacity="0.65"/>
  <path d="M 8 28 L 8 5 L 36 5" fill="none" stroke="#8c939e" stroke-width="2" stroke-opacity="0.85"/>
  <path d="M 1912 28 L 1912 5 L 1884 5" fill="none" stroke="#454a52" stroke-width="2" stroke-opacity="0.85"/>

  <g stroke="#454a52" stroke-width="1.3" stroke-opacity="0.35" fill="none">
    <polyline points="54,7 210,7 224,20 420,20"/>
    <polyline points="1320,20 1510,20 1526,8 1680,8"/>
  </g>
  <circle cx="54" cy="7" r="2.5" fill="#8c939e"/>
  <circle cx="420" cy="20" r="2.5" fill="#454a52"/>
  <circle cx="1680" cy="8" r="2.5" fill="#8c939e"/>
  <text x="1700" y="16" font-family="monospace" font-size="9.5" font-weight="bold" fill="#8c939e" fill-opacity="0.78">🎮 ENGINE // WEB_VIEWPORT 4.3</text>
</svg>"""

# Главная страница Firefox в стиле 2D/3D Viewport среды разработки игр
NEWTAB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#121316"/>
      <stop offset="50%" stop-color="#121316"/>
      <stop offset="100%" stop-color="#101114"/>
    </linearGradient>
    <radialGradient id="vpGlow" cx="50%" cy="48%" r="45%">
      <stop offset="0%" stop-color="#454a52" stop-opacity="0.15"/>
      <stop offset="55%" stop-color="#8c939e" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#121316" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid32" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#454a52" stroke-width="0.6" stroke-opacity="0.06"/>
    </pattern>
    <pattern id="grid128" width="128" height="128" patternUnits="userSpaceOnUse">
      <path d="M 128 0 L 0 0 0 128" fill="none" stroke="#454a52" stroke-width="1.1" stroke-opacity="0.14"/>
      <path d="M 123 128 L 133 128 M 128 123 L 128 133" stroke="#8c939e" stroke-width="1.3" stroke-opacity="0.42"/>
    </pattern>
  </defs>

  <rect width="1920" height="1080" fill="url(#bg)"/>
  <rect width="1920" height="1080" fill="url(#vpGlow)"/>
  <rect width="1920" height="1080" fill="url(#grid32)"/>
  <rect width="1920" height="1080" fill="url(#grid128)"/>

  <!-- Мировые оси координат X (Red) и Y (Green) -->
  <line x1="0" y1="540" x2="1920" y2="540" stroke="#5c626d" stroke-width="1.5" stroke-opacity="0.38"/>
  <line x1="960" y1="0" x2="960" y2="1080" stroke="#8c939e" stroke-width="1.5" stroke-opacity="0.38"/>

  <!-- Рамка Camera2D и центральный Gizmo-компас -->
  <rect x="340" y="150" width="1240" height="760" fill="none" stroke="#454a52" stroke-width="1.6" stroke-opacity="0.38" stroke-dasharray="10 6"/>
  <g transform="translate(960, 540)">
    <circle r="310" fill="none" stroke="#454a52" stroke-width="1.2" stroke-opacity="0.24"/>
    <circle r="240" fill="none" stroke="#8c939e" stroke-width="1.4" stroke-opacity="0.22" stroke-dasharray="6 4"/>
    <path d="M -325 -55 A 330 330 0 0 1 -230 -235" fill="none" stroke="#8c939e" stroke-width="3" stroke-opacity="0.6"/>
    <path d="M 325 -55 A 330 330 0 0 0 230 -235" fill="none" stroke="#454a52" stroke-width="3" stroke-opacity="0.6"/>
    <path d="M -325 55 A 330 330 0 0 0 -230 235" fill="none" stroke="#454a52" stroke-width="3" stroke-opacity="0.6"/>
    <path d="M 325 55 A 330 330 0 0 1 230 235" fill="none" stroke="#8c939e" stroke-width="3" stroke-opacity="0.6"/>
  </g>

  <!-- Левая панель SceneTree // Engine Nodes -->
  <g transform="translate(46, 350)">
    <rect width="265" height="230" rx="6" fill="#181a1f" fill-opacity="0.92" stroke="#2e3238" stroke-width="1.5"/>
    <rect x="0" y="0" width="265" height="3" fill="#454a52"/>
    <text x="16" y="30" font-family="monospace" font-size="11" font-weight="bold" fill="#8c939e">📂 SceneTree // WebViewport</text>
    <line x1="16" y1="42" x2="249" y2="42" stroke="#2b2e35" stroke-width="1"/>
    <text x="16" y="70" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">├─ 🎮 Root_Viewport <tspan fill="#9ea4b0">[2D]</tspan></text>
    <text x="16" y="100" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">├─ ⚡ WebRender_GPU <tspan fill="#8c939e">[ON]</tspan></text>
    <text x="16" y="130" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">├─ 🐍 Python_Runtime <tspan fill="#9ea4b0">[3.14]</tspan></text>
    <text x="16" y="160" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">└─ 🛡 Wayland_Socket <tspan fill="#8c939e">[OK]</tspan></text>
    <rect x="16" y="190" width="233" height="8" rx="3" fill="#1e2025" stroke="#2e3238" stroke-width="1"/>
    <rect x="17" y="191" width="195" height="6" rx="2" fill="#8c939e"/>
  </g>

  <!-- Правая панель Inspector // Frame Profiler -->
  <g transform="translate(1609, 350)">
    <rect width="265" height="230" rx="6" fill="#181a1f" fill-opacity="0.92" stroke="#2e3238" stroke-width="1.5"/>
    <rect x="0" y="0" width="265" height="3" fill="#8c939e"/>
    <text x="16" y="30" font-family="monospace" font-size="11" font-weight="bold" fill="#9ea4b0">🔍 Inspector // Profiler</text>
    <line x1="16" y1="42" x2="249" y2="42" stroke="#2b2e35" stroke-width="1"/>
    <text x="16" y="70" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">FRAME_TIME // <tspan fill="#8c939e">4.1 ms</tspan></text>
    <text x="16" y="100" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">RENDER_API // <tspan fill="#9ea4b0">VULKAN DRM</tspan></text>
    <text x="16" y="130" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">SHADER_CACHE // <tspan fill="#8c939e">10 GB</tspan></text>
    <text x="16" y="160" font-family="monospace" font-size="10.5" font-weight="bold" fill="#8b949e">OPERATOR   // <tspan fill="#e6edf3">ssOh-v1</tspan></text>
    <rect x="16" y="190" width="233" height="8" rx="3" fill="#1e2025" stroke="#2e3238" stroke-width="1"/>
    <rect x="17" y="191" width="210" height="6" rx="2" fill="#454a52"/>
  </g>

  <text x="960" y="28" text-anchor="middle" font-family="monospace" font-size="11" font-weight="bold" fill="#9ea4b0">🎮 GAMEDEV ENGINE STUDIO   •   VIEWPORT_2D [1920x1080]   •   X/Y GIZMO ACTIVE</text>
</svg>"""

TAB_B64 = base64.b64encode(TABBAR_SVG.encode("utf-8")).decode("ascii")
NT_B64  = base64.b64encode(NEWTAB_SVG.encode("utf-8")).decode("ascii")

USER_CHROME = f"""/* GameDev Engine Studio — Firefox IDE Theme */
:root, #main-window, #navigator-toolbox {{
    --lwt-accent-color: #121316 !important;
    --toolbox-bgcolor: #121316 !important;
    --toolbar-bgcolor: transparent !important;
    --toolbar-color: #e6edf3 !important;
    --lwt-text-color: #e6edf3 !important;
    --tab-selected-bgcolor: #1e2025 !important;
    --tab-selected-textcolor: #ffffff !important;
    --tab-loading-fill: #8c939e !important;
    --urlbar-box-bgcolor: #121316 !important;
    --urlbar-box-focus-bgcolor: #121820 !important;
    --toolbar-field-background-color: #121316 !important;
    --toolbar-field-color: #e6edf3 !important;
    --toolbar-field-border-color: #2e3238 !important;
    --toolbar-field-focus-background-color: #121820 !important;
    --toolbar-field-focus-color: #ffffff !important;
    --toolbar-field-focus-border-color: #8c939e !important;
    --tab-border-radius: 6px !important;
}}

#navigator-toolbox {{
    background-color: #121316 !important;
    background-image:
        linear-gradient(90deg, transparent 0%, #454a52 25%, #8c939e 50%, #454a52 75%, transparent 100%),
        url("data:image/svg+xml;base64,{TAB_B64}") !important;
    background-size: 100% 2px, 1920px 96px !important;
    background-position: bottom center, top left !important;
    background-repeat: no-repeat, repeat-x !important;
    border-bottom: 1px solid #2e3238 !important;
}}

#TabsToolbar, #titlebar {{ background: transparent !important; padding: 3px 6px !important; }}
#nav-bar {{ background-color: rgba(13, 17, 23, 0.90) !important; border-top: 1px solid #2b2e35 !important; box-shadow: none !important; padding: 3px 8px !important; }}

/* Вкладки в стиле открытых скриптов игрового движка */
.tabbrowser-tab .tab-background {{
    background-color: rgba(18, 23, 30, 0.82) !important;
    border: 1px solid #2b2e35 !important;
    border-left: 3px solid #454a52 !important;
    border-radius: 6px !important;
    box-shadow: none !important;
    margin-block: 3px !important;
}}

.tabbrowser-tab .tab-background:is([selected], [multiselected]) {{
    background-color: #1e2025 !important;
    border: 1px solid #454a52 !important;
    border-top: 2px solid #8c939e !important;
    border-left: 3px solid #8c939e !important;
    outline: none !important;
}}

#urlbar-background, .urlbar-background, #searchbar {{
    background-color: #121316 !important;
    border: 1px solid #2e3238 !important;
    border-left: 3px solid #8c939e !important;
    border-radius: 6px !important;
    box-shadow: none !important;
}}
"""

USER_CONTENT = f"""/* GameDev Engine Studio — Firefox NewTab Viewport */
@-moz-document url("about:newtab"), url("about:home"), url("about:blank"), url("about:privatebrowsing") {{
    html, body {{
        background-color: #121316 !important;
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
        border: 1px solid #454a52 !important;
        border-left: 4px solid #8c939e !important;
        border-radius: 6px !important;
        color: #e6edf3 !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55) !important;
    }}
    .top-site-outer .tile {{
        background-color: rgba(22, 27, 34, 0.94) !important;
        border: 1px solid #2e3238 !important;
        border-top: 2px solid #454a52 !important;
        border-radius: 6px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45) !important;
    }}
    .top-site-outer:hover .tile {{
        background-color: #262930 !important;
        border-color: #8c939e !important;
        border-top: 2px solid #8c939e !important;
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
