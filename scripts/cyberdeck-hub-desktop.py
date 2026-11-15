#!/usr/bin/env python3
from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass

import os, sys, re, glob, json, socket, shutil, subprocess, datetime, importlib.util

HOME = os.path.expanduser("~")
UID = os.getuid()
CFG_DIR = os.path.join(HOME, ".config/cyberdeck")
CACHE_DIR = os.path.join(HOME, ".cache/cyberdeck")
WORK_STATE = os.path.join(CFG_DIR, "work_theme.json")
STATE_FILE = os.path.join(CFG_DIR, "theme.json")

# Читаем активное окружение и выставляем XCURSOR_THEME ДО инициализации GTK4!
def load_active_env():
    for sf in (WORK_STATE, STATE_FILE):
        if os.path.isfile(sf):
            try:
                d = json.load(open(sf, encoding="utf-8"))
                if d.get("session") == "work":
                    return d
            except Exception:
                pass
    return {"id": "cyber-tactical", "layout": "tactical", "cursor_theme": "CyberDeck-Cursor-cyber-tactical", "symbol": "◈", "badge": "TACTICAL OS"}

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

os.environ.pop("LD_PRELOAD", None)

# Гарантируем единственный экземпляр стола
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
        out = subprocess.check_output(["ps", "-eo", "comm,%cpu,%mem", "--sort=-%cpu"], text=True, stderr=subprocess.DEVNULL).splitlines()[1:6]
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
        self.prev_idle, self.prev_total = read_cpu_stat()
        self.last_ws_sig = None
        self.pomo_sec = 25 * 60
        self.pomo_running = False
        self.pomo_lbl = None
        self.proc_lbl = None
        self.net_info_lbl = None
        self.ports_lbl = None
        self.dock_box = None

    def build_top_command_bar(self):
        top = Gtk.CenterBox(); top.add_css_class("top-deck"); top.set_vexpand(False)

        left_zone = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); left_zone.set_valign(Gtk.Align.CENTER)
        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7); brand.add_css_class("brand-pill"); brand.set_valign(Gtk.Align.CENTER)
        bdot = Gtk.Label(label=ENV_META.get("symbol", "◈")); bdot.add_css_class("brand-dot")
        bt = Gtk.Label(label=ENV_META.get("badge", "WORK DECK")); bt.add_css_class("brand-title")
        brand.append(bdot); brand.append(bt); left_zone.append(brand)

        ws_scroll = Gtk.ScrolledWindow()
        ws_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        ws_scroll.set_max_content_width(200); ws_scroll.set_propagate_natural_width(True); ws_scroll.set_valign(Gtk.Align.CENTER)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); self.ws_box.set_valign(Gtk.Align.CENTER)
        ws_scroll.set_child(self.ws_box); left_zone.append(ws_scroll)

        new_ws_btn = Gtk.Button(label="+ Стол"); new_ws_btn.add_css_class("ws-new-btn"); new_ws_btn.set_valign(Gtk.Align.CENTER)
        new_ws_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws"))
        left_zone.append(new_ws_btn)

        self.bg_menu_btn = Gtk.Button(label="◈ Фон [0]"); self.bg_menu_btn.add_css_class("ws-new-btn"); self.bg_menu_btn.set_valign(Gtk.Align.CENTER)
        self.bg_menu_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-bg-menu"))
        left_zone.append(self.bg_menu_btn)

        self.theme_btn = Gtk.Button(label="◈ Тема"); self.theme_btn.add_css_class("ctrl-pill"); self.theme_btn.set_valign(Gtk.Align.CENTER)
        self.theme_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme menu"))
        left_zone.append(self.theme_btn)
        top.set_start_widget(left_zone)

        center_pod = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); center_pod.add_css_class("telemetry-pod"); center_pod.set_valign(Gtk.Align.CENTER)
        cpu_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); cpu_row.set_valign(Gtk.Align.CENTER)
        self.cpu_lbl = Gtk.Label(label="CPU 0%"); self.cpu_lbl.add_css_class("metric-lbl")
        self.cpu_bar = Gtk.ProgressBar(); self.cpu_bar.set_valign(Gtk.Align.CENTER)
        cpu_row.append(self.cpu_lbl); cpu_row.append(self.cpu_bar); center_pod.append(cpu_row)

        s1 = Gtk.Box(); s1.add_css_class("pod-sep"); center_pod.append(s1)
        ram_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); ram_row.set_valign(Gtk.Align.CENTER)
        self.ram_lbl = Gtk.Label(label="RAM --"); self.ram_lbl.add_css_class("metric-lbl")
        self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan"); self.ram_bar.set_valign(Gtk.Align.CENTER)
        ram_row.append(self.ram_lbl); ram_row.append(self.ram_bar); center_pod.append(ram_row)

        s2 = Gtk.Box(); s2.add_css_class("pod-sep"); center_pod.append(s2)
        bat_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); bat_row.set_valign(Gtk.Align.CENTER)
        self.bat_lbl = Gtk.Label(label="BAT --%"); self.bat_lbl.add_css_class("metric-lbl")
        self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good"); self.bat_bar.set_valign(Gtk.Align.CENTER)
        bat_row.append(self.bat_lbl); bat_row.append(self.bat_bar); center_pod.append(bat_row)

        s3 = Gtk.Box(); s3.add_css_class("pod-sep"); center_pod.append(s3)
        self.net_lbl = Gtk.Label(label="● VPN"); self.net_lbl.add_css_class("net-badge"); self.net_lbl.set_valign(Gtk.Align.CENTER)
        center_pod.append(self.net_lbl); top.set_center_widget(center_pod)

        right_zone = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); right_zone.set_valign(Gtk.Align.CENTER)
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_valign(Gtk.Align.CENTER)
        self.wifi_btn.set_child(ui_svg("wifi-high.svg", 17))
        self.wifi_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-wifi-menu"))
        right_zone.append(self.wifi_btn)

        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.set_valign(Gtk.Align.CENTER)
        self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next"))
        right_zone.append(self.kb_btn)

        self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.set_valign(Gtk.Align.CENTER)
        self.pwr_btn.connect("clicked", self.on_toggle_power)
        self.update_pwr_label(); right_zone.append(self.pwr_btn)

        bri_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); bri_cap.add_css_class("audio-capsule"); bri_cap.set_valign(Gtk.Align.CENTER)
        bri_btn = Gtk.Button(); bri_btn.add_css_class("audio-icon-btn"); bri_btn.set_valign(Gtk.Align.CENTER); bri_btn.set_child(ui_svg("sun.svg", 16))
        bri_btn.connect("clicked", self.on_bri_icon_clicked); bri_cap.append(bri_btn)
        cur_b = self.get_current_bri()
        self.bri_pct_lbl = Gtk.Label(label=f"{int(cur_b)}%"); self.bri_pct_lbl.add_css_class("vol-pct"); self.bri_pct_lbl.set_valign(Gtk.Align.CENTER)
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.bri_scale.set_draw_value(False); self.bri_scale.set_size_request(52, -1); self.bri_scale.set_valign(Gtk.Align.CENTER)
        self.bri_scale.set_value(cur_b); self.bri_scale.connect("value-changed", self.on_bri_changed)
        bri_cap.append(self.bri_scale); bri_cap.append(self.bri_pct_lbl); right_zone.append(bri_cap)

        audio_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); audio_cap.add_css_class("audio-capsule"); audio_cap.set_valign(Gtk.Align.CENTER)
        audio_btn = Gtk.Button(); audio_btn.add_css_class("audio-icon-btn"); audio_btn.set_valign(Gtk.Align.CENTER); audio_btn.set_child(ui_svg("audio.svg", 16))
        audio_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-audio-menu")); audio_cap.append(audio_btn)
        cur_v = self.get_current_vol()
        self.vol_pct_lbl = Gtk.Label(label=f"{int(cur_v)}%"); self.vol_pct_lbl.add_css_class("vol-pct"); self.vol_pct_lbl.set_valign(Gtk.Align.CENTER)
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_draw_value(False); self.vol_scale.set_size_request(52, -1); self.vol_scale.set_valign(Gtk.Align.CENTER)
        self.vol_scale.set_value(cur_v); self.vol_scale.connect("value-changed", self.on_vol_changed)
        audio_cap.append(self.vol_scale); audio_cap.append(self.vol_pct_lbl); right_zone.append(audio_cap)

        sys_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2); sys_cap.add_css_class("power-capsule"); sys_cap.set_valign(Gtk.Align.CENTER)
        btop_b = Gtk.Button(label="BTOP"); btop_b.add_css_class("icon-act-btn"); btop_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-tool btop")); sys_cap.append(btop_b)
        lock_b = Gtk.Button(); lock_b.add_css_class("icon-act-btn"); lock_b.set_child(ui_svg("lock.svg", 15)); lock_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-lock")); sys_cap.append(lock_b)
        sddm_b = Gtk.Button(label="SDDM"); sddm_b.add_css_class("danger-act-btn"); sddm_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session work; hyprctl dispatch exit")); sys_cap.append(sddm_b)
        reb_b = Gtk.Button(); reb_b.add_css_class("icon-act-btn"); reb_b.set_child(ui_svg("reboot.svg", 15)); reb_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session work; systemctl reboot")); sys_cap.append(reb_b)
        off_b = Gtk.Button(); off_b.add_css_class("danger-act-btn"); off_b.set_child(ui_svg("power.svg", 15)); off_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-theme --sync-session work; systemctl poweroff")); sys_cap.append(off_b)
        right_zone.append(sys_cap)

        _, _, hz_mon = get_monitor_info()
        cbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7); cbox.add_css_class("clock-pill"); cbox.set_valign(Gtk.Align.CENTER)
        self.clock_lbl = Gtk.Label(label="00:00"); self.clock_lbl.add_css_class("clock-time")
        hz_lbl = Gtk.Label(label=f"{hz_mon}Hz"); hz_lbl.add_css_class("clock-hz")
        cbox.append(self.clock_lbl); cbox.append(hz_lbl); right_zone.append(cbox)
        top.set_end_widget(right_zone)
        return top

    def build_action_search_row(self):
        act_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); act_row.set_vexpand(False)
        self.search = Gtk.Entry()
        self.search.add_css_class("search-entry"); self.search.set_hexpand(True)
        self.search.connect("changed", self.on_filter); act_row.append(self.search)

        for b_lbl, b_cmd, cls in [
            ("▶ Терминал", "~/.local/bin/launch-free-ws foot", "primary-btn"),
            ("📁 Проводник", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm", "secondary-btn"),
            ("◈ Поверх окон [SUPER+P]", "~/.local/bin/hyprwork-pin-window", "secondary-btn"),
            ("Пипетка", "~/.local/bin/cyber-tool pick", "ctrl-pill"),
            ("Скриншот", "~/.local/bin/cyber-tool shot", "ctrl-pill"),
            ("Все программы", f'rofi -show drun -theme "{ROFI_THEME}" -run-command "$HOME/.local/bin/launch-free-ws {{cmd}}"', "ctrl-pill"),
        ]:
            b = Gtk.Button(label=b_lbl); b.add_css_class(cls)
            b.connect("clicked", lambda _b, c=b_cmd: self.spawn_raw(c))
            act_row.append(b)
        return act_row

    def build_app_grid(self, max_cols=5):
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True); scroll.set_hexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.flow = Gtk.FlowBox(); self.flow.set_valign(Gtk.Align.START)
        self.flow.set_max_children_per_line(max_cols); self.flow.set_min_children_per_line(2)
        self.flow.set_column_spacing(14); self.flow.set_row_spacing(14)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.flow)
        return scroll

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

        # Верхняя панель присутствует во всех окружениях, но нижнее рабочее пространство строится уникально!
        root_box.append(self.build_top_command_bar())
        root_box.append(self.build_action_search_row())

        if self.layout_mode == "ronin":
            # === ОКРУЖЕНИЕ 2: ARASAKA RONIN (Сетка приложений + Правая тактическая стойка с Pomodoro и Заметками) ===
            mid_split = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            mid_split.set_hexpand(True); mid_split.set_vexpand(True)
            mid_split.append(self.build_app_grid(max_cols=4))

            side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            side.add_css_class("widget-panel"); side.set_size_request(330, -1); side.set_vexpand(True)

            # Виджет 1: Таймер фокусировки Ронина (Pomodoro)
            pt = Gtk.Label(label="❖ ТАЙМЕР ФОКУСА // KATANA SPRINT"); pt.add_css_class("panel-header"); pt.set_xalign(0)
            side.append(pt)

            pomo_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            self.pomo_lbl = Gtk.Label(label="25:00"); self.pomo_lbl.add_css_class("timer-digits")
            pomo_row.append(self.pomo_lbl)

            btn_start = Gtk.Button(label="Старт / Пауза"); btn_start.add_css_class("primary-btn")
            btn_start.connect("clicked", self.on_pomo_toggle); pomo_row.append(btn_start)

            btn_rst = Gtk.Button(label="Сброс"); btn_rst.add_css_class("ctrl-pill")
            btn_rst.connect("clicked", self.on_pomo_reset); pomo_row.append(btn_rst)
            side.append(pomo_row)

            # Виджет 2: Сохраняемый блокнот оператора
            nt = Gtk.Label(label="❖ ОПЕРАТИВНЫЕ ЗАМЕТКИ (АВТОСОХРАНЕНИЕ)"); nt.add_css_class("panel-header"); nt.set_xalign(0)
            side.append(nt)

            n_scroll = Gtk.ScrolledWindow(); n_scroll.set_vexpand(True)
            tview = Gtk.TextView(); tview.add_css_class("notes-view"); tview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            buf = tview.get_buffer()
            if os.path.isfile(NOTES_FILE):
                try: buf.set_text(open(NOTES_FILE, "r", encoding="utf-8").read())
                except Exception: pass
            else:
                buf.set_text("• Задачи спринта:\n  1. Проверить физику и FPS игры\n  2. Собрать билд под Linux/Win\n")
            buf.connect("changed", lambda b: open(NOTES_FILE, "w", encoding="utf-8").write(b.get_text(b.get_start_iter(), b.get_end_iter(), False)))
            n_scroll.set_child(tview); side.append(n_scroll)

            # Виджет 3: Быстрые действия разработчика
            kb_btn = Gtk.Button(label="⚡ Очистить кэш ОЗУ (Drop Caches)"); kb_btn.add_css_class("secondary-btn")
            kb_btn.connect("clicked", lambda _b: self.spawn_raw("sudo -n /usr/local/bin/cyber-power-hw purge-ram && notify-send '❖ RONIN OS' 'Кэш ОЗУ успешно очищен'"))
            side.append(kb_btn)

            mid_split.append(side)
            root_box.append(mid_split)
            GLib.timeout_add_seconds(1, self.on_pomo_tick)

        elif self.layout_mode == "netrunner":
            # === ОКРУЖЕНИЕ 3: NETRUNNER CONSTRUCT (Левый живой инспектор процессов/сети + Сетка + Нижний CLI-раннер) ===
            mid_split = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            mid_split.set_hexpand(True); mid_split.set_vexpand(True)

            left_insp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            left_insp.add_css_class("widget-panel"); left_insp.set_size_request(340, -1); left_insp.set_vexpand(True)

            lh1 = Gtk.Label(label="⌬ МОНИТОР ПРОЦЕССОВ (TOP CPU/RAM)"); lh1.add_css_class("panel-header"); lh1.set_xalign(0)
            left_insp.append(lh1)
            self.proc_lbl = Gtk.Label(label=read_top_processes()); self.proc_lbl.add_css_class("panel-sub"); self.proc_lbl.set_xalign(0)
            left_insp.append(self.proc_lbl)

            lh2 = Gtk.Label(label="⌬ СЕТЕВОЙ ИНСПЕКТОР И DEV-ПОРТЫ"); lh2.add_css_class("panel-header"); lh2.set_xalign(0)
            left_insp.append(lh2)
            self.net_info_lbl = Gtk.Label(label=f"Локальный IP: {read_local_ip()}\nПорты: {scan_dev_ports()}")
            self.net_info_lbl.add_css_class("panel-sub"); self.net_info_lbl.set_xalign(0)
            left_insp.append(self.net_info_lbl)

            sp_box = Gtk.Box(); sp_box.set_vexpand(True); left_insp.append(sp_box)

            b_ram = Gtk.Button(label="⚡ Сбросить кэш ОЗУ (Drop Caches)"); b_ram.add_css_class("primary-btn")
            b_ram.connect("clicked", lambda _b: self.spawn_raw("sudo -n /usr/local/bin/cyber-power-hw purge-ram && notify-send '⌬ NETRUNNER' 'Страничный кэш ОЗУ очищен'"))
            left_insp.append(b_ram)

            b_dns = Gtk.Button(label="🩺 Восстановить сеть / DNS без VPN"); b_dns.add_css_class("secondary-btn")
            b_dns.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-net-doctor && notify-send '⌬ NETRUNNER' 'Маршруты и DNS проверены'"))
            left_insp.append(b_dns)

            mid_split.append(left_insp)
            mid_split.append(self.build_app_grid(max_cols=4))
            root_box.append(mid_split)

            # Нижний интерактивный CLI-раннер для мгновенного выполнения bash-команд со стола
            cli_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            cli_bar.add_css_class("footer-bar"); cli_bar.set_vexpand(False)
            cli_lbl = Gtk.Label(label="⌬ BASH // EXEC ⟫"); cli_lbl.add_css_class("panel-header")
            cli_bar.append(cli_lbl)
            cli_entry = Gtk.Entry(); cli_entry.set_placeholder_text("Введите команду (например: htop, git status, python3 ...) и нажмите Enter...")
            cli_entry.add_css_class("search-entry"); cli_entry.set_hexpand(True)
            cli_entry.connect("activate", lambda e: (self.spawn_raw(f"~/.local/bin/launch-free-ws foot -e sh -c '{e.get_text()}; exec bash'"), e.set_text("")) if e.get_text().strip() else None)
            cli_bar.append(cli_entry)
            root_box.append(cli_bar)

        elif self.layout_mode == "cryo":
            # === ОКРУЖЕНИЕ 4: ORBITAL CRYO STUDIO (Крупный орбитальный дашборд + Сетка + Нижний док избранного) ===
            hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=22)
            hero.add_css_class("hero-banner"); hero.set_vexpand(False)

            clk_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            self.hero_time = Gtk.Label(label=datetime.datetime.now().strftime("%H:%M")); self.hero_time.add_css_class("big-clock"); self.hero_time.set_xalign(0)
            self.hero_date = Gtk.Label(label=datetime.datetime.now().strftime("✦ %d.%m.%Y  •  ORBITAL STUDIO READY")); self.hero_date.add_css_class("big-sub"); self.hero_date.set_xalign(0)
            clk_col.append(self.hero_time); clk_col.append(self.hero_date)
            hero.append(clk_col)

            h_sp = Gtk.Box(); h_sp.set_hexpand(True); hero.append(h_sp)

            for title_b, sub_b, cmd_b in [
                ("✦ Новый рабочий стол", "Свободный стол", "~/.local/bin/launch-free-ws"),
                ("✦ Терминал Studio", "Консоль разработчика", "~/.local/bin/launch-free-ws foot"),
                ("✦ Менеджер файлов", "Открыть проект", "~/.local/bin/launch-free-ws ~/.local/bin/cyber-fm"),
                ("✦ Сменить окружение", "Выбор темы", "~/.local/bin/cyber-theme menu"),
            ]:
                tb = Gtk.Button(); tb.add_css_class("hero-tile")
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); vb.set_valign(Gtk.Align.CENTER)
                l1 = Gtk.Label(label=title_b); l1.add_css_class("card-title"); l1.set_xalign(0)
                l2 = Gtk.Label(label=sub_b); l2.add_css_class("card-sub"); l2.set_xalign(0)
                vb.append(l1); vb.append(l2); tb.set_child(vb)
                tb.connect("clicked", lambda _b, c=cmd_b: self.spawn_raw(c))
                hero.append(tb)

            root_box.append(hero)
            root_box.append(self.build_app_grid(max_cols=5))

            # Нижний парящий док закреплённых (избранных) приложений
            dock_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            dock_wrap.add_css_class("bottom-dock"); dock_wrap.set_halign(Gtk.Align.CENTER); dock_wrap.set_vexpand(False)
            dlbl = Gtk.Label(label="✦ ИЗБРАННЫЙ ДОК:"); dlbl.add_css_class("panel-header"); dock_wrap.append(dlbl)
            self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            dock_wrap.append(self.dock_box)
            root_box.append(dock_wrap)

        else:
            # === ОКРУЖЕНИЕ 1: CYBERDECK TACTICAL OS (Инспектор активных dev-портов + 5-колоночная матрица + Хоткеи) ===
            dev_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            dev_bar.add_css_class("footer-bar"); dev_bar.set_vexpand(False)
            dl1 = Gtk.Label(label="◈ TACTICAL DEV RADAR //"); dl1.add_css_class("panel-header"); dev_bar.append(dl1)
            self.ports_lbl = Gtk.Label(label=f"Активные порты: {scan_dev_ports()}   •   Локальный узел: {read_local_ip()}")
            self.ports_lbl.add_css_class("panel-sub"); dev_bar.append(self.ports_lbl)
            dsp = Gtk.Box(); dsp.set_hexpand(True); dev_bar.append(dsp)
            b_purge = Gtk.Button(label="⚡ Очистить ОЗУ"); b_purge.add_css_class("ws-new-btn")
            b_purge.connect("clicked", lambda _b: self.spawn_raw("sudo -n /usr/local/bin/cyber-power-hw purge-ram && notify-send '◈ TACTICAL OS' 'Кэш ОЗУ освобождён'"))
            dev_bar.append(b_purge)
            root_box.append(dev_bar)

            root_box.append(self.build_app_grid(max_cols=5))

            footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            footer.add_css_class("footer-bar"); footer.set_halign(Gtk.Align.CENTER); footer.set_vexpand(False)
            for k_txt, d_txt in [("SUPER+SPACE", "Свободный стол"), ("SUPER+T", "Сменить окружение"), ("SUPER+SHIFT+P", "Перфоманс/Эко"), ("SUPER+P", "Поверх окон"), ("SUPER+E", "Проводник"), ("SUPER+H", "В фон"), ("SUPER+L", "Блокировка")]:
                kl = Gtk.Label(label=k_txt); kl.add_css_class("key-badge")
                dl = Gtk.Label(label=d_txt); dl.add_css_class("key-desc")
                footer.append(kl); footer.append(dl)
            root_box.append(footer)

        overlay.add_overlay(root_box); win.set_child(overlay)
        self.populate_apps(); self.refresh_workspaces(); self.refresh_status()
        GLib.timeout_add(1200, self.refresh_workspaces)
        GLib.timeout_add_seconds(3, self.refresh_status)
        win.present()

    def on_pomo_toggle(self, _b):
        self.pomo_running = not self.pomo_running

    def on_pomo_reset(self, _b):
        self.pomo_running = False
        self.pomo_sec = 25 * 60
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
        self.search.set_placeholder_text(f"{ENV_META.get('symbol', '◈')} Поиск среди {len(items)} рабочих программ (ЛКМ: новый стол • ПКМ: закрепить)...")

        for name, cmd, icon_spec, cat_tag in items:
            is_pin = name in self.pinned
            btn = Gtk.Button(); btn.add_css_class("app-card")
            hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

            stripe = Gtk.Box(); stripe.add_css_class("stripe-pinned" if is_pin else "stripe-normal"); stripe.set_vexpand(True); hb.append(stripe)
            ic_box = Gtk.Box(); ic_box.add_css_class("icon-frame"); ic_box.set_valign(Gtk.Align.CENTER)
            ic_box.append(make_cyber_icon_widget(icon_spec, "applications-development-symbolic", 34)); hb.append(ic_box)

            vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5); vb.set_valign(Gtk.Align.CENTER); vb.set_hexpand(True)
            t = Gtk.Label(label=name); t.add_css_class("card-title"); t.set_xalign(0.0); t.set_ellipsize(Pango.EllipsizeMode.END); t.set_max_width_chars(20); vb.append(t)
            meta_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            chip = Gtk.Label(label=cat_tag); chip.add_css_class("cat-chip")
            sub = Gtk.Label(label="★ PINNED" if is_pin else "FREE WS"); sub.add_css_class("card-sub"); sub.set_xalign(0.0)
            meta_row.append(chip); meta_row.append(sub); vb.append(meta_row); hb.append(vb)

            glyph = Gtk.Label(label="⟫"); glyph.add_css_class("launch-glyph"); glyph.set_valign(Gtk.Align.CENTER); hb.append(glyph)
            btn.set_child(hb)
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
            for name, cmd, icon_spec, _cat in favs:
                db = Gtk.Button(label=name[:14]); db.add_css_class("ws-btn")
                db.connect("clicked", lambda _b, c=cmd: self.spawn_raw(f"$HOME/.local/bin/launch-free-ws {c}"))
                self.dock_box.append(db)

        self.on_filter(self.search)

    def toggle_pin(self, name):
        if name in self.pinned: self.pinned.remove(name)
        else: self.pinned.add(name)
        save_pinned(self.pinned); self.populate_apps()

    def on_filter(self, entry):
        q = entry.get_text().strip().lower()
        for tl, btn in self.cards:
            if btn.get_parent(): btn.get_parent().set_visible((not q) or (q in tl))

    def refresh_workspaces(self):
        try:
            if os.path.isfile(KB_FILE):
                kb_code = open(KB_FILE).read().strip() or "EN"
                if self.kb_btn.get_label() != kb_code: self.kb_btn.set_label(kb_code)
        except Exception: pass
        try:
            bg_list = cyber_bg.get_bg_and_open_items()
            total_bg = sum(i.get("count", 1) for i in bg_list)
            lbl_bg = f"◈ Фон [{total_bg}]"
            if self.bg_menu_btn.get_label() != lbl_bg: self.bg_menu_btn.set_label(lbl_bg)

            clients = cyber_bg.hypr_ipc_json("clients")
            ws_map = {}
            for cl in clients:
                wid = cl.get("workspace", {}).get("id", -1)
                if wid > 0 and wid not in ws_map: ws_map[wid] = (cl.get("class") or cl.get("title") or "App")[:10]
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
        val = int(scale.get_value()); self.bri_pct_lbl.set_label(f"{val}%"); self.set_hw_bri(val)

    def on_bri_icon_clicked(self, _b):
        cur = int(self.bri_scale.get_value()); self.bri_scale.set_value(100 if cur < 95 else 60)

    def get_current_vol(self):
        try: return float(subprocess.check_output(["pamixer", "--get-volume"], text=True, stderr=subprocess.DEVNULL).strip())
        except Exception: return 50.0

    def on_vol_changed(self, scale):
        val = int(scale.get_value()); self.vol_pct_lbl.set_label(f"{val}%")
        subprocess.Popen(["pamixer", "--set-volume", str(val)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def apply_battery_ui(self, binfo):
        pct, status, watts = int(binfo.get("pct", 100)), binfo.get("status", "AC"), float(binfo.get("watts", 0.0))
        if not binfo.get("present", False): self.bat_lbl.set_label("AC 100%")
        else: self.bat_lbl.set_label(f"BAT {'+' if status == 'Charging' else ''}{pct}%{f' • {watts:.0f}W' if watts >= 1.0 else ''}")
        self.bat_bar.set_fraction(min(1.0, max(0.0, pct / 100.0)))

    def refresh_status(self):
        now_s = datetime.datetime.now().strftime("%H:%M")
        self.clock_lbl.set_label(now_s)
        if getattr(self, "hero_time", None): self.hero_time.set_label(now_s)

        idle, total = read_cpu_stat()
        dt, di = total - self.prev_total, idle - self.prev_idle
        self.prev_idle, self.prev_total = idle, total
        cpu_pct = int(round(100.0 * (dt - di) / dt)) if dt > 0 else 0
        self.cpu_lbl.set_label(f"CPU {cpu_pct}%"); self.cpu_bar.set_fraction(min(1.0, max(0.0, cpu_pct / 100.0)))

        ram_txt, ram_frac = read_ram_info()
        self.ram_lbl.set_label(f"RAM {ram_txt}"); self.ram_bar.set_fraction(ram_frac)
        self.apply_battery_ui(read_battery())

        w_info = read_wifi_state()
        self.wifi_btn.set_child(ui_svg(w_info.get("icon", "wifi-high.svg"), 17))
        z_ok = subprocess.call(["pgrep", "-x", "nfqws"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        self.net_lbl.set_label(f"● VPN • {'ВКЛ' if z_ok else 'ОК'}")
        self.update_pwr_label()

        if self.proc_lbl: self.proc_lbl.set_label(read_top_processes())
        if self.net_info_lbl: self.net_info_lbl.set_label(f"Локальный IP: {read_local_ip()}\nПорты: {scan_dev_ports()}")
        if self.ports_lbl: self.ports_lbl.set_label(f"Активные порты: {scan_dev_ports()}   •   Локальный узел: {read_local_ip()}")
        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    WorkHubApp().run(None)
