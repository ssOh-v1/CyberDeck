#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
except Exception:
    pass

import os, sys, re, glob, json, socket, hashlib, urllib.request, urllib.parse, calendar, threading, subprocess, datetime

HOME = os.path.expanduser("~")
UID = os.getuid()
CFG_DIR     = os.path.join(HOME, ".config/cyberdeck")
CACHE_DIR   = os.path.join(HOME, ".cache/cyberdeck")
BG_PNG      = os.path.join(CACHE_DIR, "work_hud_bg.png")
NOTES_FILE  = os.path.join(CFG_DIR, "studio_notes.txt")
PIN_FILE    = os.path.join(CFG_DIR, "pinned_work_apps.json")
STATE_FILE  = os.path.join(CFG_DIR, "widgets_state.json")
CHAT_FILE   = os.path.join(CFG_DIR, "ai_chat_history.json")
MODELS_FILE = os.path.join(CFG_DIR, "ai_models.json")
ROFI_T      = os.path.join(HOME, ".config/hypr/cyber_wifi.rasi")
NOTIF_TRIG  = "/tmp/studio_toggle_notif_center"
ART_CACHE   = "/tmp/studio_art_cache"
os.makedirs(ART_CACHE, exist_ok=True)
os.makedirs(CFG_DIR, exist_ok=True)

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

SINGLE_PIN_WID = sys.argv[2] if (len(sys.argv) > 2 and sys.argv[1] == "--pin-window") else None

if SINGLE_PIN_WID is None:
    _my_pid = os.getpid()
    for _p in os.listdir("/proc"):
        if _p.isdigit() and int(_p) != _my_pid:
            try:
                _cmd = open(f"/proc/{_p}/cmdline", "rb").read().decode("utf-8", "ignore")
                if ("work-hub-desktop.py" in _cmd or "cyberdeck-hub-desktop.py" in _cmd) and "--pin-window" not in _cmd:
                    os.kill(int(_p), 9)
            except Exception:
                pass

