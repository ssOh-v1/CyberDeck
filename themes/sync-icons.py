#!/usr/bin/python3
import os, re, glob, shutil, hashlib, subprocess

HOME = os.path.expanduser("~")
THEME_DIR = os.path.join(HOME, ".local/share/icons/CyberDeck-Icons")
APPS_DIR  = os.path.join(THEME_DIR, "scalable/apps")
LOCAL_APPS = os.path.join(HOME, ".local/share/applications")
os.makedirs(APPS_DIR, exist_ok=True)
os.makedirs(LOCAL_APPS, exist_ok=True)

open(os.path.join(THEME_DIR, "index.theme"), "w", encoding="utf-8").write("""[Icon Theme]
Name=CyberDeck-Icons
Comment=Studio Monochrome Grey Universal Icons
Inherits=hicolor
Directories=scalable/apps

[scalable/apps]
Size=48
Type=Scalable
MinSize=16
MaxSize=512
""")

def wrap_squircle(inner_svg):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#22252c"/>
      <stop offset="100%" stop-color="#14161a"/>
    </linearGradient>
  </defs>
  <rect x="3" y="3" width="42" height="42" rx="11" fill="url(#bg)" stroke="#3c414b" stroke-width="1.6"/>
  <rect x="5" y="5" width="38" height="38" rx="9" fill="none" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1"/>
  {inner_svg}
