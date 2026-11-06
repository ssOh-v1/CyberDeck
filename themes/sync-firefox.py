#!/usr/bin/env python3
import os, sys, glob, base64, configparser

HOME = os.path.expanduser("~")

# Векторное HUD-полотно для верхней панели и панели вкладок (сетка, шевроны, дорожки платы, сканер)
TABBAR_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="96" viewBox="0 0 1920 96">
  <defs>
    <linearGradient id="tbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#05070d"/>
      <stop offset="100%" stop-color="#0a0f1c"/>
    </linearGradient>
    <pattern id="tgrid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#4c6ef5" stroke-width="0.6" stroke-opacity="0.08"/>
    </pattern>
  </defs>
  <rect width="1920" height="96" fill="url(#tbg)"/>
  <rect width="1920" height="96" fill="url(#tgrid)"/>

  <!-- Верхняя неоновая рельса и угловые скобы шапки -->
  <line x1="0" y1="1" x2="1920" y2="1" stroke="#22b8cf" stroke-width="1.5" stroke-opacity="0.55"/>
  <path d="M 8 26 L 8 5 L 36 5" fill="none" stroke="#22b8cf" stroke-width="2" stroke-opacity="0.85"/>
  <path d="M 1912 26 L 1912 5 L 1884 5" fill="none" stroke="#22b8cf" stroke-width="2" stroke-opacity="0.85"/>

  <!-- Схемотехнические дорожки вдоль панели вкладок -->
  <g stroke="#4c6ef5" stroke-width="1.3" stroke-opacity="0.32" fill="none">
    <polyline points="48,6 190,6 206,20 390,20"/>
    <polyline points="620,8 760,8 776,22 980,22 996,8 1180,8"/>
    <polyline points="1360,20 1540,20 1558,7 1740,7"/>
  </g>
  <g fill="#22b8cf" fill-opacity="0.65">
    <circle cx="48" cy="6" r="2.5"/><circle cx="390" cy="20" r="2.5"/>
    <circle cx="620" cy="8" r="2.5"/><circle cx="1180" cy="8" r="2.5"/>
    <circle cx="1360" cy="20" r="2.5"/><circle cx="1740" cy="7" r="2.5"/>
  </g>

  <!-- Тактические шевроны на правом и левом крыле шапки -->
  <g stroke="#22b8cf" stroke-width="2" stroke-opacity="0.38">
    <line x1="1620" y1="6" x2="1612" y2="18"/><line x1="1630" y1="6" x2="1622" y2="18"/>
    <line x1="1640" y1="6" x2="1632" y2="18"/><line x1="1650" y1="6" x2="1642" y2="18"/>
    <line x1="1660" y1="6" x2="1652" y2="18"/><line x1="1670" y1="6" x2="1662" y2="18"/>
    <line x1="1680" y1="6" x2="1672" y2="18"/><line x1="1690" y1="6" x2="1682" y2="18"/>
  </g>
  <text x="1705" y="16" font-family="Noto Sans, monospace" font-size="9" font-weight="bold" fill="#66d9e8" fill-opacity="0.55">◈ DECK.WEB // HUD_V2</text>
