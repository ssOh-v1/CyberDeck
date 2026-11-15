#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
except Exception:
    pass

import os, sys, re, glob, json, calendar, subprocess, datetime, importlib.util

HOME = os.path.expanduser("~")
UID = os.getuid()
CFG_DIR = os.path.join(HOME, ".config/cyberdeck")
CACHE_DIR = os.path.join(HOME, ".cache/cyberdeck")
NOTES_FILE = os.path.join(CFG_DIR, "studio_notes.txt")

os.environ["XCURSOR_THEME"] = "GameDev-Cursor-Grey"
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
PIN_FILE = os.path.join(CFG_DIR, "pinned_work_apps.json")
KB_FILE = f"/tmp/alpora_kb_layout_{UID}"

_spec = importlib.util.spec_from_file_location("cyber_bg_helper", os.path.join(HOME, ".local/bin/cyber-bg-helper.py"))
cyber_bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cyber_bg)

RU_MONTHS = [
    "", "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ",
    "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"
]

def load_css():
    p = os.path.join(CFG_DIR, "active_hub.css")
    if os.path.isfile(p):
        try: return open(p, "r", encoding="utf-8").read()
        except Exception: pass
    return "window { background-color: #121316; color: #d4d8de; }"

def ui_svg(name, sz=14):
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
    elif any(x in low for x in ("thunar", "nautilus", "dolphin", "files", "folder")): candidates.append("folder")
    elif any(x in low for x in ("telegram", "ayugram")): candidates.append("telegram")
    elif any(x in low for x in ("discord", "vesktop", "legcord")): candidates.append("discord")
    elif "steam" in low: candidates.append("steam")
    candidates.append(fallback_glyph)
    for c in candidates:
        if c and os.path.isfile(os.path.join(theme_apps, f"{c}.svg")):
            return os.path.join(theme_apps, f"{c}.svg")
    return os.path.join(theme_apps, "default.svg") if os.path.isfile(os.path.join(theme_apps, "default.svg")) else None

def make_cyber_icon_widget(icon_spec, fallback_glyph="default", size=20):
    svg_path = resolve_cyber_svg(icon_spec, fallback_glyph)
    img = Gtk.Image.new_from_file(svg_path) if svg_path else Gtk.Image.new_from_icon_name(icon_spec or "application-x-executable")
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
        return f"{used/1048576.0:.1f} / {tot/1048576.0:.0f} GB", min(1.0, max(0.0, used / tot))
    except Exception: return "--", 0.0

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
                if p in (3000, 4000, 5000, 5173, 7860, 8000, 8080, 8888, 11434) and f":{p}" not in ports:
                    ports.append(f":{p}")
    except Exception: pass
    return " ".join(ports[:4]) if ports else "нет активных"