</svg>"""

# Векторные глифы для конкретных программ
GLYPHS = {
    "terminal": """
      <path d="M14 18 L21 24 L14 30" fill="none" stroke="#e6e9ef" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="24" y1="30" x2="34" y2="30" stroke="#9ea4b0" stroke-width="2.6" stroke-linecap="round"/>
    """,
    "browser": """
      <circle cx="24" cy="24" r="12" fill="none" stroke="#e6e9ef" stroke-width="2.2"/>
      <ellipse cx="24" cy="24" rx="5.5" ry="12" fill="none" stroke="#9ea4b0" stroke-width="1.6"/>
      <line x1="12" y1="24" x2="36" y2="24" stroke="#9ea4b0" stroke-width="1.6"/>
    """,
    "code": """
      <path d="M18 17 L11 24 L18 31 M30 17 L37 24 L30 31" fill="none" stroke="#e6e9ef" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="26" y1="15" x2="22" y2="33" stroke="#9ea4b0" stroke-width="2.2" stroke-linecap="round"/>
    """,
    "folder": """
      <path d="M11 16 H20 L23 19 H37 V33 H11 Z" fill="#282c34" stroke="#e6e9ef" stroke-width="2.2" stroke-linejoin="round"/>
      <line x1="11" y1="22" x2="37" y2="22" stroke="#9ea4b0" stroke-width="1.6"/>
    """,
    "telegram": """
      <path d="M35 13 L11 22.5 L19.5 26 L22.5 34.5 L27 29.5 L32.5 33.5 Z" fill="#282c34" stroke="#e6e9ef" stroke-width="2.1" stroke-linejoin="round"/>
      <line x1="19.5" y1="26" x2="35" y2="13" stroke="#9ea4b0" stroke-width="1.8"/>
    """,
    "discord": """
      <path d="M14 16 C18 14, 30 14, 34 16 C36 21, 36 27, 34 32 C31 34, 28 33, 27 31 L21 31 C20 33, 17 34, 14 32 C12 27, 12 21, 14 16 Z" fill="#282c34" stroke="#e6e9ef" stroke-width="2.1" stroke-linejoin="round"/>
      <circle cx="19.5" cy="23.5" r="2.2" fill="#e6e9ef"/>
      <circle cx="28.5" cy="23.5" r="2.2" fill="#e6e9ef"/>
    """,
    "steam": """
      <circle cx="28.5" cy="19.5" r="5.2" fill="none" stroke="#e6e9ef" stroke-width="2.3"/>
      <circle cx="28.5" cy="19.5" r="2.0" fill="#9ea4b0"/>
      <circle cx="17.5" cy="30.0" r="3.8" fill="none" stroke="#9ea4b0" stroke-width="2.1"/>
      <line x1="20.2" y1="27.5" x2="25.2" y2="22.8" stroke="#e6e9ef" stroke-width="3.0" stroke-linecap="round"/>
    """,
    "happ": """
      <path d="M24 11 L35 16 V24 C35 30.5 30 35 24 37 C18 35 13 30.5 13 24 V16 Z" fill="#282c34" stroke="#e6e9ef" stroke-width="2.2" stroke-linejoin="round"/>
      <path d="M18 24 H22 L24 19 L26 29 L28 24 H30" fill="none" stroke="#9ea4b0" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "media": """
      <circle cx="24" cy="24" r="12" fill="none" stroke="#e6e9ef" stroke-width="2.2"/>
      <polygon points="21,18 31,24 21,30" fill="#e6e9ef"/>
    """,
    "graphics": """
      <polygon points="24,12 36,34 12,34" fill="none" stroke="#e6e9ef" stroke-width="2.2" stroke-linejoin="round"/>
      <circle cx="24" cy="26" r="3.5" fill="#9ea4b0"/>
    """,
    "gamedev": """
      <rect x="12" y="16" width="24" height="16" rx="5" fill="#282c34" stroke="#e6e9ef" stroke-width="2.2"/>
      <line x1="17" y1="21" x2="17" y2="27" stroke="#e6e9ef" stroke-width="2.0" stroke-linecap="round"/>
      <line x1="14" y1="24" x2="20" y2="24" stroke="#e6e9ef" stroke-width="2.0" stroke-linecap="round"/>
      <circle cx="29" cy="22" r="1.6" fill="#9ea4b0"/>
      <circle cx="32" cy="26" r="1.6" fill="#e6e9ef"/>
    """,
    "network": """
      <circle cx="24" cy="28" r="2.6" fill="#e6e9ef"/>
      <path d="M18 23 A8.5 8.5 0 0 1 30 23" fill="none" stroke="#e6e9ef" stroke-width="2.2" stroke-linecap="round"/>
      <path d="M14 18 A14 14 0 0 1 34 18" fill="none" stroke="#9ea4b0" stroke-width="2.2" stroke-linecap="round"/>
    """,
    "monitor": """
      <rect x="12" y="14" width="24" height="20" rx="3" fill="none" stroke="#e6e9ef" stroke-width="2.1"/>
      <polyline points="15,28 20,23 24,26 29,18 33,22" fill="none" stroke="#9ea4b0" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    """,
    "settings": """
      <circle cx="24" cy="24" r="6" fill="none" stroke="#e6e9ef" stroke-width="2.4"/>
      <line x1="24" y1="11" x2="24" y2="15" stroke="#9ea4b0" stroke-width="2.4" stroke-linecap="round"/>
      <line x1="24" y1="33" x2="24" y2="37" stroke="#9ea4b0" stroke-width="2.4" stroke-linecap="round"/>
      <line x1="11" y1="24" x2="15" y2="24" stroke="#9ea4b0" stroke-width="2.4" stroke-linecap="round"/>
      <line x1="33" y1="24" x2="37" y2="24" stroke="#9ea4b0" stroke-width="2.4" stroke-linecap="round"/>
    """,
    "archive": """
      <rect x="13" y="13" width="22" height="22" rx="4" fill="none" stroke="#e6e9ef" stroke-width="2.2"/>
      <line x1="24" y1="13" x2="24" y2="35" stroke="#9ea4b0" stroke-width="2.0" stroke-dasharray="3 2"/>
    """,
}

def make_monogram_svg(app_name):
    # Создаёт персональную студийную иконку с монограммой и геометрическим контуром для любого редкого приложения
    clean = re.sub(r"[^A-Za-zА-Яа-я0-9]", " ", app_name).strip()
    words = [w for w in clean.split() if w]
    if len(words) >= 2:
        mono = (words[0][0] + words[1][0]).upper()
    elif words:
        mono = words[0][:2].upper()
    else:
        mono = "▣"
    inner = f"""
      <rect x="11" y="11" width="26" height="26" rx="6" fill="#1b1e24" stroke="#454a54" stroke-width="1.4"/>
      <path d="M11 17 V13 C11 11.8 11.8 11 13 11 H17 M37 31 V35 C37 36.2 36.2 37 35 37 H31" fill="none" stroke="#9ea4b0" stroke-width="2.0"/>
      <text x="24" y="29" text-anchor="middle" font-family="JetBrainsMono Nerd Font, Inter, monospace" font-weight="800" font-size="13.5" fill="#e6e9ef">{mono}</text>
    """
    return wrap_squircle(inner)

