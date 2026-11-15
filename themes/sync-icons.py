#!/usr/bin/python3
import os, shutil, subprocess

HOME = os.path.expanduser("~")
THEME_DIR = os.path.join(HOME, ".local/share/icons/CyberDeck-Icons")
APPS_DIR  = os.path.join(THEME_DIR, "scalable/apps")
os.makedirs(APPS_DIR, exist_ok=True)

open(os.path.join(THEME_DIR, "index.theme"), "w", encoding="utf-8").write("""[Icon Theme]
Name=CyberDeck-Icons
Comment=Studio Monochrome Grey Icons
Inherits=Adwaita,hicolor
Directories=scalable/apps

[scalable/apps]
Size=48
Type=Scalable
MinSize=16
MaxSize=256
""")

def wrap_squircle(inner_svg):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#23262d"/>
      <stop offset="100%" stop-color="#15171b"/>
    </linearGradient>
  </defs>
  <rect x="3" y="3" width="42" height="42" rx="11" fill="url(#bg)" stroke="#3e434d" stroke-width="1.6"/>
  <rect x="5" y="5" width="38" height="38" rx="9" fill="none" stroke="#ffffff" stroke-opacity="0.05" stroke-width="1"/>
  {inner_svg}
</svg>"""

GLYPHS = {
    "foot": """
      <path d="M14 18 L21 24 L14 30" fill="none" stroke="#e2e6ed" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="24" y1="30" x2="34" y2="30" stroke="#9ea4b0" stroke-width="2.6" stroke-linecap="round"/>
    """,
    "firefox": """
      <circle cx="24" cy="24" r="12" fill="none" stroke="#d4d8de" stroke-width="2.2"/>
      <ellipse cx="24" cy="24" rx="5.5" ry="12" fill="none" stroke="#8c939e" stroke-width="1.6"/>
      <line x1="12" y1="24" x2="36" y2="24" stroke="#8c939e" stroke-width="1.6"/>
    """,
    "code": """
      <path d="M18 17 L11 24 L18 31 M30 17 L37 24 L30 31" fill="none" stroke="#e2e6ed" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="26" y1="15" x2="22" y2="33" stroke="#8c939e" stroke-width="2.2" stroke-linecap="round"/>
    """,
    "folder": """
      <path d="M11 16 H20 L23 19 H37 V33 H11 Z" fill="#2a2e37" stroke="#d4d8de" stroke-width="2.2" stroke-linejoin="round"/>
      <line x1="11" y1="22" x2="37" y2="22" stroke="#8c939e" stroke-width="1.6"/>
    """,
    "telegram": """
      <path d="M35 14 L12 23 L20 26 L23 34 L27 29 L32 33 Z" fill="none" stroke="#e2e6ed" stroke-width="2.2" stroke-linejoin="round"/>
      <line x1="20" y1="26" x2="35" y2="14" stroke="#8c939e" stroke-width="1.8"/>
    """,
    "discord": """
      <rect x="12" y="16" width="24" height="16" rx="6" fill="none" stroke="#e2e6ed" stroke-width="2.2"/>
      <circle cx="19" cy="24" r="2.2" fill="#d4d8de"/>
      <circle cx="29" cy="24" r="2.2" fill="#d4d8de"/>
    """,
    "steam": """
      <circle cx="28" cy="20" r="5" fill="none" stroke="#e2e6ed" stroke-width="2.2"/>
      <circle cx="18" cy="30" r="3.5" fill="none" stroke="#9ea4b0" stroke-width="2.0"/>
      <line x1="20" y1="28" x2="25" y2="23" stroke="#d4d8de" stroke-width="2.6" stroke-linecap="round"/>
    """,
    "cs2": """
      <circle cx="24" cy="24" r="11" fill="none" stroke="#d4d8de" stroke-width="2.0"/>
      <line x1="24" y1="9" x2="24" y2="16" stroke="#9ea4b0" stroke-width="2.0"/>
      <line x1="24" y1="32" x2="24" y2="39" stroke="#9ea4b0" stroke-width="2.0"/>
      <line x1="9" y1="24" x2="16" y2="24" stroke="#9ea4b0" stroke-width="2.0"/>
      <line x1="32" y1="24" x2="39" y2="24" stroke="#9ea4b0" stroke-width="2.0"/>
      <circle cx="24" cy="24" r="2.2" fill="#e2e6ed"/>
    """,
    "default": """
      <rect x="14" y="14" width="8" height="8" rx="2" fill="none" stroke="#e2e6ed" stroke-width="2.0"/>
      <rect x="26" y="14" width="8" height="8" rx="2" fill="none" stroke="#9ea4b0" stroke-width="2.0"/>
      <rect x="14" y="26" width="8" height="8" rx="2" fill="none" stroke="#9ea4b0" stroke-width="2.0"/>
      <rect x="26" y="26" width="8" height="8" rx="2" fill="none" stroke="#e2e6ed" stroke-width="2.0"/>
    """,
}

ALIASES = {
    "foot": ["utilities-terminal", "terminal", "kitty", "alacritty", "org.codeberg.dnkl.foot"],
    "firefox": ["firefox-developer-edition", "web-browser", "system-file-manager-web", "zen", "chromium", "brave"],
    "code": ["code-oss", "vscodium", "zed", "godot", "unity", "applications-development", "applications-development-symbolic"],
    "folder": ["thunar", "org.xfce.thunar", "nautilus", "org.gnome.Nautilus", "dolphin", "pcmanfm", "system-file-manager"],
    "telegram": ["org.telegram.desktop", "ayugram", "telegram-desktop"],
    "discord": ["vesktop", "legcord", "webcord", "equibop"],
    "steam": ["steam-native", "lutris", "heroic", "applications-games", "applications-games-symbolic"],
    "cs2": ["csgo"],
    "default": ["applications-system", "applications-system-symbolic", "btop", "htop"],
}

for base_name, inner in GLYPHS.items():
    svg_txt = wrap_squircle(inner)
    open(os.path.join(APPS_DIR, f"{base_name}.svg"), "w", encoding="utf-8").write(svg_txt)
    for al in ALIASES.get(base_name, []):
        open(os.path.join(APPS_DIR, f"{al}.svg"), "w", encoding="utf-8").write(svg_txt)

subprocess.run(["gtk-update-icon-cache", "-f", "-t", THEME_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "Adwaita"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", "CyberDeck-Icons"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
