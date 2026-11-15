#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
except Exception:
    pass

import os, sys, re, glob, json, socket, urllib.request, urllib.parse, calendar, threading, subprocess, datetime

HOME = os.path.expanduser("~")
UID = os.getuid()
CFG_DIR = os.path.join(HOME, ".config/cyberdeck")
NOTES_FILE = os.path.join(CFG_DIR, "studio_notes.txt")
PIN_FILE   = os.path.join(CFG_DIR, "pinned_work_apps.json")
STATE_FILE = os.path.join(CFG_DIR, "widgets_state.json")
CHAT_FILE  = os.path.join(CFG_DIR, "ai_chat_history.json")

os.environ["XCURSOR_THEME"] = "GameDev-Cursor-Grey"
os.environ["XCURSOR_SIZE"] = "28"

ORIG_GTK_THEME = os.environ.get("GTK_THEME")
os.environ["GTK_THEME"] = "Adwaita:dark"

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Pango, Gtk4LayerShell

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

RU_MONTHS = ["", "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]

DEFAULT_WIDGETS = {
    "ai":       {"title": "▣ AI CHAT",       "x": 18,   "y": 46,  "w": 325, "h": 285, "min_w": 240, "min_h": 175, "top": False, "collapsed": False},
    "notes":    {"title": "▣ ЗАМЕТКИ",       "x": 18,   "y": 342, "w": 285, "h": 185, "min_w": 210, "min_h": 120, "top": False, "collapsed": False},
    "gamedev":  {"title": "▣ DEV & GIT",     "x": 18,   "y": 538, "w": 285, "h": 145, "min_w": 210, "min_h": 115, "top": False, "collapsed": False},
    "calendar": {"title": "▣ КАЛЕНДАРЬ",     "x": 1632, "y": 46,  "w": 270, "h": 180, "min_w": 220, "min_h": 155, "top": False, "collapsed": False},
    "media":    {"title": "▣ МУЗЫКА И ЗВУК", "x": 1632, "y": 238, "w": 270, "h": 165, "min_w": 220, "min_h": 145, "top": False, "collapsed": False},
}

def get_hypr_sock():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    xdg = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{UID}")
    for p in (os.path.join(xdg, "hypr", sig, ".socket.sock"), f"/tmp/hypr/{sig}/.socket.sock"):
        if os.path.exists(p): return p
    return None

HYPR_SOCK = get_hypr_sock()

def get_cursor_screen_pos():
    if HYPR_SOCK:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(0.05)
                s.connect(HYPR_SOCK)
                s.sendall(b"cursorpos")
                raw = s.recv(64).decode("utf-8", errors="ignore").strip()
                parts = raw.split(",")
                if len(parts) == 2:
                    return int(parts[0].strip()), int(parts[1].strip())
        except Exception:
            pass
    return None

def load_widgets_state():
    st = json.loads(json.dumps(DEFAULT_WIDGETS))
    try:
        if os.path.isfile(STATE_FILE):
            saved = json.load(open(STATE_FILE, encoding="utf-8"))
            for k, v in saved.items():
                if k in st and isinstance(v, dict):
                    st[k].update(v)
                    st[k]["title"] = DEFAULT_WIDGETS[k]["title"]
    except Exception:
        pass
    return st

def save_widgets_state(st):
    os.makedirs(CFG_DIR, exist_ok=True)
    json.dump(st, open(STATE_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def resolve_cyber_svg(spec, fallback_glyph="default"):
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

def make_cyber_icon_widget(icon_spec, size=18):
    svg_path = resolve_cyber_svg(icon_spec)
    img = Gtk.Image.new_from_file(svg_path) if svg_path else Gtk.Image.new_from_icon_name("application-x-executable")
    img.set_pixel_size(size)
    return img

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
    return " ".join(ports[:4]) if ports else "нет"

def read_git_projects_status():
    rows = []
    candidates = [os.path.join(HOME, "CyberDeck")]
    for d in sorted(glob.glob(os.path.join(HOME, "*"))):
        if os.path.isdir(os.path.join(d, ".git")) and d not in candidates:
            candidates.append(d)
    for repo in candidates[:2]:
        if not os.path.isdir(os.path.join(repo, ".git")): continue
        name = os.path.basename(repo)
        try:
            br = subprocess.check_output(["git", "-C", repo, "symbolic-ref", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
            chg = len(subprocess.check_output(["git", "-C", repo, "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL).splitlines())
            st = f"изм:{chg}" if chg > 0 else "ок"
            rows.append(f"▸ {name[:12]:<12} [{br}] • {st}")
        except Exception: pass
    return "\n".join(rows) if rows else "▸ Git-репозитории готовы"

def read_music_status():
    try:
        status = subprocess.check_output(["playerctl", "status"], text=True, stderr=subprocess.DEVNULL, timeout=0.5).strip()
        title  = subprocess.check_output(["playerctl", "metadata", "xesam:title"], text=True, stderr=subprocess.DEVNULL, timeout=0.5).strip()
        artist = subprocess.check_output(["playerctl", "metadata", "xesam:artist"], text=True, stderr=subprocess.DEVNULL, timeout=0.5).strip()
        if title:
            ic = "󰐊" if status == "Playing" else "󰏤"
            return f"{ic} {title[:24]}", f"{artist[:24] or 'Медиаплеер'}"
    except Exception:
        pass
    return "󰓛 Нет активного трека", "Ожидание воспроизведения"

def get_current_bri():
    try:
        for bdir in sorted(glob.glob("/sys/class/backlight/*")):
            cur = float(open(os.path.join(bdir, "brightness")).read().strip())
            mx = float(open(os.path.join(bdir, "max_brightness")).read().strip())
            if mx > 0: return max(5.0, min(100.0, round(cur * 100.0 / mx)))
    except Exception: pass
    return 90.0

def set_hw_bri(val):
    val = max(5, min(100, int(val)))
    for bdir in sorted(glob.glob("/sys/class/backlight/*")):
        try:
            mx = int(open(os.path.join(bdir, "max_brightness")).read().strip())
            open(os.path.join(bdir, "brightness"), "w").write(str(max(1, int(round(mx * val / 100.0)))))
            return
        except Exception: pass
    subprocess.Popen(["brightnessctl", "-q", "set", f"{val}%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_current_vol():
    try: return float(subprocess.check_output(["pamixer", "--get-volume"], text=True, stderr=subprocess.DEVNULL).strip())
    except Exception: return 50.0

def query_ai_llm(model_key, messages):
    if model_key == "ollama":
        try:
            models_out = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1.5).read().decode())
            m_list = [m["name"] for m in models_out.get("models", [])]
            target_m = m_list[0] if m_list else "llama3"
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/chat",
                data=json.dumps({"model": target_m, "messages": messages, "stream": False}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8"))
            return resp.get("message", {}).get("content", "").strip()
        except Exception:
            return "Локальный сервер Ollama не запущен (выполните `ollama serve` или выберите вкладку Coder / GPT-4o / DeepSeek)."

    model_map = {"coder": "qwen-coder", "gpt": "openai", "deepseek": "deepseek"}
    api_model = model_map.get(model_key, "openai")

    try:
        payload = {
            "model": api_model,
            "messages": [{"role": "system", "content": "Отвечай кратко, чётко и по делу на русском языке. Если нужен код — пиши чистый рабочий код."}] + messages[-6:],
        }
        req = urllib.request.Request(
            "https://text.pollinations.ai/openai",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "StudioWidget/1.0"},
        )
        raw = urllib.request.urlopen(req, timeout=35).read().decode("utf-8", errors="ignore")
        data = json.loads(raw)
        ans = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if ans:
            return ans
    except Exception:
        pass

    try:
        last_q = messages[-1]["content"]
        url = f"https://text.pollinations.ai/{urllib.parse.quote(last_q)}?model={api_model}"
        req = urllib.request.Request(url, headers={"User-Agent": "StudioWidget/1.0"})
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return f"Ошибка соединения с нейросетью: {e}"

# ==============================================================================
# КОМПАКТНЫЙ ВИДЖЕТ НА РАБОЧЕМ СТОЛЕ (ВСЕГДА ВИДЕН, ПЕРЕМЕЩАЕМЫЙ, ПОВЕРХ ОКОН)
# ==============================================================================
class MovableStudioWidget:
    def __init__(self, app, wid, state_dict, build_body_fn):
        self.app = app
        self.wid = wid
        self.st = state_dict
        self.m_start_xy = (0, 0)
        self.m_start_cursor = None
        self.r_start_wh = (280, 180)
        self.r_start_cursor = None

        self.win = Gtk.Window(application=app, title=f"StudioWidget-{wid}")
        Gtk4LayerShell.init_for_window(self.win)
        Gtk4LayerShell.set_namespace(self.win, f"studio-widget-{wid}")
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.RIGHT, False)
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.BOTTOM, False)
        Gtk4LayerShell.set_exclusive_zone(self.win, -1)
        Gtk4LayerShell.set_keyboard_mode(self.win, Gtk4LayerShell.KeyboardMode.ON_DEMAND)

        self.frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.frame.add_css_class("widget-frame")

        # Шапка виджета: перетаскивание ⠿ + кнопка «Поверх окон» [󰐃] + кнопка свернуть [—]
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hdr.add_css_class("widget-header")

        drag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        drag_box.set_hexpand(True)
        drag_lbl = Gtk.Label(label=f"⠿ {self.st[wid].get('title', wid.upper())}", xalign=0, hexpand=True)
        drag_lbl.add_css_class("widget-title")
        drag_box.append(drag_lbl)
        drag_box.set_tooltip_text("Зажмите ЛКМ и перетащите в любое место рабочего стола")
        hdr.append(drag_box)

        move_gest = Gtk.GestureDrag.new()
        move_gest.set_button(1)
        move_gest.connect("drag-begin", self.on_move_begin)
        move_gest.connect("drag-update", self.on_move_update)
        move_gest.connect("drag-end", self.on_move_end)
        drag_box.add_controller(move_gest)

        # Кнопка закрепления виджета ПОВЕРХ ВСЕХ ПРИЛОЖЕНИЙ (Always on Top)
        self.pin_btn = Gtk.Button(label="󰐃")
        self.pin_btn.set_tooltip_text("Закрепить виджет ПОВЕРХ открытых приложений / вернуть на стол")
        self.pin_btn.connect("clicked", self.on_toggle_top)
        hdr.append(self.pin_btn)

        # Кнопка компактного сворачивания в полоску
        col_btn = Gtk.Button(label="—")
        col_btn.add_css_class("w-hdr-btn")
        col_btn.set_tooltip_text("Свернуть / развернуть содержимое виджета")
        col_btn.connect("clicked", self.on_toggle_collapse)
        hdr.append(col_btn)

        self.frame.append(hdr)

        # Тело виджета + уголок изменения размера ◢
        self.body_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.body_wrap.add_css_class("widget-body")
        self.body_wrap.set_vexpand(True); self.body_wrap.set_hexpand(True)

        content_w = build_body_fn()
        content_w.set_vexpand(True); content_w.set_hexpand(True)
        self.body_wrap.append(content_w)

        btm_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        sp = Gtk.Box(); sp.set_hexpand(True); btm_row.append(sp)
        grip_box = Gtk.Box()
        grip = Gtk.Label(label="◢")
        grip.add_css_class("resize-grip")
        grip_box.append(grip)
        grip_box.set_tooltip_text("Потяните ЛКМ за уголок, чтобы изменить размер виджета")

        rsz_gest = Gtk.GestureDrag.new()
        rsz_gest.set_button(1)
        rsz_gest.connect("drag-begin", self.on_resize_begin)
        rsz_gest.connect("drag-update", self.on_resize_update)
        rsz_gest.connect("drag-end", self.on_resize_end)
        grip_box.add_controller(rsz_gest)
        btm_row.append(grip_box)
        self.body_wrap.append(btm_row)

        self.frame.append(self.body_wrap)
        self.win.set_child(self.frame)
        self.apply_geometry_and_layer()

    def apply_geometry_and_layer(self):
        cfg = self.st[self.wid]
        x = max(4, min(1840, int(cfg.get("x", 20))))
        y = max(38, min(1030, int(cfg.get("y", 50))))
        w = max(int(cfg.get("min_w", 210)), int(cfg.get("w", 280)))
        h = max(int(cfg.get("min_h", 105)), int(cfg.get("h", 180)))
        is_top = bool(cfg.get("top", False))
        is_col = bool(cfg.get("collapsed", False))

        Gtk4LayerShell.set_margin(self.win, Gtk4LayerShell.Edge.LEFT, x)
        Gtk4LayerShell.set_margin(self.win, Gtk4LayerShell.Edge.TOP, y)
        Gtk4LayerShell.set_layer(self.win, Gtk4LayerShell.Layer.TOP if is_top else Gtk4LayerShell.Layer.BOTTOM)

        self.pin_btn.remove_css_class("w-pin-active")
        self.pin_btn.remove_css_class("w-hdr-btn")
        self.pin_btn.add_css_class("w-pin-active" if is_top else "w-hdr-btn")

        self.frame.remove_css_class("widget-frame")
        self.frame.remove_css_class("widget-frame-top")
        self.frame.add_css_class("widget-frame-top" if is_top else "widget-frame")

        self.body_wrap.set_visible(not is_col)
        if is_col:
            self.frame.set_size_request(w, 26)
            self.win.set_default_size(w, 26)
        else:
            self.frame.set_size_request(w, h)
            self.win.set_default_size(w, h)

    def on_move_begin(self, _g, _x, _y):
        cfg = self.st[self.wid]
        self.m_start_xy = (int(cfg.get("x", 20)), int(cfg.get("y", 50)))
        self.m_start_cursor = get_cursor_screen_pos()

    def on_move_update(self, _g, off_x, off_y):
        cfg = self.st[self.wid]
        cur = get_cursor_screen_pos()
        if cur and self.m_start_cursor:
            nx = self.m_start_xy[0] + (cur[0] - self.m_start_cursor[0])
            ny = self.m_start_xy[1] + (cur[1] - self.m_start_cursor[1])
        else:
            nx = self.m_start_xy[0] + int(off_x)
            ny = self.m_start_xy[1] + int(off_y)
        cfg["x"] = max(4, min(1920 - int(cfg["w"]) - 4, nx))
        cfg["y"] = max(38, min(1080 - 36, ny))
        Gtk4LayerShell.set_margin(self.win, Gtk4LayerShell.Edge.LEFT, cfg["x"])
        Gtk4LayerShell.set_margin(self.win, Gtk4LayerShell.Edge.TOP, cfg["y"])

    def on_move_end(self, _g, _ox, _oy):
        save_widgets_state(self.st)

    def on_resize_begin(self, _g, _x, _y):
        cfg = self.st[self.wid]
        self.r_start_wh = (int(cfg.get("w", 280)), int(cfg.get("h", 180)))
        self.r_start_cursor = get_cursor_screen_pos()

    def on_resize_update(self, _g, off_x, off_y):
        cfg = self.st[self.wid]
        cur = get_cursor_screen_pos()
        if cur and self.r_start_cursor:
            nw = self.r_start_wh[0] + (cur[0] - self.r_start_cursor[0])
            nh = self.r_start_wh[1] + (cur[1] - self.r_start_cursor[1])
        else:
            nw = self.r_start_wh[0] + int(off_x)
            nh = self.r_start_wh[1] + int(off_y)
        cfg["w"] = max(int(cfg.get("min_w", 210)), min(900, nw))
        cfg["h"] = max(int(cfg.get("min_h", 105)), min(850, nh))
        self.frame.set_size_request(cfg["w"], cfg["h"])
        self.win.set_default_size(cfg["w"], cfg["h"])

    def on_resize_end(self, _g, _ox, _oy):
        save_widgets_state(self.st)

    def on_toggle_top(self, _b):
        cfg = self.st[self.wid]
        cfg["top"] = not bool(cfg.get("top", False))
        self.apply_geometry_and_layer()
        save_widgets_state(self.st)

    def on_toggle_collapse(self, _b):
        cfg = self.st[self.wid]
        cfg["collapsed"] = not bool(cfg.get("collapsed", False))
        self.apply_geometry_and_layer()
        save_widgets_state(self.st)

# ==============================================================================
# МЕНЕДЖЕР ПОСТОЯННЫХ ВИДЖЕТОВ И ДОКА НА РАБОЧЕМ СТОЛЕ
# ==============================================================================
class StudioWidgetsDaemon(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.alpora.WorkDeckLayer")
        self.st = load_widgets_state()
        self.widgets = {}
        self.pinned = self.load_pinned()
        self.last_pin_mtime = 0

        self.ai_model = "coder"
        self.model_btns = {}
        self.chat_history = self.load_chat_history()
        self.ai_busy = False

        now = datetime.date.today()
        self.cal_year, self.cal_month = now.year, now.month

    def load_pinned(self):
        try: return set(json.load(open(PIN_FILE, encoding="utf-8"))) if os.path.isfile(PIN_FILE) else set()
        except Exception: return set()

    def save_pinned(self):
        os.makedirs(os.path.dirname(PIN_FILE), exist_ok=True)
        json.dump(sorted(self.pinned), open(PIN_FILE, "w", encoding="utf-8"), ensure_ascii=False)

    def load_chat_history(self):
        try:
            if os.path.isfile(CHAT_FILE):
                return json.load(open(CHAT_FILE, encoding="utf-8"))[-12:]
        except Exception:
            pass
        return [{"role": "assistant", "content": "Готов к работе! Выберите модель сверху и напишите вопрос или задачу по коду прямо здесь."}]

    def save_chat_history(self):
        try:
            json.dump(self.chat_history[-12:], open(CHAT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        except Exception:
            pass

    # --- 1. ВИДЖЕТ НЕЙРОСЕТЕЙ (ПРЯМОЕ ОБЩЕНИЕ ВНУТРИ ВИДЖЕТА) ---
    def build_ai_widget(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        m_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for m_id, m_lbl in [("coder", "Coder"), ("gpt", "GPT-4o"), ("deepseek", "DeepSeek"), ("ollama", "Ollama")]:
            mb = Gtk.Button(label=m_lbl)
            mb.add_css_class("model-pill-active" if m_id == self.ai_model else "model-pill")
            mb.set_hexpand(True)
            mb.connect("clicked", self.on_select_ai_model, m_id)
            self.model_btns[m_id] = mb
            m_row.append(mb)
        box.append(m_row)

        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.set_hexpand(True)
        self.chat_tv = Gtk.TextView()
        self.chat_tv.set_editable(False); self.chat_tv.set_cursor_visible(False)
        self.chat_tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.chat_tv.add_css_class("chat-view")
        self.chat_buf = self.chat_tv.get_buffer()
        sc.set_child(self.chat_tv)
        box.append(sc)
        self.render_chat_log()

        in_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.ai_entry = Gtk.Entry()
        self.ai_entry.add_css_class("compact-entry"); self.ai_entry.set_hexpand(True)
        self.ai_entry.set_placeholder_text("Сообщение нейросети (Enter)...")
        self.ai_entry.connect("activate", self.on_send_ai_msg)
        in_row.append(self.ai_entry)

        b_send = Gtk.Button(label="➤"); b_send.add_css_class("mini-btn")
        b_send.connect("clicked", self.on_send_ai_msg)
        in_row.append(b_send)

        b_copy = Gtk.Button(label="󰆏"); b_copy.add_css_class("mini-btn")
        b_copy.set_tooltip_text("Скопировать ответ нейросети")
        b_copy.connect("clicked", self.on_copy_last_ai)
        in_row.append(b_copy)

        b_clr = Gtk.Button(label="󰩺"); b_clr.add_css_class("mini-btn")
        b_clr.set_tooltip_text("Очистить чат")
        b_clr.connect("clicked", self.on_clear_ai_chat)
        in_row.append(b_clr)

        box.append(in_row)
        return box

    def on_select_ai_model(self, _b, m_id):
        self.ai_model = m_id
        for k, btn in self.model_btns.items():
            btn.remove_css_class("model-pill-active")
            btn.remove_css_class("model-pill")
            btn.add_css_class("model-pill-active" if k == m_id else "model-pill")

    def render_chat_log(self, thinking=False):
        lines = []
        for msg in self.chat_history[-10:]:
            prefix = "▸ ВЫ:" if msg["role"] == "user" else f"▣ AI [{self.ai_model.upper()}]:"
            lines.append(f"{prefix}\n{msg['content']}")
        if thinking:
            lines.append(f"▣ AI [{self.ai_model.upper()}]:\n▪ генерация ответа...")
        self.chat_buf.set_text("\n\n".join(lines))
        GLib.idle_add(self.scroll_chat_bottom)

    def scroll_chat_bottom(self):
        end_it = self.chat_buf.get_end_iter()
        mark = self.chat_buf.create_mark(None, end_it, False)
        self.chat_tv.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        return False

    def on_send_ai_msg(self, *_args):
        if self.ai_busy: return
        q = self.ai_entry.get_text().strip()
        if not q: return
        self.ai_entry.set_text("")
        self.chat_history.append({"role": "user", "content": q})
        self.ai_busy = True
        self.render_chat_log(thinking=True)

        model_now = self.ai_model
        msgs_snapshot = list(self.chat_history)

        def worker():
            ans = query_ai_llm(model_now, msgs_snapshot)
            GLib.idle_add(self.on_ai_response_ready, ans)

        threading.Thread(target=worker, daemon=True).start()

    def on_ai_response_ready(self, ans):
        self.ai_busy = False
        self.chat_history.append({"role": "assistant", "content": ans})
        self.save_chat_history()
        self.render_chat_log(thinking=False)
        return False

    def on_copy_last_ai(self, _b):
        for msg in reversed(self.chat_history):
            if msg["role"] == "assistant":
                subprocess.run(["wl-copy"], input=msg["content"], text=True, stderr=subprocess.DEVNULL)
                self.spawn_raw("notify-send -a cyber-kb '▣ AI CHAT' 'Ответ скопирован в буфер обмена'")
                break

    def on_clear_ai_chat(self, _b):
        self.chat_history = [{"role": "assistant", "content": "Диалог очищен. Напишите новый вопрос."}]
        self.save_chat_history()
        self.render_chat_log()

    # --- 2. ВИДЖЕТ ЗАМЕТОК ---
    def build_notes_widget(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.set_hexpand(True)
        tv = Gtk.TextView(); tv.add_css_class("notes-view"); tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.notes_buf = tv.get_buffer()
        if os.path.isfile(NOTES_FILE):
            try: self.notes_buf.set_text(open(NOTES_FILE, "r", encoding="utf-8").read())
            except Exception: pass
        else:
            self.notes_buf.set_text("[x] Единое серое окружение\n[ ] Доработать физику в игре\n[ ] Подготовить зачёты\n")
        self.notes_buf.connect("changed", lambda b: open(NOTES_FILE, "w", encoding="utf-8").write(b.get_text(b.get_start_iter(), b.get_end_iter(), False)))
        sc.set_child(tv); box.append(sc)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        b_add = Gtk.Button(label="+ Задача"); b_add.add_css_class("mini-btn"); b_add.set_hexpand(True)
        b_add.connect("clicked", lambda _b: self.notes_buf.insert(self.notes_buf.get_end_iter(), "\n[ ] "))
        b_cp = Gtk.Button(label="󰆏 Копировать"); b_cp.add_css_class("mini-btn"); b_cp.set_hexpand(True)
        b_cp.connect("clicked", lambda _b: subprocess.run(["wl-copy"], input=self.notes_buf.get_text(self.notes_buf.get_start_iter(), self.notes_buf.get_end_iter(), False), text=True))
        row.append(b_add); row.append(b_cp)
        box.append(row)
        return box

    # --- 3. ВИДЖЕТ КАЛЕНДАРЯ ---
    def build_calendar_widget(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.cal_title_lbl = Gtk.Label(label="", xalign=0, hexpand=True, css_classes=["widget-title"])
        nav.append(self.cal_title_lbl)
        for sym, d in [("◀", -1), ("●", 0), ("▶", 1)]:
            b = Gtk.Button(label=sym); b.add_css_class("mini-btn")
            b.connect("clicked", lambda _b, delta=d: self.shift_cal(delta))
            nav.append(b)
        box.append(nav)

        self.cal_grid = Gtk.Grid()
        self.cal_grid.set_column_spacing(4); self.cal_grid.set_row_spacing(2)
        self.cal_grid.set_halign(Gtk.Align.CENTER); self.cal_grid.set_vexpand(True)
        box.append(self.cal_grid)
        self.refresh_cal()
        return box

    def shift_cal(self, delta):
        if delta == 0:
            t = datetime.date.today()
            self.cal_year, self.cal_month = t.year, t.month
        else:
            m = self.cal_month + delta
            if m < 1: self.cal_month = 12; self.cal_year -= 1
            elif m > 12: self.cal_month = 1; self.cal_year += 1
            else: self.cal_month = m
        self.refresh_cal()

    def refresh_cal(self):
        self.cal_title_lbl.set_label(f"{RU_MONTHS[self.cal_month]} {self.cal_year}")
        while True:
            c = self.cal_grid.get_first_child()
            if c is None: break
            self.cal_grid.remove(c)
        for i, d in enumerate(("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")):
            self.cal_grid.attach(Gtk.Label(label=d, css_classes=["cal-dow"]), i, 0, 1, 1)
        today = datetime.date.today()
        for r_i, week in enumerate(calendar.Calendar(0).monthdayscalendar(self.cal_year, self.cal_month), 1):
            for c_i, day in enumerate(week):
                lbl = Gtk.Label(label=" " if day == 0 else f"{day:2d}")
                is_t = (day == today.day and self.cal_month == today.month and self.cal_year == today.year)
                lbl.add_css_class("cal-today" if is_t else "cal-day")
                self.cal_grid.attach(lbl, c_i, r_i, 1, 1)

    # --- 4. ВИДЖЕТ МУЗЫКИ + ПОЛЗУНКИ ЗВУКА И ЯРКОСТИ ---
    def build_media_widget(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        t_s, a_s = read_music_status()
        self.track_lbl = Gtk.Label(label=t_s, xalign=0, css_classes=["track-title"])
        self.track_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.artist_lbl = Gtk.Label(label=a_s, xalign=0, css_classes=["track-artist"])
        self.artist_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        box.append(self.track_lbl); box.append(self.artist_lbl)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for lbl, cmd in [("󰒮", "playerctl previous"), ("󰐎 Пуск/Пауза", "playerctl play-pause"), ("󰒭", "playerctl next"), ("󰕾", "~/.local/bin/cyber-audio-menu")]:
            b = Gtk.Button(label=lbl); b.add_css_class("mini-btn"); b.set_hexpand(True)
            b.connect("clicked", lambda _b, c=cmd: self.spawn_raw(c))
            row.append(b)
        box.append(row)

        # Ползунок звука
        v_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        v_row.append(Gtk.Label(label="󰕾 Звук", css_classes=["mono-sub"]))
        cur_v = get_current_vol()
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_draw_value(False); self.vol_scale.set_hexpand(True); self.vol_scale.set_value(cur_v)
        self.vol_lbl = Gtk.Label(label=f"{int(cur_v)}%", css_classes=["mono-sub"])
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        v_row.append(self.vol_scale); v_row.append(self.vol_lbl)
        box.append(v_row)

        # Ползунок яркости экрана
        b_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        b_row.append(Gtk.Label(label="󰃠 Экран", css_classes=["mono-sub"]))
        cur_b = get_current_bri()
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.bri_scale.set_draw_value(False); self.bri_scale.set_hexpand(True); self.bri_scale.set_value(cur_b)
        self.bri_lbl = Gtk.Label(label=f"{int(cur_b)}%", css_classes=["mono-sub"])
        self.bri_scale.connect("value-changed", self.on_bri_changed)
        b_row.append(self.bri_scale); b_row.append(self.bri_lbl)
        box.append(b_row)

        return box

    def on_vol_changed(self, scale):
        val = int(scale.get_value())
        self.vol_lbl.set_label(f"{val}%")
        subprocess.Popen(["pamixer", "--set-volume", str(val)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def on_bri_changed(self, scale):
        val = int(scale.get_value())
        self.bri_lbl.set_label(f"{val}%")
        set_hw_bri(val)

    # --- 5. ВИДЖЕТ РАЗРАБОТКИ ИГР И КОДА ---
    def build_gamedev_widget(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.git_lbl = Gtk.Label(label=read_git_projects_status(), xalign=0, css_classes=["mono-sub"])
        self.ports_lbl = Gtk.Label(label=f"Порты: {scan_dev_ports()}", xalign=0, css_classes=["mono-sub"])
        box.append(self.git_lbl); box.append(self.ports_lbl)

        for row_btns in [
            [("⌨ IDE", "code || codium || zed || foot"), ("🐍 Pygame", "foot -e python3"), ("📁 Проекты", "~/.local/bin/cyber-fm ~")],
            [("🎨 Пипетка", "~/.local/bin/cyber-tool pick"), ("📷 Скрин", "~/.local/bin/cyber-tool shot"), ("⚡ ОЗУ", "sudo -n /usr/local/bin/cyber-power-hw purge-ram")],
        ]:
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            for l, c in row_btns:
                b = Gtk.Button(label=l); b.add_css_class("mini-btn"); b.set_hexpand(True)
                b.connect("clicked", lambda _b, cmd=c: self.spawn_raw(cmd))
                r.append(b)
            box.append(r)
        return box

    def build_bottom_dock(self):
        self.dock_win = Gtk.Window(application=self, title="StudioBottomDock")
        Gtk4LayerShell.init_for_window(self.dock_win)
        Gtk4LayerShell.set_namespace(self.dock_win, "studio-bottom-dock")
        Gtk4LayerShell.set_layer(self.dock_win, Gtk4LayerShell.Layer.BOTTOM)
        Gtk4LayerShell.set_anchor(self.dock_win, Gtk4LayerShell.Edge.BOTTOM, True)
        Gtk4LayerShell.set_margin(self.dock_win, Gtk4LayerShell.Edge.BOTTOM, 10)
        Gtk4LayerShell.set_exclusive_zone(self.dock_win, -1)

        wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        wrap.add_css_class("bottom-dock")
        self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        wrap.append(self.dock_box)

        # Компактная кнопка + в самом доке для добавления/удаления закреплённых программ
        add_b = Gtk.Button(label="+")
        add_b.add_css_class("dock-item")
        add_b.set_tooltip_text("Настроить закреплённые программы в доке")
        add_b.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-pin-menu"))
        wrap.append(add_b)

        self.dock_win.set_child(wrap)
        self.populate_dock()
        self.dock_win.present()

    def populate_dock(self):
        items = []
        seen = set()
        for ad in (os.path.join(HOME, ".local/share/applications"), "/usr/share/applications"):
            if not os.path.isdir(ad): continue
            for df in sorted(glob.glob(os.path.join(ad, "*.desktop"))):
                try:
                    txt = open(df, errors="ignore").read()
                    if re.search(r"^NoDisplay=true", txt, re.M) or re.search(r"^Hidden=true", txt, re.M): continue
                    nm, ex, ic = re.search(r"^Name=(.*)$", txt, re.M), re.search(r"^Exec=(.*)$", txt, re.M), re.search(r"^Icon=(.*)$", txt, re.M)
                    if nm and ex and nm.group(1).strip() not in seen:
                        n = nm.group(1).strip(); seen.add(n)
                        items.append((n, re.sub(r"\s+%[fFuUdDnNickvm]", "", ex.group(1).strip()), ic.group(1).strip() if ic else "default"))
                except Exception: pass

        self.last_pin_mtime = os.path.getmtime(PIN_FILE) if os.path.isfile(PIN_FILE) else 0
        while True:
            c = self.dock_box.get_first_child()
            if c is None: break
            self.dock_box.remove(c)
        favs = [it for it in items if it[0] in self.pinned]
        for name, cmd, icon_spec in favs:
            db = Gtk.Button(); db.add_css_class("dock-item")
            db.set_tooltip_text(f"{name} (ЛКМ: запустить • ПКМ: открепить)")
            hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
            hb.append(make_cyber_icon_widget(icon_spec, 18))
            hb.append(Gtk.Label(label=name[:16]))
            db.set_child(hb)
            db.connect("clicked", lambda _b, c=cmd: self.spawn_raw(c))
            rc = Gtk.GestureClick.new(); rc.set_button(3)
            rc.connect("pressed", lambda _g, _n, _x, _y, nm=name: self.toggle_pin(nm))
            db.add_controller(rc)
            self.dock_box.append(db)

    def toggle_pin(self, name):
        if name in self.pinned: self.pinned.remove(name)
        else: self.pinned.add(name)
        self.save_pinned(); self.populate_dock()

    def do_activate(self):
        prov = Gtk.CssProvider()
        css_p = os.path.join(CFG_DIR, "active_hub.css")
        if os.path.isfile(css_p):
            prov.load_from_string(open(css_p, "r", encoding="utf-8").read())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 25)

        builders = {
            "ai":       self.build_ai_widget,
            "notes":    self.build_notes_widget,
            "gamedev":  self.build_gamedev_widget,
            "calendar": self.build_calendar_widget,
            "media":    self.build_media_widget,
        }
        for wid, b_fn in builders.items():
            wobj = MovableStudioWidget(self, wid, self.st, b_fn)
            self.widgets[wid] = wobj
            wobj.win.present()

        self.build_bottom_dock()
        GLib.timeout_add(1500, self.tick_fast)
        GLib.timeout_add_seconds(4, self.tick_slow)

    def tick_fast(self):
        try:
            mt = os.path.getmtime(PIN_FILE) if os.path.isfile(PIN_FILE) else 0
            if mt != self.last_pin_mtime:
                self.pinned = self.load_pinned()
                self.populate_dock()
        except Exception: pass
        t_s, a_s = read_music_status()
        if self.track_lbl.get_label() != t_s: self.track_lbl.set_label(t_s)
        if self.artist_lbl.get_label() != a_s: self.artist_lbl.set_label(a_s)

        # Синхронизируем ползунки звука и яркости, если они были изменены с Waybar или клавишами
        try:
            v_now = get_current_vol()
            if abs(self.vol_scale.get_value() - v_now) > 1.5:
                self.vol_scale.handler_block_by_func(self.on_vol_changed)
                self.vol_scale.set_value(v_now)
                self.vol_lbl.set_label(f"{int(v_now)}%")
                self.vol_scale.handler_unblock_by_func(self.on_vol_changed)
            b_now = get_current_bri()
            if abs(self.bri_scale.get_value() - b_now) > 1.5:
                self.bri_scale.handler_block_by_func(self.on_bri_changed)
                self.bri_scale.set_value(b_now)
                self.bri_lbl.set_label(f"{int(b_now)}%")
                self.bri_scale.handler_unblock_by_func(self.on_bri_changed)
        except Exception:
            pass
        return True

    def tick_slow(self):
        self.git_lbl.set_label(read_git_projects_status())
        self.ports_lbl.set_label(f"Порты: {scan_dev_ports()}")
        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    StudioWidgetsDaemon().run(None)