</svg>"""

# Полноэкранное векторное HUD-полотно для главной страницы / новой вкладки (радар, крылья телеметрии, соты, рельсы)
NEWTAB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#06080f"/>
      <stop offset="50%" stop-color="#090d18"/>
      <stop offset="100%" stop-color="#05070c"/>
    </linearGradient>
    <radialGradient id="glowC" cx="50%" cy="46%" r="42%">
      <stop offset="0%" stop-color="#22b8cf" stop-opacity="0.13"/>
      <stop offset="55%" stop-color="#4c6ef5" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#07090f" stop-opacity="0"/>
    </radialGradient>
    <pattern id="fineGrid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#4c6ef5" stroke-width="0.5" stroke-opacity="0.05"/>
    </pattern>
    <pattern id="majGrid" width="96" height="96" patternUnits="userSpaceOnUse">
      <path d="M 96 0 L 0 0 0 96" fill="none" stroke="#4c6ef5" stroke-width="1" stroke-opacity="0.11"/>
      <path d="M 92 96 L 100 96 M 96 92 L 96 100" stroke="#22b8cf" stroke-width="1.2" stroke-opacity="0.32"/>
    </pattern>
  </defs>

  <rect width="1920" height="1080" fill="url(#bg)"/>
  <rect width="1920" height="1080" fill="url(#glowC)"/>
  <rect width="1920" height="1080" fill="url(#fineGrid)"/>
  <rect width="1920" height="1080" fill="url(#majGrid)"/>

  <!-- Верхняя и нижняя тактические рельсы -->
  <rect x="0" y="0" width="1920" height="38" fill="#080c17" fill-opacity="0.9"/>
  <rect x="0" y="1042" width="1920" height="38" fill="#080c17" fill-opacity="0.9"/>
  <line x1="0" y1="38" x2="1920" y2="38" stroke="#24355a" stroke-width="1.5"/>
  <line x1="0" y1="1042" x2="1920" y2="1042" stroke="#24355a" stroke-width="1.5"/>

  <!-- Двойные периметральные HUD-скобы -->
  <g fill="none" stroke="#4c6ef5" stroke-width="2.5" stroke-opacity="0.8">
    <path d="M 20 108 L 20 52 L 82 52"/><path d="M 1900 108 L 1900 52 L 1838 52"/>
    <path d="M 20 972 L 20 1028 L 82 1028"/><path d="M 1900 972 L 1900 1028 L 1838 1028"/>
  </g>
  <g fill="none" stroke="#22b8cf" stroke-width="1.8" stroke-opacity="0.75">
    <path d="M 30 92 L 30 62 L 64 62"/><path d="M 1890 92 L 1890 62 L 1856 62"/>
    <path d="M 30 988 L 30 1018 L 64 1018"/><path d="M 1890 988 L 1890 1018 L 1856 1018"/>
  </g>

  <!-- Центральный орбитальный радарный комплекс -->
  <g transform="translate(960, 500)">
    <circle r="350" fill="none" stroke="#4c6ef5" stroke-width="1" stroke-opacity="0.22" stroke-dasharray="8 6"/>
    <circle r="290" fill="none" stroke="#22b8cf" stroke-width="1.4" stroke-opacity="0.24"/>
    <circle r="210" fill="none" stroke="#4c6ef5" stroke-width="1.2" stroke-opacity="0.18"/>
    <path d="M -368 -60 A 372 372 0 0 1 -260 -268" fill="none" stroke="#22b8cf" stroke-width="3" stroke-opacity="0.55"/>
    <path d="M 368 -60 A 372 372 0 0 0 260 -268" fill="none" stroke="#22b8cf" stroke-width="3" stroke-opacity="0.55"/>
    <path d="M -368 60 A 372 372 0 0 0 -260 268" fill="none" stroke="#4c6ef5" stroke-width="3" stroke-opacity="0.55"/>
    <path d="M 368 60 A 372 372 0 0 1 260 268" fill="none" stroke="#4c6ef5" stroke-width="3" stroke-opacity="0.55"/>
    <line x1="-430" y1="0" x2="-310" y2="0" stroke="#22b8cf" stroke-width="1.5" stroke-opacity="0.4"/>
    <line x1="310" y1="0" x2="430" y2="0" stroke="#22b8cf" stroke-width="1.5" stroke-opacity="0.4"/>
  </g>

  <!-- Схемотехнические шины от краёв экрана -->
  <g fill="none" stroke="#4c6ef5" stroke-width="1.8" stroke-opacity="0.32">
    <polyline points="20,210 110,210 150,250 340,250"/>
    <polyline points="20,830 120,830 165,785 350,785"/>
    <polyline points="1900,210 1810,210 1770,250 1580,250"/>
    <polyline points="1900,830 1800,830 1755,785 1570,785"/>
  </g>
  <g fill="#22b8cf" fill-opacity="0.7">
    <circle cx="340" cy="250" r="4"/><circle cx="350" cy="785" r="4"/>
    <circle cx="1580" cy="250" r="4"/><circle cx="1570" cy="785" r="4"/>
  </g>

  <!-- Левое тактическое крыло телеметрии -->
  <g transform="translate(56, 370)">
    <rect width="275" height="220" rx="12" fill="#090e1b" fill-opacity="0.88" stroke="#223254" stroke-width="1.5"/>
    <rect x="0" y="18" width="3.5" height="32" fill="#22b8cf"/>
    <text x="18" y="34" font-family="Noto Sans, sans-serif" font-size="11" font-weight="bold" fill="#e5ecff">◈ WEB.TELEMETRY // NODE_01</text>
    <line x1="18" y1="48" x2="257" y2="48" stroke="#1d2b4a" stroke-width="1"/>
    <text x="18" y="76" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">ENGINE     // <tspan fill="#66d9e8">GECKO WAYLAND</tspan></text>
    <text x="18" y="108" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">RENDER     // <tspan fill="#91a7ff">WEBRENDER GPU</tspan></text>
    <text x="18" y="140" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">PROTOCOL   // <tspan fill="#63e6be">TLS 1.3 SECURE</tspan></text>
    <text x="18" y="172" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">DESIGN     // <tspan fill="#e5ecff">CYBERDECK HUD</tspan></text>
    <rect x="18" y="192" width="239" height="6" rx="3" fill="#131d33"/>
    <rect x="18" y="192" width="186" height="6" rx="3" fill="#22b8cf"/>
  </g>

  <!-- Правое тактическое крыло окружения -->
  <g transform="translate(1589, 370)">
    <rect width="275" height="220" rx="12" fill="#090e1b" fill-opacity="0.88" stroke="#223254" stroke-width="1.5"/>
    <rect x="271.5" y="18" width="3.5" height="32" fill="#4c6ef5"/>
    <text x="18" y="34" font-family="Noto Sans, sans-serif" font-size="11" font-weight="bold" fill="#e5ecff">◈ DECK.MATRIX // SYNCED</text>
    <line x1="18" y1="48" x2="257" y2="48" stroke="#1d2b4a" stroke-width="1"/>
    <text x="18" y="76" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">COMPOSITOR // <tspan fill="#91a7ff">HYPRLAND DRM</tspan></text>
    <text x="18" y="108" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">WORKSPACES // <tspan fill="#66d9e8">FREE-WS ∞</tspan></text>
    <text x="18" y="140" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">CURSOR     // <tspan fill="#63e6be">CYBER 28PX</tspan></text>
    <text x="18" y="172" font-family="Noto Sans, monospace" font-size="10.5" font-weight="bold" fill="#6b7c9e">STATUS     // <tspan fill="#e5ecff">OPERATIONAL</tspan></text>
    <rect x="18" y="192" width="239" height="6" rx="3" fill="#131d33"/>
    <rect x="18" y="192" width="215" height="6" rx="3" fill="#4c6ef5"/>
  </g>

  <!-- Гексагональные кластеры по углам -->
  <g fill="none" stroke="#22b8cf" stroke-width="1.2" stroke-opacity="0.22">
    <polygon points="120,120 142,132 142,158 120,170 98,158 98,132"/>
    <polygon points="164,120 186,132 186,158 164,170 142,158 142,132"/>
    <polygon points="142,158 164,170 164,196 142,208 120,196 120,170"/>
    <polygon points="1756,870 1778,882 1778,908 1756,920 1734,908 1734,882"/>
    <polygon points="1800,870 1822,882 1822,908 1800,920 1778,908 1778,882"/>
  </g>

  <text x="960" y="24" text-anchor="middle" font-family="Noto Sans, monospace" font-size="11" font-weight="bold" fill="#66d9e8" fill-opacity="0.85">◈ CYBER DECK // NEURAL WEB GATEWAY   •   HYPRLAND WAYLAND ENGINE</text>
  <text x="960" y="1065" text-anchor="middle" font-family="Noto Sans, monospace" font-size="10" font-weight="bold" fill="#6b7c9e" fill-opacity="0.75">SYS.GRID // 96PX   •   HUD OVERLAY ACTIVE   •   ZERO TELEMETRY LEAK</text>
</svg>"""