def pick_glyph_for_app(icon_key, app_name, categories):
    blob = f"{icon_key} {app_name} {categories}".lower()
    if any(k in blob for k in ("happ", "v2ray", "nekoray", "throne", "sing-box", "amnezia", "vpn", "proxy", "clash", "wireguard")):
        return wrap_squircle(GLYPHS["happ"])
    if any(k in blob for k in ("telegram", "ayugram", "kotatogram", "materialgram")):
        return wrap_squircle(GLYPHS["telegram"])
    if any(k in blob for k in ("discord", "vesktop", "legcord", "webcord", "equibop", "armcord", "vencord")):
        return wrap_squircle(GLYPHS["discord"])
    if any(k in blob for k in ("steam", "lutris", "heroic", "bottles", "prism", "minecraft")):
        return wrap_squircle(GLYPHS["steam"])
    if any(k in blob for k in ("foot", "kitty", "alacritty", "wezterm", "xterm", "konsole", "terminal", "console")):
        return wrap_squircle(GLYPHS["terminal"])
    if any(k in blob for k in ("firefox", "chrom", "brave", "zen", "vivaldi", "librewolf", "tor-browser", "webbrowser", "browser")):
        return wrap_squircle(GLYPHS["browser"])
    if any(k in blob for k in ("code", "codium", "zed", "nvim", "neovim", "vim", "jetbrains", "pycharm", "idea", "clion", "rider", "studio", "kate", "geany", "sublime", "cursor")):
        return wrap_squircle(GLYPHS["code"])
    if any(k in blob for k in ("thunar", "nautilus", "dolphin", "pcmanfm", "nemo", "ranger", "yazi", "folder", "file-manager", "files")):
        return wrap_squircle(GLYPHS["folder"])
    if any(k in blob for k in ("vlc", "mpv", "spotify", "amberol", "cava", "audacity", "obs", "kdenlive", "pavucontrol", "easyeffects", "multimedia", "audio", "video", "music", "player")):
        return wrap_squircle(GLYPHS["media"])
    if any(k in blob for k in ("gimp", "inkscape", "krita", "blender", "aseprite", " libresprite", "pinta", "darktable", "flameshot", "graphics")):
        return wrap_squircle(GLYPHS["graphics"])
    if any(k in blob for k in ("godot", "unity", "unreal", "tiled", "ldtk", "osu", "cs2", "game")):
        return wrap_squircle(GLYPHS["gamedev"])
    if any(k in blob for k in ("btop", "htop", "nvtop", "missioncenter", "resources", "system-monitor")):
        return wrap_squircle(GLYPHS["monitor"])
    if any(k in blob for k in ("network", "wifi", "nm-", "bluetooth", "blueman", "qbittorrent", "transmission", "deluge")):
        return wrap_squircle(GLYPHS["network"])
    if any(k in blob for k in ("ark", "file-roller", "engrampa", "peazip", "7z", "archive")):
        return wrap_squircle(GLYPHS["archive"])
    if any(k in blob for k in ("settings", "control", "qt5ct", "qt6ct", "nwg-look", "lxappearance", "kvantum", "preferences")):
        return wrap_squircle(GLYPHS["settings"])
    return make_monogram_svg(app_name or icon_key)

