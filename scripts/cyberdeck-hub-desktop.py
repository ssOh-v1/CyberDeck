#!/usr/bin/python3
from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass

import os, sys, re, glob, json, math, socket, shutil, subprocess, datetime, importlib.util

HOME = os.path.expanduser("~")
UID = os.getuid()
CFG_DIR = os.path.join(HOME, ".config/cyberdeck")
CACHE_DIR = os.path.join(HOME, ".cache/cyberdeck")
WORK_STATE = os.path.join(CFG_DIR, "work_theme.json")
STATE_FILE = os.path.join(CFG_DIR, "theme.json")

def load_active_env():
    for sf in (WORK_STATE, STATE_FILE):
        if os.path.isfile(sf):
            try:
                d = json.load(open(sf, encoding="utf-8"))
                if d.get("session") == "work":
                    return d
            except Exception:
                pass
    return {"id": "cyber-tactical", "layout": "tactical", "cursor_theme": "CyberDeck-Cursor-cyber-tactical", "symbol": "◈", "badge": "TACTICAL OS", "primary": "#4c6ef5", "accent": "#22b8cf"}

ENV_META = load_active_env()
CUR_THEME_NAME = ENV_META.get("cursor_theme") or f"CyberDeck-Cursor-{ENV_META.get('id', 'cyber-tactical')}"
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
            if "hub-desktop.py" in _cmd:
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

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

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

