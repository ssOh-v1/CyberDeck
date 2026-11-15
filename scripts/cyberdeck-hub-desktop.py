#!/usr/bin/python3
from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass

import os, sys, re, glob, json, math, time, random, socket, shutil, subprocess, datetime, importlib.util

HOME = os.path.expanduser("~")
UID = os.getuid()
CFG_DIR = os.path.join(HOME, ".config/cyberdeck")
CACHE_DIR = os.path.join(HOME, ".cache/cyberdeck")
WORK_STATE = os.path.join(CFG_DIR, "work_theme.json")
STATE_FILE = os.path.join(CFG_DIR, "theme.json")

def load_active_env():
    for sf in (STATE_FILE, WORK_STATE):
        if os.path.isfile(sf):
            try:
                return json.load(open(sf, encoding="utf-8"))
            except Exception:
                pass
    return {"id": "cyberdeck", "layout": "cyberdeck", "cursor_theme": "CyberDeck-Cursor-cyberdeck", "symbol": "◈", "badge": "CYBERDECK // V2"}

ENV_META = load_active_env()
CUR_THEME_NAME = ENV_META.get("cursor_theme") or f"CyberDeck-Cursor-{ENV_META.get('id', 'cyberdeck')}"
os.environ["XCURSOR_THEME"] = CUR_THEME_NAME
os.environ["XCURSOR_SIZE"] = "28"

ORIG_GTK_THEME = os.environ.get("GTK_THEME")
os.environ["GTK_THEME"] = "Adwaita:dark"

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Pango, Gtk4LayerShell
import cairo

os.environ.pop("LD_PRELOAD", None)

_my_pid = os.getpid()
for _p in os.listdir("/proc"):
    if _p.isdigit() and int(_p) != _my_pid:
        try:
            _cmd = open(f"/proc/{_p}/cmdline", "rb").read().decode("utf-8", "ignore")
            if "work-hub-desktop.py" in _cmd or "cyberdeck-hub-desktop.py" in _cmd:
                os.kill(int(_p), 9)
        except Exception:
            pass

BG_PNG = os.path.join(CACHE_DIR, "work_hud_bg.png")
UI_ICONS = os.path.join(HOME, ".config/hypr/assets/ui")
ROFI_THEME = os.path.join(HOME, ".config/hypr/gaming_launcher.rasi")
PIN_FILE = os.path.join(CFG_DIR, "pinned_work_apps.json")
NOTES_FILE = os.path.join(CFG_DIR, "ronin_notes.txt")
KB_FILE = f"/tmp/alpora_kb_layout_{UID}"

_spec = importlib.util.spec_from_file_location("cyber_bg_helper", os.path.join(HOME, ".local/bin/cyber-bg-helper.py"))
cyber_bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cyber_bg)

def load_css():
    p = os.path.join(CFG_DIR, "active_hub.css")
    if os.path.isfile(p):
        try: return open(p, "r", encoding="utf-8").read()
        except Exception: pass
    return "window { background-color: #07090f; color: #dce3f5; }"

def ui_svg(name, sz=16):
    p = os.path.join(UI_ICONS, name)
    img = Gtk.Image.new_from_file(p) if os.path.isfile(p) else Gtk.Image.new_from_icon_name("applications-system-symbolic")
    img.set_pixel_size(sz)
    return img

def resolve_cyber_svg(spec, fallback_glyph):
    theme_apps = os.path.join(HOME, ".local/share/icons/CyberDeck-Icons/scalable/apps")
    raw = os.path.splitext(os.path.basename(spec or ""))[0]
    low = raw.lower()
    candidates = [raw, low]
    if "firefox" in low: candidates.append("firefox")
    elif any(x in low for x in ("foot", "kitty", "alacritty", "terminal")): candidates.append("foot")
    elif any(x in low for x in ("code", "vscodium", "zed", "unity", "godot")): candidates.append("code")
    elif any(x in low for x in ("telegram", "ayugram")): candidates.append("telegram")
    elif any(x in low for x in ("discord", "vesktop", "legcord")): candidates.append("discord")
    candidates.append(fallback_glyph)
    for c in candidates:
        if c and os.path.isfile(os.path.join(theme_apps, f"{c}.svg")):
            return os.path.join(theme_apps, f"{c}.svg")
    return None

def make_cyber_icon_widget(icon_spec, fallback_glyph="applications-development-symbolic", size=34):
    svg_path = resolve_cyber_svg(icon_spec, fallback_glyph)
    img = Gtk.Image.new_from_file(svg_path) if svg_path else (Gtk.Image.new_from_file(icon_spec) if (icon_spec and os.path.isfile(icon_spec)) else Gtk.Image.new_from_icon_name(icon_spec or fallback_glyph))
    img.set_pixel_size(size)
    return img

def get_monitor_info():
    try:
        out = subprocess.check_output(["hyprctl", "monitors"], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"(\d+)x(\d+)@(\d+(?:\.\d+)?)", out)
        if m: return int(m.group(1)), int(m.group(2)), int(round(float(m.group(3))))
    except Exception: pass
    return 1920, 1080, 60

def read_cpu_stat():
    try:
        parts = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        return parts[3] + (parts[4] if len(parts) > 4 else 0), sum(parts)
    except Exception: return 0, 0

def read_ram_info():
    try:
        info = {l.split(":")[0].strip(): int(l.split(":")[1].strip().split()[0]) for l in open("/proc/meminfo")}
        tot = info.get("MemTotal", 1)
        used = tot - info.get("MemAvailable", 0)
        return f"{used/1048576.0:.1f}/{tot/1048576.0:.0f}G", min(1.0, max(0.0, used / tot))
    except Exception: return "--", 0.0

def read_wifi_state():
    try: return json.loads(subprocess.check_output([os.path.join(HOME, ".local/bin/wifi-status")], text=True, stderr=subprocess.DEVNULL, timeout=1.0))
    except Exception: return {"enabled": True, "connected": False, "ssid": "", "signal": 0, "icon": "wifi-high.svg"}

def read_battery():
    try: return json.loads(subprocess.check_output([os.path.join(HOME, ".local/bin/battery-status"), "--json"], text=True, stderr=subprocess.DEVNULL))
    except Exception: return {"present": False, "pct": 100, "status": "AC", "watts": 0.0, "temp_c": 45}

def scan_dev_ports():
    ports = []
    try:
        for ln in open("/proc/net/tcp").readlines()[1:]:
            parts = ln.split()
            if len(parts) > 3 and parts[3] == "0A":
                p = int(parts[1].split(":")[1], 16)
                if p in (3000, 4000, 5000, 5173, 8000, 8080, 8888, 9000) and f":{p}" not in ports:
                    ports.append(f":{p}")
    except Exception: pass
    return " ".join(ports[:4]) if ports else "НЕТ АКТИВНЫХ DEV-ПОРТОВ"

def read_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_pinned():
    try: return set(json.load(open(PIN_FILE, encoding="utf-8"))) if os.path.isfile(PIN_FILE) else set()
    except Exception: return set()

def save_pinned(pins):
    os.makedirs(os.path.dirname(PIN_FILE), exist_ok=True)
    json.dump(sorted(pins), open(PIN_FILE, "w", encoding="utf-8"), ensure_ascii=False)