# 1. Записываем базовые системные имена иконок
BASE_MAP = {
    "foot": "terminal", "utilities-terminal": "terminal", "terminal": "terminal", "kitty": "terminal", "alacritty": "terminal",
    "firefox": "browser", "web-browser": "browser", "chromium": "browser", "brave": "browser", "zen": "browser",
    "code": "code", "vscodium": "code", "zed": "code", "nvim": "code", "applications-development": "code",
    "folder": "folder", "thunar": "folder", "org.xfce.thunar": "folder", "nautilus": "folder", "org.gnome.Nautilus": "folder", "dolphin": "folder", "system-file-manager": "folder",
    "telegram": "telegram", "org.telegram.desktop": "telegram", "telegram-desktop": "telegram", "ayugram": "telegram", "com.ayugram.desktop": "telegram",
    "discord": "discord", "vesktop": "discord", "dev.vencord.Vesktop": "discord", "legcord": "discord", "webcord": "discord", "equibop": "discord",
    "steam": "steam", "steam-native": "steam", "com.valvesoftware.Steam": "steam", "lutris": "steam", "heroic": "steam",
    "happ": "happ", "happ-desktop": "happ", "Happ": "happ", "ru.happ.desktop": "happ", "io.happ.desktop": "happ",
    "btop": "monitor", "htop": "monitor", "default": "settings", "application-x-executable": "settings",
}
for ikey, gtype in BASE_MAP.items():
    open(os.path.join(APPS_DIR, f"{ikey}.svg"), "w", encoding="utf-8").write(wrap_squircle(GLYPHS[gtype]))

# 2. Сканируем ВСЕ .desktop файлы в системе и генерируем иконку под КАЖДОЕ приложение!
desktop_dirs = [
    "/usr/share/applications",
    "/var/lib/flatpak/exports/share/applications",
    os.path.join(HOME, ".local/share/flatpak/exports/share/applications"),
    LOCAL_APPS,
]

for ddir in desktop_dirs:
    if not os.path.isdir(ddir):
        continue
    for df in sorted(glob.glob(os.path.join(ddir, "*.desktop"))):
        try:
            txt = open(df, "r", encoding="utf-8", errors="ignore").read()
            nm_m = re.search(r"^Name=(.*)$", txt, re.M)
            ic_m = re.search(r"^Icon=(.*)$", txt, re.M)
            ct_m = re.search(r"^Categories=(.*)$", txt, re.M)
            if not ic_m:
                continue
            app_name = nm_m.group(1).strip() if nm_m else os.path.splitext(os.path.basename(df))[0]
            raw_icon = ic_m.group(1).strip()
            cats = ct_m.group(1).strip() if ct_m else ""
            if not raw_icon:
                continue

            # Если в .desktop файле прописан жёсткий абсолютный путь (/opt/happ/..., /usr/share/pixmaps/...),
            # создаём переопределение в ~/.local/share/applications с чистым именем иконки!
            if raw_icon.startswith("/") or raw_icon.endswith((".png", ".svg", ".xpm")):
                slug = "studio-" + re.sub(r"[^a-zA-Z0-9_-]", "-", os.path.splitext(os.path.basename(df))[0]).lower()
                svg_content = pick_glyph_for_app(raw_icon, app_name, cats)
                open(os.path.join(APPS_DIR, f"{slug}.svg"), "w", encoding="utf-8").write(svg_content)

                base_icon_stem = os.path.splitext(os.path.basename(raw_icon))[0]
                if base_icon_stem:
                    open(os.path.join(APPS_DIR, f"{base_icon_stem}.svg"), "w", encoding="utf-8").write(svg_content)

                if raw_icon.startswith("/"):
                    new_txt = re.sub(r"^Icon=.*$", f"Icon={slug}", txt, flags=re.M)
                    local_df = os.path.join(LOCAL_APPS, os.path.basename(df))
                    open(local_df, "w", encoding="utf-8").write(new_txt)
            else:
                svg_path = os.path.join(APPS_DIR, f"{raw_icon}.svg")
                svg_content = pick_glyph_for_app(raw_icon, app_name, cats)
                open(svg_path, "w", encoding="utf-8").write(svg_content)
                open(os.path.join(APPS_DIR, f"{raw_icon.lower()}.svg"), "w", encoding="utf-8").write(svg_content)
        except Exception:
            pass

subprocess.run(["gtk-update-icon-cache", "-f", "-t", THEME_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["update-desktop-database", LOCAL_APPS], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Adwaita"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "CyberDeck-Icons"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