TAB_B64 = base64.b64encode(TABBAR_SVG.encode("utf-8")).decode("ascii")
NT_B64 = base64.b64encode(NEWTAB_SVG.encode("utf-8")).decode("ascii")

USER_CHROME = f"""/* CyberDeck — Heavy HUD Firefox TabBar & Navigation Deck */
:root, #main-window, #navigator-toolbox {{
    --lwt-accent-color: #060911 !important;
    --lwt-accent-color-inactive: #060911 !important;
    --toolbox-bgcolor: #060911 !important;
    --toolbox-bgcolor-inactive: #060911 !important;
    --toolbar-bgcolor: transparent !important;
    --toolbar-color: #dce3f5 !important;
    --lwt-text-color: #dce3f5 !important;
    --tab-selected-bgcolor: #121d36 !important;
    --tab-selected-textcolor: #f0f4ff !important;
    --tab-loading-fill: #22b8cf !important;
    --urlbar-box-bgcolor: #0a101f !important;
    --urlbar-box-focus-bgcolor: #0f182e !important;
    --urlbar-box-hover-bgcolor: #0f182e !important;
    --toolbar-field-background-color: #0a101f !important;
    --toolbar-field-color: #e5ecff !important;
    --toolbar-field-border-color: #26385e !important;
    --toolbar-field-focus-background-color: #0f182e !important;
    --toolbar-field-focus-color: #f0f4ff !important;
    --toolbar-field-focus-border-color: #22b8cf !important;
    --arrowpanel-background: #0b101d !important;
    --arrowpanel-color: #dce3f5 !important;
    --arrowpanel-border-color: #283a61 !important;
    --tab-border-radius: 8px !important;
}}

/* Полноценное HUD-полотно на шапке браузера и панели вкладок */
#navigator-toolbox {{
    background-color: #060911 !important;
    background-image:
        linear-gradient(90deg, transparent 0%, #4c6ef5 20%, #22b8cf 50%, #4c6ef5 80%, transparent 100%),
        url("data:image/svg+xml;base64,{TAB_B64}") !important;
    background-size: 100% 2px, 1920px 96px !important;
    background-position: bottom center, top left !important;
    background-repeat: no-repeat, repeat-x !important;
    border-bottom: 1px solid #1e2d4d !important;
}}

#TabsToolbar, #titlebar {{
    background: transparent !important;
    padding: 3px 6px 2px 6px !important;
}}

#nav-bar {{
    background-color: rgba(8, 12, 23, 0.86) !important;
    border-top: 1px solid rgba(76, 110, 245, 0.24) !important;
    box-shadow: none !important;
    padding: 3px 8px !important;
}}

#PersonalToolbar {{
    background-color: rgba(7, 10, 18, 0.94) !important;
    border-top: 1px solid rgba(34, 184, 207, 0.16) !important;
}}

/* Неактивные вкладки — тактические бронекапсулы */
.tabbrowser-tab .tab-background {{
    background-color: rgba(12, 18, 32, 0.78) !important;
    border: 1px solid #1f2d4a !important;
    border-left: 2px solid #364fc7 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    margin-block: 3px !important;
}}

.tabbrowser-tab:hover:not([selected]) .tab-background {{
    background-color: rgba(18, 27, 48, 0.92) !important;
    border-color: #4c6ef5 !important;
}}

/* Активная вкладка — 4 угловые HUD-скобы + верхний неоновый сканер */
.tabbrowser-tab .tab-background:is([selected], [multiselected]) {{
    background-color: #121e38 !important;
    background-image:
        linear-gradient(90deg, transparent 12%, #22b8cf 50%, transparent 88%),
        linear-gradient(#22b8cf, #22b8cf), linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#22b8cf, #22b8cf), linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#4c6ef5, #4c6ef5), linear-gradient(#4c6ef5, #4c6ef5),
        linear-gradient(#4c6ef5, #4c6ef5), linear-gradient(#4c6ef5, #4c6ef5),
        repeating-linear-gradient(-45deg, rgba(34, 184, 207, 0.05) 0px, rgba(34, 184, 207, 0.05) 2px, transparent 2px, transparent 8px) !important;
    background-repeat: no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, repeat !important;
    background-size: 76% 2px, 11px 2px, 2px 11px, 11px 2px, 2px 11px, 11px 2px, 2px 11px, 11px 2px, 2px 11px, 100% 100% !important;
    background-position: top center, top left, top left, top right, top right, bottom left, bottom left, bottom right, bottom right, center !important;
    border: 1px solid #36528c !important;
    outline: none !important;
}}

#tabs-newtab-button, #new-tab-button {{
    background-color: rgba(15, 23, 42, 0.88) !important;
    border: 1px solid #28426b !important;
    border-radius: 8px !important;
    margin: 4px 4px !important;
    color: #66d9e8 !important;
}}
#tabs-newtab-button:hover, #new-tab-button:hover {{
    background-color: #182949 !important;
    border-color: #22b8cf !important;
}}

/* Строка адреса с прицельными скобами */
#urlbar-background, .urlbar-background, #searchbar {{
    background-color: #0a101f !important;
    background-image:
        linear-gradient(#22b8cf, #22b8cf), linear-gradient(#22b8cf, #22b8cf),
        linear-gradient(#4c6ef5, #4c6ef5), linear-gradient(#4c6ef5, #4c6ef5) !important;
    background-repeat: no-repeat !important;
    background-size: 10px 2px, 2px 10px, 10px 2px, 2px 10px !important;
    background-position: top left, top left, bottom right, bottom right !important;
    border: 1px solid #243558 !important;
    border-left: 3px solid #22b8cf !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}}

#urlbar:is([focused="true"], [focused], [open]) > :is(#urlbar-background, .urlbar-background) {{
    background-color: #0f182e !important;
    border-color: #22b8cf !important;
    outline: none !important;
}}
"""