def read_top_processes():
    try:
        out = subprocess.check_output(["ps", "-eo", "comm,%cpu,%mem", "--sort=-%cpu"], text=True, stderr=subprocess.DEVNULL).splitlines()[1:7]
        rows = []
        for ln in out:
            ps = ln.split()
            if len(ps) >= 3:
                rows.append(f"▸ {ps[0][:14]:<14}  CPU {ps[1]:>4}%   RAM {ps[2]:>4}%")
        return "\n".join(rows) if rows else "Нет данных"
    except Exception:
        return "Нет данных"

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
        self.layout_mode = ENV_META.get("layout", "tactical")
        self.cards = []
        self.pinned = load_pinned()
        self.active_cat = "ALL"
        self.cat_btns = {}
        self.prev_idle, self.prev_total = read_cpu_stat()
        self.last_ws_sig = None

        # Живые метрики для круговых колец Cryo Studio
        self.cur_cpu_frac = 0.1
        self.cur_ram_frac = 0.3
        self.cur_bat_frac = 1.0
        self.rings_area = None

        # Опциональные виджеты, зависящие от выбранного окружения
        self.clock_lbl = None
        self.cpu_lbl = None
        self.cpu_bar = None
        self.ram_lbl = None
        self.ram_bar = None
        self.bat_lbl = None
        self.bat_bar = None
        self.net_lbl = None
        self.wifi_btn = None
        self.kb_btn = None
        self.pwr_btn = None
        self.bg_menu_btn = None
        self.ws_box = None
        self.bri_scale = None
        self.bri_pct_lbl = None
        self.vol_scale = None
        self.vol_pct_lbl = None
        self.pomo_sec = 25 * 60
        self.pomo_running = False
        self.pomo_lbl = None
        self.proc_lbl = None
        self.net_info_lbl = None
        self.ports_lbl = None
        self.dock_box = None
        self.tui_out_buf = None

    def make_sliders_pair(self, width_px=52):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); box.set_valign(Gtk.Align.CENTER)

        bri_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); bri_cap.add_css_class("audio-capsule"); bri_cap.set_valign(Gtk.Align.CENTER)
        bri_btn = Gtk.Button(); bri_btn.add_css_class("audio-icon-btn"); bri_btn.set_child(ui_svg("sun.svg", 15))
        bri_btn.connect("clicked", self.on_bri_icon_clicked); bri_cap.append(bri_btn)
        cur_b = self.get_current_bri()
        self.bri_pct_lbl = Gtk.Label(label=f"{int(cur_b)}%"); self.bri_pct_lbl.add_css_class("vol-pct")
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.bri_scale.set_draw_value(False); self.bri_scale.set_size_request(width_px, -1); self.bri_scale.set_value(cur_b)
        self.bri_scale.connect("value-changed", self.on_bri_changed)
        bri_cap.append(self.bri_scale); bri_cap.append(self.bri_pct_lbl)
        box.append(bri_cap)

        audio_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); audio_cap.add_css_class("audio-capsule"); audio_cap.set_valign(Gtk.Align.CENTER)
        audio_btn = Gtk.Button(); audio_btn.add_css_class("audio-icon-btn"); audio_btn.set_child(ui_svg("audio.svg", 15))
        audio_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-audio-menu")); audio_cap.append(audio_btn)
        cur_v = self.get_current_vol()
        self.vol_pct_lbl = Gtk.Label(label=f"{int(cur_v)}%"); self.vol_pct_lbl.add_css_class("vol-pct")
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_draw_value(False); self.vol_scale.set_size_request(width_px, -1); self.vol_scale.set_value(cur_v)
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        audio_cap.append(self.vol_scale); audio_cap.append(self.vol_pct_lbl)
        box.append(audio_cap)
        return box

    def make_sys_power_capsule(self):
        sys_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2); sys_cap.add_css_class("power-capsule"); sys_cap.set_valign(Gtk.Align.CENTER)
        btop_b = Gtk.Button(label="BTOP"); btop_b.add_css_class("icon-act-btn"); btop_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-tool btop")); sys_cap.append(btop_b)
        lock_b = Gtk.Button(); lock_b.add_css_class("icon-act-btn"); lock_b.set_child(ui_svg("lock.svg", 15)); lock_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-lock")); sys_cap.append(lock_b)
        sddm_b = Gtk.Button(label="SDDM"); sddm_b.add_css_class("danger-act-btn"); sddm_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session work; hyprctl dispatch exit")); sys_cap.append(sddm_b)
        reb_b = Gtk.Button(); reb_b.add_css_class("icon-act-btn"); reb_b.set_child(ui_svg("reboot.svg", 15)); reb_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session work; systemctl reboot")); sys_cap.append(reb_b)
        off_b = Gtk.Button(); off_b.add_css_class("danger-act-btn"); off_b.set_child(ui_svg("power.svg", 15)); off_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session work; systemctl poweroff")); sys_cap.append(off_b)
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
    # АРХИТЕКТУРА 1: CYBERDECK TACTICAL OS (Классическая дека + Радар проектов)
    # ==========================================================================
    def build_env_tactical(self, root_box):
        top = Gtk.CenterBox(); top.add_css_class("top-deck")
        left_z = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); left_z.set_valign(Gtk.Align.CENTER)
        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7); brand.add_css_class("brand-pill")
        bdot = Gtk.Label(label="◈"); bdot.add_css_class("brand-dot")
        bt = Gtk.Label(label="TACTICAL OS"); bt.add_css_class("brand-title")
        brand.append(bdot); brand.append(bt); left_z.append(brand)

        ws_sc = Gtk.ScrolledWindow(); ws_sc.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER); ws_sc.set_max_content_width(190); ws_sc.set_propagate_natural_width(True)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); ws_sc.set_child(self.ws_box); left_z.append(ws_sc)

        nb = Gtk.Button(label="+ Стол"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); left_z.append(nb)
        self.bg_menu_btn = Gtk.Button(label="◈ Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); left_z.append(self.bg_menu_btn)
        tb = Gtk.Button(label="◈ Тема"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); left_z.append(tb)
        top.set_start_widget(left_z)

        cpod = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); cpod.add_css_class("telemetry-pod"); cpod.set_valign(Gtk.Align.CENTER)
        self.cpu_lbl = Gtk.Label(label="CPU 0%"); self.cpu_lbl.add_css_class("metric-lbl")
        self.cpu_bar = Gtk.ProgressBar(); self.cpu_bar.set_valign(Gtk.Align.CENTER)
        self.ram_lbl = Gtk.Label(label="RAM --"); self.ram_lbl.add_css_class("metric-lbl")
        self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan"); self.ram_bar.set_valign(Gtk.Align.CENTER)
        self.bat_lbl = Gtk.Label(label="BAT --%"); self.bat_lbl.add_css_class("metric-lbl")
        self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good"); self.bat_bar.set_valign(Gtk.Align.CENTER)
        self.net_lbl = Gtk.Label(label="● VPN"); self.net_lbl.add_css_class("net-badge")
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar, self.net_lbl): cpod.append(w)
        top.set_center_widget(cpod)

        right_z = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); right_z.set_valign(Gtk.Align.CENTER)
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_child(ui_svg("wifi-high.svg", 17))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu")); right_z.append(self.wifi_btn)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); right_z.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); right_z.append(self.pwr_btn)
        right_z.append(self.make_sliders_pair(48))
        right_z.append(self.make_sys_power_capsule())

        _, _, hz = get_monitor_info()
        cbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); cbox.add_css_class("clock-pill")
        self.clock_lbl = Gtk.Label(label="00:00"); self.clock_lbl.add_css_class("clock-time")
        hzl = Gtk.Label(label=f"{hz}Hz"); hzl.add_css_class("clock-hz")
        cbox.append(self.clock_lbl); cbox.append(hzl); right_z.append(cbox)
        top.set_end_widget(right_z)
        root_box.append(top)

        # Строка поиска + быстрые хабы проектов
        act_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.set_hexpand(True); self.search.connect("changed", self.on_filter)
        act_row.append(self.search)
        for lbl, cmd, cls in [
            ("▶ Терминал", "~/.local/bin/launch-free-ws foot", "primary-btn"),
            ("📁 Проекты ~/CyberDeck", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~/CyberDeck", "secondary-btn"),
            ("⚙ Конфиги Hypr", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm ~/.config/hypr", "secondary-btn"),
            ("◈ Поверх [SUPER+P]", "~/.local/bin/hyprwork-pin-window", "ctrl-pill"),
            ("Скриншот", "~/.local/bin/cyber-tool shot", "ctrl-pill"),
        ]:
            b = Gtk.Button(label=lbl); b.add_css_class(cls); b.connect("clicked", lambda _b, c=cmd: self.spawn_raw(c)); act_row.append(b)
        root_box.append(act_row)

        # Радар dev-портов и локального IP
        dev_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12); dev_bar.add_css_class("footer-bar")
        dl1 = Gtk.Label(label="◈ TACTICAL DEV RADAR //"); dl1.add_css_class("panel-header"); dev_bar.append(dl1)
        self.ports_lbl = Gtk.Label(label=f"Активные порты: {scan_dev_ports()}   •   Локальный IP: {read_local_ip()}")
        self.ports_lbl.add_css_class("panel-sub"); dev_bar.append(self.ports_lbl)
        sp = Gtk.Box(); sp.set_hexpand(True); dev_bar.append(sp)
        bp = Gtk.Button(label="⚡ Сбросить кэш ОЗУ"); bp.add_css_class("ws-new-btn")
        bp.connect("clicked", lambda _b: self.spawn_raw("sudo -n /usr/local/bin/cyber-power-hw purge-ram && notify-send '◈ TACTICAL OS' 'Кэш ОЗУ освобождён'"))
        dev_bar.append(bp)
        root_box.append(dev_bar)

        root_box.append(self.build_app_grid(max_cols=5))

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); footer.add_css_class("footer-bar"); footer.set_halign(Gtk.Align.CENTER)
        for k_t, d_t in [("SUPER+SPACE", "Свободный стол"), ("SUPER+T", "Сменить окружение"), ("SUPER+SHIFT+P", "Перфоманс/Эко"), ("SUPER+P", "Поверх окон"), ("SUPER+E", "Проводник"), ("SUPER+L", "Блокировка")]:
            kl = Gtk.Label(label=k_t); kl.add_css_class("key-badge"); dl = Gtk.Label(label=d_t); dl.add_css_class("key-desc")
            footer.append(kl); footer.append(dl)
        root_box.append(footer)

    # ==========================================================================
    # АРХИТЕКТУРА 2: ARASAKA RONIN OS (БЕЗ ВЕРХНЕЙ ПАНЕЛИ! 3-колоночный кокпит)
    # ==========================================================================
    def build_env_ronin(self, root_box):
        cockpit = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        cockpit.set_hexpand(True); cockpit.set_vexpand(True)

        # --- КОЛОНКА 1: ЛЕВАЯ ВЕРТИКАЛЬНАЯ СТОЙКА УПРАВЛЕНИЯ (260px) ---
        left_pillar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left_pillar.add_css_class("side-rail"); left_pillar.set_size_request(265, -1); left_pillar.set_vexpand(True)

        hdr = Gtk.Label(label="❖ ARASAKA // RONIN OS"); hdr.add_css_class("panel-header"); hdr.set_xalign(0)
        left_pillar.append(hdr)

        self.clock_lbl = Gtk.Label(label="00:00"); self.clock_lbl.add_css_class("big-clock"); self.clock_lbl.set_xalign(0)
        left_pillar.append(self.clock_lbl)

        # Вертикальный блок телеметрии
        self.cpu_lbl = Gtk.Label(label="CPU 0%"); self.cpu_lbl.add_css_class("metric-lbl"); self.cpu_lbl.set_xalign(0)
        self.cpu_bar = Gtk.ProgressBar()
        self.ram_lbl = Gtk.Label(label="RAM --"); self.ram_lbl.add_css_class("metric-lbl"); self.ram_lbl.set_xalign(0)
        self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan")
        self.bat_lbl = Gtk.Label(label="BAT --%"); self.bat_lbl.add_css_class("metric-lbl"); self.bat_lbl.set_xalign(0)
        self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good")
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar):
            left_pillar.append(w)

        # Фильтр категорий приложений (уникальная фишка Ronin OS!)
        cat_hdr = Gtk.Label(label="❖ МАТРИЦА КАТЕГОРИЙ"); cat_hdr.add_css_class("panel-header"); cat_hdr.set_xalign(0)
        left_pillar.append(cat_hdr)

        for cid, clbl in [("ALL", "❖ ВСЕ МОДУЛИ"), ("PIN", "★ ИЗБРАННЫЕ"), ("DEV", "❖ РАЗРАБОТКА / КОД"), ("WEB", "❖ БРАУЗЕРЫ / СЕТЬ"), ("CHAT", "❖ СВЯЗЬ / МЕССЕНДЖЕРЫ"), ("SYS", "❖ СИСТЕМА / ТЕРМИНАЛ")]:
            cb = Gtk.Button(label=clbl)
            cb.add_css_class("cat-tab-active" if cid == "ALL" else "cat-tab")
            cb.connect("clicked", self.on_ronin_cat_clicked, cid)
            self.cat_btns[cid] = cb
            left_pillar.append(cb)

        # Быстрые кнопки столов и фона
        ws_hdr = Gtk.Label(label="❖ АКТИВНЫЕ СТОЛЫ И ФОН"); ws_hdr.add_css_class("panel-header"); ws_hdr.set_xalign(0)
        left_pillar.append(ws_hdr)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        left_pillar.append(self.ws_box)

        row_ acts = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        b_nws = Gtk.Button(label="+ Стол"); b_nws.add_css_class("ws-new-btn"); b_nws.set_hexpand(True); b_nws.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws"))
        self.bg_menu_btn = Gtk.Button(label="◈ Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.set_hexpand(True); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu"))
        row_acts.append(b_nws); row_acts.append(self.bg_menu_btn)
        left_pillar.append(row_acts)

        b_thm = Gtk.Button(label="❖ Сменить окружение [SUPER+T]"); b_thm.add_css_class("primary-btn")
        b_thm.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu"))
        left_pillar.append(b_thm)

        sp_l = Gtk.Box(); sp_l.set_vexpand(True); left_pillar.append(sp_l)

        # Нижний блок управления в левой колонке
        ctrl_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_child(ui_svg("wifi-high.svg", 16))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu"))
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next"))
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.set_hexpand(True); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label()
        ctrl_row.append(self.wifi_btn); ctrl_row.append(self.kb_btn); ctrl_row.append(self.pwr_btn)
        left_pillar.append(ctrl_row)

        left_pillar.append(self.make_sliders_pair(54))
        left_pillar.append(self.make_sys_power_capsule())
        cockpit.append(left_pillar)

        # --- КОЛОНКА 2: ЦЕНТРАЛЬНАЯ МАТРИЦА ГОРИЗОНТАЛЬНЫХ МЕХА-ПЛАСТИН ---
        center_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        center_col.set_hexpand(True); center_col.set_vexpand(True)

        top_act = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.set_hexpand(True); self.search.connect("changed", self.on_filter)
        top_act.append(self.search)
        for bl, bc in [("▶ Консоль", "~/.local/bin/launch-free-ws foot"), ("📁 Файлы", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm"), ("❖ Поверх", "~/.local/bin/hyprwork-pin-window")]:
            b = Gtk.Button(label=bl); b.add_css_class("primary-btn"); b.connect("clicked", lambda _b, c=bc: self.spawn_raw(c)); top_act.append(b)
        center_col.append(top_act)

        center_col.append(self.build_app_grid(max_cols=2))
        cockpit.append(center_col)

        # --- КОЛОНКА 3: ПРАВАЯ ОПЕРАТИВНАЯ СТОЙКА САМУРАЯ (Pomodoro + Заметки + Кэш) ---
        right_deck = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_deck.add_css_class("widget-panel"); right_deck.set_size_request(330, -1); right_deck.set_vexpand(True)

        pt = Gtk.Label(label="❖ ТАЙМЕР ФОКУСА // KATANA SPRINT"); pt.add_css_class("panel-header"); pt.set_xalign(0)
        right_deck.append(pt)
        pomo_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.pomo_lbl = Gtk.Label(label="25:00"); self.pomo_lbl.add_css_class("timer-digits"); pomo_row.append(self.pomo_lbl)
        bs = Gtk.Button(label="Старт/Пауза"); bs.add_css_class("primary-btn"); bs.connect("clicked", self.on_pomo_toggle); pomo_row.append(bs)
        br = Gtk.Button(label="Сброс"); br.add_css_class("ctrl-pill"); br.connect("clicked", self.on_pomo_reset); pomo_row.append(br)
        right_deck.append(pomo_row)

        nt = Gtk.Label(label="❖ ЖУРНАЛ ОПЕРАТОРА (АВТОСОХРАНЕНИЕ)"); nt.add_css_class("panel-header"); nt.set_xalign(0)
        right_deck.append(nt)
        n_sc = Gtk.ScrolledWindow(); n_sc.set_vexpand(True)
        tv = Gtk.TextView(); tv.add_css_class("notes-view"); tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        buf = tv.get_buffer()
        buf.set_text(open(NOTES_FILE, "r", encoding="utf-8").read() if os.path.isfile(NOTES_FILE) else "• Задачи спринта:\n  1. Отладить физику и ИИ в игре\n  2. Проверить FPS в режиме Перфоманс\n")
        buf.connect("changed", lambda b: open(NOTES_FILE, "w", encoding="utf-8").write(b.get_text(b.get_start_iter(), b.get_end_iter(), False)))
        n_sc.set_child(tv); right_deck.append(n_sc)

        b_purge = Gtk.Button(label="⚡ Сбросить кэш ОЗУ (Drop Caches)"); b_purge.add_css_class("secondary-btn")
        b_purge.connect("clicked", lambda _b: self.spawn_raw("sudo -n /usr/local/bin/cyber-power-hw purge-ram && notify-send '❖ RONIN OS' 'Кэш ОЗУ очищен'"))
        right_deck.append(b_purge)

        cockpit.append(right_deck)
        root_box.append(cockpit)
        GLib.timeout_add_seconds(1, self.on_pomo_tick)

    def on_ronin_cat_clicked(self, _btn, cat_id):
        self.active_cat = cat_id
        for cid, b in self.cat_btns.items():
            b.remove_css_class("cat-tab-active")
            b.remove_css_class("cat-tab")
            b.add_css_class("cat-tab-active" if cid == cat_id else "cat-tab")
        self.on_filter(self.search)

    # ==========================================================================
    # АРХИТЕКТУРА 3: NETRUNNER CONSTRUCT (Тайлинговый TUI-мейнфрейм + Живая консоль)
    # ==========================================================================
    def build_env_netrunner(self, root_box):
        # 1. Тонкая терминальная строка статуса сверху
        tstrip = Gtk.CenterBox(); tstrip.add_css_class("tui-strip")
        lz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); lz.set_valign(Gtk.Align.CENTER)
        tl = Gtk.Label(label="⌬ [NETRUNNER::MAINFRAME]"); tl.add_css_class("panel-header"); lz.append(tl)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); lz.append(self.ws_box)
        nb = Gtk.Button(label="[+WS]"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); lz.append(nb)
        self.bg_menu_btn = Gtk.Button(label="◈ Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); lz.append(self.bg_menu_btn)
        tb = Gtk.Button(label="⌬ Тема"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); lz.append(tb)
        tstrip.set_start_widget(lz)

        cz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12); cz.set_valign(Gtk.Align.CENTER)
        self.cpu_lbl = Gtk.Label(label="CPU 0%"); self.cpu_lbl.add_css_class("panel-sub")
        self.ram_lbl = Gtk.Label(label="RAM --"); self.ram_lbl.add_css_class("panel-sub")
        self.bat_lbl = Gtk.Label(label="BAT --%"); self.bat_lbl.add_css_class("panel-sub")
        for w in (self.cpu_lbl, self.ram_lbl, self.bat_lbl): cz.append(w)
        tstrip.set_center_widget(cz)

        rz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); rz.set_valign(Gtk.Align.CENTER)
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_child(ui_svg("wifi-high.svg", 15))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu")); rz.append(self.wifi_btn)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); rz.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); rz.append(self.pwr_btn)
        rz.append(self.make_sliders_pair(46))
        rz.append(self.make_sys_power_capsule())
        self.clock_lbl = Gtk.Label(label="00:00"); self.clock_lbl.add_css_class("clock-time"); rz.append(self.clock_lbl)
        tstrip.set_end_widget(rz)
        root_box.append(tstrip)

        # 2. Трёхпанельный тайлинговый мейнфрейм
        panes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        panes.set_hexpand(True); panes.set_vexpand(True)

        # ПАНЕЛЬ A (Слева): Монитор процессов и сетевых сокетов
        p_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        p_left.add_css_class("widget-panel"); p_left.set_size_request(330, -1); p_left.set_vexpand(True)
        p_left.append(Gtk.Label(label="⌬ PANE_01 // TOP PROCESSES", xalign=0, css_classes=["panel-header"]))
        self.proc_lbl = Gtk.Label(label=read_top_processes(), xalign=0, css_classes=["panel-sub"])
        p_left.append(self.proc_lbl)

        p_left.append(Gtk.Label(label="⌬ PANE_02 // NETWORK & PORTS", xalign=0, css_classes=["panel-header"]))
        self.net_info_lbl = Gtk.Label(label=f"NODE IP : {read_local_ip()}\nPORTS   : {scan_dev_ports()}", xalign=0, css_classes=["panel-sub"])
        p_left.append(self.net_info_lbl)

        sp = Gtk.Box(); sp.set_vexpand(True); p_left.append(sp)
        for lbl_h, cmd_h in [
            ("⚡ [KERNEL] Drop RAM Caches", "sudo -n /usr/local/bin/cyber-power-hw purge-ram && notify-send '⌬ NETRUNNER' 'Кэш ОЗУ очищен'"),
            ("🩺 [NET] Heal DNS & Routes", "~/.local/bin/cyber-net-doctor && notify-send '⌬ NETRUNNER' 'DNS и маршруты проверены'"),
            ("📊 [MON] Launch Floating Btop", "~/.local/bin/cyber-tool btop"),
        ]:
            bh = Gtk.Button(label=lbl_h); bh.add_css_class("secondary-btn"); bh.connect("clicked", lambda _b, c=cmd_h: self.spawn_raw(c)); p_left.append(bh)
        panes.append(p_left)

        # ПАНЕЛЬ B (Центр): Нумерованный реестр бинарных модулей
        p_mid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        p_mid.set_hexpand(True); p_mid.set_vexpand(True)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.connect("changed", self.on_filter)
        p_mid.append(self.search)
        p_mid.append(self.build_app_grid(max_cols=2))
        panes.append(p_mid)

        # ПАНЕЛЬ C (Справа): ЖИВАЯ ВСТРОЕННАЯ КОНСОЛЬ ПРЯМО НА РАБОЧЕМ СТОЛЕ!
        p_right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        p_right.add_css_class("widget-panel"); p_right.set_size_request(390, -1); p_right.set_vexpand(True)
        p_right.append(Gtk.Label(label="⌬ PANE_03 // LIVE DECK CONSOLE (STDOUT)", xalign=0, css_classes=["panel-header"]))

        out_sc = Gtk.ScrolledWindow(); out_sc.set_vexpand(True)
        out_tv = Gtk.TextView(); out_tv.set_editable(False); out_tv.set_cursor_visible(False)
        out_tv.add_css_class("notes-view"); out_tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.tui_out_buf = out_tv.get_buffer()
        self.tui_out_buf.set_text(
            f"⌬ NETRUNNER LIVE SHELL // {datetime.datetime.now().strftime('%H:%M:%S')}\n"
            "Введите любую bash-команду снизу для мгновенного вывода прямо на рабочий стол.\n"
            "──────────────────────────────────────────\n"
        )
        out_sc.set_child(out_tv); p_right.append(out_sc)

        cmd_entry = Gtk.Entry(); cmd_entry.add_css_class("search-entry")
        cmd_entry.set_placeholder_text("⌬ Введите команду (ls, git status, uname -a, df -h)...")
        cmd_entry.connect("activate", self.on_netrunner_exec)
        p_right.append(cmd_entry)

        q_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for ql, qc in [("uname -sr", "uname -sr"), ("df -h /", "df -h /"), ("free -h", "free -h"), ("ip -br a", "ip -br a")]:
            qb = Gtk.Button(label=ql); qb.add_css_class("ctrl-pill"); qb.connect("clicked", lambda _b, c=qc: self.run_live_cmd(c)); q_row.append(qb)
        p_right.append(q_row)

        panes.append(p_right)
        root_box.append(panes)

    def run_live_cmd(self, cmd_str):
        if not self.tui_out_buf: return
        try:
            res = subprocess.check_output(["/bin/bash", "-c", cmd_str], stderr=subprocess.STDOUT, text=True, timeout=3.0)
        except subprocess.CalledProcessError as e:
            res = e.output or f"Exit code: {e.returncode}"
        except Exception as e:
            res = str(e)
        old = self.tui_out_buf.get_text(self.tui_out_buf.get_start_iter(), self.tui_out_buf.get_end_iter(), False)
        new_txt = f"{old}\n⌬ ⟫ {cmd_str}\n{res.strip()}\n"
        self.tui_out_buf.set_text(new_txt[-3500:])

    def on_netrunner_exec(self, entry):
        cmd_str = entry.get_text().strip()
        if not cmd_str: return
        entry.set_text("")
        self.run_live_cmd(cmd_str)

    # ==========================================================================
    # АРХИТЕКТУРА 4: ORBITAL CRYO STUDIO (Парящий остров + Круговые кольца + Док)
    # ==========================================================================
    def build_env_cryo(self, root_box):
        # 1. Компактный парящий остров по центру сверху (не во всю ширину!)
        island_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        island_wrap.add_css_class("floating-island"); island_wrap.set_halign(Gtk.Align.CENTER)

        bdot = Gtk.Label(label="✦ CRYO STUDIO"); bdot.add_css_class("brand-dot"); island_wrap.append(bdot)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); island_wrap.append(self.ws_box)
        nb = Gtk.Button(label="+ Стол"); nb.add_css_class("ws-new-btn"); nb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws")); island_wrap.append(nb)
        self.bg_menu_btn = Gtk.Button(label="◈ Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu")); island_wrap.append(self.bg_menu_btn)
        tb = Gtk.Button(label="✦ Тема"); tb.add_css_class("ctrl-pill"); tb.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu")); island_wrap.append(tb)

        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_child(ui_svg("wifi-high.svg", 16))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu")); island_wrap.append(self.wifi_btn)
        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); island_wrap.append(self.kb_btn)
        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); island_wrap.append(self.pwr_btn)
        island_wrap.append(self.make_sys_power_capsule())
        root_box.append(island_wrap)

        # 2. Орбитальный Hero-дашборд с ЖИВЫМИ КРУГОВЫМИ КОЛЬЦАМИ (Cairo DrawingArea)
        hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        hero.add_css_class("hero-banner")

        clk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); clk_box.set_valign(Gtk.Align.CENTER)
        self.clock_lbl = Gtk.Label(label="00:00"); self.clock_lbl.add_css_class("big-clock"); self.clock_lbl.set_xalign(0)
        sub_d = Gtk.Label(label=datetime.datetime.now().strftime("✦ %d.%m.%Y  •  ORBITAL CRYO LAB")); sub_d.add_css_class("big-sub"); sub_d.set_xalign(0)
        clk_box.append(self.clock_lbl); clk_box.append(sub_d)
        hero.append(clk_box)

        # Круговые датчики CPU / RAM / BAT на Cairo
        self.rings_area = Gtk.DrawingArea()
        self.rings_area.set_size_request(290, 92)
        self.rings_area.set_draw_func(self.draw_cryo_rings)
        hero.append(self.rings_area)

        sp = Gtk.Box(); sp.set_hexpand(True); hero.append(sp)

        right_studio = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); right_studio.set_valign(Gtk.Align.CENTER)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.set_size_request(360, -1); self.search.connect("changed", self.on_filter)
        right_studio.append(self.search)
        right_studio.append(self.make_sliders_pair(75))
        hero.append(right_studio)
        root_box.append(hero)

        # 3. Пространственная сетка крупных квадратных плиток (6 в ряд)
        root_box.append(self.build_app_grid(max_cols=6))

        # 4. Нижний парящий док избранных приложений
        dock_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dock_wrap.add_css_class("bottom-dock"); dock_wrap.set_halign(Gtk.Align.CENTER)
        dock_wrap.append(Gtk.Label(label="✦ STUDIO DOCK:", css_classes=["panel-header"]))
        self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dock_wrap.append(self.dock_box)
        root_box.append(dock_wrap)

    def draw_cryo_rings(self, _area, cr, w, h, *_args):
        PRIM = hex_rgb(ENV_META.get("primary", "#1c7ed6"))
        ACC  = hex_rgb(ENV_META.get("accent", "#74c0fc"))
        gauges = [
            ("CPU", self.cur_cpu_frac, f"{int(self.cur_cpu_frac*100)}%"),
            ("RAM", self.cur_ram_frac, f"{int(self.cur_ram_frac*100)}%"),
            ("PWR", self.cur_bat_frac, f"{int(self.cur_bat_frac*100)}%"),
        ]
        cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for idx, (label, frac, val_s) in enumerate(gauges):
            cx = 48 + idx * 94
            cy = h * 0.5
            r = 34
            cr.set_line_width(6.0); cr.set_source_rgba(1, 1, 1, 0.10)
            cr.arc(cx, cy, r, 0, 2 * math.pi); cr.stroke()

            cr.set_line_width(6.0); cr.set_source_rgb(*(ACC if idx % 2 == 0 else PRIM))
            cr.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + max(0.05, frac) * 2 * math.pi); cr.stroke()

            cr.set_font_size(11); cr.set_source_rgb(0.92, 0.96, 1.0)
            e1 = cr.text_extents(val_s)
            cr.move_to(cx - e1.width / 2, cy + 1); cr.show_text(val_s)

            cr.set_font_size(9); cr.set_source_rgb(*ACC)
            e2 = cr.text_extents(label)
            cr.move_to(cx - e2.width / 2, cy + 15); cr.show_text(label)

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
        if os.path.isfile(BG_PNG):
            bg_pic = Gtk.Picture.new_for_filename(BG_PNG)
            bg_pic.set_can_shrink(True)
            if hasattr(Gtk, "ContentFit"): bg_pic.set_content_fit(Gtk.ContentFit.COVER)
            overlay.set_child(bg_pic)

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root_box.add_css_class("hub-overlay")
        root_box.set_hexpand(True); root_box.set_vexpand(True)

        if self.layout_mode == "ronin":
            self.build_env_ronin(root_box)
        elif self.layout_mode == "netrunner":
            self.build_env_netrunner(root_box)
        elif self.layout_mode == "cryo":
            self.build_env_cryo(root_box)
        else:
            self.build_env_tactical(root_box)

        overlay.add_overlay(root_box); win.set_child(overlay)
        self.populate_apps(); self.refresh_workspaces(); self.refresh_status()
        GLib.timeout_add(1200, self.refresh_workspaces)
        GLib.timeout_add_seconds(3, self.refresh_status)
        win.present()

    def on_pomo_toggle(self, _b): self.pomo_running = not self.pomo_running
    def on_pomo_reset(self, _b):
        self.pomo_running = False; self.pomo_sec = 25 * 60
        if self.pomo_lbl: self.pomo_lbl.set_label("25:00")

    def on_pomo_tick(self):
        if self.pomo_running and self.pomo_lbl:
            if self.pomo_sec > 0:
                self.pomo_sec -= 1
                self.pomo_lbl.set_label(f"{self.pomo_sec // 60:02d}:{self.pomo_sec % 60:02d}")
            else:
                self.pomo_running = False
                self.spawn_raw("notify-send '❖ ТАЙМЕР РОНИНА' 'Спринт фокусировки завершён!'")
        return True

    def populate_apps(self):
        while True:
            ch = self.flow.get_first_child()
            if ch is None: break
            self.flow.remove(ch)
        self.cards.clear()

        items = discover_work_apps()
        items.sort(key=lambda x: (0 if x[0] in self.pinned else 1, x[0].lower()))
        self.search.set_placeholder_text(f"{ENV_META.get('symbol', '◈')} Поиск среди {len(items)} модулей (ЛКМ: новый стол • ПКМ: в избранное)...")

        for idx, (name, cmd, icon_spec, cat_tag) in enumerate(items, 1):
            is_pin = name in self.pinned
            btn = Gtk.Button()

            if self.layout_mode == "ronin":
                # Горизонтальная меха-пластина Ронина с номером слота
                btn.add_css_class("ronin-blade")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                idx_l = Gtk.Label(label=f"[{idx:02d}]"); idx_l.add_css_class("blade-idx"); hb.append(idx_l)
                hb.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 24))
                t = Gtk.Label(label=name); t.add_css_class("card-title"); t.set_xalign(0); t.set_hexpand(True); t.set_ellipsize(Pango.EllipsizeMode.END); hb.append(t)
                chip = Gtk.Label(label="★" if is_pin else cat_tag); chip.add_css_class("cat-chip"); hb.append(chip)
                btn.set_child(hb)

            elif self.layout_mode == "netrunner":
                # Строка терминального модуля Netrunner
                btn.add_css_class("tui-row")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                t = Gtk.Label(label=f"[{idx:02d}] ⌬ {name[:18]:<18}"); t.add_css_class("tui-text"); t.set_xalign(0); t.set_hexpand(True); hb.append(t)
                tag = Gtk.Label(label=f":: {'PIN' if is_pin else cat_tag}"); tag.add_css_class("tui-tag"); hb.append(tag)
                btn.set_child(hb)

            elif self.layout_mode == "cryo":
                # Вертикальная пространственная плитка Cryo Studio с крупной иконкой по центру
                btn.add_css_class("cryo-tile")
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); vb.set_valign(Gtk.Align.CENTER); vb.set_halign(Gtk.Align.CENTER)
                vb.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 42))
                t = Gtk.Label(label=name); t.add_css_class("card-title"); t.set_ellipsize(Pango.EllipsizeMode.END); t.set_max_width_chars(15); vb.append(t)
                sub = Gtk.Label(label="★ STUDIO PIN" if is_pin else cat_tag); sub.add_css_class("card-sub"); vb.append(sub)
                btn.set_child(vb)

            else:
                # Классическая карточка Tactical OS
                btn.add_css_class("app-card")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                stripe = Gtk.Box(); stripe.add_css_class("stripe-pinned" if is_pin else "stripe-normal"); stripe.set_vexpand(True); hb.append(stripe)
                ic_box = Gtk.Box(); ic_box.add_css_class("icon-frame"); ic_box.set_valign(Gtk.Align.CENTER)
                ic_box.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 34)); hb.append(ic_box)
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5); vb.set_valign(Gtk.Align.CENTER); vb.set_hexpand(True)
                t = Gtk.Label(label=name); t.add_css_class("card-title"); t.set_xalign(0.0); t.set_ellipsize(Pango.EllipsizeMode.END); t.set_max_width_chars(20); vb.append(t)
                meta_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                chip = Gtk.Label(label=cat_tag); chip.add_css_class("cat-chip")
                sub = Gtk.Label(label="★ PINNED" if is_pin else "FREE WS"); sub.add_css_class("card-sub")
                meta_row.append(chip); meta_row.append(sub); vb.append(meta_row); hb.append(vb)
                glyph = Gtk.Label(label="⟫"); glyph.add_css_class("launch-glyph"); hb.append(glyph)
                btn.set_child(hb)

            btn.connect("clicked", lambda _b, c=cmd: self.spawn_raw(f"$HOME/.local/bin/launch-free-ws {c}"))
            rc = Gtk.GestureClick.new(); rc.set_button(3)
            rc.connect("pressed", lambda _g, _n, _x, _y, nm=name: self.toggle_pin(nm))
            btn.add_controller(rc)
            self.flow.append(btn)
            self.cards.append((name.lower(), cat_tag, is_pin, btn))

        if self.dock_box is not None:
            while True:
                c = self.dock_box.get_first_child()
                if c is None: break
                self.dock_box.remove(c)
            favs = [it for it in items if it[0] in self.pinned][:7] or items[:6]
            for name, cmd, _ic, _cat in favs:
                db = Gtk.Button(label=f"✦ {name[:14]}"); db.add_css_class("ws-btn")
                db.connect("clicked", lambda _b, c=cmd: self.spawn_raw(f"$HOME/.local/bin/launch-free-ws {c}"))
                self.dock_box.append(db)

        self.on_filter(self.search)

    def toggle_pin(self, name):
        if name in self.pinned: self.pinned.remove(name)
        else: self.pinned.add(name)
        save_pinned(self.pinned); self.populate_apps()

    def on_filter(self, entry):
        q = entry.get_text().strip().lower() if entry else ""
        for tl, cat_tag, is_pin, btn in self.cards:
            cat_ok = True
            if self.active_cat == "PIN": cat_ok = is_pin
            elif self.active_cat == "DEV": cat_ok = (cat_tag in ("DEV", "TERM", "ART"))
            elif self.active_cat == "WEB": cat_ok = (cat_tag == "WEB")
            elif self.active_cat == "CHAT": cat_ok = (cat_tag in ("CHAT", "MEDIA"))
            elif self.active_cat == "SYS": cat_ok = (cat_tag in ("SYS", "TERM"))
            if btn.get_parent():
                btn.get_parent().set_visible(cat_ok and ((not q) or (q in tl)))

    def refresh_workspaces(self):
        try:
            if os.path.isfile(KB_FILE) and self.kb_btn:
                kb_code = open(KB_FILE).read().strip() or "EN"
                if self.kb_btn.get_label() != kb_code: self.kb_btn.set_label(kb_code)
        except Exception: pass
        try:
            bg_list = cyber_bg.get_bg_and_open_items()
            lbl_bg = f"◈ Фон [{sum(i.get('count', 1) for i in bg_list)}]"
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
        now_s = datetime.datetime.now().strftime("%H:%M")
        if self.clock_lbl: self.clock_lbl.set_label(now_s)

        idle, total = read_cpu_stat()
        dt, di = total - self.prev_total, idle - self.prev_idle
        self.prev_idle, self.prev_total = idle, total
        cpu_pct = int(round(100.0 * (dt - di) / dt)) if dt > 0 else 0
        self.cur_cpu_frac = min(1.0, max(0.0, cpu_pct / 100.0))
        if self.cpu_lbl: self.cpu_lbl.set_label(f"CPU {cpu_pct}%")
        if self.cpu_bar: self.cpu_bar.set_fraction(self.cur_cpu_frac)

        ram_txt, ram_frac = read_ram_info()
        self.cur_ram_frac = ram_frac
        if self.ram_lbl: self.ram_lbl.set_label(f"RAM {ram_txt}")
        if self.ram_bar: self.ram_bar.set_fraction(ram_frac)

        binfo = read_battery()
        pct = int(binfo.get("pct", 100))
        self.cur_bat_frac = min(1.0, max(0.0, pct / 100.0))
        if self.bat_lbl:
            self.bat_lbl.set_label("AC 100%" if not binfo.get("present") else f"BAT {pct}%")
        if self.bat_bar: self.bat_bar.set_fraction(self.cur_bat_frac)

        if self.rings_area:
            self.rings_area.queue_draw()

        if self.wifi_btn:
            w_info = read_wifi_state()
            self.wifi_btn.set_child(ui_svg(w_info.get("icon", "wifi-high.svg"), 16))
        self.update_pwr_label()

        if self.proc_lbl: self.proc_lbl.set_label(read_top_processes())
        if self.net_info_lbl: self.net_info_lbl.set_label(f"NODE IP : {read_local_ip()}\nPORTS   : {scan_dev_ports()}")
        if self.ports_lbl: self.ports_lbl.set_label(f"Активные порты: {scan_dev_ports()}   •   Локальный IP: {read_local_ip()}")
        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    WorkHubApp().run(None)
