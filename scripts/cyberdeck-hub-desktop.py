#!/usr/bin/env python3
import os, sys, re, glob, json, shutil, subprocess, datetime, importlib.util

ORIG_GTK_THEME = os.environ.get("GTK_THEME")
os.environ["GTK_THEME"] = "Adwaita:dark"

from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Pango

HAS_LAYER = False
try:
    gi.require_version("Gtk4LayerShell", "1.0")
    from gi.repository import Gtk4LayerShell
    HAS_LAYER = True
except Exception:
    HAS_LAYER = False

os.environ.pop("LD_PRELOAD", None)

HOME = os.path.expanduser("~")
UID = os.getuid()
CACHE_DIR = os.path.join(HOME, ".cache/cyberdeck")
BG_PNG = os.path.join(CACHE_DIR, "cyberdeck_hud_bg.png")
if not os.path.isfile(BG_PNG):
    BG_PNG = os.path.join(CACHE_DIR, "work_hud_bg.png")
HW_JSON = os.path.join(CACHE_DIR, "hw_profile.json")
UI_ICONS = os.path.join(HOME, ".config/hypr/assets/ui")
ROFI_THEME = os.path.join(HOME, ".config/hypr/gaming_launcher.rasi")
PIN_FILE = os.path.join(HOME, ".config/cyberdeck/pinned_cyberdeck_apps.json")
KB_FILE = f"/tmp/alpora_kb_layout_{UID}"

_spec = importlib.util.spec_from_file_location("cyber_bg_helper", os.path.join(HOME, ".local/bin/cyber-bg-helper.py"))
cyber_bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cyber_bg)

CSS = open(os.path.join(HOME, ".local/bin/work-hub-desktop.py"), encoding="utf-8").read().split('CSS = """', 1)[1].split('"""', 1)[0]

def load_hw_profile():
    try: return json.load(open(HW_JSON, encoding="utf-8"))
    except Exception: return {"form_factor": "desktop", "has_battery": False, "has_wifi": False, "terminal": "foot"}

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
    if "firefox" in low or "librewolf" in low or "zen" in low: candidates.append("firefox")
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
        mons = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"], text=True, stderr=subprocess.DEVNULL))
        if mons:
            sc = float(mons[0].get("scale", 1.0)) or 1.0
            return int(mons[0]["width"] / sc), int(mons[0]["height"] / sc), int(round(float(mons[0]["refreshRate"])))
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

def read_power_telemetry():
    try: return json.loads(subprocess.check_output([os.path.join(HOME, ".local/bin/battery-status"), "--json"], text=True, stderr=subprocess.DEVNULL))
    except Exception: return {"present": False, "pct": 100, "status": "AC", "watts": 0.0, "temp_c": 45}

def read_net_telemetry():
    try: return json.loads(subprocess.check_output([os.path.join(HOME, ".local/bin/net-status")], text=True, stderr=subprocess.DEVNULL, timeout=1.2))
    except Exception: return {"mode": "lan", "connected": True, "has_wifi": False, "label": "ONLINE", "signal": 100, "icon": "lan.svg", "vpn": False, "zapret": False}

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
    if "game" in low: return "GAME"
    return "SYS"

def discover_apps():
    apps, seen = [], set()
    for ad in (os.path.join(HOME, ".local/share/applications"), "/usr/share/applications"):
        if not os.path.isdir(ad): continue
        for df in sorted(glob.glob(os.path.join(ad, "*.desktop"))):
            try:
                txt = open(df, errors="ignore").read()
                if re.search(r"^NoDisplay=true", txt, re.M) or re.search(r"^Hidden=true", txt, re.M): continue
                cats_m = re.search(r"^Categories=(.*)$", txt, re.M)
                cats = cats_m.group(1) if cats_m else ""
                nm, ex, ic = re.search(r"^Name=(.*)$", txt, re.M), re.search(r"^Exec=(.*)$", txt, re.M), re.search(r"^Icon=(.*)$", txt, re.M)
                if not (nm and ex): continue
                name = nm.group(1).strip()
                if name in seen: continue
                cmd = re.sub(r"\s+%[fFuUdDnNickvm]", "", ex.group(1).strip())
                icon = ic.group(1).strip() if ic else "applications-system-symbolic"
                seen.add(name)
                apps.append((name, cmd, icon, classify_cat(cats, name)))
            except Exception: pass
    return apps

class CyberDeckHubApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.cyberdeck.AdaptiveHub")
        self.hw = load_hw_profile()
        self.cards = []
        self.pinned = load_pinned()
        self.prev_idle, self.prev_total = read_cpu_stat()
        self.last_ws_sig = None
        self.last_bg_sig = None

    def do_activate(self):
        settings = Gtk.Settings.get_default()
        if settings: settings.set_property("gtk-application-prefer-dark-theme", True)
        prov = Gtk.CssProvider()
        if hasattr(prov, "load_from_string"): prov.load_from_string(CSS)
        else: prov.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 20)

        win = Gtk.ApplicationWindow(application=self, title="CyberDeckHubDesktop")
        if HAS_LAYER and Gtk4LayerShell.is_supported():
            Gtk4LayerShell.init_for_window(win)
            Gtk4LayerShell.set_namespace(win, "cyberdeck-hub-wallpaper")
            Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.BACKGROUND)
            for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
                Gtk4LayerShell.set_anchor(win, edge, True)
            Gtk4LayerShell.set_exclusive_zone(win, -1)
            Gtk4LayerShell.set_keyboard_mode(win, Gtk4LayerShell.KeyboardMode.ON_DEMAND)
        else:
            win.fullscreen()

        overlay = Gtk.Overlay()
        if os.path.isfile(BG_PNG):
            bg_pic = Gtk.Picture.new_for_filename(BG_PNG)
            bg_pic.set_can_shrink(True)
            if hasattr(Gtk, "ContentFit"): bg_pic.set_content_fit(Gtk.ContentFit.COVER)
            overlay.set_child(bg_pic)

        w_mon, h_mon, hz_mon = get_monitor_info()
        cols_max = 6 if w_mon >= 2400 else (5 if w_mon >= 1750 else (4 if w_mon >= 1360 else 3))

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root_box.add_css_class("hub-overlay")
        root_box.set_hexpand(True); root_box.set_vexpand(True)

        top = Gtk.CenterBox(); top.add_css_class("top-deck"); top.set_vexpand(False)

        left_zone = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); left_zone.set_valign(Gtk.Align.CENTER)
        brand = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7); brand.add_css_class("brand-pill"); brand.set_valign(Gtk.Align.CENTER)
        bdot = Gtk.Label(label="◈"); bdot.add_css_class("brand-dot")
        mode_tag = "LAPTOP" if self.hw.get("form_factor") == "laptop" else "PC"
        bt = Gtk.Label(label=f"CYBER DECK // {mode_tag}"); bt.add_css_class("brand-title")
        brand.append(bdot); brand.append(bt); left_zone.append(brand)

        ws_scroll = Gtk.ScrolledWindow()
        ws_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        ws_scroll.set_max_content_width(max(150, int(w_mon * 0.12)))
        ws_scroll.set_propagate_natural_width(True); ws_scroll.set_valign(Gtk.Align.CENTER)
        self.ws_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); self.ws_box.set_valign(Gtk.Align.CENTER)
        ws_scroll.set_child(self.ws_box); left_zone.append(ws_scroll)

        new_ws_btn = Gtk.Button(label="+ Стол"); new_ws_btn.add_css_class("ws-new-btn"); new_ws_btn.set_valign(Gtk.Align.CENTER)
        new_ws_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/launch-free-ws"))
        left_zone.append(new_ws_btn)

        self.dock_sep = Gtk.Box(); self.dock_sep.add_css_class("dock-sep"); self.dock_sep.set_visible(False)
        left_zone.append(self.dock_sep)

        app_scroll = Gtk.ScrolledWindow()
        app_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        app_scroll.set_max_content_width(max(160, int(w_mon * 0.13)))
        app_scroll.set_propagate_natural_width(True); app_scroll.set_valign(Gtk.Align.CENTER)
        self.bg_items_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); self.bg_items_box.set_valign(Gtk.Align.CENTER)
        app_scroll.set_child(self.bg_items_box); left_zone.append(app_scroll)
        top.set_start_widget(left_zone)

        center_pod = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9); center_pod.add_css_class("telemetry-pod"); center_pod.set_valign(Gtk.Align.CENTER)
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
        pwr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); pwr_row.set_valign(Gtk.Align.CENTER)
        self.bat_lbl = Gtk.Label(label="BAT --%" if self.hw.get("has_battery") else "TEMP --°C"); self.bat_lbl.add_css_class("metric-lbl")
        self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good"); self.bat_bar.set_valign(Gtk.Align.CENTER)
        pwr_row.append(self.bat_lbl); pwr_row.append(self.bat_bar); center_pod.append(pwr_row)

        s3 = Gtk.Box(); s3.add_css_class("pod-sep"); center_pod.append(s3)
        self.net_lbl = Gtk.Label(label="● ONLINE"); self.net_lbl.add_css_class("net-badge"); self.net_lbl.set_valign(Gtk.Align.CENTER)
        center_pod.append(self.net_lbl); top.set_center_widget(center_pod)

        right_zone = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); right_zone.set_valign(Gtk.Align.CENTER)
        self.wifi_btn = Gtk.Button(); self.wifi_btn.add_css_class("wifi-btn"); self.wifi_btn.set_valign(Gtk.Align.CENTER)
        self.wifi_btn.set_child(ui_svg("wifi-high.svg" if self.hw.get("has_wifi") else "lan.svg", 17))
        self.wifi_btn.connect("clicked", self.on_net_clicked); right_zone.append(self.wifi_btn)

        self.kb_btn = Gtk.Button(label="EN"); self.kb_btn.add_css_class("kb-btn"); self.kb_btn.set_valign(Gtk.Align.CENTER)
        self.kb_btn.connect("clicked", lambda _b: self.spawn_raw("hyprctl switchxkblayout all next")); right_zone.append(self.kb_btn)

        self.pwr_btn = None
        if shutil.which("powerprofilesctl"):
            self.pwr_btn = Gtk.Button(); self.pwr_btn.add_css_class("ctrl-pill"); self.pwr_btn.set_valign(Gtk.Align.CENTER)
            self.pwr_btn.connect("clicked", self.on_toggle_power); self.update_pwr_label(); right_zone.append(self.pwr_btn)

        audio_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); audio_cap.add_css_class("audio-capsule"); audio_cap.set_valign(Gtk.Align.CENTER)
        audio_btn = Gtk.Button(); audio_btn.add_css_class("audio-icon-btn"); audio_btn.set_valign(Gtk.Align.CENTER)
        audio_btn.set_child(ui_svg("audio.svg", 16)); audio_btn.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-audio-menu"))
        audio_cap.append(audio_btn)

        cur_v = self.get_current_vol()
        self.vol_pct_lbl = Gtk.Label(label=f"{int(cur_v)}%"); self.vol_pct_lbl.add_css_class("vol-pct"); self.vol_pct_lbl.set_valign(Gtk.Align.CENTER)
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_draw_value(False); self.vol_scale.set_size_request(74, -1); self.vol_scale.set_valign(Gtk.Align.CENTER)
        self.vol_scale.set_value(cur_v); self.vol_scale.connect("value-changed", self.on_vol_changed)
        audio_cap.append(self.vol_scale); audio_cap.append(self.vol_pct_lbl); right_zone.append(audio_cap)

        sys_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2); sys_cap.add_css_class("power-capsule"); sys_cap.set_valign(Gtk.Align.CENTER)
        btop_b = Gtk.Button(label="BTOP"); btop_b.add_css_class("icon-act-btn"); btop_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-tool btop")); sys_cap.append(btop_b)
        lock_b = Gtk.Button(); lock_b.add_css_class("icon-act-btn"); lock_b.set_child(ui_svg("lock.svg", 15)); lock_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-lock")); sys_cap.append(lock_b)
        sddm_b = Gtk.Button(label="SDDM"); sddm_b.add_css_class("danger-act-btn"); sddm_b.connect("clicked", lambda _b: self.spawn_raw("hyprctl dispatch exit")); sys_cap.append(sddm_b)
        reb_b = Gtk.Button(); reb_b.add_css_class("icon-act-btn"); reb_b.set_child(ui_svg("reboot.svg", 15)); reb_b.connect("clicked", lambda _b: self.spawn_raw("systemctl reboot")); sys_cap.append(reb_b)
        off_b = Gtk.Button(); off_b.add_css_class("danger-act-btn"); off_b.set_child(ui_svg("power.svg", 15)); off_b.connect("clicked", lambda _b: self.spawn_raw("systemctl poweroff")); sys_cap.append(off_b)
        right_zone.append(sys_cap)

        cbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7); cbox.add_css_class("clock-pill"); cbox.set_valign(Gtk.Align.CENTER)
        self.clock_lbl = Gtk.Label(label="00:00"); self.clock_lbl.add_css_class("clock-time")
        hz_lbl = Gtk.Label(label=f"{hz_mon}Hz"); hz_lbl.add_css_class("clock-hz")
        cbox.append(self.clock_lbl); cbox.append(hz_lbl); right_zone.append(cbox)
        top.set_end_widget(right_zone); root_box.append(top)

        act_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10); act_row.set_vexpand(False)
        self.search = Gtk.Entry(); self.search.add_css_class("search-entry"); self.search.set_hexpand(True)
        self.search.connect("changed", self.on_filter); act_row.append(self.search)

        term_bin = self.hw.get("terminal") or "foot"
        for b_lbl, b_cmd, cls in [
            ("▶ Терминал [Новый стол]", f"~/.local/bin/launch-free-ws {term_bin}", "primary-btn"),
            ("◈ Окно поверх [SUPER+P]", "~/.local/bin/hyprwork-pin-window", "secondary-btn"),
            ("Пипетка HEX", "~/.local/bin/cyber-tool pick", "ctrl-pill"),
            ("Скриншот", "~/.local/bin/cyber-tool shot", "secondary-btn"),
            ("Все приложения", f'rofi -show drun -theme "{ROFI_THEME}" -run-command "$HOME/.local/bin/launch-free-ws {{cmd}}"', "ctrl-pill"),
            ("Обновить", "REFRESH", "ctrl-pill"),
        ]:
            b = Gtk.Button(label=b_lbl); b.add_css_class(cls)
            if b_cmd == "REFRESH": b.connect("clicked", lambda _b: self.populate_apps())
            else: b.connect("clicked", lambda _b, c=b_cmd: self.spawn_raw(c))
            act_row.append(b)
        root_box.append(act_row)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True); scroll.set_hexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.flow = Gtk.FlowBox(); self.flow.set_valign(Gtk.Align.START)
        self.flow.set_max_children_per_line(cols_max); self.flow.set_min_children_per_line(2)
        self.flow.set_column_spacing(14); self.flow.set_row_spacing(14)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        scroll.set_child(self.flow); root_box.append(scroll)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        footer.add_css_class("footer-bar"); footer.set_halign(Gtk.Align.CENTER); footer.set_vexpand(False)
        for k_txt, d_txt in [("SUPER+SPACE", "Свободный стол"), ("SUPER+P", "Поверх окон"), ("SUPER+ЛКМ", "Двигать окно"), ("SUPER+H", "В фон"), ("SUPER+S", "Скриншот"), ("SUPER+Q", "Закрыть"), ("SUPER+L", "Блокировка")]:
            kl = Gtk.Label(label=k_txt); kl.add_css_class("key-badge")
            dl = Gtk.Label(label=d_txt); dl.add_css_class("key-desc")
            footer.append(kl); footer.append(dl)
        root_box.append(footer)

        overlay.add_overlay(root_box); win.set_child(overlay)
        self.populate_apps(); self.refresh_workspaces(); self.refresh_status()
        GLib.timeout_add(950, self.refresh_workspaces)
        GLib.timeout_add_seconds(3, self.refresh_status)
        win.present()

    def on_net_clicked(self, _b):
        n = read_net_telemetry()
        if n.get("has_wifi"): self.spawn_raw("~/.local/bin/cyber-wifi-menu")
        else: self.spawn_raw(f'notify-send -a cyber-wifi "◈ ПРОВОДНАЯ СЕТЬ // ПК" "Статус: {n.get("label", "Ethernet")}"')

    def populate_apps(self):
        while True:
            ch = self.flow.get_first_child()
            if ch is None: break
            self.flow.remove(ch)
        self.cards.clear()
        items = discover_apps()
        items.sort(key=lambda x: (0 if x[0] in self.pinned else 1, x[0].lower()))
        self.search.set_placeholder_text(f"◈ Поиск среди {len(items)} установленных приложений (ЛКМ: новый стол • ПКМ: закрепить)...")
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
            sig_bg = tuple((i["name"], i["count"], i["is_bg"], i["lclick"]) for i in bg_list)
            if sig_bg != self.last_bg_sig:
                self.last_bg_sig = sig_bg
                while True:
                    c = self.bg_items_box.get_first_child()
                    if c is None: break
                    self.bg_items_box.remove(c)
                self.dock_sep.set_visible(bool(bg_list))
                for item in bg_list:
                    b = Gtk.Button(); b.add_css_class("top-app-bg" if item["is_bg"] else "top-app-btn"); b.set_valign(Gtk.Align.CENTER)
                    hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); hb.set_valign(Gtk.Align.CENTER)
                    hb.append(make_cyber_icon_widget(item["icon_spec"], "applications-system-symbolic", 20))
                    cnt_lbl = Gtk.Label(label="●" if item.get("is_daemon") else str(item["count"]))
                    cnt_lbl.add_css_class("app-cnt-multi" if item["count"] > 1 else "app-cnt-single"); cnt_lbl.set_valign(Gtk.Align.CENTER)
                    hb.append(cnt_lbl); b.set_child(hb)
                    b.connect("clicked", lambda _b, cmd=item["lclick"]: self.spawn_raw(cmd))
                    rc = Gtk.GestureClick.new(); rc.set_button(3)
                    rc.connect("pressed", lambda _g, _n, _x, _y, cmd=item["rclick"]: self.spawn_raw(cmd))
                    b.add_controller(rc); self.bg_items_box.append(b)
            clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"], text=True, stderr=subprocess.DEVNULL))
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

    def update_pwr_label(self):
        if not self.pwr_btn: return
        try: prof = subprocess.check_output(["powerprofilesctl", "get"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception: prof = "balanced"
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6); hb.set_valign(Gtk.Align.CENTER)
        if prof == "performance": hb.append(ui_svg("turbo.svg", 14)); hb.append(Gtk.Label(label="Турбо"))
        elif prof == "power-saver": hb.append(ui_svg("eco.svg", 14)); hb.append(Gtk.Label(label="Эко"))
        else: hb.append(ui_svg("bolt.svg", 14)); hb.append(Gtk.Label(label="Баланс"))
        self.pwr_btn.set_child(hb)

    def on_toggle_power(self, _b):
        try: prof = subprocess.check_output(["powerprofilesctl", "get"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception: prof = "balanced"
        cycle = ({"balanced": "power-saver", "power-saver": "performance", "performance": "balanced"} if self.hw.get("has_battery") else {"balanced": "performance", "performance": "balanced", "power-saver": "balanced"})
        subprocess.run(["powerprofilesctl", "set", cycle.get(prof, "balanced")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.update_pwr_label()

    def get_current_vol(self):
        try: return float(subprocess.check_output(["pamixer", "--get-volume"], text=True, stderr=subprocess.DEVNULL).strip())
        except Exception: return 50.0

    def on_vol_changed(self, scale):
        val = int(scale.get_value()); self.vol_pct_lbl.set_label(f"{val}%")
        subprocess.Popen(["pamixer", "--set-volume", str(val)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def apply_power_or_temp_ui(self, pinfo):
        for cls in ("bat-good", "bat-warn", "bat-crit"): self.bat_bar.remove_css_class(cls)
        if pinfo.get("present", False):
            pct, st, watts = int(pinfo.get("pct", 100)), pinfo.get("status", "Discharging"), float(pinfo.get("watts", 0.0))
            self.bat_lbl.set_label(f"BAT {'+' if st == 'Charging' else ''}{pct}%{f' • {watts:.0f}W' if watts >= 1.0 else ''}")
            self.bat_bar.set_fraction(min(1.0, max(0.0, pct / 100.0)))
            self.bat_bar.add_css_class("bat-good" if (st == "Charging" or pct > 30) else ("bat-warn" if pct > 15 else "bat-crit"))
        else:
            tc = int(pinfo.get("temp_c") or 42)
            self.bat_lbl.set_label(f"TEMP {tc}°C")
            self.bat_bar.set_fraction(min(1.0, max(0.1, tc / 100.0)))
            self.bat_bar.add_css_class("bat-good" if tc < 72 else ("bat-warn" if tc < 85 else "bat-crit"))

    def refresh_status(self):
        self.clock_lbl.set_label(datetime.datetime.now().strftime("%H:%M"))
        idle, total = read_cpu_stat()
        dt, di = total - self.prev_total, idle - self.prev_idle
        self.prev_idle, self.prev_total = idle, total
        cpu_pct = int(round(100.0 * (dt - di) / dt)) if dt > 0 else 0
        self.cpu_lbl.set_label(f"CPU {cpu_pct}%"); self.cpu_bar.set_fraction(min(1.0, max(0.0, cpu_pct / 100.0)))
        ram_txt, ram_frac = read_ram_info()
        self.ram_lbl.set_label(f"RAM {ram_txt}"); self.ram_bar.set_fraction(ram_frac)
        self.apply_power_or_temp_ui(read_power_telemetry())
        n = read_net_telemetry()
        self.wifi_btn.set_child(ui_svg(n.get("icon", "lan.svg"), 17))
        tags = (["VPN"] if n.get("vpn") else []) + (["DPI"] if n.get("zapret") else []) + [("WI-FI" if n.get("mode") == "wifi" and n.get("connected") else ("LAN" if n.get("connected") else "OFFLINE"))]
        self.net_lbl.set_label("● " + " • ".join(tags))
        self.update_pwr_label()
        try:
            vol_v = float(subprocess.check_output(["pamixer", "--get-volume"], text=True, stderr=subprocess.DEVNULL).strip())
            if abs(self.vol_scale.get_value() - vol_v) > 1.5:
                self.vol_scale.handler_block_by_func(self.on_vol_changed)
                self.vol_scale.set_value(vol_v); self.vol_pct_lbl.set_label(f"{int(vol_v)}%")
                self.vol_scale.handler_unblock_by_func(self.on_vol_changed)
        except Exception: pass
        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    CyberDeckHubApp().run(None)