def classify_cat(cats, name):
    low = (cats + " " + name).lower()
    if any(k in low for k in ("development", "ide", "code", "godot", "unity", "git", "python")): return "DEV"
    if any(k in low for k in ("terminal", "shell", "kitty", "foot", "alacritty")): return "TERM"
    if any(k in low for k in ("webbrowser", "firefox", "chrom", "brave", "zen")): return "WEB"
    if any(k in low for k in ("graphics", "blender", "gimp", "inkscape", "krita", "font")): return "ART"
    if any(k in low for k in ("instantmessaging", "chat", "telegram", "discord", "vesktop")): return "CHAT"
    if any(k in low for k in ("audio", "video", "obs", "vlc", "mpv")): return "MEDIA"
    return "SYS"

def discover_work_apps():
    apps, seen = [], set()
    skip_names = {"steam", "lutris", "heroic", "mangohud", "gamemode"}
    for ad in (os.path.join(HOME, ".local/share/applications"), "/usr/share/applications"):
        if not os.path.isdir(ad): continue
        for df in sorted(glob.glob(os.path.join(ad, "*.desktop"))):
            try:
                txt = open(df, errors="ignore").read()
                if re.search(r"^NoDisplay=true", txt, re.M) or re.search(r"^Hidden=true", txt, re.M): continue
                cats_m = re.search(r"^Categories=(.*)$", txt, re.M)
                cats = cats_m.group(1) if cats_m else ""
                if "Game" in cats and "Development" not in cats: continue
                nm, ex, ic = re.search(r"^Name=(.*)$", txt, re.M), re.search(r"^Exec=(.*)$", txt, re.M), re.search(r"^Icon=(.*)$", txt, re.M)
                if not (nm and ex): continue
                name = nm.group(1).strip()
                if name in seen or name.lower() in skip_names: continue
                cmd = re.sub(r"\s+%[fFuUdDnNickvm]", "", ex.group(1).strip())
                icon = ic.group(1).strip() if ic else "applications-system-symbolic"
                seen.add(name)
                apps.append((name, cmd, icon, classify_cat(cats, name)))
            except Exception: pass
    return apps

class WorkHubApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.alpora.WorkDeckLayer")
        self.layout_mode = ENV_META.get("layout", "cyberdeck")
        self.cards = []
        self.pinned = load_pinned()
        self.prev_idle, self.prev_total = read_cpu_stat()
        self.last_ws_sig = None
        self.t0 = time.monotonic()

        # Вспомогательные ссылки на элементы текущего Shell
        self.clock_lbl = None
        self.cpu_lbl = None; self.cpu_bar = None
        self.ram_lbl = None; self.ram_bar = None
        self.bat_lbl = None; self.bat_bar = None
        self.wifi_btn = None; self.kb_btn = None; self.pwr_btn = None
        self.bg_menu_btn = None; self.ws_box = None
        self.bri_scale = None; self.bri_pct_lbl = None
        self.vol_scale = None; self.vol_pct_lbl = None
        self.dock_box = None; self.ports_lbl = None
        self.loot_lbl = None; self.ide_out_buf = None
        self.pomo_sec = 20 * 60; self.pomo_running = False; self.pomo_lbl = None

        # Частицы живых обоев для 2-й темы (The Dungeon of God)
        random.seed(77)
        self.embers = [
            [random.uniform(0.05, 0.95), random.uniform(0.10, 0.98), random.uniform(18, 48), random.uniform(-14, 14), random.uniform(1.8, 4.2), random.random()]
            for _ in range(44)
        ]

    # ==========================================================================
    # ЖИВЫЕ ОБОИ ДЛЯ 2-Й ТЕМЫ: THE DUNGEON OF GOD (ssOh-v1 Edition)
    # ==========================================================================
    def draw_dungeon_live_bg(self, _area, cr, w, h, *_args):
        dt = time.monotonic() - self.t0
        cr.save()
        cr.scale(w / 1920.0, h / 1080.0)
        W, H = 1920, 1080

        # 1. Глубокий свод подземелья и каменные арки
        cr.set_source_rgb(0.042, 0.025, 0.022); cr.paint()
        for row, y in enumerate(range(0, H, 72)):
            ox = 54 if (row % 2) else 0
            for x in range(-54, W, 108):
                cr.set_source_rgba(0.085, 0.052, 0.045, 0.85)
                cr.rectangle(x + ox + 2, y + 2, 104, 68); cr.fill_preserve()
                cr.set_line_width(1.1); cr.set_source_rgba(0.20, 0.12, 0.10, 0.40); cr.stroke()

        # 2. Живое мерцание двух боковых факелов и центрального рунического алтаря
        flicker1 = 1.0 + 0.12 * math.sin(dt * 7.5) + 0.06 * math.cos(dt * 13.0)
        flicker2 = 1.0 + 0.12 * math.cos(dt * 6.8) + 0.06 * math.sin(dt * 11.4)
        for (tx, ty), fl in [((W*0.18, H*0.44), flicker1), ((W*0.82, H*0.44), flicker2), ((W*0.50, H*0.54), (flicker1+flicker2)*0.5)]:
            rad = 420 * fl
            rg = cairo.RadialGradient(tx, ty, 8, tx, ty, rad)
            rg.add_color_stop_rgba(0.0, 0.98, 0.68, 0.22, 0.28)
            rg.add_color_stop_rgba(0.45, 0.85, 0.22, 0.14, 0.12)
            rg.add_color_stop_rgba(1.0, 0, 0, 0, 0)
            cr.set_source(rg); cr.paint()

        # 3. Вращающаяся печать Древнего Алтаря в центре
        cx, cy = W * 0.50, H * 0.54
        cr.save(); cr.translate(cx, cy); cr.rotate(dt * 0.18)
        cr.set_line_width(2.2); cr.set_source_rgba(0.96, 0.72, 0.22, 0.28)
        cr.arc(0, 0, 235, 0, 2*math.pi); cr.stroke()
        cr.arc(0, 0, 215, 0, 2*math.pi); cr.stroke()
        for i in range(8):
            ang = i * math.pi / 4.0
            cr.move_to(215 * math.cos(ang), 215 * math.sin(ang))
            cr.line_to(235 * math.cos(ang), 235 * math.sin(ang))
        cr.stroke()
        cr.restore()

        # 4. Поднимающиеся живые искры пламени и золотые частицы лута
        for idx, (x0, y0, spd, vx, sz, ph) in enumerate(self.embers):
            cyc = ((dt * (spd / 320.0)) + ph) % 1.0
            ex = (x0 * W + math.sin(dt * 2.0 + idx) * 28 + cyc * vx) % W
            ey = H - cyc * (H * 0.92)
            alpha = math.sin(cyc * math.pi) * 0.85
            if idx % 3 == 0:
                cr.set_source_rgba(0.98, 0.80, 0.25, alpha)
            else:
                cr.set_source_rgba(0.95, 0.35, 0.18, alpha)
            cr.arc(ex, ey, sz, 0, 2 * math.pi); cr.fill()

        cr.restore()

    def make_sliders_pair(self, width_px=48):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); box.set_valign(Gtk.Align.CENTER)
        bri_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); bri_cap.add_css_class("audio-capsule")
        bri_btn = Gtk.Button(); bri_btn.add_css_class("audio-icon-btn"); bri_btn.set_child(ui_svg("sun.svg", 15))
        bri_btn.connect("clicked", self.on_bri_icon_clicked); bri_cap.append(bri_btn)
        cur_b = self.get_current_bri()
        self.bri_pct_lbl = Gtk.Label(label=f"{int(cur_b)}%"); self.bri_pct_lbl.add_css_class("vol-pct")
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.bri_scale.set_draw_value(False); self.bri_scale.set_size_request(width_px, -1); self.bri_scale.set_value(cur_b)
        self.bri_scale.connect("value-changed", self.on_bri_changed)
        bri_cap.append(self.bri_scale); bri_cap.append(self.bri_pct_lbl); box.append(bri_cap)

        audio_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); audio_cap.add_css_class("audio-capsule")
        audio_btn = Gtk.Button(); audio_btn.add_css_class("audio-icon-btn"); audio_btn.set_child(ui_svg("audio.svg", 15))
        audio_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-audio-menu")); audio_cap.append(audio_btn)
        cur_v = self.get_current_vol()
        self.vol_pct_lbl = Gtk.Label(label=f"{int(cur_v)}%"); self.vol_pct_lbl.add_css_class("vol-pct")
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_draw_value(False); self.vol_scale.set_size_request(width_px, -1); self.vol_scale.set_value(cur_v)
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        audio_cap.append(self.vol_scale); audio_cap.append(self.vol_pct_lbl); box.append(audio_cap)
        return box

    def make_sys_power_capsule(self):
        sys_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2); sys_cap.add_css_class("power-capsule")
        btop_b = Gtk.Button(label="BTOP"); btop_b.add_css_class("icon-act-btn"); btop_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-tool btop")); sys_cap.append(btop_b)
        lock_b = Gtk.Button(); lock_b.add_css_class("icon-act-btn"); lock_b.set_child(ui_svg("lock.svg", 15)); lock_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-lock")); sys_cap.append(lock_b)
        sddm_b = Gtk.Button(label="SDDM"); sddm_b.add_css_class("danger-act-btn"); sddm_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session; hyprctl dispatch exit")); sys_cap.append(sddm_b)
        reb_b = Gtk.Button(); reb_b.add_css_class("icon-act-btn"); reb_b.set_child(ui_svg("reboot.svg", 15)); reb_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session; systemctl reboot")); sys_cap.append(reb_b)
        off_b = Gtk.Button(); off_b.add_css_class("danger-act-btn"); off_b.set_child(ui_svg("power.svg", 15)); off_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session; systemctl poweroff")); sys_cap.append(off_b)
        return sys_cap

    def build_app_grid(self, max_cols=5):
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True); scroll.set_hexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.flow = Gtk.FlowBox(); self.flow.set_valign(Gtk.Align.START)
        self.flow.set_max_children_per_line(max_cols); self.flow.set_min_children_per_line(1)
        self.flow.set_column_spacing(12); self.flow.set_row_spacing(12)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.flow)
        return scroll

    # ==========================================================================
    # ТЕМЫ 1..5: ПОСТРОЕНИЕ 5 НЕЗАВИСИМЫХ ОБОЛОЧЕК И ВИДЖЕТОВ
    # ==========================================================================

    # --- 1. КЛАССИЧЕСКАЯ CYBERDECK ---
    def build_world_cyberdeck(self, root_box):
        top = Gtk.CenterBox(); top.add_css_class("top-deck")
        lz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7); brand.add_css_class("brand-pill")
        brand.append(Gtk.Label(label="◈", css_classes=["brand-dot"]))
        brand.append(Gtk.Label(label="CYBERDECK // V2", css_classes=["brand-title"]))
        lz.append(brand)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); lz.append(self.ws_box)
        nb = Gtk.Button(label="+ Стол"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); lz.append(nb)
        self.bg_menu_btn = Gtk.Button(label="◈ Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); lz.append(self.bg_menu_btn)
        tb = Gtk.Button(label="◈ Мир / Тема"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); lz.append(tb)
        top.set_start_widget(lz)

        cp = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); cp.add_css_class("telemetry-pod")
        self.cpu_lbl = Gtk.Label(label="CPU 0%", css_classes=["metric-lbl"]); self.cpu_bar = Gtk.ProgressBar(); self.cpu_bar.set_valign(Gtk.Align.CENTER)
        self.ram_lbl = Gtk.Label(label="RAM --", css_classes=["metric-lbl"]); self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan"); self.ram_bar.set_valign(Gtk.Align.CENTER)
        self.bat_lbl = Gtk.Label(label="BAT --%", css_classes=["metric-lbl"]); self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good"); self.bat_bar.set_valign(Gtk.Align.CENTER)
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar): cp.append(w)
        top.set_center_widget(cp)

        rz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_child(ui_svg("wifi-high.svg", 16))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu")); rz.append(self.wifi_btn)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); rz.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); rz.append(self.pwr_btn)
        rz.append(self.make_sliders_pair(48))
        rz.append(self.make_sys_power_capsule())
        self.clock_lbl = Gtk.Label(label="00:00", css_classes=["clock-time"]); rz.append(self.clock_lbl)
        top.set_end_widget(rz)
        root_box.append(top)

        act = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.set_hexpand(True); self.search.connect("changed", self.on_filter); act.append(self.search)
        for bl, bc, cls in [("▶ Терминал", "~/.local/bin/launch-free-ws foot", "primary-btn"), ("📁 Проводник", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm", "secondary-btn"), ("◈ Поверх [SUPER+P]", "~/.local/bin/hyprwork-pin-window", "ctrl-pill"), ("Скриншот", "~/.local/bin/cyber-tool shot", "ctrl-pill")]:
            b = Gtk.Button(label=bl); b.add_css_class(cls); b.connect("clicked", lambda _b, c=bc: self.spawn_raw(c)); act.append(b)
        root_box.append(act)

        root_box.append(self.build_app_grid(max_cols=5))

        ftr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); ftr.add_css_class("footer-bar"); ftr.set_halign(Gtk.Align.CENTER)
        for kt, dt in [("SUPER+SPACE", "Свободный стол"), ("SUPER+T", "Выбор из 5 миров"), ("SUPER+SHIFT+P", "Перфоманс/Эко"), ("SUPER+P", "Поверх окон"), ("SUPER+E", "Проводник")]:
            ftr.append(Gtk.Label(label=kt, css_classes=["key-badge"])); ftr.append(Gtk.Label(label=dt, css_classes=["key-desc"]))
        root_box.append(ftr)

    # --- 2. THE DUNGEON OF GOD (ssOh-v1 Dark Fantasy Rogue-Platformer HUD) ---
    def build_world_dungeon(self, root_box):
        # Верхний RPG HUD Bar (HP = CPU, MANA = RAM, STAMINA = Battery)
        rpg_top = Gtk.CenterBox(); rpg_top.add_css_class("rpg-bar")

        lz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); lz.set_valign(Gtk.Align.CENTER)
        hero_badge = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); hero_badge.add_css_class("brand-pill")
        hero_badge.append(Gtk.Label(label="⚔ ssOh-v1 // LVL 99 DEV", css_classes=["brand-title"]))
        lz.append(hero_badge)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); lz.append(self.ws_box)
        b_portal = Gtk.Button(label="+ Портал"); b_portal.add_css_class("ws-new-btn"); b_portal.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); lz.append(b_portal)
        self.bg_menu_btn = Gtk.Button(label="🎒 Инвентарь фона [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); lz.append(self.bg_menu_btn)
        tb = Gtk.Button(label="⚔ Сменить мир"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); lz.append(tb)
        rpg_top.set_start_widget(lz)

        # Центральные RPG-шкалы: HP (Красный), MANA (Синий), STAMINA (Золотой)
        bars = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); bars.set_valign(Gtk.Align.CENTER)
        self.cpu_lbl = Gtk.Label(label="❤ HP 100%", css_classes=["metric-lbl"])
        self.cpu_bar = Gtk.ProgressBar(); self.cpu_bar.add_css_class("hp-bar"); self.cpu_bar.set_valign(Gtk.Align.CENTER)
        self.ram_lbl = Gtk.Label(label="✦ MANA", css_classes=["metric-lbl"])
        self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("mana-bar"); self.ram_bar.set_valign(Gtk.Align.CENTER)
        self.bat_lbl = Gtk.Label(label="⚡ STAMINA", css_classes=["metric-lbl"])
        self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("stamina-bar"); self.bat_bar.set_valign(Gtk.Align.CENTER)
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar): bars.append(w)
        rpg_top.set_center_widget(bars)

        rz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); rz.set_valign(Gtk.Align.CENTER)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); rz.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); rz.append(self.pwr_btn)
        rz.append(self.make_sliders_pair(46))
        rz.append(self.make_sys_power_capsule())
        self.clock_lbl = Gtk.Label(label="00:00", css_classes=["clock-time"]); rz.append(self.clock_lbl)
        rpg_top.set_end_widget(rz)
        root_box.append(rpg_top)

        # Основная область Подземелья: Левый Алтарь Лута и Квестов + Правый Гримуар Артефактов (программ)
        mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16); mid.set_hexpand(True); mid.set_vexpand(True)

        shrine = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        shrine.add_css_class("rpg-bar"); shrine.set_size_request(340, -1); shrine.set_vexpand(True)
        shrine.append(Gtk.Label(label="⚔ THE DUNGEON OF GOD // SHRINE", xalign=0, css_classes=["panel-header"]))
        shrine.append(Gtk.Label(label="Разработчик: ssOh-v1 (ssOh)\nЖанр: 2D Dark Rogue-Platformer", xalign=0, css_classes=["card-sub"]))

        # Виджет 1: Генератор карточек оружия и артефактов (как в самой игре!)
        shrine.append(Gtk.Label(label="🎲 АЛТАРЬ ДРЕВНИХ АРТЕФАКТОВ", xalign=0, css_classes=["panel-header"]))
        self.loot_lbl = Gtk.Label(
            label="[МИФИЧЕСКИЙ АРТЕФАКТ]\n⚔ Клинок Бога Подземелья\n• Урон в прыжке: +45%\n• Шанс крита: +20%\n• Эффект: Поджигает мобов",
            xalign=0, css_classes=["panel-sub"]
        )
        shrine.append(self.loot_lbl)

        b_roll = Gtk.Button(label="🎲 Выковать случайный артефакт"); b_roll.add_css_class("primary-btn")
        b_roll.connect("clicked", self.on_roll_dungeon_loot)
        shrine.append(b_roll)

        # Виджет 2: Свиток квестов разработки
        shrine.append(Gtk.Label(label="📜 СВИТОК КВЕСТОВ (ЗАМЕТКИ)", xalign=0, css_classes=["panel-header"]))
        n_sc = Gtk.ScrolledWindow(); n_sc.set_vexpand(True)
        tv = Gtk.TextView(); tv.add_css_class("notes-view"); tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        buf = tv.get_buffer()
        buf.set_text(open(NOTES_FILE, "r", encoding="utf-8").read() if os.path.isfile(NOTES_FILE) else "• Квесты The Dungeon of God:\n  1. Анимации подбора предметов\n  2. Карточки характеристик оружия\n  3. Новые мобы и босс этажа\n")
        buf.connect("changed", lambda b: open(NOTES_FILE, "w", encoding="utf-8").write(b.get_text(b.get_start_iter(), b.get_end_iter(), False)))
        n_sc.set_child(tv); shrine.append(n_sc)

        for lbl_d, cmd_d in [
            ("▶ Открыть консоль подземелья", "~/.local/bin/launch-free-ws foot"),
            ("📁 Открыть сундук файлов", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm"),
        ]:
            bd = Gtk.Button(label=lbl_d); bd.add_css_class("secondary-btn"); bd.connect("clicked", lambda _b, c=cmd_d: self.spawn_raw(c)); shrine.append(bd)

        mid.append(shrine)

        inv_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); inv_col.set_hexpand(True); inv_col.set_vexpand(True)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.connect("changed", self.on_filter)
        inv_col.append(self.search)
        inv_col.append(self.build_app_grid(max_cols=3))
        mid.append(inv_col)
        root_box.append(mid)

    def on_roll_dungeon_loot(self, _b):
        artifacts = [
            ("[МИФИЧЕСКИЙ] ⚔ Коса Падшего Бога", "+65% Урон в воздухе • +15% Вампиризм • Рывок сквозь шипы"),
            ("[ЛЕГЕНДАРНЫЙ] 🛡 Эгида Бездны", "+40 Броня • Отражает снаряды мобов обратно во врагов"),
            ("[ЛЕГЕНДАРНЫЙ] 💍 Кольцо ssOh-v1", "+100% Скорость компиляции Python • Нулевой пинг"),
            ("[ЭПИЧЕСКИЙ] 🗡 Парные Клинки Теней", "+35% Скорость атаки • Двойной прыжок в подземелье"),
            ("[ЛЕГЕНДАРНЫЙ] 🔥 Фонарь Душ", "Освещает скрытые комнаты • +25% Шанс редкого дропа"),
        ]
        name, stats = random.choice(artifacts)
        if self.loot_lbl:
            self.loot_lbl.set_label(f"{name}\n{stats.replace(' • ', chr(10) + '• ')}")

    # --- 3. ЛЕСНОЙ РУЧЕЙ (Парящий Waybar из 3 островов + Природный виджет + Нижний Док) ---
    def build_world_forest(self, root_box):
        # Верхний Waybar из 3 отдельных полупрозрачных капсул
        wb_row = Gtk.CenterBox()

        pill_l = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); pill_l.add_css_class("waybar-pill")
        pill_l.append(Gtk.Label(label="🌿 Лесной Ручей", css_classes=["brand-title"]))
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); pill_l.append(self.ws_box)
        nb = Gtk.Button(label="+ Поляна"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); pill_l.append(nb)
        self.bg_menu_btn = Gtk.Button(label="🌿 Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); pill_l.append(self.bg_menu_btn)
        tb = Gtk.Button(label="🌿 Сменить мир"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); pill_l.append(tb)
        wb_row.set_start_widget(pill_l)

        pill_c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12); pill_c.add_css_class("waybar-pill")
        self.clock_lbl = Gtk.Label(label="00:00", css_classes=["clock-time"]); pill_c.append(self.clock_lbl)
        self.cpu_lbl = Gtk.Label(label="CPU 0%", css_classes=["metric-lbl"]); pill_c.append(self.cpu_lbl)
        self.ram_lbl = Gtk.Label(label="RAM --", css_classes=["metric-lbl"]); pill_c.append(self.ram_lbl)
        self.bat_lbl = Gtk.Label(label="BAT --%", css_classes=["metric-lbl"]); pill_c.append(self.bat_lbl)
        wb_row.set_center_widget(pill_c)

        pill_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); pill_r.add_css_class("waybar-pill")
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_child(ui_svg("wifi-high.svg", 15))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu")); pill_r.append(self.wifi_btn)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); pill_r.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); pill_r.append(self.pwr_btn)
        pill_r.append(self.make_sliders_pair(48))
        pill_r.append(self.make_sys_power_capsule())
        wb_row.set_end_widget(pill_r)
        root_box.append(wb_row)

        # Природная карточка спокойствия и лесного таймера
        zen_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18); zen_bar.add_css_class("hero-banner")
        z_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        z_left.append(Gtk.Label(label="🌿 ШЕПОТ ЛЕСНОГО РУЧЬЯ // ПРОСТРАНСТВО ФОКУСА", xalign=0, css_classes=["panel-header"]))
        z_left.append(Gtk.Label(label="Чистый воздух • Шум горной воды • Плавный тайлинг", xalign=0, css_classes=["card-sub"]))
        zen_bar.append(z_left)

        # Виджет лесного таймера отдыха и работы
        self.pomo_lbl = Gtk.Label(label="20:00", css_classes=["timer-digits"]); zen_bar.append(self.pomo_lbl)
        b_ps = Gtk.Button(label="🌿 Таймер потока"); b_ps.add_css_class("primary-btn"); b_ps.connect("clicked", lambda _b: setattr(self, "pomo_running", not self.pomo_running)); zen_bar.append(b_ps)

        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.set_hexpand(True); self.search.connect("changed", self.on_filter)
        zen_bar.append(self.search)
        root_box.append(zen_bar)
        GLib.timeout_add_seconds(1, self.on_pomo_tick)

        root_box.append(self.build_app_grid(max_cols=5))

        # Нижний плавающий док в стиле macOS / Waybar Dock
        dock = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dock.add_css_class("bottom-dock"); dock.set_halign(Gtk.Align.CENTER)
        dock.append(Gtk.Label(label="🌿 ЛЕСНОЙ ДОК:", css_classes=["panel-header"]))
        self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dock.append(self.dock_box)
        root_box.append(dock)

    # --- 4. ИМПАСТО ПЕЙЗАЖ (Рельефная масляная живопись + Левый мольберт + Смешивание красок) ---
    def build_world_impasto(self, root_box):
        atelier = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16); atelier.set_hexpand(True); atelier.set_vexpand(True)

        # Левая вертикальная панель-мольберт (Waybar Side Atelier)
        easel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        easel.add_css_class("side-rail"); easel.set_size_request(280, -1); easel.set_vexpand(True)
        easel.append(Gtk.Label(label="🎨 МАСТЕРСКАЯ // ИМПАСТО", xalign=0, css_classes=["panel-header"]))
        self.clock_lbl = Gtk.Label(label="00:00", xalign=0, css_classes=["big-clock"]); easel.append(self.clock_lbl)

        self.cpu_lbl = Gtk.Label(label="CPU 0%", xalign=0, css_classes=["metric-lbl"]); self.cpu_bar = Gtk.ProgressBar()
        self.ram_lbl = Gtk.Label(label="RAM --", xalign=0, css_classes=["metric-lbl"]); self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan")
        self.bat_lbl = Gtk.Label(label="BAT --%", xalign=0, css_classes=["metric-lbl"]); self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good")
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar): easel.append(w)

        # Уникальная фишка 4-й темы: Интерактивная палитра масляных красок (клик копирует HEX в буфер!)
        easel.append(Gtk.Label(label="🎨 ПАЛИТРА МАЗКОВ (КЛИК -> HEX)", xalign=0, css_classes=["panel-header"]))
        swatches = [
            ("Охра Золотая",   "#F2CC8F"),
            ("Терракота",      "#E07A5F"),
            ("Ультрамарин",    "#3D405B"),
            ("Шалфей Масло",   "#81B29A"),
            ("Киноварь Заката","#E76F51"),
        ]
        for s_name, s_hex in swatches:
            sb = Gtk.Button(label=f"🖌 {s_name} ({s_hex})"); sb.add_css_class("secondary-btn")
            sb.connect("clicked", lambda _b, h=s_hex, n=s_name: self.spawn_raw(f"printf '{h}' | wl-copy && notify-send '🎨 ПАЛИТРА ИМПАСТО' 'Краска {n} ({h}) скопирована в буфер!'"))
            easel.append(sb)

        easel.append(Gtk.Label(label="🎨 ХОЛСТЫ И ФОН", xalign=0, css_classes=["panel-header"]))
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); easel.append(self.ws_box)
        row_b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        nb = Gtk.Button(label="+ Холст"); nb.add_css_class("ws-new-btn"); nb.set_hexpand(True); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws"))
        self.bg_menu_btn = Gtk.Button(label="🎨 Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.set_hexpand(True); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu"))
        row_b.append(nb); row_b.append(self.bg_menu_btn); easel.append(row_b)

        tb = Gtk.Button(label="🎨 Сменить мир [SUPER+T]"); tb.add_css_class("primary-btn"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); easel.append(tb)

        sp = Gtk.Box(); sp.set_vexpand(True); easel.append(sp)
        easel.append(self.make_sliders_pair(54))
        easel.append(self.make_sys_power_capsule())
        atelier.append(easel)

        # Правая галерея картин-приложений (с открытым видом на рельефные мазки пейзажа!)
        gallery = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); gallery.set_hexpand(True); gallery.set_vexpand(True)
        top_g = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); top_g.add_css_class("top-deck")
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.set_hexpand(True); self.search.connect("changed", self.on_filter)
        top_g.append(self.search)
        for bl, bc in [("🖌 Пипетка экрана", "~/.local/bin/cyber-tool pick"), ("🖼 Скриншот холста", "~/.local/bin/cyber-tool shot"), ("📁 Галерея файлов", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm")]:
            b = Gtk.Button(label=bl); b.add_css_class("primary-btn"); b.connect("clicked", lambda _b, c=bc: self.spawn_raw(c)); top_g.append(b)
        gallery.append(top_g)

        gallery.append(self.build_app_grid(max_cols=4))
        atelier.append(gallery)
        root_box.append(atelier)

    # --- 5. СРЕДА РАЗРАБОТКИ ИГР (GameDev Engine Studio — Godot / Pygame-CE IDE) ---
    def build_world_gamedev(self, root_box):
        # 1. Верхний Тулбар Игрового Движка с кнопками Playtest [▶ Play] [🔨 Build]
        bar = Gtk.CenterBox(); bar.add_css_class("ide-toolbar")

        lz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); lz.set_valign(Gtk.Align.CENTER)
        lz.append(Gtk.Label(label="🎮 ENGINE // IDE 4.3", css_classes=["panel-header"]))
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); lz.append(self.ws_box)
        nb = Gtk.Button(label="+ Scene"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); lz.append(nb)
        self.bg_menu_btn = Gtk.Button(label="📦 Nodes [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); lz.append(self.bg_menu_btn)
        tb = Gtk.Button(label="🎮 Сменить мир"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); lz.append(tb)
        bar.set_start_widget(lz)

        # Центральный кластер Playtest (как в Godot / Unity)
        play_cluster = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); play_cluster.set_valign(Gtk.Align.CENTER)
        b_play = Gtk.Button(label="▶ Play Game (Тест проекта)"); b_play.add_css_class("ide-play-btn")
        b_play.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-power performance; ~/.local/bin/launch-free-ws foot"))
        b_bld = Gtk.Button(label="🔨 Build Win/Linux"); b_bld.add_css_class("ide-build-btn")
        b_bld.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~"))
        b_prof = Gtk.Button(label="📊 Profiler (Btop)"); b_prof.add_css_class("ctrl-pill")
        b_prof.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-tool btop"))
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label()
        for w in (b_play, b_bld, b_prof, self.pwr_btn): play_cluster.append(w)
        bar.set_center_widget(play_cluster)

        rz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); rz.set_valign(Gtk.Align.CENTER)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); rz.append(self.kb_btn)
        rz.append(self.make_sliders_pair(46))
        rz.append(self.make_sys_power_capsule())
        self.clock_lbl = Gtk.Label(label="00:00", css_classes=["clock-time"]); rz.append(self.clock_lbl)
        bar.set_end_widget(rz)
        root_box.append(bar)

        # 2. Трёхпанельный интерфейс движка: SceneTree (Слева) | 2D Viewport (Центр) | Inspector + Консоль (Справа)
        ide_body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12); ide_body.set_hexpand(True); ide_body.set_vexpand(True)

        # СЛЕВА: SceneTree & FileSystem Dock
        scene_dock = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scene_dock.add_css_class("ide-panel"); scene_dock.set_size_request(280, -1); scene_dock.set_vexpand(True)
        scene_dock.append(Gtk.Label(label="📂 SceneTree // Иерархия проекта", xalign=0, css_classes=["panel-header"]))
        for n_lbl, n_cmd in [
            ("├─ 🎮 RootNode (Домашняя папка)", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~"),
            ("├─ ⚔ TheDungeonOfGod (Поиск)", "~/.local/bin/launch-free-ws foot -e sh -c 'find ~ -maxdepth 3 -iname \"*dungeon*\" -o -iname \"*game*\"; exec bash'"),
            ("├─ 🖼 Sprites & Assets (Pictures)", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~/Pictures"),
            ("├─ 📦 Builds & Exports (Downloads)", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~/Downloads"),
            ("├─ ⚙ Engine Config (~/CyberDeck)", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~/CyberDeck"),
            ("└─ 🖥 Debug Terminal (Pygame-CE)", "~/.local/bin/launch-free-ws foot"),
        ]:
            nb = Gtk.Button(label=n_lbl); nb.add_css_class("ws-btn"); nb.connect("clicked", lambda _b, c=n_cmd: self.spawn_raw(c)); scene_dock.append(nb)

        scene_dock.append(Gtk.Label(label="📡 Local Dev Server & Ports", xalign=0, css_classes=["panel-header"]))
        self.ports_lbl = Gtk.Label(label=f"Порты: {scan_dev_ports()}\nIP: {read_local_ip()}", xalign=0, css_classes=["panel-sub"])
        scene_dock.append(self.ports_lbl)
        ide_body.append(scene_dock)

        # ЦЕНТР: 2D Viewport (Сетка инструментов и движков)
        vp_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); vp_col.set_hexpand(True); vp_col.set_vexpand(True)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.connect("changed", self.on_filter)
        vp_col.append(self.search)
        vp_col.append(self.build_app_grid(max_cols=3))
        ide_body.append(vp_col)

        # СПРАВА: Inspector (Профайлер FPS/FrameTime + Живая Python/Bash консоль движка)
        insp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        insp.add_css_class("ide-panel"); insp.set_size_request(350, -1); insp.set_vexpand(True)
        insp.append(Gtk.Label(label="🔍 Inspector // Node Properties", xalign=0, css_classes=["panel-header"]))

        self.cpu_lbl = Gtk.Label(label="CPU Load: 0%", xalign=0, css_classes=["panel-sub"]); self.cpu_bar = Gtk.ProgressBar()
        self.ram_lbl = Gtk.Label(label="VRAM/RAM: --", xalign=0, css_classes=["panel-sub"]); self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan")
        self.bat_lbl = Gtk.Label(label="Power/Temp: --", xalign=0, css_classes=["panel-sub"]); self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good")
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar): insp.append(w)

        insp.append(Gtk.Label(label="🐍 Output // Интерактивная консоль движка", xalign=0, css_classes=["panel-header"]))
        out_sc = Gtk.ScrolledWindow(); out_sc.set_vexpand(True)
        tv = Gtk.TextView(); tv.set_editable(False); tv.add_css_class("notes-view"); tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.ide_out_buf = tv.get_buffer()
        self.ide_out_buf.set_text("🎮 Engine Console Ready (Python 3 / Bash).\nВведите команду снизу для проверки логов или расчёта.\n")
        out_sc.set_child(tv); insp.append(out_sc)

        ide_ent = Gtk.Entry(); ide_ent.add_css_class("search-entry")
        ide_ent.set_placeholder_text("Команда (python3 -V, git status, ls)...")
        ide_ent.connect("activate", self.on_ide_cmd)
        insp.append(ide_ent)

        ide_body.append(insp)
        root_box.append(ide_body)

    def on_ide_cmd(self, entry):
        cmd = entry.get_text().strip()
        if not cmd or not self.ide_out_buf: return
        entry.set_text("")
        try:
            out = subprocess.check_output(["/bin/bash", "-c", cmd], stderr=subprocess.STDOUT, text=True, timeout=3.0)
        except Exception as e:
            out = getattr(e, "output", str(e))
        old = self.ide_out_buf.get_text(self.ide_out_buf.get_start_iter(), self.ide_out_buf.get_end_iter(), False)
        self.ide_out_buf.set_text(f"{old}\n▶ {cmd}\n{out.strip()}\n"[-3000:])

    def do_activate(self):
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)
            settings.set_property("gtk-cursor-theme-name", CUR_THEME_NAME)
            settings.set_property("gtk-cursor-theme-size", 28)

        prov = Gtk.CssProvider()
        prov.load_from_string(load_css())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 25)

        win = Gtk.ApplicationWindow(application=self, title="WorkHubDesktop")
        Gtk4LayerShell.init_for_window(win)
        Gtk4LayerShell.set_namespace(win, "work-hub-wallpaper")
        Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.BACKGROUND)
        for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
            Gtk4LayerShell.set_anchor(win, edge, True)
        Gtk4LayerShell.set_exclusive_zone(win, -1)
        Gtk4LayerShell.set_keyboard_mode(win, Gtk4LayerShell.KeyboardMode.ON_DEMAND)

        overlay = Gtk.Overlay()
        if self.layout_mode == "dungeon":
            # В 2-й теме (The Dungeon of God) вместо статичной картинки работает ЖИВОЙ анимированный холст!
            live_area = Gtk.DrawingArea()
            live_area.set_hexpand(True); live_area.set_vexpand(True)
            live_area.set_draw_func(self.draw_dungeon_live_bg)
            GLib.timeout_add(33, lambda: (live_area.queue_draw(), True)[1])
            overlay.set_child(live_area)
        elif os.path.isfile(BG_PNG):
            bg_pic = Gtk.Picture.new_for_filename(BG_PNG)
            bg_pic.set_can_shrink(True)
            if hasattr(Gtk, "ContentFit"): bg_pic.set_content_fit(Gtk.ContentFit.COVER)
            overlay.set_child(bg_pic)

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root_box.add_css_class("hub-overlay")
        root_box.set_hexpand(True); root_box.set_vexpand(True)

        if self.layout_mode == "dungeon":
            self.build_world_dungeon(root_box)
        elif self.layout_mode == "forest":
            self.build_world_forest(root_box)
        elif self.layout_mode == "impasto":
            self.build_world_impasto(root_box)
        elif self.layout_mode == "gamedev":
            self.build_world_gamedev(root_box)
        else:
            self.build_world_cyberdeck(root_box)

        overlay.add_overlay(root_box); win.set_child(overlay)
        self.populate_apps(); self.refresh_workspaces(); self.refresh_status()
        GLib.timeout_add(1200, self.refresh_workspaces)
        GLib.timeout_add_seconds(3, self.refresh_status)
        win.present()

    def on_pomo_tick(self):
        if self.pomo_running and self.pomo_lbl:
            if self.pomo_sec > 0:
                self.pomo_sec -= 1
                self.pomo_lbl.set_label(f"{self.pomo_sec // 60:02d}:{self.pomo_sec % 60:02d}")
            else:
                self.pomo_running = False
        return True

    def populate_apps(self):
        while True:
            ch = self.flow.get_first_child()
            if ch is None: break
            self.flow.remove(ch)
        self.cards.clear()

        items = discover_work_apps()
        items.sort(key=lambda x: (0 if x[0] in self.pinned else 1, x[0].lower()))
        if self.search:
            self.search.set_placeholder_text(f"{ENV_META.get('symbol', '◈')} Поиск среди {len(items)} программ (ЛКМ: запуск • ПКМ: в избранное)...")

        rpg_buffs = ["+25% СКОРОСТЬ КОДА", "+40% FPS РЕНДЕРА", "+30% КРИТ АЛГОРИТМОВ", "+50 ЗАЩИТА ЯДРА", "+20% РЕГЕНЕРАЦИЯ ОЗУ"]

        for idx, (name, cmd, icon_spec, cat_tag) in enumerate(items, 1):
            is_pin = name in self.pinned
            btn = Gtk.Button()

            if self.layout_mode == "dungeon":
                # Карточка Артефакта / Оружия из The Dungeon of God
                btn.add_css_class("dungeon-card-legendary" if is_pin else "dungeon-card-epic")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                ic_box = Gtk.Box(); ic_box.add_css_class("icon-frame"); ic_box.set_valign(Gtk.Align.CENTER)
                ic_box.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 34)); hb.append(ic_box)
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3); vb.set_valign(Gtk.Align.CENTER); vb.set_hexpand(True)
                rar = Gtk.Label(label="★ [МИФИЧЕСКИЙ АРТЕФАКТ]" if is_pin else f"⚔ [{cat_tag} // РЕЛИКВИЯ]", xalign=0)
                rar.add_css_class("rarity-leg" if is_pin else "rarity-epic"); vb.append(rar)
                t = Gtk.Label(label=name, xalign=0, css_classes=["card-title"]); t.set_ellipsize(Pango.EllipsizeMode.END); vb.append(t)
                buff = Gtk.Label(label=rpg_buffs[idx % len(rpg_buffs)], xalign=0, css_classes=["stat-buff"]); vb.append(buff)
                hb.append(vb); btn.set_child(hb)

            elif self.layout_mode == "forest":
                btn.add_css_class("forest-card")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                hb.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 34))
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); vb.set_valign(Gtk.Align.CENTER); vb.set_hexpand(True)
                vb.append(Gtk.Label(label=name[:20], xalign=0, css_classes=["card-title"]))
                vb.append(Gtk.Label(label="🌿 Избранное" if is_pin else f"🌿 {cat_tag}", xalign=0, css_classes=["card-sub"]))
                hb.append(vb); btn.set_child(hb)

            elif self.layout_mode == "impasto":
                btn.add_css_class("impasto-card")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                hb.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 34))
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); vb.set_valign(Gtk.Align.CENTER); vb.set_hexpand(True)
                vb.append(Gtk.Label(label=name[:20], xalign=0, css_classes=["card-title"]))
                vb.append(Gtk.Label(label=f"🎨 Холст #{idx:02d} • {cat_tag}", xalign=0, css_classes=["card-sub"]))
                hb.append(vb); btn.set_child(hb)

            elif self.layout_mode == "gamedev":
                btn.add_css_class("gamedev-node")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                hb.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 28))
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); vb.set_valign(Gtk.Align.CENTER); vb.set_hexpand(True)
                vb.append(Gtk.Label(label=f"Node2D :: {name[:16]}", xalign=0, css_classes=["card-title"]))
                vb.append(Gtk.Label(label=f"[{cat_tag}_SCRIPT] • Ready", xalign=0, css_classes=["panel-sub"]))
                hb.append(vb); btn.set_child(hb)

            else:
                btn.add_css_class("app-card")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                stripe = Gtk.Box(); stripe.add_css_class("stripe-pinned" if is_pin else "stripe-normal"); stripe.set_vexpand(True); hb.append(stripe)
                ic_box = Gtk.Box(); ic_box.add_css_class("icon-frame"); ic_box.set_valign(Gtk.Align.CENTER)
                ic_box.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 34)); hb.append(ic_box)
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); vb.set_valign(Gtk.Align.CENTER); vb.set_hexpand(True)
                vb.append(Gtk.Label(label=name[:20], xalign=0, css_classes=["card-title"]))
                vb.append(Gtk.Label(label="★ PINNED" if is_pin else f"{cat_tag} • FREE WS", xalign=0, css_classes=["card-sub"]))
                hb.append(vb); hb.append(Gtk.Label(label="⟫", css_classes=["launch-glyph"])); btn.set_child(hb)

            btn.connect("clicked", lambda _b, c=cmd: self.spawn_raw(f"$HOME/.local/bin/launch-free-ws {c}"))
            rc = Gtk.GestureClick.new(); rc.set_button(3)
            rc.connect("pressed", lambda _g, _n, _x, _y, nm=name: self.toggle_pin(nm))
            btn.add_controller(rc)
            self.flow.append(btn); self.cards.append((name.lower(), btn))

        if self.dock_box is not None:
            while True:
                c = self.dock_box.get_first_child()
                if c is None: break
                self.dock_box.remove(c)
            favs = [it for it in items if it[0] in self.pinned][:7] or items[:6]
            for name, cmd, _ic, _cat in favs:
                db = Gtk.Button(label=name[:14]); db.add_css_class("ws-btn")
                db.connect("clicked", lambda _b, c=cmd: self.spawn_raw(f"$HOME/.local/bin/launch-free-ws {c}"))
                self.dock_box.append(db)

        self.on_filter(self.search)

    def toggle_pin(self, name):
        if name in self.pinned: self.pinned.remove(name)
        else: self.pinned.add(name)
        save_pinned(self.pinned); self.populate_apps()

    def on_filter(self, entry):
        q = entry.get_text().strip().lower() if entry else ""
        for tl, btn in self.cards:
            if btn.get_parent(): btn.get_parent().set_visible((not q) or (q in tl))

    def refresh_workspaces(self):
        try:
            if os.path.isfile(KB_FILE) and self.kb_btn:
                kb_code = open(KB_FILE).read().strip() or "EN"
                if self.kb_btn.get_label() != kb_code: self.kb_btn.set_label(kb_code)
        except Exception: pass
        try:
            bg_list = cyber_bg.get_bg_and_open_items()
            cnt = sum(i.get("count", 1) for i in bg_list)
            lbl_bg = f"🎒 Фон [{cnt}]" if self.layout_mode == "dungeon" else f"◈ Фон [{cnt}]"
            if self.bg_menu_btn and self.bg_menu_btn.get_label() != lbl_bg:
                self.bg_menu_btn.set_label(lbl_bg)

            if self.ws_box:
                clients = cyber_bg.hypr_ipc_json("clients")
                ws_map = {}
                for cl in clients:
                    wid = cl.get("workspace", {}).get("id", -1)
                    if wid > 0 and wid not in ws_map: ws_map[wid] = (cl.get("class") or cl.get("title") or "App")[:8]
                sig = tuple(sorted(ws_map.items()))
                if sig != self.last_ws_sig:
                    self.last_ws_sig = sig
                    while True:
                        ch = self.ws_box.get_first_child()
                        if ch is None: break
                        self.ws_box.remove(ch)
                    for wid, cname in sig:
                        b = Gtk.Button(label=f"[{wid}] {cname}"); b.add_css_class("ws-btn")
                        b.connect("clicked", lambda _b, w=wid: self.spawn_raw(f"hyprctl dispatch workspace {w}"))
                        self.ws_box.append(b)
        except Exception: pass
        return True

    def read_power_mode(self):
        try:
            if os.path.isfile("/run/cyberdeck-power-mode") and open("/run/cyberdeck-power-mode").read().strip() == "performance":
                return "performance"
        except Exception: pass
        return "eco"

    def update_pwr_label(self):
        if not self.pwr_btn: return
        is_perf = (self.read_power_mode() == "performance")
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); hb.set_valign(Gtk.Align.CENTER)
        hb.append(ui_svg("turbo.svg" if is_perf else "eco.svg", 14))
        hb.append(Gtk.Label(label="Перфоманс" if is_perf else "Эко"))
        self.pwr_btn.set_child(hb)

    def on_toggle_power(self, _b):
        subprocess.run([os.path.join(HOME, ".local/bin/cyber-power"), "toggle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.update_pwr_label()

    def get_current_bri(self):
        try:
            for bdir in sorted(glob.glob("/sys/class/backlight/*")):
                cur = float(open(os.path.join(bdir, "brightness")).read().strip())
                mx = float(open(os.path.join(bdir, "max_brightness")).read().strip())
                if mx > 0: return max(5.0, min(100.0, round(cur * 100.0 / mx)))
        except Exception: pass
        return 90.0

    def set_hw_bri(self, val):
        val = max(5, min(100, int(val)))
        for bdir in sorted(glob.glob("/sys/class/backlight/*")):
            try:
                mx = int(open(os.path.join(bdir, "max_brightness")).read().strip())
                open(os.path.join(bdir, "brightness"), "w").write(str(max(1, int(round(mx * val / 100.0)))))
                return
            except Exception: pass
        subprocess.Popen(["brightnessctl", "-q", "set", f"{val}%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def on_bri_changed(self, scale):
        val = int(scale.get_value())
        if self.bri_pct_lbl: self.bri_pct_lbl.set_label(f"{val}%")
        self.set_hw_bri(val)

    def on_bri_icon_clicked(self, _b):
        if self.bri_scale:
            cur = int(self.bri_scale.get_value()); self.bri_scale.set_value(100 if cur < 95 else 60)

    def get_current_vol(self):
        try: return float(subprocess.check_output(["pamixer", "--get-volume"], text=True, stderr=subprocess.DEVNULL).strip())
        except Exception: return 50.0

    def on_vol_changed(self, scale):
        val = int(scale.get_value())
        if self.vol_pct_lbl: self.vol_pct_lbl.set_label(f"{val}%")
        subprocess.Popen(["pamixer", "--set-volume", str(val)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def refresh_status(self):
        if self.clock_lbl: self.clock_lbl.set_label(datetime.datetime.now().strftime("%H:%M"))

        idle, total = read_cpu_stat()
        dt, di = total - self.prev_total, idle - self.prev_idle
        self.prev_idle, self.prev_total = idle, total
        cpu_pct = int(round(100.0 * (dt - di) / dt)) if dt > 0 else 0
        cpu_f = min(1.0, max(0.0, cpu_pct / 100.0))

        ram_txt, ram_frac = read_ram_info()
        binfo = read_battery()
        pct = int(binfo.get("pct", 100))

        if self.layout_mode == "dungeon":
            if self.cpu_lbl: self.cpu_lbl.set_label(f"❤ HP {100 - cpu_pct}%")
            if self.cpu_bar: self.cpu_bar.set_fraction(max(0.08, 1.0 - cpu_f))
            if self.ram_lbl: self.ram_lbl.set_label(f"✦ MP {ram_txt}")
            if self.ram_bar: self.ram_bar.set_fraction(ram_frac)
            if self.bat_lbl: self.bat_lbl.set_label(f"⚡ STAM {pct}%")
            if self.bat_bar: self.bat_bar.set_fraction(min(1.0, max(0.0, pct / 100.0)))
        else:
            if self.cpu_lbl: self.cpu_lbl.set_label(f"CPU {cpu_pct}%")
            if self.cpu_bar: self.cpu_bar.set_fraction(cpu_f)
            if self.ram_lbl: self.ram_lbl.set_label(f"RAM {ram_txt}")
            if self.ram_bar: self.ram_bar.set_fraction(ram_frac)
            if self.bat_lbl: self.bat_lbl.set_label("AC 100%" if not binfo.get("present") else f"BAT {pct}%")
            if self.bat_bar: self.bat_bar.set_fraction(min(1.0, max(0.0, pct / 100.0)))

        if self.wifi_btn:
            w_info = read_wifi_state()
            self.wifi_btn.set_child(ui_svg(w_info.get("icon", "wifi-high.svg"), 15))
        self.update_pwr_label()
        if self.ports_lbl:
            self.ports_lbl.set_label(f"Порты: {scan_dev_ports()}\nIP: {read_local_ip()}")
        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    WorkHubApp().run(None)
