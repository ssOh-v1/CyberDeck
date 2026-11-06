#!/usr/bin/env python3
import os, re, glob, shutil, subprocess

HOME = os.path.expanduser("~")
THEME_ROOT = os.path.join(HOME, ".local/share/icons/CyberDeck-Icons")
APPS_DIR = os.path.join(THEME_ROOT, "scalable", "apps")
os.makedirs(APPS_DIR, exist_ok=True)

with open(os.path.join(THEME_ROOT, "index.theme"), "w", encoding="utf-8") as f:
    f.write("""[Icon Theme]
Name=CyberDeck-Icons
Comment=Cyber HUD Vector App Icons
Inherits=Papirus-Dark,Adwaita,hicolor
Directories=scalable/apps

[scalable/apps]
Size=64
Type=Scalable
MinSize=16
MaxSize=512
Context=Applications
""")

GLYPHS = {
    "terminal": """
      <rect x="15" y="18" width="34" height="28" rx="5" fill="#10182b" stroke="#4c6ef5" stroke-width="2.2"/>
      <path d="M22 27 L28 32 L22 37" fill="none" stroke="#22b8cf" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="31" y1="37" x2="40" y2="37" stroke="#e5ecff" stroke-width="2.8" stroke-linecap="round"/>
    """,
    "browser": """
      <circle cx="32" cy="32" r="15" fill="#10182b" stroke="#4c6ef5" stroke-width="2.2"/>
      <ellipse cx="32" cy="32" rx="7" ry="15" fill="none" stroke="#22b8cf" stroke-width="1.8"/>
      <line x1="17" y1="32" x2="47" y2="32" stroke="#22b8cf" stroke-width="1.8"/>
      <circle cx="39" cy="24" r="3" fill="#e5ecff"/>
    """,
    "firefox": """
      <circle cx="32" cy="32" r="15" fill="#111a2e" stroke="#4c6ef5" stroke-width="2.2"/>
      <path d="M24 39 C20 31, 25 20, 35 21 C41 22, 45 28, 42 36 C39 42, 29 44, 24 39 Z" fill="none" stroke="#22b8cf" stroke-width="2.5"/>
      <path d="M31 27 L39 24 L36 33 Z" fill="#4c6ef5"/>
    """,
    "code": """
      <path d="M25 23 L16 32 L25 41" fill="none" stroke="#22b8cf" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M39 23 L48 32 L39 41" fill="none" stroke="#22b8cf" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="35" y1="20" x2="29" y2="44" stroke="#4c6ef5" stroke-width="2.6" stroke-linecap="round"/>
    """,
    "steam": """
      <circle cx="38" cy="26" r="7" fill="#10182b" stroke="#22b8cf" stroke-width="2.4"/>
      <circle cx="38" cy="26" r="2.6" fill="#e5ecff"/>
      <circle cx="24" cy="39" r="5.5" fill="#10182b" stroke="#4c6ef5" stroke-width="2.4"/>
      <line x1="28" y1="36" x2="34" y2="30" stroke="#e5ecff" stroke-width="3.2" stroke-linecap="round"/>
    """,
    "game": """
      <rect x="15" y="22" width="34" height="20" rx="9" fill="#10182b" stroke="#4c6ef5" stroke-width="2.2"/>
      <path d="M24 28 V36 M20 32 H28" stroke="#22b8cf" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="39" cy="29" r="2" fill="#22b8cf"/>
      <circle cx="43" cy="33" r="2" fill="#e5ecff"/>
    """,
    "cs2": """
      <circle cx="32" cy="32" r="14" fill="#10182b" stroke="#22b8cf" stroke-width="2.2"/>
      <line x1="32" y1="14" x2="32" y2="23" stroke="#e5ecff" stroke-width="2.2"/>
      <line x1="32" y1="41" x2="32" y2="50" stroke="#e5ecff" stroke-width="2.2"/>
      <line x1="14" y1="32" x2="23" y2="32" stroke="#e5ecff" stroke-width="2.2"/>
      <line x1="41" y1="32" x2="50" y2="32" stroke="#e5ecff" stroke-width="2.2"/>
      <circle cx="32" cy="32" r="2.5" fill="#4c6ef5"/>
    """,
    "discord": """
      <rect x="16" y="20" width="32" height="24" rx="8" fill="#10182b" stroke="#4c6ef5" stroke-width="2.2"/>
      <circle cx="26" cy="31" r="3" fill="#22b8cf"/>
      <circle cx="38" cy="31" r="3" fill="#22b8cf"/>
      <path d="M25 38 Q32 41 39 38" fill="none" stroke="#e5ecff" stroke-width="2" stroke-linecap="round"/>
    """,
    "chat": """
      <path d="M17 31 L45 19 L38 45 L30 36 L23 41 L25 34 Z" fill="#10182b" stroke="#22b8cf" stroke-width="2.2" stroke-linejoin="round"/>
    """,
    "files": """
      <path d="M16 22 H27 L31 26 H48 V44 H16 Z" fill="#10182b" stroke="#4c6ef5" stroke-width="2.2" stroke-linejoin="round"/>
      <line x1="22" y1="34" x2="42" y2="34" stroke="#22b8cf" stroke-width="2.2" stroke-linecap="round"/>
    """,
    "media": """
      <circle cx="32" cy="32" r="15" fill="#10182b" stroke="#4c6ef5" stroke-width="2.2"/>
      <polygon points="28,24 41,32 28,40" fill="#22b8cf"/>
    """,
    "art": """
      <polygon points="32,17 47,26 47,38 32,47 17,38 17,26" fill="#10182b" stroke="#22b8cf" stroke-width="2.2"/>
      <circle cx="32" cy="32" r="5" fill="none" stroke="#e5ecff" stroke-width="2.0"/>
    """,
    "monitor": """
      <rect x="16" y="19" width="32" height="26" rx="5" fill="#10182b" stroke="#4c6ef5" stroke-width="2.2"/>
      <polyline points="20,35 26,35 29,26 34,40 37,31 44,31" fill="none" stroke="#22b8cf" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "settings": """
      <circle cx="32" cy="32" r="11" fill="#10182b" stroke="#4c6ef5" stroke-width="2.4"/>
      <circle cx="32" cy="32" r="4" fill="#22b8cf"/>
      <path d="M32 16 V20 M32 44 V48 M16 32 H20 M44 32 H48 M21 21 L24 24 M40 40 L43 43 M43 21 L40 24 M24 40 L21 43" stroke="#e5ecff" stroke-width="2.2" stroke-linecap="round"/>
    """,
}

def make_svg(glyph_key, monogram=""):
    if glyph_key in GLYPHS:
        inner = GLYPHS[glyph_key]
    else:
        ch = (monogram[:2] or "◈").upper()
        ch = re.sub(r"[^A-ZА-Я0-9]", "", ch) or "◈"
        inner = f"""
          <polygon points="32,17 45,24.5 45,39.5 32,47 19,39.5 19,24.5" fill="#10182b" stroke="#4c6ef5" stroke-width="2.0"/>
          <text x="32" y="36.5" text-anchor="middle" font-family="Noto Sans, sans-serif" font-weight="bold" font-size="13" fill="#66d9e8">{ch}</text>
        """
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d1323"/>
      <stop offset="100%" stop-color="#080b14"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="56" height="56" rx="14" fill="url(#bg)" stroke="#243252" stroke-width="1.8"/>
  <path d="M14 5 H23 M5 14 V23" stroke="#22b8cf" stroke-width="2.2" stroke-linecap="round"/>
  <path d="M50 59 H41 M59 50 V41" stroke="#4c6ef5" stroke-width="2.2" stroke-linecap="round"/>
  {inner}
</svg>
"""

def detect_glyph(icon_name, app_name, cats):
    blob = f"{icon_name} {app_name} {cats}".lower()
    if "firefox" in blob or "librewolf" in blob or "zen" in blob: return "firefox"
    if any(k in blob for k in ("chrom", "brave", "vivaldi", "webbrowser", "browser")): return "browser"
    if any(k in blob for k in ("kitty", "foot", "alacritty", "ghostty", "wezterm", "konsole", "terminal")): return "terminal"
    if any(k in blob for k in ("cs2", "counter-strike", "730")): return "cs2"
    if "steam" in blob: return "steam"
    if any(k in blob for k in ("discord", "vesktop", "legcord", "equibop", "webcord")): return "discord"
    if any(k in blob for k in ("telegram", "ayugram", "signal", "element", "chat", "instantmessaging")): return "chat"
    if any(k in blob for k in ("code", "vscodium", "nvim", "neovim", "jetbrains", "pycharm", "idea", "zed", "git", "godot", "python", "development", "editor")): return "code"
    if any(k in blob for k in ("thunar", "nautilus", "dolphin", "nemo", "pcmanfm", "filemanager", "folder", "files")): return "files"
    if any(k in blob for k in ("gimp", "inkscape", "krita", "blender", "aseprite", "graphics", "hyprpicker")): return "art"
    if any(k in blob for k in ("obs", "vlc", "mpv", "spotify", "amberol", "pavucontrol", "audio", "video", "multimedia")): return "media"
    if any(k in blob for k in ("btop", "htop", "missioncenter", "monitor", "system")): return "monitor"
    if any(k in blob for k in ("settings", "control", "config", "tweaks", "nwg-look", "bluetooth", "network")): return "settings"
    if "game" in blob or any(k in blob for k in ("lutris", "heroic", "prismlauncher", "retroarch", "bottles")): return "game"
    return "mono"

# Базовые системные иконки
base_map = {
    "utilities-terminal": "terminal", "kitty": "terminal", "foot": "terminal", "Alacritty": "terminal",
    "firefox": "firefox", "chromium": "browser", "brave-browser": "browser",
    "code": "code", "code-oss": "code", "vscodium": "code", "applications-development-symbolic": "code",
    "steam": "steam", "cs2": "cs2", "applications-games-symbolic": "game", "applications-games": "game",
    "discord": "discord", "vesktop": "discord", "telegram": "chat", "org.telegram.desktop": "chat",
    "btop": "monitor", "applications-system-symbolic": "settings", "system-file-manager": "files",
}
for k, g in base_map.items():
    open(os.path.join(APPS_DIR, f"{k}.svg"), "w", encoding="utf-8").write(make_svg(g, k))

# Автогенерация кастомных кибер-иконок под каждое установленное приложение в системе
for ad in ("/usr/share/applications", os.path.join(HOME, ".local/share/applications")):
    if not os.path.isdir(ad): continue
    for df in sorted(glob.glob(os.path.join(ad, "*.desktop"))):
        try:
            txt = open(df, errors="ignore").read()
            nm = re.search(r"^Name=(.*)$", txt, re.M)
            ic = re.search(r"^Icon=(.*)$", txt, re.M)
            ct = re.search(r"^Categories=(.*)$", txt, re.M)
            if not (nm and ic): continue
            app_name = nm.group(1).strip()
            icon_raw = ic.group(1).strip()
            cats = ct.group(1).strip() if ct else ""
            icon_key = os.path.splitext(os.path.basename(icon_raw))[0]
            if not icon_key or "/" in icon_key: continue
            out_svg = os.path.join(APPS_DIR, f"{icon_key}.svg")
            if not os.path.isfile(out_svg):
                gk = detect_glyph(icon_key, app_name, cats)
                words = [w for w in re.split(r"\s+", app_name) if w]
                mono = (words[0][0] + (words[1][0] if len(words) > 1 else words[0][1:2])) if words else "AP"
                open(out_svg, "w", encoding="utf-8").write(make_svg(gk if gk != "mono" else "", mono))
        except Exception:
            pass

subprocess.run(["gtk-update-icon-cache", "-f", "-t", THEME_ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