RU_MONTHS = ["", "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]

def get_logical_monitor_size():
    try:
        raw = subprocess.check_output(["hyprctl", "monitors", "-j"], text=True, stderr=subprocess.DEVNULL)
        mons = json.loads(raw)
        if mons:
            m = mons[0]
            sc = float(m.get("scale", 1.0)) or 1.0
            return int(round(m.get("width", 1920) / sc)), int(round(m.get("height", 1080) / sc))
    except Exception:
        pass
    return 1920, 1080

W_MON, H_MON = get_logical_monitor_size()

DEFAULT_WIDGETS = {
    "ai":       {"title": "▣ AI STUDIO",  "x": 18,            "y": 46,  "w": 335, "h": 295, "base_w": 335, "base_h": 295, "min_w": 240, "min_h": 180, "collapsed": False},
    "notes":    {"title": "▣ ЗАМЕТКИ",    "x": 18,            "y": 352, "w": 335, "h": 205, "base_w": 335, "base_h": 205, "min_w": 210, "min_h": 130, "collapsed": False},
    "calendar": {"title": "▣ КАЛЕНДАРЬ",  "x": W_MON - 298,   "y": 46,  "w": 280, "h": 205, "base_w": 280, "base_h": 205, "min_w": 220, "min_h": 160, "collapsed": False},
    "media":    {"title": "▣ МЕДИАПЛЕЕР", "x": W_MON - 298,   "y": 262, "w": 280, "h": 128, "base_w": 280, "base_h": 128, "min_w": 230, "min_h": 110, "collapsed": False},
}

FALLBACK_ART = os.path.join(ART_CACHE, "fallback_vinyl.svg")
open(FALLBACK_ART, "w", encoding="utf-8").write("""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 52 52">
  <rect width="52" height="52" rx="6" fill="#16181d"/>
  <circle cx="26" cy="26" r="18" fill="none" stroke="#3a3f48" stroke-width="2"/>
  <circle cx="26" cy="26" r="12" fill="none" stroke="#282c34" stroke-width="1.5"/>
  <circle cx="26" cy="26" r="5" fill="#6c727d"/>
  <circle cx="26" cy="26" r="2" fill="#16181d"/>
</svg>""")

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
            for k in list(st.keys()):
                if k in saved and isinstance(saved[k], dict):
                    st[k].update(saved[k])
                    st[k]["title"] = DEFAULT_WIDGETS[k]["title"]
                    st[k]["base_w"] = DEFAULT_WIDGETS[k]["base_w"]
                    st[k]["base_h"] = DEFAULT_WIDGETS[k]["base_h"]
                    # Гарантируем, что виджет находится в пределах видимой области экрана
                    w = int(st[k].get("w", 280))
                    h = int(st[k].get("h", 180))
                    st[k]["x"] = max(6, min(W_MON - w - 6, int(st[k].get("x", 18))))
                    st[k]["y"] = max(40, min(H_MON - 60, int(st[k].get("y", 46))))
    except Exception:
        pass
    return st

def save_widgets_state(st):
    os.makedirs(CFG_DIR, exist_ok=True)
    clean_st = {k: st[k] for k in DEFAULT_WIDGETS if k in st}
    json.dump(clean_st, open(STATE_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

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

def get_media_sink_inputs():
    ids, vols = [], []
    try:
        raw = subprocess.check_output(["pactl", "-f", "json", "list", "sink-inputs"], text=True, stderr=subprocess.DEVNULL, timeout=0.6)
        data = json.loads(raw)
        for item in data:
            idx = item.get("index")
            props = item.get("properties", {})
            bin_name = (props.get("application.process.binary") or "").lower()
            media_name = (props.get("media.name") or "").lower()
            if "speech-dispatcher" in bin_name or "bell" in media_name:
                continue
            ids.append(idx)
            v_dict = item.get("volume", {})
            for ch_v in v_dict.values():
                vp = ch_v.get("value_percent", "100%").replace("%", "").strip()
                if vp.isdigit():
                    vols.append(int(vp))
                    break
    except Exception:
        pass
    return ids, (sum(vols) / len(vols) if vols else None)

def set_media_stream_only_volume(val_pct):
    val_pct = max(0, min(100, int(val_pct)))
    ids, _ = get_media_sink_inputs()
    if ids:
        for sink_id in ids:
            subprocess.Popen(
                ["pactl", "set-sink-input-volume", str(sink_id), f"{val_pct}%"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
    else:
        subprocess.Popen(
            ["playerctl", "volume", f"{val_pct / 100.0:.2f}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

def read_music_and_art():
    try:
        out = subprocess.check_output(
            ["playerctl", "metadata", "--format", "{{status}}\t{{xesam:title}}\t{{xesam:artist}}\t{{mpris:artUrl}}"],
            text=True, stderr=subprocess.DEVNULL, timeout=0.6
        ).strip()
        parts = out.split("\t")
        while len(parts) < 4:
            parts.append("")
        status, title, artist, art_url = parts[0], parts[1].strip(), parts[2].strip(), parts[3].strip()
        if title:
            ic = "󰐊" if status == "Playing" else "󰏤"
            art_file = FALLBACK_ART
            if art_url.startswith("file://"):
                local_p = urllib.parse.unquote(art_url[7:])
                if os.path.isfile(local_p):
                    art_file = local_p
            elif art_url.startswith(("http://", "https://")):
                h = hashlib.md5(art_url.encode()).hexdigest()
                cached_p = os.path.join(ART_CACHE, f"{h}.jpg")
                if os.path.isfile(cached_p) and os.path.getsize(cached_p) > 200:
                    art_file = cached_p
                else:
                    subprocess.Popen(
                        ["curl", "-L", "-s", "--max-time", "4", "-o", cached_p, art_url],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            return f"{ic} {title[:28]}", f"{artist[:28] or 'Медиапоток'}", art_file
    except Exception:
        pass
    return "󰓛 Нет активного медиа", "Запустите музыку или видео", FALLBACK_ART

def load_ai_models():
    try:
        if os.path.isfile(MODELS_FILE):
            m = json.load(open(MODELS_FILE, encoding="utf-8"))
            if isinstance(m, list) and m:
                return m
    except Exception:
        pass
    return [{"id": "gemini-argon", "name": "Gemini Argon (Флагманский ИИ и Код)", "provider": "pollinations", "model": "gemini"}]

def query_ai_llm(model_meta, messages):
    prov = model_meta.get("provider", "pollinations")
    mod_name = model_meta.get("model", "gemini")
    m_title = model_meta.get("name", "Gemini Argon")

    if prov == "ollama":
        try:
            if mod_name == "auto":
                tags = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2.0).read().decode())
                mlist = [x["name"] for x in tags.get("models", [])]
                if not mlist:
                    return "В Ollama нет скачанных моделей. Выполните: ollama run qwen2.5-coder:7b (или выберите Gemini Argon сверху)."
                mod_name = mlist[0]
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/chat",
                data=json.dumps({"model": mod_name, "messages": messages, "stream": False}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
            return resp.get("message", {}).get("content", "").strip()
        except Exception:
            return "Локальный сервер Ollama не запущен. Запустите `ollama serve` или выберите Gemini Argon сверху."

    if prov == "custom" and model_meta.get("url"):
        try:
            payload = {"model": mod_name, "messages": messages[-8:]}
            res = subprocess.run(
                ["curl", "-s", "-L", "--max-time", "40", "-X", "POST", model_meta["url"],
                 "-H", "Content-Type: application/json",
                 "-H", f"Authorization: Bearer {model_meta.get('key', '')}",
                 "-d", json.dumps(payload)],
                capture_output=True, text=True
            )
            data = json.loads(res.stdout)
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Ошибка пользовательского API: {e}"

    sys_prompt = f"Ты — {m_title}. Отвечай чётко, лаконично и по делу на русском языке. При написании кода выдавай чистый рабочий код."
    payload = {"model": mod_name, "messages": [{"role": "system", "content": sys_prompt}] + messages[-6:]}
    try:
        res = subprocess.run(
            ["curl", "-s", "-L", "--connect-timeout", "8", "--max-time", "35",
             "-X", "POST", "https://text.pollinations.ai/openai",
             "-H", "Content-Type: application/json",
             "-A", "Mozilla/5.0 (X11; Linux x86_64)",
             "-d", json.dumps(payload, ensure_ascii=False)],
            capture_output=True, text=True
        )
        if res.returncode == 0 and res.stdout.strip():
            raw = res.stdout.strip()
            try:
                data = json.loads(raw)
                if "choices" in data and data["choices"]:
                    content = data["choices"][0].get("message", {}).get("content", "").strip()
                    if content:
                        return content
            except Exception:
                if not raw.startswith("<!DOCTYPE") and len(raw) > 2:
                    return raw
    except Exception:
        pass

    try:
        last_q = messages[-1]["content"]
        enc_q = urllib.parse.quote(f"Ответь на русском языке как {m_title}: {last_q}")
        res2 = subprocess.run(
            ["curl", "-s", "-L", "--connect-timeout", "8", "--max-time", "30",
             "-A", "Mozilla/5.0",
             f"https://text.pollinations.ai/{enc_q}?model={mod_name}"],
            capture_output=True, text=True
        )
        if res2.returncode == 0 and res2.stdout.strip():
            return res2.stdout.strip()
    except Exception as e:
        return f"Не удалось получить ответ: {e}"

    return "Сервер модели перегружен, попробуйте повторить запрос через пару секунд."

# ==============================================================================
# КАРТОЧКА ВИДЖЕТА (ПРЯМОЕ ПОЗИЦИОНИРОВАНИЕ В OVERLAY + ПРОПОРЦИОНАЛЬНЫЙ МАСШТАБ)
# ==============================================================================
class OverlayWidgetCard:
    def __init__(self, app, wid, state_dict, build_body_fn, is_standalone=False):
        self.app = app
        self.wid = wid
        self.st = state_dict
        self.is_standalone = is_standalone
        self.m_start_xy = (0, 0)
        self.m_start_cursor = None
        self.r_start_wh = (280, 180)
        self.r_start_cursor = None
        self.on_scale_hook = None

        self.scale_css = Gtk.CssProvider()
        try:
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), self.scale_css, Gtk.STYLE_PROVIDER_PRIORITY_USER + 35
            )
        except Exception:
            pass

        self.frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.frame.add_css_class("widget-frame-top" if is_standalone else "widget-frame")
        self.frame.add_css_class(f"wscale-{wid}")

        if not is_standalone:
            self.frame.set_halign(Gtk.Align.START)
            self.frame.set_valign(Gtk.Align.START)

        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hdr.add_css_class("widget-header")

        drag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        drag_box.set_hexpand(True)
        drag_lbl = Gtk.Label(label=f"⠿ {self.st[wid].get('title', wid.upper())}", xalign=0, hexpand=True)
        drag_lbl.add_css_class("widget-title")
        drag_box.append(drag_lbl)
        drag_box.set_tooltip_text("Зажмите ЛКМ и перетащите виджет в любое место экрана")
        hdr.append(drag_box)

        if not is_standalone:
            move_gest = Gtk.GestureDrag.new()
            move_gest.set_button(1)
            move_gest.connect("drag-begin", self.on_move_begin)
            move_gest.connect("drag-update", self.on_move_update)
            move_gest.connect("drag-end", self.on_move_end)
            drag_box.add_controller(move_gest)

        # Монохромная иконка булавки 󰐃 для закрепления поверх окон
        self.pin_btn = Gtk.Button(label="󰐃" if not is_standalone else "✕")
        self.pin_btn.add_css_class("w-pin-active" if is_standalone else "w-hdr-btn")
        self.pin_btn.set_tooltip_text("Закрепить виджет ПОВЕРХ открытых приложений" if not is_standalone else "Закрыть окно поверх приложений")
        self.pin_btn.connect("clicked", self.on_toggle_pin_top)
        hdr.append(self.pin_btn)

        if not is_standalone:
            col_btn = Gtk.Button(label="—")
            col_btn.add_css_class("w-hdr-btn")
            col_btn.set_tooltip_text("Свернуть / развернуть виджет")
            col_btn.connect("clicked", self.on_toggle_collapse)
            hdr.append(col_btn)

        self.frame.append(hdr)

        self.body_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.body_wrap.add_css_class("widget-body")
        self.body_wrap.set_vexpand(True); self.body_wrap.set_hexpand(True)

        content_w = build_body_fn(self)
        content_w.set_vexpand(True); content_w.set_hexpand(True)
        self.body_wrap.append(content_w)

        if not is_standalone:
            btm_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            sp = Gtk.Box(); sp.set_hexpand(True); btm_row.append(sp)
            grip_box = Gtk.Box()
            grip = Gtk.Label(label="◢")
            grip.add_css_class("resize-grip")
            grip_box.append(grip)
            grip_box.set_tooltip_text("Потяните ЛКМ за уголок — всё содержимое масштабируется пропорционально!")

            rsz_gest = Gtk.GestureDrag.new()
            rsz_gest.set_button(1)
            rsz_gest.connect("drag-begin", self.on_resize_begin)
            rsz_gest.connect("drag-update", self.on_resize_update)
            rsz_gest.connect("drag-end", self.on_resize_end)
            grip_box.add_controller(rsz_gest)
            btm_row.append(grip_box)
            self.body_wrap.append(btm_row)

        self.frame.append(self.body_wrap)
        self.apply_geometry()

    def update_proportional_scale(self, w, h):
        cfg = self.st[self.wid]
        bw = float(cfg.get("base_w", 280))
        bh = float(cfg.get("base_h", 190))
        scale = max(0.80, min(2.60, min(w / bw, h / bh)))

        f_title  = max(9,  int(round(10.5 * scale)))
        f_text   = max(9,  int(round(11.0 * scale)))
        f_btn    = max(9,  int(round(10.5 * scale)))
        f_cal_d  = max(9,  int(round(11.0 * scale)))
        f_cal_w  = max(8,  int(round(9.5  * scale)))
        f_track  = max(10, int(round(11.5 * scale)))
        f_artist = max(9,  int(round(10.0 * scale)))
        pad_v    = max(2,  int(round(3.0  * scale)))
        pad_h    = max(5,  int(round(7.0  * scale)))
        cell_w   = max(20, int(round(26.0 * scale)))
        cell_h   = max(16, int(round(20.0 * scale)))

        css = f"""
        .wscale-{self.wid} .widget-title {{ font-size: {f_title}px; }}
        .wscale-{self.wid} .chat-view,
        .wscale-{self.wid} .notes-view,
        .wscale-{self.wid} entry.compact-entry {{ font-size: {f_text}px; }}
        .wscale-{self.wid} button.mini-btn {{ font-size: {f_btn}px; padding: {pad_v}px {pad_h}px; min-height: {int(20 * scale)}px; }}
        .wscale-{self.wid} .cal-dow {{ font-size: {f_cal_w}px; min-width: {cell_w}px; }}
        .wscale-{self.wid} .cal-day,
        .wscale-{self.wid} .cal-today {{ font-size: {f_cal_d}px; min-width: {cell_w}px; min-height: {cell_h}px; }}
        .wscale-{self.wid} .track-title {{ font-size: {f_track}px; }}
        .wscale-{self.wid} .track-artist,
        .wscale-{self.wid} .mono-sub {{ font-size: {f_artist}px; }}
        """
        try:
            self.scale_css.load_from_string(css)
        except Exception:
            pass

        if callable(self.on_scale_hook):
            self.on_scale_hook(scale, w, h)

    def apply_geometry(self):
        cfg = self.st[self.wid]
        w = max(int(cfg.get("min_w", 210)), int(cfg.get("w", 280)))
        h = max(int(cfg.get("min_h", 110)), int(cfg.get("h", 180)))
        x = max(6, min(W_MON - w - 6, int(cfg.get("x", 18))))
        y = max(40, min(H_MON - 40, int(cfg.get("y", 46))))
        is_col = bool(cfg.get("collapsed", False)) and not self.is_standalone

        if not self.is_standalone:
            self.frame.set_margin_start(x)
            self.frame.set_margin_top(y)

        self.body_wrap.set_visible(not is_col)
        self.frame.set_size_request(w, 26 if is_col else h)
        self.update_proportional_scale(w, h)

    def on_move_begin(self, _g, _x, _y):
        cfg = self.st[self.wid]
        self.m_start_xy = (int(cfg.get("x", 18)), int(cfg.get("y", 46)))
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
        cfg["x"] = max(6, min(W_MON - int(cfg["w"]) - 6, nx))
        cfg["y"] = max(40, min(H_MON - 40, ny))
        self.frame.set_margin_start(cfg["x"])
        self.frame.set_margin_top(cfg["y"])

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
        cfg["w"] = max(int(cfg.get("min_w", 210)), min(960, nw))
        cfg["h"] = max(int(cfg.get("min_h", 110)), min(880, nh))
        self.frame.set_size_request(cfg["w"], cfg["h"])
        self.update_proportional_scale(cfg["w"], cfg["h"])

    def on_resize_end(self, _g, _ox, _oy):
        save_widgets_state(self.st)

    def on_toggle_pin_top(self, _b):
        if self.is_standalone:
            self.app.quit()
            return
        cfg = self.st[self.wid]
        x, y, w, h = int(cfg["x"]), int(cfg["y"]), int(cfg["w"]), int(cfg["h"])
        cmd = f'hyprctl dispatch exec "[float; pin; move {x} {y}; size {w} {h}] /usr/bin/python3 {HOME}/.local/bin/work-hub-desktop.py --pin-window {self.wid}"'
        self.app.spawn_raw(cmd)

    def on_toggle_collapse(self, _b):
        cfg = self.st[self.wid]
        cfg["collapsed"] = not bool(cfg.get("collapsed", False))
        self.apply_geometry()
        save_widgets_state(self.st)

# ==============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ РАБОЧЕГО СТОЛА И ВИДЖЕТОВ (НА LAYER.BOTTOM НАД SWAYBG)
# ==============================================================================
class StudioDesktopApp(Gtk.Application):
    def __init__(self):
        app_id = f"org.alpora.PinWidget.{SINGLE_PIN_WID}.{os.getpid()}" if SINGLE_PIN_WID else "org.alpora.WorkDeckLayer"
        super().__init__(application_id=app_id)
        self.st = load_widgets_state()
        self.cards = {}
        self.pinned = self.load_pinned()
        self.last_pin_mtime = 0
        self.last_models_mtime = 0

        self.ai_models = load_ai_models()
        self.active_model_idx = 0
        self.chat_history = self.load_chat_history()
        self.ai_busy = False

        now = datetime.date.today()
        self.cal_year, self.cal_month = now.year, now.month
        self.last_art_path = ""
        self.updating_vol_ui = False
        self.notif_frame = None

        self.bg_surface = None
        if SINGLE_PIN_WID is None and os.path.isfile(BG_PNG):
            try:
                self.bg_surface = cairo.ImageSurface.create_from_png(BG_PNG)
            except Exception:
                self.bg_surface = None

    def on_draw_bg(self, _area, cr, w, h, *_args):
        cr.save()
        cr.scale(w / 1920.0, h / 1080.0)
        if self.bg_surface is not None:
            cr.set_source_surface(self.bg_surface, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0.07, 0.075, 0.086)
            cr.paint()
        cr.restore()

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
        return [{"role": "assistant", "content": "Gemini Argon готов к работе! Нажмите на кнопку модели сверху для смены ИИ (или «+ ИИ» для добавления своей) и введите запрос ниже."}]

    def save_chat_history(self):
        try:
            json.dump(self.chat_history[-12:], open(CHAT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        except Exception:
            pass

    # --- 1. ВИДЖЕТ НЕЙРОСЕТЕЙ (GEMINI ARGON ПО УМОЛЧАНИЮ + МОНОХРОМНЫЕ ИКОНКИ) ---
    def build_ai_widget(self, _card):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        cur_m_name = self.ai_models[self.active_model_idx]["name"] if self.ai_models else "Gemini Argon"
        self.model_sel_btn = Gtk.Button(label=f"󰚩 {cur_m_name[:26]} ▾")
        self.model_sel_btn.add_css_class("mini-btn")
        self.model_sel_btn.set_hexpand(True)
        self.model_sel_btn.set_tooltip_text("ЛКМ: Открыть список доступных нейросетей • ПКМ: Следующая модель")
        self.model_sel_btn.connect("clicked", self.on_open_model_list_rofi)
        rc_m = Gtk.GestureClick.new(); rc_m.set_button(3)
        rc_m.connect("pressed", lambda *_a: self.cycle_next_model())
        self.model_sel_btn.add_controller(rc_m)
        top_row.append(self.model_sel_btn)

        b_manage = Gtk.Button(label="+ ИИ")
        b_manage.add_css_class("mini-btn")
        b_manage.set_tooltip_text("Добавить свою нейросеть или выбрать из каталога")
        b_manage.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/studio-ai-manager"))
        top_row.append(b_manage)
        box.append(top_row)

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
        b_copy.set_tooltip_text("Скопировать последний ответ")
        b_copy.connect("clicked", self.on_copy_last_ai)
        in_row.append(b_copy)

        b_clr = Gtk.Button(label="󰩺"); b_clr.add_css_class("mini-btn")
        b_clr.set_tooltip_text("Очистить чат")
        b_clr.connect("clicked", self.on_clear_ai_chat)
        in_row.append(b_clr)

        box.append(in_row)
        self.last_models_mtime = os.path.getmtime(MODELS_FILE) if os.path.isfile(MODELS_FILE) else 0
        return box

    def cycle_next_model(self):
        self.ai_models = load_ai_models()
        if not self.ai_models: return
        self.active_model_idx = (self.active_model_idx + 1) % len(self.ai_models)
        cur_m_name = self.ai_models[self.active_model_idx]["name"]
        self.model_sel_btn.set_label(f"󰚩 {cur_m_name[:26]} ▾")
        self.render_chat_log()

    def on_open_model_list_rofi(self, _b):
        self.ai_models = load_ai_models()
        def _pick():
            lines = []
            for idx, m in enumerate(self.ai_models):
                mark = " [● АКТИВНА]" if idx == self.active_model_idx else ""
                lines.append(f"{idx+1}. 󰚩 {m['name']}{mark}")
            lines.append("➕ Добавить новую нейросеть в список...")
            cmd = ["rofi", "-dmenu", "-i", "-p", "󰚩 ВЫБОР НЕЙРОСЕТИ"]
            if os.path.isfile(ROFI_T): cmd += ["-theme", ROFI_T]
            p = subprocess.run(cmd, input="\n".join(lines), text=True, capture_output=True)
            if p.returncode == 0 and p.stdout.strip():
                ch = p.stdout.strip()
                if "Добавить новую" in ch:
                    subprocess.Popen(["/usr/bin/python3", os.path.join(HOME, ".local/bin/studio-ai-manager")])
                elif "." in ch:
                    try:
                        sel_i = int(ch.split(".", 1)[0]) - 1
                        if 0 <= sel_i < len(self.ai_models):
                            GLib.idle_add(self.set_active_model_idx, sel_i)
                    except Exception:
                        pass
        threading.Thread(target=_pick, daemon=True).start()

    def set_active_model_idx(self, idx):
        self.active_model_idx = idx
        cur_m_name = self.ai_models[self.active_model_idx]["name"]
        self.model_sel_btn.set_label(f"󰚩 {cur_m_name[:26]} ▾")
        self.render_chat_log()
        return False

    def render_chat_log(self, thinking=False):
        m_meta = self.ai_models[self.active_model_idx] if self.ai_models else {"name": "Gemini Argon"}
        short_m = m_meta["name"].split("(")[0].strip()
        lines = []
        for msg in self.chat_history[-10:]:
            prefix = "▸ ВЫ:" if msg["role"] == "user" else f"▣ {short_m}:"
            lines.append(f"{prefix}\n{msg['content']}")
        if thinking:
            lines.append(f"▣ {short_m}:\n▪ генерация ответа...")
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

        m_meta = self.ai_models[self.active_model_idx] if self.ai_models else {"provider": "pollinations", "model": "gemini"}
        msgs_snapshot = list(self.chat_history)

        def worker():
            ans = query_ai_llm(m_meta, msgs_snapshot)
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
                self.spawn_raw("notify-send -a cyber-kb '▣ AI STUDIO' 'Ответ скопирован в буфер обмена'")
                break

    def on_clear_ai_chat(self, _b):
        self.chat_history = [{"role": "assistant", "content": "Диалог очищен. Введите новый вопрос."}]
        self.save_chat_history()
        self.render_chat_log()

    # --- 2. ВИДЖЕТ ЗАМЕТОК ---
    def build_notes_widget(self, _card):
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

    # --- 3. ПРОПОРЦИОНАЛЬНО МАСШТАБИРУЕМЫЙ ВИДЖЕТ КАЛЕНДАРЯ ---
    def build_calendar_widget(self, card):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_hexpand(True); box.set_vexpand(True)

        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.cal_title_lbl = Gtk.Label(label="", xalign=0, hexpand=True, css_classes=["widget-title"])
        nav.append(self.cal_title_lbl)
        for sym, d in [("◀", -1), ("●", 0), ("▶", 1)]:
            b = Gtk.Button(label=sym); b.add_css_class("mini-btn")
            b.connect("clicked", lambda _b, delta=d: self.shift_cal(delta))
            nav.append(b)
        box.append(nav)

        self.cal_grid = Gtk.Grid()
        self.cal_grid.set_hexpand(True); self.cal_grid.set_vexpand(True)
        self.cal_grid.set_halign(Gtk.Align.FILL); self.cal_grid.set_valign(Gtk.Align.FILL)
        self.cal_grid.set_column_homogeneous(True)
        self.cal_grid.set_row_homogeneous(True)
        self.cal_grid.set_column_spacing(4); self.cal_grid.set_row_spacing(3)
        box.append(self.cal_grid)

        def _on_cal_scale(scale, _w, _h):
            sp = max(2, int(round(4 * scale)))
            self.cal_grid.set_column_spacing(sp)
            self.cal_grid.set_row_spacing(max(1, sp - 1))

        card.on_scale_hook = _on_cal_scale
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
            dl = Gtk.Label(label=d, css_classes=["cal-dow"])
            dl.set_hexpand(True); dl.set_vexpand(True)
            self.cal_grid.attach(dl, i, 0, 1, 1)
        today = datetime.date.today()
        for r_i, week in enumerate(calendar.Calendar(0).monthdayscalendar(self.cal_year, self.cal_month), 1):
            for c_i, day in enumerate(week):
                lbl = Gtk.Label(label=" " if day == 0 else f"{day:2d}")
                lbl.set_hexpand(True); lbl.set_vexpand(True)
                is_t = (day == today.day and self.cal_month == today.month and self.cal_year == today.year)
                lbl.add_css_class("cal-today" if is_t else "cal-day")
                self.cal_grid.attach(lbl, c_i, r_i, 1, 1)

    # --- 4. ПРОПОРЦИОНАЛЬНО МАСШТАБИРУЕМЫЙ ВИДЖЕТ МУЗЫКИ С ОБЛОЖКОЙ ---
    def build_media_widget(self, card):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_hexpand(True); box.set_vexpand(True)

        top_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_h.set_vexpand(True)
        self.art_pic = Gtk.Picture()
        self.art_pic.set_size_request(54, 54)
        self.art_pic.add_css_class("cover-frame")
        if hasattr(Gtk, "ContentFit"):
            self.art_pic.set_content_fit(Gtk.ContentFit.COVER)
        self.art_pic.set_filename(FALLBACK_ART)
        top_h.append(self.art_pic)

        meta_v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        meta_v.set_hexpand(True); meta_v.set_valign(Gtk.Align.CENTER)
        t_s, a_s, _ = read_music_and_art()
        self.track_lbl = Gtk.Label(label=t_s, xalign=0, css_classes=["track-title"])
        self.track_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.artist_lbl = Gtk.Label(label=a_s, xalign=0, css_classes=["track-artist"])
        self.artist_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        meta_v.append(self.track_lbl); meta_v.append(self.artist_lbl)

        ctrl_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for lbl, cmd in [("󰒮", "playerctl previous"), ("󰐎", "playerctl play-pause"), ("󰒭", "playerctl next")]:
            b = Gtk.Button(label=lbl); b.add_css_class("mini-btn"); b.set_hexpand(True)
            b.connect("clicked", lambda _b, c=cmd: self.spawn_raw(c))
            ctrl_r.append(b)
        meta_v.append(ctrl_r)
        top_h.append(meta_v)
        box.append(top_h)

        # Ползунок громкости ТОЛЬКО для музыки/видео (с монохромной иконкой 󰕾)
        v_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        v_row.append(Gtk.Label(label="󰕾 Медиа", css_classes=["mono-sub"]))
        _, cur_mv = get_media_sink_inputs()
        init_v = cur_mv if cur_mv is not None else 85.0
        self.media_vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.media_vol_scale.set_draw_value(False); self.media_vol_scale.set_hexpand(True); self.media_vol_scale.set_value(init_v)
        self.media_vol_scale.set_tooltip_text("Громкость только активного видео/плеера (системный звук не меняется)")
        self.media_vol_lbl = Gtk.Label(label=f"{int(init_v)}%", css_classes=["mono-sub"])
        self.media_vol_scale.connect("value-changed", self.on_media_vol_changed)
        v_row.append(self.media_vol_scale); v_row.append(self.media_vol_lbl)
        box.append(v_row)

        def _on_media_scale(scale, _w, _h):
            art_sz = max(44, min(140, int(round(54 * scale))))
            self.art_pic.set_size_request(art_sz, art_sz)

        card.on_scale_hook = _on_media_scale
        return box

    def on_media_vol_changed(self, scale):
        if self.updating_vol_ui:
            return
        val = int(scale.get_value())
        self.media_vol_lbl.set_label(f"{val}%")
        set_media_stream_only_volume(val)

    # --- ЦЕНТР УВЕДОМЛЕНИЙ (ПО КЛИКУ НА 󰂚 / 󰂜 НА WAYBAR) ---
    def build_notification_center_card(self):
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame.add_css_class("widget-frame-top")
        frame.set_halign(Gtk.Align.START)
        frame.set_valign(Gtk.Align.START)
        frame.set_margin_start(max(10, W_MON - 334))
        frame.set_margin_top(44)
        frame.set_size_request(320, 320)

        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr.add_css_class("widget-header")
        hdr.append(Gtk.Label(label="󰂚 ЦЕНТР УВЕДОМЛЕНИЙ", xalign=0, hexpand=True, css_classes=["widget-title"]))

        b_dnd = Gtk.Button(label="󰂛 DND")
        b_dnd.add_css_class("w-hdr-btn")
        b_dnd.connect("clicked", lambda _b: self.spawn_raw("makoctl mode -t do-not-disturb"))
        hdr.append(b_dnd)

        b_clr = Gtk.Button(label="Очистить")
        b_clr.add_css_class("w-hdr-btn")
        b_clr.connect("clicked", lambda _b: (self.spawn_raw("makoctl dismiss -a"), self.refresh_notif_list()))
        hdr.append(b_clr)

        b_close = Gtk.Button(label="✕")
        b_close.add_css_class("w-hdr-btn")
        b_close.connect("clicked", lambda _b: frame.set_visible(False))
        hdr.append(b_close)
        frame.append(hdr)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        body.add_css_class("widget-body")
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.set_hexpand(True)
        self.notif_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sc.set_child(self.notif_list_box)
        body.append(sc)
        frame.append(body)
        frame.set_visible(False)
        return frame

    def refresh_notif_list(self):
        if not self.notif_frame: return
        while True:
            c = self.notif_list_box.get_first_child()
            if c is None: break
            self.notif_list_box.remove(c)
        try:
            raw = subprocess.check_output(["makoctl", "history"], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            raw = ""
        blocks = [b.strip() for b in raw.split("Notification ") if b.strip()]
        if not blocks:
            lbl = Gtk.Label(label="Нет новых уведомлений", css_classes=["mono-sub"])
            lbl.set_valign(Gtk.Align.CENTER); lbl.set_vexpand(True)
            self.notif_list_box.append(lbl)
            return
        for blk in blocks[:12]:
            lines = blk.splitlines()
            head = lines[0] if lines else "Уведомление"
            summary = head.split(":", 1)[1].strip() if ":" in head else head
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            card.add_css_class("notif-card")
            t_l = Gtk.Label(label=summary[:38], xalign=0, css_classes=["track-title"])
            t_l.set_ellipsize(Pango.EllipsizeMode.END)
            card.append(t_l)
            for ln in lines[1:3]:
                card.append(Gtk.Label(label=ln.strip()[:44], xalign=0, css_classes=["track-artist"]))
            self.notif_list_box.append(card)

    def populate_dock(self):
        if not hasattr(self, "dock_box"): return
        items, seen = [], set()
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
        for name, cmd, icon_spec in [it for it in items if it[0] in self.pinned]:
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
            try:
                prov.load_from_string(open(css_p, "r", encoding="utf-8").read())
            except Exception:
                pass
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 25)

        builders = {
            "ai":       self.build_ai_widget,
            "notes":    self.build_notes_widget,
            "calendar": self.build_calendar_widget,
            "media":    self.build_media_widget,
        }

        if SINGLE_PIN_WID in builders:
            cfg = self.st[SINGLE_PIN_WID]
            pwin = Gtk.ApplicationWindow(application=self, title=f"Pinned-{SINGLE_PIN_WID}")
            pwin.set_default_size(int(cfg["w"]), int(cfg["h"]))
            card = OverlayWidgetCard(self, SINGLE_PIN_WID, self.st, builders[SINGLE_PIN_WID], is_standalone=True)
            pwin.set_child(card.frame)
            pwin.present()
            GLib.timeout_add(600, self.tick_fast)
            return

        # Размещаем слой виджетов на Layer.BOTTOM (строго НАД swaybg и ПОД обычными окнами!)
        win = Gtk.ApplicationWindow(application=self, title="WorkHubDesktop")
        win.set_default_size(W_MON, H_MON)
        Gtk4LayerShell.init_for_window(win)
        Gtk4LayerShell.set_namespace(win, "work-hub-wallpaper")
        Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.BOTTOM)
        for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
            Gtk4LayerShell.set_anchor(win, edge, True)
        Gtk4LayerShell.set_exclusive_zone(win, -1)
        Gtk4LayerShell.set_keyboard_mode(win, Gtk4LayerShell.KeyboardMode.ON_DEMAND)

        overlay = Gtk.Overlay()

        bg_area = Gtk.DrawingArea()
        bg_area.set_hexpand(True); bg_area.set_vexpand(True)
        bg_area.set_size_request(W_MON, H_MON)
        bg_area.set_draw_func(self.on_draw_bg)
        overlay.set_child(bg_area)

        # Добавляем все 4 виджета напрямую как независимые слои Gtk.Overlay (проверенный механизм!)
        for wid, b_fn in builders.items():
            card = OverlayWidgetCard(self, wid, self.st, b_fn, is_standalone=False)
            self.cards[wid] = card
            overlay.add_overlay(card.frame)

        # Центр уведомлений
        self.notif_frame = self.build_notification_center_card()
        overlay.add_overlay(self.notif_frame)

        # Нижний док закреплённых приложений
        dock_align = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dock_align.set_valign(Gtk.Align.END); dock_align.set_halign(Gtk.Align.CENTER)
        dock_align.set_margin_bottom(12)
        dock_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dock_wrap.add_css_class("bottom-dock")
        self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dock_wrap.append(self.dock_box)

        add_b = Gtk.Button(label="+")
        add_b.add_css_class("dock-item")
        add_b.set_tooltip_text("Закрепить / открепить приложения в доке")
        add_b.connect("clicked", lambda _b: self.spawn_raw("/usr/bin/python3 ~/.local/bin/cyber-pin-menu"))
        dock_wrap.append(add_b)
        dock_align.append(dock_wrap)
        overlay.add_overlay(dock_align)

        win.set_child(overlay)
        self.populate_dock()
        win.present()

        GLib.timeout_add(450, self.tick_fast)

    def tick_fast(self):
        if os.path.exists(NOTIF_TRIG):
            try: os.remove(NOTIF_TRIG)
            except Exception: pass
            if self.notif_frame:
                vis = not self.notif_frame.get_visible()
                if vis: self.refresh_notif_list()
                self.notif_frame.set_visible(vis)

        try:
            mt = os.path.getmtime(PIN_FILE) if os.path.isfile(PIN_FILE) else 0
            if mt != self.last_pin_mtime:
                self.pinned = self.load_pinned()
                self.populate_dock()
        except Exception: pass

        try:
            mt_m = os.path.getmtime(MODELS_FILE) if os.path.isfile(MODELS_FILE) else 0
            if mt_m != self.last_models_mtime:
                self.last_models_mtime = mt_m
                self.ai_models = load_ai_models()
                self.active_model_idx = max(0, min(self.active_model_idx, len(self.ai_models) - 1))
                if hasattr(self, "model_sel_btn") and self.ai_models:
                    self.model_sel_btn.set_label(f"󰚩 {self.ai_models[self.active_model_idx]['name'][:26]} ▾")
        except Exception: pass

        if hasattr(self, "track_lbl"):
            t_s, a_s, art_p = read_music_and_art()
            if self.track_lbl.get_label() != t_s: self.track_lbl.set_label(t_s)
            if self.artist_lbl.get_label() != a_s: self.artist_lbl.set_label(a_s)
            if art_p != self.last_art_path and os.path.isfile(art_p):
                self.last_art_path = art_p
                self.art_pic.set_filename(art_p)

            _, mv = get_media_sink_inputs()
            if mv is not None and abs(self.media_vol_scale.get_value() - mv) > 2.0:
                self.updating_vol_ui = True
                self.media_vol_scale.set_value(mv)
                self.media_vol_lbl.set_label(f"{int(mv)}%")
                self.updating_vol_ui = False

        return True

    def spawn_raw(self, cmd):
        clean_env = {k: v for k, v in os.environ.items() if k not in ("LD_PRELOAD", "GTK_THEME")}
        if ORIG_GTK_THEME is not None: clean_env["GTK_THEME"] = ORIG_GTK_THEME
        subprocess.Popen(["/bin/sh", "-c", cmd], env=clean_env, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    StudioDesktopApp().run(None)
