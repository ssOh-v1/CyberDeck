#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
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
    return " ".join(ports[:4]) if ports else "нет активных портов"

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

        # Предзагружаем поверхность обоев один раз в RAM (гарантирует отсутствие чёрного экрана и 0% лагов!)
        self.bg_surface = None
        if os.path.isfile(BG_PNG):
            try:
                self.bg_surface = cairo.ImageSurface.create_from_png(BG_PNG)
            except Exception:
                self.bg_surface = None

        self.flow = None
        self.search = None
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

        random.seed(77)
        self.embers = [
            (random.uniform(0.08, 0.92), random.uniform(22.0, 52.0), random.uniform(-16.0, 16.0), random.uniform(1.8, 3.6), random.random())
            for _ in range(22)
        ]

    # ==========================================================================
    # ОТРИСОВКА ОБОЕВ (Статичные для 1,3,4,5 + Быстрые живые обои для 2-й темы!)
    # ==========================================================================
    def on_draw_background(self, _area, cr, w, h, *_args):
        cr.save()
        cr.scale(w / 1920.0, h / 1080.0)
        W, H = 1920, 1080

        if self.bg_surface is not None:
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0.05, 0.06, 0.09)
            cr.paint()

        if self.layout_mode == "dungeon":
            # Лёгкая 20-FPS анимация поверх предрендеренной сцены The Dungeon of God (< 0.4 мс на кадр!)
            dt = time.monotonic() - self.t0
            cx, cy = W * 0.5, H * 0.56

            # 1. Пульсация пламени в двух жаровнях на платформе
            fl = 0.75 + 0.25 * math.sin(dt * 6.5)
            for bx in (cx - 250, cx + 250):
                by = H * 0.74 - 46
                cr.set_source_rgba(0.98, 0.42, 0.15, 0.70 * fl)
                cr.arc(bx, by, 16 * fl, 0, 2 * math.pi); cr.fill()
                cr.set_source_rgba(1.0, 0.85, 0.30, 0.95)
                cr.arc(bx, by - 4 * fl, 8 * fl, 0, 2 * math.pi); cr.fill()

            # 2. Левитирующий мифический меч над центральным алтарём
            bob_y = math.sin(dt * 2.4) * 11.0
            sx, sy = cx, H * 0.74 - 125 + bob_y
            # Золотая аура вокруг клинка
            cr.set_line_width(2.0); cr.set_source_rgba(0.96, 0.74, 0.22, 0.45 + 0.25 * math.sin(dt * 3.2))
            cr.arc(sx, sy, 54, 0, 2 * math.pi); cr.stroke()
            # Гарда и лезвие меча
            cr.set_source_rgb(0.96, 0.74, 0.22)
            cr.rectangle(sx - 4, sy - 68, 8, 22); cr.fill()
            cr.move_to(sx - 24, sy - 46); cr.line_to(sx + 24, sy - 46); cr.line_to(sx + 16, sy - 38); cr.line_to(sx - 16, sy - 38); cr.close_path(); cr.fill()
            cr.set_source_rgb(0.92, 0.24, 0.18)
            cr.move_to(sx - 7, sy - 38); cr.line_to(sx + 7, sy - 38); cr.line_to(sx, sy + 36); cr.close_path(); cr.fill_preserve()
            cr.set_line_width(1.6); cr.set_source_rgb(1.0, 0.82, 0.35); cr.stroke()

            # 3. 22 лёгкие искры пламени, поднимающиеся к сводам подземелья
            for x0, spd, vx, sz, ph in self.embers:
                cyc = ((dt * (spd / 280.0)) + ph) % 1.0
                ex = (x0 * W + cyc * vx * 2.5) % W
                ey = H - cyc * (H * 0.88)
                cr.set_source_rgba(0.98, 0.76, 0.24, (1.0 - cyc) * 0.85)
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
        sddm_b = Gtk.Button(label="SDDM"); sddm_b.add_css_class("danger-act-btn"); sddm_b.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme --sync-session; hyprctl dispatch exit")); sys_cap.append(sddm_b)
        reb_b = Gtk.Button(); reb_b.add_css_class("icon-act-btn"); reb_b.set_child(ui_svg("reboot.svg", 15)); reb_b.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme --sync-session; systemctl reboot")); sys_cap.append(reb_b)
        off_b = Gtk.Button(); off_b.add_css_class("danger-act-btn"); off_b.set_child(ui_svg("power.svg", 15)); off_b.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme --sync-session; systemctl poweroff")); sys_cap.append(off_b)
        return sys_cap

    def make_compact_dock(self, prefix_sym="◈", rofi_label="Все приложения"):
        dock = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dock.add_css_class("bottom-dock"); dock.set_halign(Gtk.Align.CENTER); dock.set_vexpand(False)
        for lbl, cmd in [
            (f"{prefix_sym} Терминал", "~/.local/bin/launch-free-ws foot"),
            (f"{prefix_sym} Проводник", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm"),
            (f"{prefix_sym} Браузер", "~/.local/bin/launch-free-ws firefox"),
            (f"{prefix_sym} Поверх окон", "~/.local/bin/hyprwork-pin-window"),
            (f"{prefix_sym} Скриншот", "~/.local/bin/cyber-tool shot"),
        ]:
            b = Gtk.Button(label=lbl); b.add_css_class("dock-item")
            b.connect("clicked", lambda _b, c=cmd: self.spawn_raw(c))
            dock.append(b)

        self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dock.append(self.dock_box)

        all_b = Gtk.Button(label=f"🚀 {rofi_label} [Rofi]"); all_b.add_css_class("primary-btn")
        all_b.connect("clicked", lambda _b: self.spawn_raw(f'rofi -show drun -theme "{ROFI_THEME}" -run-command "$HOME/.local/bin/launch-free-ws {{cmd}}"'))
        dock.append(all_b)
        return dock

    # ==========================================================================
    # 1. CYBERDECK CLASSIC (Единственная тема с полноэкранным GTK-меню карточек!)
    # ==========================================================================
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
        tb = Gtk.Button(label="◈ Сменить мир"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme menu")); lz.append(tb)
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

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True); scroll.set_hexpand(True)
        self.flow = Gtk.FlowBox(); self.flow.set_valign(Gtk.Align.START); self.flow.set_max_children_per_line(5); self.flow.set_min_children_per_line(2)
        self.flow.set_column_spacing(12); self.flow.set_row_spacing(12); self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.flow); root_box.append(scroll)

        ftr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); ftr.add_css_class("footer-bar"); ftr.set_halign(Gtk.Align.CENTER)
        for kt, dt in [("SUPER+SPACE", "Свободный стол"), ("SUPER+T", "Выбор из 5 миров"), ("SUPER+SHIFT+P", "Перфоманс/Эко"), ("SUPER+P", "Поверх окон"), ("SUPER+E", "Проводник")]:
            ftr.append(Gtk.Label(label=kt, css_classes=["key-badge"])); ftr.append(Gtk.Label(label=dt, css_classes=["key-desc"]))
        root_box.append(ftr)

    # ==========================================================================
    # 2. THE DUNGEON OF GOD (Открытый живой рабочий стол + RPG-панель + Угловой Алтарь + Хотбар)
    # ==========================================================================
    def build_world_dungeon(self, root_box):
        # 1. Верхняя RPG HUD-панель
        rpg_top = Gtk.CenterBox(); rpg_top.add_css_class("rpg-bar"); rpg_top.set_vexpand(False)
        lz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); hb.add_css_class("brand-pill")
        hb.append(Gtk.Label(label="⚔ THE DUNGEON OF GOD // ssOh-v1", css_classes=["brand-title"]))
        lz.append(hb)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); lz.append(self.ws_box)
        bp = Gtk.Button(label="+ Этаж"); bp.add_css_class("ws-new-btn"); bp.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); lz.append(bp)
        self.bg_menu_btn = Gtk.Button(label="🎒 Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); lz.append(self.bg_menu_btn)
        tb = Gtk.Button(label="⚔ Сменить мир"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme menu")); lz.append(tb)
        rpg_top.set_start_widget(lz)

        bars = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.cpu_lbl = Gtk.Label(label="❤ HP 100%", css_classes=["metric-lbl"]); self.cpu_bar = Gtk.ProgressBar(); self.cpu_bar.add_css_class("hp-bar"); self.cpu_bar.set_valign(Gtk.Align.CENTER)
        self.ram_lbl = Gtk.Label(label="✦ MP", css_classes=["metric-lbl"]); self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("mana-bar"); self.ram_bar.set_valign(Gtk.Align.CENTER)
        self.bat_lbl = Gtk.Label(label="⚡ STAM", css_classes=["metric-lbl"]); self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("stamina-bar"); self.bat_bar.set_valign(Gtk.Align.CENTER)
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar): bars.append(w)
        rpg_top.set_center_widget(bars)

        rz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); rz.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); rz.append(self.pwr_btn)
        rz.append(self.make_sliders_pair(46))
        rz.append(self.make_sys_power_capsule())
        self.clock_lbl = Gtk.Label(label="00:00", css_classes=["clock-time"]); rz.append(self.clock_lbl)
        rpg_top.set_end_widget(rz)
        root_box.append(rpg_top)

        # 2. Открытый рабочий стол (центр полностью свободен для живых обоев с мечом и вратами!)
        mid_space = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL); mid_space.set_vexpand(True); mid_space.set_hexpand(True)

        # Компактный угловой виджет «Алтарь Артефактов» слева внизу (не закрывает центр!)
        shrine_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        shrine_card.add_css_class("rpg-bar"); shrine_card.set_size_request(310, -1)
        shrine_card.set_valign(Gtk.Align.END); shrine_card.set_halign(Gtk.Align.START)
        shrine_card.append(Gtk.Label(label="🎲 АЛТАРЬ АРТЕФАКТОВ // ssOh-v1", xalign=0, css_classes=["panel-header"]))
        self.loot_lbl = Gtk.Label(
            label="[МИФИЧЕСКИЙ] ⚔ Клинок Бога\n• Урон в прыжке: +45%  • Крит: +20%",
            xalign=0, css_classes=["panel-sub"]
        )
        shrine_card.append(self.loot_lbl)
        b_roll = Gtk.Button(label="🎲 Выковать случайный предмет"); b_roll.add_css_class("primary-btn")
        b_roll.connect("clicked", self.on_roll_dungeon_loot)
        shrine_card.append(b_roll)
        mid_space.append(shrine_card)
        root_box.append(mid_space)

        # 3. Нижний пояс-хотбар искателя подземелий (RPG Action Belt)
        root_box.append(self.make_compact_dock("⚔", "Гримуар свитков"))

    def on_roll_dungeon_loot(self, _b):
        artifacts = [
            ("[МИФИЧЕСКИЙ] ⚔ Коса Падшего Бога", "• +65% Урон в воздухе  • +15% Вампиризм"),
            ("[ЛЕГЕНДАРНЫЙ] 🛡 Эгида Бездны", "• +40 Броня  • Отражает снаряды мобов"),
            ("[ЛЕГЕНДАРНЫЙ] 💍 Кольцо ssOh-v1", "• +100% Скорость кода  • 0 мс задержка"),
            ("[ЭПИЧЕСКИЙ] 🗡 Парные Клинки Теней", "• +35% Скорость атаки  • Двойной рывок"),
            ("[ЛЕГЕНДАРНЫЙ] 🔥 Фонарь Душ", "• Освещает секреты  • +25% Редкий лут"),
        ]
        name, stats = random.choice(artifacts)
        if self.loot_lbl:
            self.loot_lbl.set_label(f"{name}\n{stats}")

    # ==========================================================================
    # 3. ЛЕСНОЙ РУЧЕЙ (Открытый стол с соснами и ручьём + Парящий Waybar + Док)
    # ==========================================================================
    def build_world_forest(self, root_box):
        # Верхний парящий Waybar из 3 капсул
        wb = Gtk.CenterBox(); wb.set_vexpand(False)

        pl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); pl.add_css_class("waybar-pill")
        pl.append(Gtk.Label(label="🌿 Лесной Ручей", css_classes=["brand-title"]))
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); pl.append(self.ws_box)
        nb = Gtk.Button(label="+ Поляна"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); pl.append(nb)
        self.bg_menu_btn = Gtk.Button(label="🌿 Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); pl.append(self.bg_menu_btn)
        tb = Gtk.Button(label="🌿 Сменить мир"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme menu")); pl.append(tb)
        wb.set_start_widget(pl)

        pc = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12); pc.add_css_class("waybar-pill")
        self.clock_lbl = Gtk.Label(label="00:00", css_classes=["clock-time"]); pc.append(self.clock_lbl)
        self.cpu_lbl = Gtk.Label(label="CPU 0%", css_classes=["metric-lbl"]); pc.append(self.cpu_lbl)
        self.ram_lbl = Gtk.Label(label="RAM --", css_classes=["metric-lbl"]); pc.append(self.ram_lbl)
        self.bat_lbl = Gtk.Label(label="BAT --%", css_classes=["metric-lbl"]); pc.append(self.bat_lbl)
        wb.set_center_widget(pc)

        pr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); pr.add_css_class("waybar-pill")
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_child(ui_svg("wifi-high.svg", 15))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu")); pr.append(self.wifi_btn)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); pr.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); pr.append(self.pwr_btn)
        pr.append(self.make_sliders_pair(46))
        pr.append(self.make_sys_power_capsule())
        wb.set_end_widget(pr)
        root_box.append(wb)

        # Открытый центр рабочего стола + маленький угловой виджет «Таймер Потока» справа вверху
        mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL); mid.set_vexpand(True); mid.set_hexpand(True)
        sp = Gtk.Box(); sp.set_hexpand(True); mid.append(sp)

        zen_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        zen_card.add_css_class("widget-panel"); zen_card.set_size_request(240, -1)
        zen_card.set_valign(Gtk.Align.START); zen_card.set_halign(Gtk.Align.END)
        zen_card.append(Gtk.Label(label="🌿 ТАЙМЕР ПОТОКА", xalign=0, css_classes=["panel-header"]))
        self.pomo_lbl = Gtk.Label(label="20:00", xalign=0, css_classes=["timer-digits"]); zen_card.append(self.pomo_lbl)
        bp = Gtk.Button(label="Старт / Пауза"); bp.add_css_class("primary-btn")
        bp.connect("clicked", lambda _b: setattr(self, "pomo_running", not self.pomo_running))
        zen_card.append(bp)
        mid.append(zen_card)
        root_box.append(mid)
        GLib.timeout_add_seconds(1, self.on_pomo_tick)

        # Нижний стеклянный док
        root_box.append(self.make_compact_dock("🌿", "Все программы"))

    # ==========================================================================
    # 4. ИМПАСТО ПЕЙЗАЖ (Открытый холст с 3D-мазками + Узкий левый мольберт + Палитра в углу)
    # ==========================================================================
    def build_world_impasto(self, root_box):
        atelier = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16); atelier.set_hexpand(True); atelier.set_vexpand(True)

        # Левый вертикальный мольберт-док (Side-Waybar 235px)
        easel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        easel.add_css_class("side-rail"); easel.set_size_request(235, -1); easel.set_vexpand(True)
        easel.append(Gtk.Label(label="🎨 ИМПАСТО // ХОЛСТ", xalign=0, css_classes=["panel-header"]))
        self.clock_lbl = Gtk.Label(label="00:00", xalign=0, css_classes=["big-clock"]); easel.append(self.clock_lbl)

        self.cpu_lbl = Gtk.Label(label="CPU 0%", xalign=0, css_classes=["metric-lbl"]); self.cpu_bar = Gtk.ProgressBar()
        self.ram_lbl = Gtk.Label(label="RAM --", xalign=0, css_classes=["metric-lbl"]); self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan")
        self.bat_lbl = Gtk.Label(label="BAT --%", xalign=0, css_classes=["metric-lbl"]); self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good")
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar): easel.append(w)

        easel.append(Gtk.Label(label="🎨 АКТИВНЫЕ ХОЛСТЫ", xalign=0, css_classes=["panel-header"]))
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); easel.append(self.ws_box)
        row_b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        nb = Gtk.Button(label="+ Холст"); nb.add_css_class("ws-new-btn"); nb.set_hexpand(True); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws"))
        self.bg_menu_btn = Gtk.Button(label="🎨 Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.set_hexpand(True); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu"))
        row_b.append(nb); row_b.append(self.bg_menu_btn); easel.append(row_b)

        tb = Gtk.Button(label="🎨 Сменить мир [SUPER+T]"); tb.add_css_class("primary-btn"); tb.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme menu")); easel.append(tb)

        easel.append(Gtk.Label(label="🎨 ПАЛИТРА МАСЛА (HEX)", xalign=0, css_classes=["panel-header"]))
        for s_name, s_hex in [("Охра Золотая", "#F2CC8F"), ("Терракота", "#E07A5F"), ("Ультрамарин", "#3D405B"), ("Шалфей Масло", "#81B29A")]:
            sb = Gtk.Button(label=f"🖌 {s_name} ({s_hex})"); sb.add_css_class("secondary-btn")
            sb.connect("clicked", lambda _b, h=s_hex, n=s_name: self.spawn_raw(f"printf '{h}' | wl-copy && notify-send '🎨 ПАЛИТРА ИМПАСТО' 'Краска {n} ({h}) скопирована!'"))
            easel.append(sb)

        sp = Gtk.Box(); sp.set_vexpand(True); easel.append(sp)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); easel.append(self.pwr_btn)
        easel.append(self.make_sliders_pair(48))
        easel.append(self.make_sys_power_capsule())
        atelier.append(easel)

        # Правая часть (85% экрана) — ПОЛНОСТЬЮ ОТКРЫТЫЙ РЕЛЬЕФНЫЙ ПЕЙЗАЖ С БУГОРКАМИ КРАСКИ + компактный док внизу!
        canvas_zone = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); canvas_zone.set_hexpand(True); canvas_zone.set_vexpand(True)
        sp_c = Gtk.Box(); sp_c.set_vexpand(True); canvas_zone.append(sp_c)
        canvas_zone.append(self.make_compact_dock("🎨", "Галерея программ"))
        atelier.append(canvas_zone)
        root_box.append(atelier)

    # ==========================================================================
    # 5. GAMEDEV ENGINE STUDIO (Открытый 2D Viewport + Тулбар движка + Компактный инспектор)
    # ==========================================================================
    def build_world_gamedev(self, root_box):
        # Верхний Тулбар Движка
        bar = Gtk.CenterBox(); bar.add_css_class("ide-toolbar"); bar.set_vexpand(False)
        lz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lz.append(Gtk.Label(label="🎮 ENGINE // STUDIO", css_classes=["panel-header"]))
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); lz.append(self.ws_box)
        nb = Gtk.Button(label="+ Scene"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); lz.append(nb)
        self.bg_menu_btn = Gtk.Button(label="📦 Nodes [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); lz.append(self.bg_menu_btn)
        tb = Gtk.Button(label="🎮 Сменить мир"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-theme menu")); lz.append(tb)
        bar.set_start_widget(lz)

        play_c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        b_play = Gtk.Button(label="▶ Play / Перфоманс"); b_play.add_css_class("ide-play-btn")
        b_play.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-power performance; ~/.local/bin/launch-free-ws foot"))
        b_bld = Gtk.Button(label="🔨 Папка проектов"); b_bld.add_css_class("ide-build-btn")
        b_bld.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~"))
        b_prof = Gtk.Button(label="📊 Btop"); b_prof.add_css_class("ctrl-pill")
        b_prof.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-tool btop"))
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label()
        for w in (b_play, b_bld, b_prof, self.pwr_btn): play_c.append(w)
        bar.set_center_widget(play_c)

        rz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); rz.append(self.kb_btn)
        rz.append(self.make_sliders_pair(46))
        rz.append(self.make_sys_power_capsule())
        self.clock_lbl = Gtk.Label(label="00:00", css_classes=["clock-time"]); rz.append(self.clock_lbl)
        bar.set_end_widget(rz)
        root_box.append(bar)

        # Открытый центральный 2D Viewport + компактный угловой виджет Инспектора справа внизу
        mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL); mid.set_vexpand(True); mid.set_hexpand(True)
        sp = Gtk.Box(); sp.set_hexpand(True); mid.append(sp)

        insp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        insp.add_css_class("ide-panel"); insp.set_size_request(300, -1)
        insp.set_valign(Gtk.Align.END); insp.set_halign(Gtk.Align.END)
        insp.append(Gtk.Label(label="🔍 INSPECTOR // TELEMETRY", xalign=0, css_classes=["panel-header"]))
        self.cpu_lbl = Gtk.Label(label="CPU: 0%", xalign=0, css_classes=["panel-sub"]); self.cpu_bar = Gtk.ProgressBar()
        self.ram_lbl = Gtk.Label(label="RAM: --", xalign=0, css_classes=["panel-sub"]); self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan")
        self.bat_lbl = Gtk.Label(label="PWR: --", xalign=0, css_classes=["panel-sub"]); self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good")
        self.ports_lbl = Gtk.Label(label=f"Ports: {scan_dev_ports()}", xalign=0, css_classes=["panel-sub"])
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar, self.ports_lbl): insp.append(w)
        mid.append(insp)
        root_box.append(mid)

        # Нижний док разработчика игр
        root_box.append(self.make_compact_dock("🎮", "Все инструменты"))

    def do_activate(self):
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)
            settings.set_property("gtk-cursor-theme-name", CUR_THEME_NAME)
            settings.set_property("gtk-cursor-theme-size", 28)

        prov = Gtk.CssProvider()
        prov.load_from_string(load_css())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 25)

        w_mon, h_mon, _ = get_monitor_info()
        win = Gtk.ApplicationWindow(application=self, title="WorkHubDesktop")
        win.set_default_size(w_mon, h_mon)
        Gtk4LayerShell.init_for_window(win)
        Gtk4LayerShell.set_namespace(win, "work-hub-wallpaper")
        Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.BACKGROUND)
        for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
            Gtk4LayerShell.set_anchor(win, edge, True)
        Gtk4LayerShell.set_exclusive_zone(win, -1)
        Gtk4LayerShell.set_keyboard_mode(win, Gtk4LayerShell.KeyboardMode.ON_DEMAND)

        overlay = Gtk.Overlay()

        # Полноэкранный холст обоев (никогда не схлопывается в чёрный экран!)
        bg_area = Gtk.DrawingArea()
        bg_area.set_hexpand(True); bg_area.set_vexpand(True)
        bg_area.set_size_request(w_mon, h_mon)
        bg_area.set_draw_func(self.on_draw_background)
        if self.layout_mode == "dungeon":
            # Лёгкий 20 FPS таймер только для парящего меча и искр (0% лагов!)
            GLib.timeout_add(50, lambda: (bg_area.queue_draw(), True)[1])
        overlay.set_child(bg_area)

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
        items = discover_work_apps()
        items.sort(key=lambda x: (0 if x[0] in self.pinned else 1, x[0].lower()))

        # Полная сетка карточек строится ТОЛЬКО в 1-й теме (CyberDeck Classic)!
        if self.flow is not None:
            while True:
                ch = self.flow.get_first_child()
                if ch is None: break
                self.flow.remove(ch)
            self.cards.clear()
            if self.search:
                self.search.set_placeholder_text(f"◈ Поиск среди {len(items)} программ (ЛКМ: новый стол • ПКМ: закрепить)...")

            for name, cmd, icon_spec, cat_tag in items:
                is_pin = name in self.pinned
                btn = Gtk.Button(); btn.add_css_class("app-card")
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

        # В темах 2, 3, 4, 5 добавляем закреплённые программы в компактный нижний док
        if self.dock_box is not None:
            while True:
                c = self.dock_box.get_first_child()
                if c is None: break
                self.dock_box.remove(c)
            favs = [it for it in items if it[0] in self.pinned][:4]
            for name, cmd, _ic, _cat in favs:
                db = Gtk.Button(label=f"★ {name[:12]}"); db.add_css_class("dock-item")
                db.connect("clicked", lambda _b, c=cmd: self.spawn_raw(f"$HOME/.local/bin/launch-free-ws {c}"))
                self.dock_box.append(db)

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
            self.ports_lbl.set_label(f"Ports: {scan_dev_ports()}")
        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    WorkHubApp().run(None)