def read_git_projects_status():
    rows = []
    candidates = [os.path.join(HOME, "CyberDeck")]
    for d in sorted(glob.glob(os.path.join(HOME, "*"))):
        if os.path.isdir(os.path.join(d, ".git")) and d not in candidates:
            candidates.append(d)
    for repo in candidates[:3]:
        if not os.path.isdir(os.path.join(repo, ".git")): continue
        name = os.path.basename(repo)
        try:
            br = subprocess.check_output(["git", "-C", repo, "symbolic-ref", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
            chg = len(subprocess.check_output(["git", "-C", repo, "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL).splitlines())
            st = f"изм: {chg}" if chg > 0 else "чисто"
            rows.append(f"▸ {name[:13]:<13} [{br}] • {st}")
        except Exception: pass
    return "\n".join(rows) if rows else "▸ Репозитории Git готовы"

def read_music_status():
    try:
        status = subprocess.check_output(["playerctl", "status"], text=True, stderr=subprocess.DEVNULL, timeout=0.6).strip()
        title  = subprocess.check_output(["playerctl", "metadata", "xesam:title"], text=True, stderr=subprocess.DEVNULL, timeout=0.6).strip()
        artist = subprocess.check_output(["playerctl", "metadata", "xesam:artist"], text=True, stderr=subprocess.DEVNULL, timeout=0.6).strip()
        player = subprocess.check_output(["playerctl", "-l"], text=True, stderr=subprocess.DEVNULL, timeout=0.6).splitlines()[0].split(".")[0]
        if title:
            icon_st = "▶" if status == "Playing" else "⏸"
            return f"{icon_st} {title[:26]}", f"{artist[:24] or 'Медиаплеер'}  •  [{player.upper()}]", status == "Playing"
    except Exception:
        pass
    return "⏹ Нет активного трека", "Запустите музыку в браузере или плеере", False

def load_pinned():
    try: return set(json.load(open(PIN_FILE, encoding="utf-8"))) if os.path.isfile(PIN_FILE) else set()
    except Exception: return set()

def save_pinned(pins):
    os.makedirs(os.path.dirname(PIN_FILE), exist_ok=True)
    json.dump(sorted(pins), open(PIN_FILE, "w", encoding="utf-8"), ensure_ascii=False)

def discover_work_apps():
    apps, seen = [], set()
    for ad in (os.path.join(HOME, ".local/share/applications"), "/usr/share/applications"):
        if not os.path.isdir(ad): continue
        for df in sorted(glob.glob(os.path.join(ad, "*.desktop"))):
            try:
                txt = open(df, errors="ignore").read()
                if re.search(r"^NoDisplay=true", txt, re.M) or re.search(r"^Hidden=true", txt, re.M): continue
                nm, ex, ic = re.search(r"^Name=(.*)$", txt, re.M), re.search(r"^Exec=(.*)$", txt, re.M), re.search(r"^Icon=(.*)$", txt, re.M)
                if not (nm and ex): continue
                name = nm.group(1).strip()
                if name in seen: continue
                cmd = re.sub(r"\s+%[fFuUdDnNickvm]", "", ex.group(1).strip())
                icon = ic.group(1).strip() if ic else "applications-system-symbolic"
                seen.add(name)
                apps.append((name, cmd, icon))
            except Exception: pass
    return apps

class GameDevStudioHub(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.alpora.WorkDeckLayer")
        self.pinned = load_pinned()
        self.last_pin_mtime = 0
        self.prev_idle, self.prev_total = read_cpu_stat()
        self.last_ws_sig = None
        self.notes_buf = None

        now = datetime.date.today()
        self.cal_year = now.year
        self.cal_month = now.month
        self.cal_title_lbl = None
        self.cal_grid = None

        self.bg_surface = None
        if os.path.isfile(BG_PNG):
            try: self.bg_surface = cairo.ImageSurface.create_from_png(BG_PNG)
            except Exception: self.bg_surface = None

    def on_draw_background(self, _area, cr, w, h, *_args):
        cr.save()
        cr.scale(w / 1920.0, h / 1080.0)
        if self.bg_surface is not None:
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0.07, 0.075, 0.086)
            cr.paint()
        cr.restore()

    def make_sliders_pair(self, width_px=44):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5); box.set_valign(Gtk.Align.CENTER)
        bri_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); bri_cap.add_css_class("audio-capsule")
        bri_btn = Gtk.Button(); bri_btn.add_css_class("audio-icon-btn"); bri_btn.set_child(ui_svg("sun.svg", 14))
        bri_btn.connect("clicked", self.on_bri_icon_clicked); bri_cap.append(bri_btn)
        cur_b = self.get_current_bri()
        self.bri_pct_lbl = Gtk.Label(label=f"{int(cur_b)}%"); self.bri_pct_lbl.add_css_class("vol-pct")
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.bri_scale.set_draw_value(False); self.bri_scale.set_size_request(width_px, -1); self.bri_scale.set_value(cur_b)
        self.bri_scale.connect("value-changed", self.on_bri_changed)
        bri_cap.append(self.bri_scale); bri_cap.append(self.bri_pct_lbl); box.append(bri_cap)

        audio_cap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4); audio_cap.add_css_class("audio-capsule")
        audio_btn = Gtk.Button(); audio_btn.add_css_class("audio-icon-btn"); audio_btn.set_child(ui_svg("audio.svg", 14))
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
        lock_b = Gtk.Button(); lock_b.add_css_class("icon-act-btn"); lock_b.set_child(ui_svg("lock.svg", 14)); lock_b.connect("clicked", lambda _b: self.spawn_raw("~/.local/bin/cyber-lock")); sys_cap.append(lock_b)
        sddm_b = Gtk.Button(label="SDDM"); sddm_b.add_css_class("danger-act-btn"); sddm_b.connect("clicked", lambda _b: self.spawn_raw("hyprctl dispatch exit")); sys_cap.append(sddm_b)
        reb_b = Gtk.Button(); reb_b.add_css_class("icon-act-btn"); reb_b.set_child(ui_svg("reboot.svg", 14)); reb_b.connect("clicked", lambda _b: self.spawn_raw("systemctl reboot")); sys_cap.append(reb_b)
        off_b = Gtk.Button(); off_b.add_css_class("danger-act-btn"); off_b.set_child(ui_svg("power.svg", 14)); off_b.connect("clicked", lambda _b: self.spawn_raw("systemctl poweroff")); sys_cap.append(off_b)
        return sys_cap

    # --- ВИДЖЕТ КАЛЕНДАРЯ ---
    def rebuild_calendar_grid(self):
        if not self.cal_grid or not self.cal_title_lbl: return
        self.cal_title_lbl.set_label(f"📅 {RU_MONTHS[self.cal_month]} {self.cal_year}")
        while True:
            ch = self.cal_grid.get_first_child()
            if ch is None: break
            self.cal_grid.remove(ch)

        for col_i, dow in enumerate(("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")):
            lbl = Gtk.Label(label=dow); lbl.add_css_class("cal-dow")
            self.cal_grid.attach(lbl, col_i, 0, 1, 1)

        today = datetime.date.today()
        cal = calendar.Calendar(firstweekday=0)
        for row_i, week in enumerate(cal.monthdayscalendar(self.cal_year, self.cal_month), start=1):
            for col_i, day_num in enumerate(week):
                if day_num == 0:
                    lbl = Gtk.Label(label=" ")
                    lbl.add_css_class("cal-day")
                else:
                    lbl = Gtk.Label(label=f"{day_num:2d}")
                    is_today = (day_num == today.day and self.cal_month == today.month and self.cal_year == today.year)
                    lbl.add_css_class("cal-today" if is_today else "cal-day")
                self.cal_grid.attach(lbl, col_i, row_i, 1, 1)

    def on_cal_shift(self, delta):
        if delta == 0:
            t = datetime.date.today()
            self.cal_year, self.cal_month = t.year, t.month
        else:
            m = self.cal_month + delta
            if m < 1:
                self.cal_month = 12; self.cal_year -= 1
            elif m > 12:
                self.cal_month = 1; self.cal_year += 1
            else:
                self.cal_month = m
        self.rebuild_calendar_grid()

    # --- ВИДЖЕТ ЗАМЕТОК ---
    def on_copy_notes(self, _b):
        if not self.notes_buf: return
        txt = self.notes_buf.get_text(self.notes_buf.get_start_iter(), self.notes_buf.get_end_iter(), False).strip()
        if txt:
            subprocess.run(["wl-copy"], input=txt, text=True, stderr=subprocess.DEVNULL)
            self.spawn_raw("notify-send -a cyber-kb '📝 ЗАМЕТКИ' 'Текст скопирован в буфер обмена'")

    def on_add_todo_item(self, _b):
        if not self.notes_buf: return
        end_it = self.notes_buf.get_end_iter()
        self.notes_buf.insert(end_it, "\n[ ] Новая задача...")

    def on_ai_quick_ask(self, entry):
        q = entry.get_text().strip()
        if not q: return
        subprocess.run(["wl-copy"], input=q, text=True, stderr=subprocess.DEVNULL)
        entry.set_text("")
        self.spawn_raw("notify-send -a cyber-kb '🧠 AI STUDIO' 'Запрос скопирован в буфер • Открываю Gemini' && firefox https://gemini.google.com")

    def do_activate(self):
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)
            settings.set_property("gtk-cursor-theme-name", "GameDev-Cursor-Grey")
            settings.set_property("gtk-cursor-theme-size", 28)
            settings.set_property("gtk-icon-theme-name", "CyberDeck-Icons")

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
        bg_area = Gtk.DrawingArea()
        bg_area.set_hexpand(True); bg_area.set_vexpand(True)
        bg_area.set_size_request(w_mon, h_mon)
        bg_area.set_draw_func(self.on_draw_background)
        overlay.set_child(bg_area)

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root_box.add_css_class("hub-overlay")
        root_box.set_hexpand(True); root_box.set_vexpand(True)

        # ======================================================================
        # 1. Верхний отступ под системный Waybar
        top_spacer = Gtk.Box(); top_spacer.set_size_request(-1, 42); root_box.append(top_spacer)

        # ======================================================================
        # 2. БОКОВЫЕ КОЛОНКИ ВИДЖЕТОВ (СЛЕВА: КАЛЕНДАРЬ + ИИ + КОД/ИГРЫ | СПРАВА: МУЗЫКА + ЗАМЕТКИ + РЕСУРСЫ)
        # ======================================================================
        mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        mid.set_vexpand(True); mid.set_hexpand(True)

        # -------------------- ЛЕВАЯ КОЛОНКА ВИДЖЕТОВ --------------------
        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left_col.set_size_request(310, -1); left_col.set_valign(Gtk.Align.FILL)

        # ВИДЖЕТ 1: КАЛЕНДАРЬ
        cal_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        cal_card.add_css_class("ide-panel")
        cal_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.cal_title_lbl = Gtk.Label(label="📅 КАЛЕНДАРЬ", xalign=0, hexpand=True, css_classes=["panel-header"])
        cal_hdr.append(self.cal_title_lbl)
        for sym_c, d_m in [("◀", -1), ("●", 0), ("▶", 1)]:
            cb = Gtk.Button(label=sym_c); cb.add_css_class("studio-btn")
            cb.connect("clicked", lambda _b, d=d_m: self.on_cal_shift(d))
            cal_hdr.append(cb)
        cal_card.append(cal_hdr)

        self.cal_grid = Gtk.Grid()
        self.cal_grid.set_column_spacing(6); self.cal_grid.set_row_spacing(3)
        self.cal_grid.set_halign(Gtk.Align.CENTER)
        cal_card.append(self.cal_grid)
        self.rebuild_calendar_grid()
        left_col.append(cal_card)

        # ВИДЖЕТ 2: НЕЙРОСЕТИ (AI & LLM STUDIO)
        ai_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ai_card.add_css_class("ide-panel")
        ai_card.append(Gtk.Label(label="🧠 НЕЙРОСЕТИ // AI STUDIO", xalign=0, css_classes=["panel-header"]))

        for row_items in [
            [("Gemini", "firefox https://gemini.google.com"), ("ChatGPT", "firefox https://chatgpt.com"), ("Claude", "firefox https://claude.ai")],
            [("DeepSeek", "firefox https://chat.deepseek.com"), ("HuggingFace", "firefox https://huggingface.co"), ("Local LLM", "foot -e sh -c 'ollama list 2>/dev/null || echo \"Ollama CLI\"; exec bash'")],
        ]:
            rbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            for albl, acmd in row_items:
                ab = Gtk.Button(label=albl); ab.add_css_class("ai-chip"); ab.set_hexpand(True)
                ab.connect("clicked", lambda _b, c=acmd: self.spawn_raw(c))
                rbox.append(ab)
            ai_card.append(rbox)

        ai_ent = Gtk.Entry(); ai_ent.add_css_class("search-entry")
        ai_ent.set_placeholder_text("Быстрый промпт (Enter -> буфер + ИИ)...")
        ai_ent.connect("activate", self.on_ai_quick_ask)
        ai_card.append(ai_ent)
        left_col.append(ai_card)

        # ВИДЖЕТ 3: РАЗРАБОТКА ИГР И КОД (GAMEDEV & CODE PIPELINE)
        dev_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        dev_card.add_css_class("ide-panel"); dev_card.set_vexpand(True)
        dev_card.append(Gtk.Label(label="🎮 GAMEDEV & CODE // ПРОЕКТЫ", xalign=0, css_classes=["panel-header"]))
        self.git_lbl = Gtk.Label(label=read_git_projects_status(), xalign=0, css_classes=["panel-sub"])
        dev_card.append(self.git_lbl)
        self.ports_lbl = Gtk.Label(label=f"Локальные порты: {scan_dev_ports()}", xalign=0, css_classes=["panel-muted"])
        dev_card.append(self.ports_lbl)

        for row_dev in [
            [("⌨ Код / IDE", "code || codium || zed || foot"), ("▶ Pygame Тест", "foot -e sh -c 'python3 -c \"import pygame; print(pygame.ver)\" 2>/dev/null; exec bash'"), ("🐍 Python", "foot -e python3")],
            [("🖼 Спрайты", "~/.local/bin/cyber-fm ~/Pictures"), ("🎨 Пипетка", "~/.local/bin/cyber-tool pick"), ("📷 Скриншот", "~/.local/bin/cyber-tool shot")],
        ]:
            dbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            for dlbl, dcmd in row_dev:
                db = Gtk.Button(label=dlbl); db.add_css_class("studio-btn"); db.set_hexpand(True)
                db.connect("clicked", lambda _b, c=dcmd: self.spawn_raw(c))
                dbox.append(db)
            dev_card.append(dbox)

        left_col.append(dev_card)
        mid.append(left_col)

        # Центральное открытое пространство рабочего стола
        sp = Gtk.Box(); sp.set_hexpand(True); mid.append(sp)

        # -------------------- ПРАВАЯ КОЛОНКА ВИДЖЕТОВ --------------------
        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_col.set_size_request(310, -1); right_col.set_valign(Gtk.Align.FILL)

        # ВИДЖЕТ 4: МУЗЫКАЛЬНЫЙ ПЛЕЕР (MEDIA STUDIO // MPRIS)
        mus_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mus_card.add_css_class("ide-panel")
        mus_card.append(Gtk.Label(label="🎵 МУЗЫКА // MEDIA PLAYER", xalign=0, css_classes=["panel-header"]))

        t_str, a_str, _ = read_music_status()
        self.track_lbl = Gtk.Label(label=t_str, xalign=0, css_classes=["track-title"])
        self.track_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.artist_lbl = Gtk.Label(label=a_str, xalign=0, css_classes=["track-artist"])
        self.artist_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        mus_card.append(self.track_lbl); mus_card.append(self.artist_lbl)

        m_ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        for mlbl, mcmd in [
            ("⏮ Пред", "playerctl previous"),
            ("⏯ Пуск/Пауза", "playerctl play-pause"),
            ("⏭ След", "playerctl next"),
            ("🎧 Звук", "~/.local/bin/cyber-audio-menu"),
        ]:
            mb = Gtk.Button(label=mlbl); mb.add_css_class("studio-btn"); mb.set_hexpand(True)
            mb.connect("clicked", lambda _b, c=mcmd: (self.spawn_raw(c), GLib.timeout_add(300, self.refresh_music)))
            m_ctrl.append(mb)
        mus_card.append(m_ctrl)
        right_col.append(mus_card)

        # ВИДЖЕТ 5: ЗАМЕТКИ (STUDIO NOTES // АВТОСОХРАНЕНИЕ)
        notes_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        notes_card.add_css_class("ide-panel"); notes_card.set_vexpand(True)
        notes_card.append(Gtk.Label(label="📝 ЗАМЕТКИ // БЛОКНОТ СТУДИИ", xalign=0, css_classes=["panel-header"]))

        n_sc = Gtk.ScrolledWindow(); n_sc.set_vexpand(True)
        ntv = Gtk.TextView(); ntv.add_css_class("prompt-view"); ntv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.notes_buf = ntv.get_buffer()
        if os.path.isfile(NOTES_FILE):
            try: self.notes_buf.set_text(open(NOTES_FILE, "r", encoding="utf-8").read())
            except Exception: pass
        else:
            self.notes_buf.set_text("[x] Настроить серое окружение студии\n[ ] Доработать механики в игре на Pygame\n[ ] Подготовить зачёты по программированию\n")
        self.notes_buf.connect("changed", lambda b: open(NOTES_FILE, "w", encoding="utf-8").write(b.get_text(b.get_start_iter(), b.get_end_iter(), False)))
        n_sc.set_child(ntv); notes_card.append(n_sc)

        n_act = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        b_todo = Gtk.Button(label="➕ Задача"); b_todo.add_css_class("studio-btn"); b_todo.set_hexpand(True); b_todo.connect("clicked", self.on_add_todo_item)
        b_ncp  = Gtk.Button(label="📋 Копировать"); b_ncp.add_css_class("studio-btn"); b_ncp.set_hexpand(True); b_ncp.connect("clicked", self.on_copy_notes)
        b_ncl  = Gtk.Button(label="🗑"); b_ncl.add_css_class("studio-btn"); b_ncl.connect("clicked", lambda _b: self.notes_buf.set_text(""))
        n_act.append(b_todo); n_act.append(b_ncp); n_act.append(b_ncl)
        notes_card.append(n_act)
        right_col.append(notes_card)

        # ВИДЖЕТ 6: СИСТЕМНЫЙ ИНСПЕКТОР РЕСУРСОВ
        insp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        insp.add_css_class("ide-panel")
        insp.append(Gtk.Label(label="🔍 МОНИТОР РЕСУРСОВ // TELEMETRY", xalign=0, css_classes=["panel-header"]))
        self.cpu_lbl = Gtk.Label(label="CPU: 0%", xalign=0, css_classes=["panel-sub"]); self.cpu_bar = Gtk.ProgressBar()
        self.ram_lbl = Gtk.Label(label="RAM: --", xalign=0, css_classes=["panel-sub"]); self.ram_bar = Gtk.ProgressBar(); self.ram_bar.add_css_class("gauge-cyan")
        self.bat_lbl = Gtk.Label(label="PWR: --", xalign=0, css_classes=["panel-sub"]); self.bat_bar = Gtk.ProgressBar(); self.bat_bar.add_css_class("bat-good")
        for w in (self.cpu_lbl, self.cpu_bar, self.ram_lbl, self.ram_bar, self.bat_lbl, self.bat_bar): insp.append(w)
        b_purge = Gtk.Button(label="⚡ Сбросить кэш ОЗУ (Drop Caches)"); b_purge.add_css_class("studio-btn")
        b_purge.connect("clicked", lambda _b: self.spawn_raw("sudo -n /usr/local/bin/cyber-power-hw purge-ram && notify-send -a cyber-kb '▣ STUDIO' 'Кэш ОЗУ освобождён'"))
        insp.append(b_purge)
        right_col.append(insp)

        mid.append(right_col)
        root_box.append(mid)

        # ======================================================================
        # 3. НИЖНИЙ ДОК (ТОЛЬКО ЗАКРЕПЛЁННЫЕ ПРОГРАММЫ С НОВЫМИ СЕРЫМИ ИКОНКАМИ)
        # ======================================================================
        dock = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dock.add_css_class("bottom-dock"); dock.set_halign(Gtk.Align.CENTER); dock.set_vexpand(False)
        self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dock.append(self.dock_box)
        root_box.append(dock)

        overlay.add_overlay(root_box); win.set_child(overlay)
        self.populate_dock(); self.refresh_workspaces(); self.refresh_status()
        GLib.timeout_add(1200, self.refresh_workspaces)
        GLib.timeout_add(1500, self.refresh_music)
        GLib.timeout_add_seconds(3, self.refresh_status)
        win.present()

    def refresh_music(self):
        t_str, a_str, _ = read_music_status()
        if self.track_lbl.get_label() != t_str: self.track_lbl.set_label(t_str)
        if self.artist_lbl.get_label() != a_str: self.artist_lbl.set_label(a_str)
        return True

    def populate_dock(self):
        items = discover_work_apps()
        self.last_pin_mtime = os.path.getmtime(PIN_FILE) if os.path.isfile(PIN_FILE) else 0
        while True:
            c = self.dock_box.get_first_child()
            if c is None: break
            self.dock_box.remove(c)
        favs = [it for it in items if it[0] in self.pinned]
        if not favs:
            empty_b = Gtk.Button(label="📌 Нажмите «📌 Док» сверху, чтобы закрепить программы")
            empty_b.add_css_class("dock-item")
            empty_b.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-pin-menu"))
            self.dock_box.append(empty_b)
        else:
            for name, cmd, icon_spec in favs:
                db = Gtk.Button(); db.add_css_class("dock-item")
                db.set_tooltip_text(f"{name} (ЛКМ: запустить • ПКМ: открепить)")
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                hb.append(make_cyber_icon_widget(icon_spec, "default", 20))
                hb.append(Gtk.Label(label=name[:18]))
                db.set_child(hb)
                db.connect("clicked", lambda _b, c=cmd: self.spawn_raw(c))
                rc = Gtk.GestureClick.new(); rc.set_button(3)
                rc.connect("pressed", lambda _g, _n, _x, _y, nm=name: self.toggle_pin(nm))
                db.add_controller(rc)
                self.dock_box.append(db)

    def toggle_pin(self, name):
        if name in self.pinned: self.pinned.remove(name)
        else: self.pinned.add(name)
        save_pinned(self.pinned); self.populate_dock()

    def refresh_workspaces(self):
        try:
            mt = os.path.getmtime(PIN_FILE) if os.path.isfile(PIN_FILE) else 0
            if mt != getattr(self, "last_pin_mtime", 0):
                self.pinned = load_pinned()
                self.populate_dock()
        except Exception: pass
        try:
            if os.path.isfile(KB_FILE):
                kb_code = open(KB_FILE).read().strip() or "EN"
                pass
        except Exception: pass
        try:
            bg_list = cyber_bg.get_bg_and_open_items()
            cnt = sum(i.get("count", 1) for i in bg_list)
            lbl_bg = f"📦 Фон [{cnt}]"
            pass
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
        pass

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
        self.bri_pct_lbl.set_label(f"{val}%")
        self.set_hw_bri(val)

    def on_bri_icon_clicked(self, _b):
        cur = int(self.bri_scale.get_value()); self.bri_scale.set_value(100 if cur < 95 else 60)

    def get_current_vol(self):
        try: return float(subprocess.check_output(["pamixer", "--get-volume"], text=True, stderr=subprocess.DEVNULL).strip())
        except Exception: return 50.0

    def on_vol_changed(self, scale):
        val = int(scale.get_value())
        self.vol_pct_lbl.set_label(f"{val}%")
        subprocess.Popen(["pamixer", "--set-volume", str(val)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def refresh_status(self):
        pass
        idle, total = read_cpu_stat()
        dt, di = total - self.prev_total, idle - self.prev_idle
        self.prev_idle, self.prev_total = idle, total
        cpu_pct = int(round(100.0 * (dt - di) / dt)) if dt > 0 else 0
        self.cpu_lbl.set_label(f"CPU: {cpu_pct}%")
        self.cpu_bar.set_fraction(min(1.0, max(0.0, cpu_pct / 100.0)))

        ram_txt, ram_frac = read_ram_info()
        self.ram_lbl.set_label(f"RAM: {ram_txt}")
        self.ram_bar.set_fraction(ram_frac)

        binfo = read_battery()
        pct = int(binfo.get("pct", 100))
        self.bat_lbl.set_label("AC: 100%" if not binfo.get("present") else f"BAT: {pct}%")
        self.bat_bar.set_fraction(min(1.0, max(0.0, pct / 100.0)))

        self.ports_lbl.set_label(f"Локальные порты: {scan_dev_ports()}")
        self.git_lbl.set_label(read_git_projects_status())
        pass
        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    GameDevStudioHub().run(None)