USER_CONTENT = f"""/* CyberDeck — Heavy HUD Firefox NewTab & Home Matrix */
@-moz-document url("about:newtab"), url("about:home"), url("about:blank"), url("about:privatebrowsing") {{
    html, body {{
        background-color: #07090f !important;
        background-image: url("data:image/svg+xml;base64,{NT_B64}") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
        color: #e5ecff !important;
    }}

    .outer-wrapper {{
        background: transparent !important;
    }}

    /* Поисковый модуль по центру радара */
    .search-wrapper .search-handoff-button,
    .search-wrapper input {{
        background-color: rgba(10, 16, 31, 0.94) !important;
        background-image:
            linear-gradient(#22b8cf, #22b8cf), linear-gradient(#22b8cf, #22b8cf),
            linear-gradient(#4c6ef5, #4c6ef5), linear-gradient(#4c6ef5, #4c6ef5) !important;
        background-repeat: no-repeat !important;
        background-size: 14px 2px, 2px 14px, 14px 2px, 2px 14px !important;
        background-position: top left, top left, bottom right, bottom right !important;
        border: 1px solid #2d4473 !important;
        border-left: 4px solid #22b8cf !important;
        border-radius: 11px !important;
        color: #f0f4ff !important;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.55) !important;
    }}

    /* Карточки сайтов в стиле карточек CyberDeck Hub */
    .top-site-outer .tile {{
        background-color: rgba(11, 17, 32, 0.93) !important;
        border: 1px solid #243558 !important;
        border-top: 2px solid #4c6ef5 !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.45) !important;
    }}

    .top-site-outer:hover .tile {{
        background-color: rgba(18, 28, 52, 0.98) !important;
        border-color: #22b8cf !important;
        border-top: 2px solid #22b8cf !important;
    }}

    .top-site-outer .title span {{
        color: #dce3f5 !important;
        font-weight: 600 !important;
    }}
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

if len(sys.argv) > 2 and sys.argv[1] == "--profile":
    target_p = sys.argv[2]
    os.makedirs(target_p, exist_ok=True)
    apply_to_profile(target_p)
    sys.exit(0)

prof_dirs = set()
for r in [
    os.path.join(HOME, ".config/mozilla/firefox"),
    os.path.join(HOME, ".mozilla/firefox"),
    os.path.join(HOME, ".var/app/org.mozilla.firefox/.mozilla/firefox"),
    os.path.join(HOME, ".var/app/org.mozilla.firefox/config/mozilla/firefox"),
    os.path.join(HOME, ".librewolf"),
    os.path.join(HOME, ".zen"),
]:
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

for pd in sorted(prof_dirs):
    apply_to_profile(pd)
    print("HUD-декорации Firefox обновлены в:", pd)
