#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
except Exception:
    pass

import os, sys, re, glob, json, time, random, socket, signal, atexit, hashlib, urllib.request, urllib.parse, calendar, threading, subprocess, datetime

signal.signal(signal.SIGHUP, signal.SIG_IGN)

HOME = os.path.expanduser("~")
UID = os.getuid()
CFG_DIR      = os.path.join(HOME, ".config/cyberdeck")
CACHE_DIR    = os.path.join(HOME, ".cache/cyberdeck")
BG_PNG       = os.path.join(CACHE_DIR, "work_hud_bg.png")
NOTES_FILE   = os.path.join(CFG_DIR, "studio_notes.txt")
NOTES_PAGES  = os.path.join(CFG_DIR, "studio_notes_pages.json")
PIN_FILE     = os.path.join(CFG_DIR, "pinned_work_apps.json")
STATE_FILE   = os.path.join(CFG_DIR, "widgets_state.json")
CHATS_DB     = os.path.join(CFG_DIR, "ai_chats.json")
GEM_KEY_FILE = os.path.join(CFG_DIR, "gemini_api_key.txt")
HIDDEN_NOTIF = os.path.join(CFG_DIR, "hidden_notifications.json")
ROFI_T       = os.path.join(HOME, ".config/hypr/cyber_wifi.rasi")
NOTIF_TRIG   = "/tmp/studio_toggle_notif_center"
ART_CACHE    = "/tmp/studio_art_cache"
PID_FILE     = f"/tmp/studio_widgets_{UID}.pid"

os.makedirs(ART_CACHE, exist_ok=True)
os.makedirs(CFG_DIR, exist_ok=True)

os.environ["XCURSOR_THEME"] = "GameDev-Cursor-Grey"
os.environ["XCURSOR_SIZE"] = "28"

ORIG_GTK_THEME = os.environ.get("GTK_THEME")
os.environ["GTK_THEME"] = "Adwaita:dark"

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Pango, Gtk4LayerShell
import cairo

os.environ.pop("LD_PRELOAD", None)

SINGLE_PIN_WID = sys.argv[2] if (len(sys.argv) > 2 and sys.argv[1] == "--pin-window") else None

if SINGLE_PIN_WID is None:
    if os.path.isfile(PID_FILE):
        try:
            old_pid = int(open(PID_FILE).read().strip())
            if old_pid != os.getpid() and os.path.exists(f"/proc/{old_pid}/cmdline"):
                cmdline = open(f"/proc/{old_pid}/cmdline", "rb").read().decode("utf-8", "ignore")
                if "work-hub-desktop.py" in cmdline and "--pin-window" not in cmdline:
                    os.kill(old_pid, signal.SIGTERM)
                    time.sleep(0.15)
        except Exception:
            pass
    try:
        open(PID_FILE, "w").write(str(os.getpid()))
    except Exception:
        pass

RU_MONTHS = ["", "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]

GEMINI_PERSONA_PROMPT = (
    "Ты — Gemini 2.5 Pro, флагманский ИИ-архитектор и персональный напарник Дениса (ssOh), встроенный в виджет его рабочего стола "
    "на базе Arch Linux / Wayland / Hyprland (тема Studio Matte-Grey). "
    "Ты глубоко разбираешься в его проектах: разработке 2D rogue-платформера на Python 3 и Pygame (pygame-ce), "
    "системном программировании, кастомизации Linux/Hyprland/Waybar и учебных дисциплинах 2 курса (Python, C#, C++, JS, Java, HTML, 1С). "
    "Давай глубокие, технически точные ответы на русском языке и пиши готовый к запуску, оптимизированный код."
)

def get_logical_monitor_size():
    for _ in range(10):
        try:
            raw = subprocess.check_output(["hyprctl", "monitors", "-j"], text=True, stderr=subprocess.DEVNULL)
            mons = json.loads(raw)
            if mons:
                m = mons[0]
                sc = float(m.get("scale", 1.0)) or 1.0
                w = int(round(m.get("width", 1920) / sc))
                h = int(round(m.get("height", 1080) / sc))
                if w >= 800 and h >= 600:
                    return w, h
        except Exception:
            pass
        time.sleep(0.1)
    return 1920, 1080

W_MON, H_MON = get_logical_monitor_size()

DEFAULT_WIDGETS = {
    "ai":       {"title": "✦ GEMINI ULTRA // 2.5 PRO",     "x": 18,          "y": 46,  "w": 355, "h": 315, "base_w": 355, "base_h": 315, "min_w": 255, "min_h": 185, "collapsed": False},
    "notes":    {"title": "▣ ЗАМЕТКИ",            "x": 18,          "y": 372, "w": 355, "h": 225, "base_w": 355, "base_h": 225, "min_w": 220, "min_h": 145, "collapsed": False},
    "calendar": {"title": "▣ КАЛЕНДАРЬ",          "x": W_MON - 298, "y": 46,  "w": 280, "h": 210, "base_w": 280, "base_h": 205, "min_w": 220, "min_h": 160, "collapsed": False},
    "media":    {"title": "▣ МЕДИАПЛЕЕР",         "x": W_MON - 298, "y": 268, "w": 280, "h": 130, "base_w": 280, "base_h": 128, "min_w": 230, "min_h": 110, "collapsed": False},
    "notif":    {"title": "󰂚 ЦЕНТР УВЕДОМЛЕНИЙ", "x": W_MON - 478, "y": 44,  "w": 460, "h": 540, "base_w": 460, "base_h": 540, "min_w": 340, "min_h": 300, "collapsed": False},
}

FALLBACK_ART = os.path.join(ART_CACHE, "fallback_vinyl.svg")
open(FALLBACK_ART, "w", encoding="utf-8").write("""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 52 52">
  <rect width="52" height="52" rx="6" fill="#16181d"/>
  <circle cx="26" cy="26" r="18" fill="none" stroke="#3a3f48" stroke-width="2"/>
  <circle cx="26" cy="26" r="12" fill="none" stroke="#282c34" stroke-width="1.5"/>
  <circle cx="26" cy="26" r="5" fill="#6c727d"/>
  <circle cx="26" cy="26" r="2" fill="#16181d"/>
</svg>""")

def rofi_prompt(prompt_title, options, default_input=""):
    cmd = ["rofi", "-dmenu", "-i", "-p", prompt_title]
    if os.path.isfile(ROFI_T):
        cmd += ["-theme", ROFI_T]
    inp = "\n".join(options) if options else default_input
    proc = subprocess.run(cmd, input=inp, text=True, capture_output=True)
    return proc.stdout.strip() if proc.returncode == 0 else ""

def get_cursor_screen_pos():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    xdg = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{UID}")
    for sock_p in (os.path.join(xdg, "hypr", sig, ".socket.sock"), f"/tmp/hypr/{sig}/.socket.sock"):
        if os.path.exists(sock_p):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.settimeout(0.05)
                    s.connect(sock_p)
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
                    for field in ("x", "y", "w", "h", "collapsed"):
                        if field in saved[k]:
                            st[k][field] = saved[k][field]
                    st[k]["title"] = DEFAULT_WIDGETS[k]["title"]
                    w = max(int(st[k]["min_w"]), min(W_MON - 20, int(st[k]["w"])))
                    h = max(int(st[k]["min_h"]), min(H_MON - 60, int(st[k]["h"])))
                    st[k]["w"] = w
                    st[k]["h"] = h
                    st[k]["x"] = max(4, min(W_MON - w - 4, int(st[k]["x"])))
                    st[k]["y"] = max(36, min(H_MON - h - 4, int(st[k]["y"])))
    except Exception:
        pass
    return st

def save_widgets_state(st):
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        clean_st = {k: st[k] for k in DEFAULT_WIDGETS if k in st}
        tmp_p = STATE_FILE + ".tmp"
        with open(tmp_p, "w", encoding="utf-8") as f:
            json.dump(clean_st, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_p, STATE_FILE)
    except Exception:
        pass

def resolve_cyber_svg(spec, fallback_glyph="default"):
    theme_apps = os.path.join(HOME, ".local/share/icons/CyberDeck-Icons/scalable/apps")
    if spec and os.path.isfile(spec):
        return spec
    raw = os.path.splitext(os.path.basename(spec or ""))[0]
    for cand in (spec, raw, raw.lower(), fallback_glyph, "default"):
        if cand and os.path.isfile(os.path.join(theme_apps, f"{cand}.svg")):
            return os.path.join(theme_apps, f"{cand}.svg")
    return None

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

def is_rate_limited_or_bad(text):
    if not text or len(text.strip()) < 2:
        return True
    low = text.lower()
    bad_markers = (
        "free limit reached",
        "1 reply every",
        "enter.pollinations.ai",
        "pollen key",
        "rate limit",
        "too many requests",
        "<!doctype",
        "<html",
        "502 bad gateway",
        "504 gateway",
        "error 52",
    )
    return any(b in low for b in bad_markers)

# ==============================================================================
# ЯДРО GEMINI ULTRA (2.5 PRO 16K + СТРОГАЯ ОЧЕРЕДНОСТЬ РОЛЕЙ + ПОДДЕРЖКА HAPP)
# ==============================================================================
def get_saved_gemini_key():
    if os.path.isfile(GEM_KEY_FILE):
        try:
            raw = open(GEM_KEY_FILE, "r", encoding="utf-8").read()
            clean = re.sub(r"[^A-Za-z0-9_-]", "", raw)
            if len(clean) >= 20:
                return clean
        except Exception:
            pass
    return ""

def detect_local_proxy():
    # Если запущен Happ / Sing-box / Xray, находим активный локальный порт для обхода гео-блокировки Google API
    for port in (2080, 10808, 10809, 7890, 12334, 1080):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.08):
                return f"http://127.0.0.1:{port}"
        except Exception:
            pass
    return None

def build_valid_gemini_contents(messages):
    # Официальный API Google требует, чтобы диалог строго начинался с роли 'user' и чередовал 'user' <-> 'model'
    cleaned = []
    for m in messages[-16:]:
        txt = (m.get("content") or "").strip()
        if not txt:
            continue
        # Игнорируем старые системные заглушки и сообщения об ошибках
        if any(bad in txt for bad in ("Публичный бесключевой шлюз", "Публичный шлюз просит", "Старый чат удалён", "История чата", "Создан новый чат", "Канал связи временно", "Привет, Денис!")):
            continue
        role = "user" if m.get("role") == "user" else "model"
        # Пропускаем любые сообщения модели, пока не встретится первое сообщение пользователя
        if not cleaned and role == "model":
            continue
        # Если две реплики подряд имеют одинаковую роль — склеиваем их в один блок
        if cleaned and cleaned[-1]["role"] == role:
            cleaned[-1]["parts"][0]["text"] += "

" + txt
        else:
            cleaned.append({"role": role, "parts": [{"text": txt}]})

    if not cleaned and messages:
        cleaned = [{"role": "user", "parts": [{"text": messages[-1].get("content", "Привет")}]}]
    return cleaned

def query_native_google_gemini_pro(api_key, sys_prompt, messages):
    contents = build_valid_gemini_contents(messages)
    payload = {
        "systemInstruction": {"parts": [{"text": sys_prompt}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.65,
            "maxOutputTokens": 16384,
        }
    }
    payload_str = json.dumps(payload, ensure_ascii=False)
    local_proxy = detect_local_proxy()

    # Каскад моделей от флагманской Pro до скоростной 2.5 Flash (если на бесплатном ключе лимит RPM для Pro исчерпан)
    last_err = ""
    for g_model in ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={api_key}"
        for use_proxy in ([False, True] if local_proxy else [False]):
            cmd = ["curl", "-s", "-L", "--connect-timeout", "8", "--max-time", "45",
                   "-X", "POST", url, "-H", "Content-Type: application/json", "-d", payload_str]
            if use_proxy and local_proxy:
                cmd = ["curl", "-s", "-L", "-x", local_proxy, "--connect-timeout", "8", "--max-time", "45",
                       "-X", "POST", url, "-H", "Content-Type: application/json", "-d", payload_str]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True)
                if not res.stdout.strip():
                    continue
                data = json.loads(res.stdout)
                if "candidates" in data and data["candidates"]:
                    parts = data["candidates"][0].get("content", {}).get("parts", [])
                    out_texts = [p.get("text", "") for p in parts if "text" in p and not p.get("thought", False)]
                    if not out_texts:
                        out_texts = [p.get("text", "") for p in parts if "text" in p]
                    ans = "
".join(out_texts).strip()
                    if ans:
                        return ans
                if "error" in data:
                    err_obj = data["error"]
                    msg = err_obj.get("message", str(err_obj))
                    last_err = msg
                    # Если гео-блок — пробуем со следующей итерацией через локальный прокси Happ
                    if "location is not supported" in msg.lower() and not use_proxy and local_proxy:
                        continue
                    # Если ключ неверный — сообщаем сразу
                    if "api_key_invalid" in msg.lower() or "api key not valid" in msg.lower():
                        return "❌ Сохранённый API-ключ отклонён сервером Google (API key not valid). Скопируй новый ключ на aistudio.google.com/apikey и нажми «🔑 PRO» -> «📋 Вставить ключ»."
            except Exception as e:
                last_err = str(e)
                continue

    if "location is not supported" in last_err.lower():
        return "🌐 Сервер Google Gemini требует включённый VPN/прокси для твоего региона. Включи туннель в Happ и отправь сообщение снова!"
    if last_err:
        return f"⚠ Ответ сервера Google API: {last_err}"
    return None

def query_gemini(messages, session_topic=""):
    topic_ctx = f" Тема текущего чата: «{session_topic}»." if session_topic else ""
    sys_prompt = GEMINI_PERSONA_PROMPT + topic_ctx

    gkey = get_saved_gemini_key()
    if gkey:
        ans_pro = query_native_google_gemini_pro(gkey, sys_prompt, messages)
        if ans_pro:
            return ans_pro

    # Если ключа нет вообще — используем бесключевой шлюз
    seed = random.randint(10000, 999999)
    payload = {
        "model": "openai-large",
        "seed": seed,
        "messages": [{"role": "system", "content": sys_prompt}] + messages[-8:],
    }
    try:
        res = subprocess.run(
            ["curl", "-s", "-L", "--connect-timeout", "8", "--max-time", "35",
             "-X", "POST", "https://text.pollinations.ai/openai",
             "-H", "Content-Type: application/json",
             "-A", "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
             "-d", json.dumps(payload, ensure_ascii=False)],
            capture_output=True, text=True
        )
        if res.returncode == 0 and res.stdout.strip():
            raw = res.stdout.strip()
            try:
                data = json.loads(raw)
                if "choices" in data and data["choices"]:
                    content = data["choices"][0].get("message", {}).get("content", "").strip()
                    if content and not is_rate_limited_or_bad(content):
                        return content
            except Exception:
                if not is_rate_limited_or_bad(raw):
                    return raw
    except Exception:
        pass

    return "⏳ Бесключевой канал перегружен. Нажми кнопку «🔑» сверху, чтобы подключить прямой ключ Google AI Studio."


class OverlayWidgetCard:
    def __init__(self, app, wid, state_dict, build_body_fn, is_standalone=False, extra_hdr_btns=None):
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
        self.frame.add_css_class("widget-frame-top" if (is_standalone or wid == "notif") else "widget-frame")
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
        drag_box.set_has_tooltip(False)
        hdr.append(drag_box)

        if not is_standalone:
            move_gest = Gtk.GestureDrag.new()
            move_gest.set_button(1)
            move_gest.connect("drag-begin", self.on_move_begin)
            move_gest.connect("drag-update", self.on_move_update)
            move_gest.connect("drag-end", self.on_move_end)
            drag_box.add_controller(move_gest)

        if extra_hdr_btns:
            for b in extra_hdr_btns:
                b.set_has_tooltip(False)
                hdr.append(b)

        if wid != "notif":
            self.pin_btn = Gtk.Button(label="󰐃" if not is_standalone else "✕")
            self.pin_btn.add_css_class("w-pin-active" if is_standalone else "w-hdr-btn")
            self.pin_btn.set_has_tooltip(False)
            self.pin_btn.connect("clicked", self.on_toggle_pin_top)
            hdr.append(self.pin_btn)

            if not is_standalone:
                col_btn = Gtk.Button(label="—")
                col_btn.add_css_class("w-hdr-btn")
                col_btn.set_has_tooltip(False)
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
            grip_box.set_has_tooltip(False)

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
        f_btn    = max(9,  int(round(10.2 * scale)))
        f_cal_d  = max(9,  int(round(11.0 * scale)))
        f_cal_w  = max(8,  int(round(9.5  * scale)))
        f_track  = max(10, int(round(11.5 * scale)))
        f_artist = max(9,  int(round(10.0 * scale)))
        pad_v    = max(2,  int(round(2.5  * scale)))
        pad_h    = max(4,  int(round(5.5  * scale)))
        cell_w   = max(20, int(round(26.0 * scale)))
        cell_h   = max(16, int(round(20.0 * scale)))

        css = f"""
        .wscale-{self.wid} .widget-title {{ font-size: {f_title}px; }}
        .wscale-{self.wid} .chat-view,
        .wscale-{self.wid} .notes-view,
        .wscale-{self.wid} entry.compact-entry {{ font-size: {f_text}px; }}
        .wscale-{self.wid} button.mini-btn,
        .wscale-{self.wid} button.del-btn {{ font-size: {f_btn}px; padding: {pad_v}px {pad_h}px; min-height: {int(20 * scale)}px; }}
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
        is_col = bool(cfg.get("collapsed", False)) and not self.is_standalone
        eff_h = 26 if is_col else h
        x = max(4, min(W_MON - w - 4, int(cfg.get("x", 18))))
        y = max(36, min(H_MON - eff_h - 4, int(cfg.get("y", 46))))

        if not self.is_standalone:
            self.frame.set_margin_start(x)
            self.frame.set_margin_top(y)

        self.body_wrap.set_visible(not is_col)
        self.frame.set_size_request(w, eff_h)
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
        cfg["x"] = max(4, min(W_MON - int(cfg["w"]) - 4, nx))
        cfg["y"] = max(36, min(H_MON - 40, ny))
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
        max_w = max(240, W_MON - int(cfg.get("x", 18)) - 6)
        max_h = max(140, H_MON - int(cfg.get("y", 46)) - 6)
        cfg["w"] = max(int(cfg.get("min_w", 210)), min(max_w, nw))
        cfg["h"] = max(int(cfg.get("min_h", 110)), min(max_h, nh))
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

class StudioDesktopApp(Gtk.Application):
    def __init__(self):
        app_id = f"org.alpora.PinWidget.{SINGLE_PIN_WID}.{os.getpid()}" if SINGLE_PIN_WID else "org.alpora.WorkDeckLayer"
        super().__init__(application_id=app_id, flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.st = load_widgets_state()
        self.cards = {}
        self.pinned = self.load_pinned()
        self.hidden_notifs = self.load_hidden_notifs()
        self.last_pin_mtime = 0

        self.chats_data = self.load_chats_db()
        self.ai_busy_sessions = set()

        self.notes_data = self.load_notes_db()
        self.updating_notes_ui = False

        now = datetime.date.today()
        self.cal_year, self.cal_month = now.year, now.month
        self.last_art_path = ""
        self.updating_vol_ui = False
        self.notif_card = None

        self.bg_surface = None
        if SINGLE_PIN_WID is None and os.path.isfile(BG_PNG):
            try:
                self.bg_surface = cairo.ImageSurface.create_from_png(BG_PNG)
            except Exception:
                self.bg_surface = None

        if SINGLE_PIN_WID is None:
            atexit.register(lambda: save_widgets_state(self.st))
            for sig_num in (signal.SIGTERM, signal.SIGINT):
                try:
                    signal.signal(sig_num, self._on_exit_signal)
                except Exception:
                    pass

    def _on_exit_signal(self, *_args):
        save_widgets_state(self.st)
        sys.exit(0)

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

    def load_hidden_notifs(self):
        try: return set(json.load(open(HIDDEN_NOTIF, encoding="utf-8"))) if os.path.isfile(HIDDEN_NOTIF) else set()
        except Exception: return set()

    def save_hidden_notifs(self):
        try: json.dump(sorted(list(self.hidden_notifs))[-200:], open(HIDDEN_NOTIF, "w", encoding="utf-8"))
        except Exception: pass

    def load_chats_db(self):
        try:
            if os.path.isfile(CHATS_DB):
                d = json.load(open(CHATS_DB, encoding="utf-8"))
                if isinstance(d, dict) and d.get("sessions"):
                    return d
        except Exception:
            pass

        default_db = {
            "active_idx": 0,
            "sessions": [
                {
                    "id": "gamedev",
                    "title": "🎮 Разработка игры",
                    "messages": [{"role": "assistant", "content": "Привет, Денис! Я обновлён до Gemini 2.5 Pro. Готов помогать с твоим 2D rogue-платформером на Pygame, логикой врагов и архитектурой кода."}],
                },
                {
                    "id": "linux-env",
                    "title": "🖥 Окружение Studio",
                    "messages": [{"role": "assistant", "content": "Чат «Окружение Studio» активен. Пиши сюда задачи по Hyprland, Waybar или скриптам."}],
                },
                {
                    "id": "college-code",
                    "title": "📚 Учёба и экзамены",
                    "messages": [{"role": "assistant", "content": "Чат «Учёба и экзамены» готов. Разберём задачи по Python, C#, C++, JS, Java, HTML или 1С."}],
                },
            ]
        }
        self.save_chats_db(default_db)
        return default_db

    def save_chats_db(self, data=None):
        if data is None:
            data = self.chats_data
        try:
            tmp_p = CHATS_DB + ".tmp"
            with open(tmp_p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_p, CHATS_DB)
        except Exception:
            pass

    def get_active_chat_session(self):
        sessions = self.chats_data.get("sessions", [])
        if not sessions:
            sessions.append({"id": "default", "title": "Основной чат", "messages": [{"role": "assistant", "content": "Новый чат готов к работе!"}]})
        idx = max(0, min(int(self.chats_data.get("active_idx", 0)), len(sessions) - 1))
        self.chats_data["active_idx"] = idx
        return idx, sessions[idx]

    def build_ai_widget(self, _card):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        # Верхняя панель: ◀ | 💬 Название (1/N) ▾ | ▶ | + | ✕ | 🔑
        chat_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)

        b_prev_c = Gtk.Button(label="◀"); b_prev_c.add_css_class("mini-btn"); b_prev_c.set_has_tooltip(False)
        b_prev_c.connect("clicked", lambda _b: self.shift_chat_session(-1))
        chat_row.append(b_prev_c)

        self.chat_sel_btn = Gtk.Button(label="💬 Основной чат (1/1) ▾")
        self.chat_sel_btn.add_css_class("mini-btn"); self.chat_sel_btn.set_hexpand(True); self.chat_sel_btn.set_has_tooltip(False)
        self.chat_sel_btn.connect("clicked", self.on_open_chats_rofi_menu)
        rc_c = Gtk.GestureClick.new(); rc_c.set_button(3)
        rc_c.connect("pressed", lambda *_a: self.shift_chat_session(1))
        self.chat_sel_btn.add_controller(rc_c)
        chat_row.append(self.chat_sel_btn)

        b_next_c = Gtk.Button(label="▶"); b_next_c.add_css_class("mini-btn"); b_next_c.set_has_tooltip(False)
        b_next_c.connect("clicked", lambda _b: self.shift_chat_session(1))
        chat_row.append(b_next_c)

        b_new_c = Gtk.Button(label="+"); b_new_c.add_css_class("mini-btn"); b_new_c.set_has_tooltip(False)
        b_new_c.connect("clicked", self.on_create_new_chat_dialog)
        chat_row.append(b_new_c)

        b_del_c = Gtk.Button(label="✕"); b_del_c.add_css_class("del-btn"); b_del_c.set_has_tooltip(False)
        b_del_c.connect("clicked", self.on_delete_current_chat_btn)
        rc_del_c = Gtk.GestureClick.new(); rc_del_c.set_button(3)
        rc_del_c.connect("pressed", lambda *_a: self.on_open_delete_old_chats_menu())
        b_del_c.add_controller(rc_del_c)
        chat_row.append(b_del_c)

        # Кнопка подключения прямого ключа Gemini 2.5 Pro API
        self.b_key = Gtk.Button(label="🔑 PRO" if get_saved_gemini_key() else "🔑"); self.b_key.add_css_class("mini-btn"); self.b_key.set_has_tooltip(False)
        b_key = self.b_key
        b_key.connect("clicked", self.on_set_gemini_key_dialog)
        chat_row.append(b_key)

        box.append(chat_row)

        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.set_hexpand(True)
        self.chat_tv = Gtk.TextView()
        self.chat_tv.set_editable(False); self.chat_tv.set_cursor_visible(False)
        self.chat_tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.chat_tv.add_css_class("chat-view")
        self.chat_buf = self.chat_tv.get_buffer()
        sc.set_child(self.chat_tv)
        box.append(sc)

        in_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.ai_entry = Gtk.Entry()
        self.ai_entry.add_css_class("compact-entry"); self.ai_entry.set_hexpand(True); self.ai_entry.set_has_tooltip(False)
        self.ai_entry.set_placeholder_text("Напиши мне вопрос или задачу (Enter)...")
        self.ai_entry.connect("activate", self.on_send_ai_msg)
        in_row.append(self.ai_entry)

        b_send = Gtk.Button(label="➤"); b_send.add_css_class("mini-btn"); b_send.set_has_tooltip(False)
        b_send.connect("clicked", self.on_send_ai_msg)
        in_row.append(b_send)

        b_copy = Gtk.Button(label="󰆏"); b_copy.add_css_class("mini-btn"); b_copy.set_has_tooltip(False)
        b_copy.connect("clicked", self.on_copy_last_ai)
        in_row.append(b_copy)

        b_clr = Gtk.Button(label="󰩺"); b_clr.add_css_class("mini-btn"); b_clr.set_has_tooltip(False)
        b_clr.connect("clicked", self.on_clear_ai_chat)
        in_row.append(b_clr)

        box.append(in_row)
        self.render_chat_log()
        return box

    def on_set_gemini_key_dialog(self, _b):
        def _worker():
            has_k = os.path.isfile(GEM_KEY_FILE) and bool(open(GEM_KEY_FILE).read().strip())
            st_lbl = "АКТИВЕН ПРЯМОЙ GEMINI 2.5 PRO" if has_k else "ПУБЛИЧНЫЙ ШЛЮЗ"
            ch = rofi_prompt(f"🔑 GEMINI 2.5 PRO [{st_lbl}]", [
                "📋 Вставить API-ключ из буфера обмена (Ctrl+C -> клик сюда)",
                "🌐 Открыть Google AI Studio в браузере (получить бесплатный ключ)",
                "🗑 Удалить ключ и вернуться на публичный шлюз",
            ])
            if not ch:
                return
            if "Вставить API-ключ" in ch:
                try:
                    clip = subprocess.check_output(["wl-paste", "-n"], text=True, stderr=subprocess.DEVNULL).strip()
                except Exception:
                    clip = ""
                if clip and len(clip) > 15:
                    open(GEM_KEY_FILE, "w", encoding="utf-8").write( re.sub(r"[^A-Za-z0-9_-]", "", clip) )
                    GLib.idle_add(self.b_key.set_label, "🔑 PRO")
                    self.spawn_raw("notify-send -a cyber-kb '✦ GEMINI 2.5 PRO' 'Прямой ключ из буфера обмена подключён!'")
                else:
                    manual = rofi_prompt("Вставьте ключ AIzaSy...", [""])
                    if manual.strip():
                        open(GEM_KEY_FILE, "w", encoding="utf-8").write( re.sub(r"[^A-Za-z0-9_-]", "", manual) )
                        GLib.idle_add(self.b_key.set_label, "🔑 PRO")
                        self.spawn_raw("notify-send -a cyber-kb '✦ GEMINI 2.5 PRO' 'Прямой ключ успешно подключён!'")
            elif "Открыть Google AI Studio" in ch:
                self.spawn_raw("xdg-open 'https://aistudio.google.com/apikey'")
            elif "Удалить ключ" in ch:
                if os.path.isfile(GEM_KEY_FILE):
                    os.remove(GEM_KEY_FILE)
                self.spawn_raw("notify-send -a cyber-kb '✦ GEMINI' 'Включён публичный шлюз'")
            elif ch.strip().startswith("AIza"):
                open(GEM_KEY_FILE, "w", encoding="utf-8").write(ch.strip())
                self.spawn_raw("notify-send -a cyber-kb '✦ GEMINI 2.5 PRO' 'Прямой ключ успешно подключён!'")
        threading.Thread(target=_worker, daemon=True).start()

    def on_delete_current_chat_btn(self, _b):
        idx, _ = self.get_active_chat_session()
        self._finish_delete_chat(idx)

    def on_open_delete_old_chats_menu(self):
        def _worker():
            sessions = self.chats_data.get("sessions", [])
            cur_idx = int(self.chats_data.get("active_idx", 0))
            lines = ["🔥 Удалить ВСЕ старые чаты, кроме текущего"]
            for i, s in enumerate(sessions):
                tag = " [ТЕКУЩИЙ]" if i == cur_idx else ""
                clean_t = re.sub(r"^[💬\s]+", "", s.get("title", "")).strip() or "Чат"
                lines.append(f"{i+1}. 🗑 Удалить чат «{clean_t}» ({len(s.get('messages', []))} сообщ.){tag}")
            ch = rofi_prompt("🗑 УДАЛЕНИЕ СТАРЫХ ЧАТОВ", lines)
            if not ch:
                return
            if "Удалить ВСЕ старые" in ch:
                GLib.idle_add(self._finish_keep_only_current_chat)
            elif "." in ch:
                try:
                    sel_i = int(ch.split(".", 1)[0]) - 1
                    if 0 <= sel_i < len(sessions):
                        GLib.idle_add(self._finish_delete_chat, sel_i)
                except Exception:
                    pass
        threading.Thread(target=_worker, daemon=True).start()

    def _finish_keep_only_current_chat(self):
        _, cur_sess = self.get_active_chat_session()
        self.chats_data["sessions"] = [cur_sess]
        self.chats_data["active_idx"] = 0
        self.save_chats_db()
        self.render_chat_log()
        return False

    def shift_chat_session(self, delta):
        sessions = self.chats_data.get("sessions", [])
        if not sessions: return
        self.chats_data["active_idx"] = (int(self.chats_data.get("active_idx", 0)) + delta) % len(sessions)
        self.save_chats_db()
        self.render_chat_log()

    def on_create_new_chat_dialog(self, _b):
        def _worker():
            title = rofi_prompt("💬 Название нового чата", ["🎮 Разработка игры", "🖥 Окружение Linux", "🐍 Скрипты и код", "📚 Учёба"])
            if title:
                GLib.idle_add(self._finish_create_chat, title)
        threading.Thread(target=_worker, daemon=True).start()

    def _finish_create_chat(self, title):
        clean_t = re.sub(r"^[💬\s]+", "", title).strip() or "Новый чат"
        self.chats_data["sessions"].append({
            "id": f"chat-{int(time.time())}",
            "title": clean_t,
            "messages": [{"role": "assistant", "content": f"Создан новый чат «{clean_t}». Слушаю тебя, Денис — какую задачу разбираем?"}],
        })
        self.chats_data["active_idx"] = len(self.chats_data["sessions"]) - 1
        self.save_chats_db()
        self.render_chat_log()
        return False

    def on_open_chats_rofi_menu(self, _b):
        def _worker():
            sessions = self.chats_data.get("sessions", [])
            cur_idx = int(self.chats_data.get("active_idx", 0))
            lines = []
            for i, s in enumerate(sessions):
                clean_t = re.sub(r"^[💬\s]+", "", s.get("title", "")).strip() or "Чат"
                lines.append(f"{i+1}. 💬 {clean_t}" + ("  [● АКТИВЕН]" if i == cur_idx else f"  ({len(s.get('messages', []))} сообщ.)"))
            lines += [
                "➕ Создать новый чат...",
                "✎ Переименовать текущий чат...",
                "🗑 Выбрать и удалить старые чаты...",
                "🔥 Удалить все старые чаты, кроме текущего",
            ]
            ch = rofi_prompt("💬 ЧАТЫ С GEMINI 2.5 PRO", lines)
            if not ch: return
            if "Создать новый" in ch:
                new_t = rofi_prompt("💬 Название нового чата", ["🎮 Новый проект"])
                if new_t: GLib.idle_add(self._finish_create_chat, new_t)
            elif "Переименовать" in ch:
                ren_t = rofi_prompt("✎ Новое название чата", [sessions[cur_idx]["title"]])
                if ren_t: GLib.idle_add(self._finish_rename_chat, cur_idx, ren_t)
            elif "Выбрать и удалить" in ch:
                self.on_open_delete_old_chats_menu()
            elif "Удалить все старые" in ch:
                GLib.idle_add(self._finish_keep_only_current_chat)
            elif "." in ch:
                try:
                    sel_i = int(ch.split(".", 1)[0]) - 1
                    if 0 <= sel_i < len(sessions): GLib.idle_add(self._finish_select_chat, sel_i)
                except Exception: pass
        threading.Thread(target=_worker, daemon=True).start()

    def _finish_select_chat(self, idx):
        self.chats_data["active_idx"] = idx
        self.save_chats_db(); self.render_chat_log()
        return False

    def _finish_rename_chat(self, idx, new_title):
        clean_t = re.sub(r"^[💬\s]+", "", new_title).strip() or "Чат"
        self.chats_data["sessions"][idx]["title"] = clean_t
        self.save_chats_db(); self.render_chat_log()
        return False

    def _finish_delete_chat(self, idx):
        if len(self.chats_data["sessions"]) > 1:
            self.chats_data["sessions"].pop(idx)
            self.chats_data["active_idx"] = max(0, min(idx, len(self.chats_data["sessions"]) - 1))
        else:
            self.chats_data["sessions"] = [{
                "id": f"chat-{int(time.time())}",
                "title": "Основной чат",
                "messages": [{"role": "assistant", "content": "Старый чат удалён. Готов к новой задаче!"}],
            }]
            self.chats_data["active_idx"] = 0
        self.save_chats_db()
        self.render_chat_log()
        return False

    def render_chat_log(self):
        idx, sess = self.get_active_chat_session()
        total_c = len(self.chats_data.get("sessions", []))
        clean_t = re.sub(r"^[💬\s]+", "", sess.get("title", "")).strip() or "Основной чат"
        if hasattr(self, "chat_sel_btn"):
            self.chat_sel_btn.set_label(f"💬 {clean_t[:16]} ({idx+1}/{total_c}) ▾")

        lines = []
        for msg in sess.get("messages", [])[-12:]:
            prefix = "▸ ВЫ:" if msg["role"] == "user" else "✦ Gemini 2.5 Pro:"
            lines.append(f"{prefix}\n{msg['content']}")
        if sess["id"] in self.ai_busy_sessions:
            lines.append("✦ Gemini 2.5 Pro:\n▪ анализирую и пишу ответ...")
        self.chat_buf.set_text("\n\n".join(lines))
        GLib.idle_add(self.scroll_chat_bottom)

    def scroll_chat_bottom(self):
        end_it = self.chat_buf.get_end_iter()
        mark = self.chat_buf.create_mark(None, end_it, False)
        self.chat_tv.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        return False

    def on_send_ai_msg(self, *_args):
        _, sess = self.get_active_chat_session()
        sid = sess["id"]
        if sid in self.ai_busy_sessions: return
        q = self.ai_entry.get_text().strip()
        if not q: return
        self.ai_entry.set_text("")
        sess.setdefault("messages", []).append({"role": "user", "content": q})
        self.save_chats_db()
        self.ai_busy_sessions.add(sid)
        self.render_chat_log()

        msgs_snapshot = list(sess["messages"])
        topic_title = re.sub(r"^[💬\s]+", "", sess.get("title", "")).strip()

        def worker():
            ans = query_gemini(msgs_snapshot, session_topic=topic_title)
            GLib.idle_add(self.on_ai_response_ready, sid, ans)

        threading.Thread(target=worker, daemon=True).start()

    def on_ai_response_ready(self, target_sid, ans):
        self.ai_busy_sessions.discard(target_sid)
        for s in self.chats_data.get("sessions", []):
            if s.get("id") == target_sid:
                s.setdefault("messages", []).append({"role": "assistant", "content": ans})
                break
        self.save_chats_db()
        self.render_chat_log()
        return False

    def on_copy_last_ai(self, _b):
        _, sess = self.get_active_chat_session()
        for msg in reversed(sess.get("messages", [])):
            if msg["role"] == "assistant":
                subprocess.run(["wl-copy"], input=msg["content"], text=True, stderr=subprocess.DEVNULL)
                self.spawn_raw("notify-send -a cyber-kb '✦ GEMINI 2.5 PRO' 'Ответ скопирован в буфер обмена'")
                break

    def on_clear_ai_chat(self, _b):
        _, sess = self.get_active_chat_session()
        clean_t = re.sub(r"^[💬\s]+", "", sess.get("title", "")).strip() or "Основной чат"
        sess["messages"] = [{"role": "assistant", "content": f"История чата «{clean_t}» очищена. О чём поговорим?"}]
        self.save_chats_db()
        self.render_chat_log()

    # ==========================================================================
    # 2. ВИДЖЕТ ЗАМЕТОК
    # ==========================================================================
    def load_notes_db(self):
        try:
            if os.path.isfile(NOTES_PAGES):
                d = json.load(open(NOTES_PAGES, encoding="utf-8"))
                if isinstance(d, dict) and d.get("pages"):
                    return d
        except Exception:
            pass

        first_text = "[x] Настроить серое окружение студии\n[ ] Доработать физику прыжка в игре\n[ ] Подготовить зачёты\n"
        if os.path.isfile(NOTES_FILE):
            try:
                raw_t = open(NOTES_FILE, "r", encoding="utf-8").read().strip()
                if raw_t: first_text = raw_t + "\n"
            except Exception: pass

        default_notes = {
            "active_idx": 0,
            "pages": [
                {"id": "game-notes", "title": "🎮 Разработка игры", "content": first_text},
                {"id": "env-notes", "title": "🖥 Окружение Linux", "content": "[x] Waybar с ползунками и 3 режимами питания\n[x] Виджет с Gemini 2.5 Pro и удалением старых чатов\n"},
                {"id": "study-notes", "title": "📚 Учёба и зачёты", "content": "[ ] Зачёты в декабре (Python, C#, C++)\n"},
            ]
        }
        self.save_notes_db(default_notes)
        return default_notes

    def save_notes_db(self, data=None):
        if data is None: data = self.notes_data
        try:
            tmp_p = NOTES_PAGES + ".tmp"
            with open(tmp_p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_p, NOTES_PAGES)
        except Exception: pass

    def get_active_note_page(self):
        pages = self.notes_data.get("pages", [])
        if not pages:
            pages.append({"id": "default", "title": "Заметка 1", "content": ""})
        idx = max(0, min(int(self.notes_data.get("active_idx", 0)), len(pages) - 1))
        self.notes_data["active_idx"] = idx
        return idx, pages[idx]

    def build_notes_widget(self, _card):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        nav_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        b_prev_n = Gtk.Button(label="◀"); b_prev_n.add_css_class("mini-btn"); b_prev_n.set_has_tooltip(False)
        b_prev_n.connect("clicked", lambda _b: self.shift_note_page(-1))
        nav_row.append(b_prev_n)

        self.note_sel_btn = Gtk.Button(label="📑 Заметка ▾")
        self.note_sel_btn.add_css_class("mini-btn"); self.note_sel_btn.set_hexpand(True); self.note_sel_btn.set_has_tooltip(False)
        self.note_sel_btn.connect("clicked", self.on_open_notes_rofi_menu)
        rc_n = Gtk.GestureClick.new(); rc_n.set_button(3)
        rc_n.connect("pressed", lambda *_a: self.shift_note_page(1))
        self.note_sel_btn.add_controller(rc_n)
        nav_row.append(self.note_sel_btn)

        b_next_n = Gtk.Button(label="▶"); b_next_n.add_css_class("mini-btn"); b_next_n.set_has_tooltip(False)
        b_next_n.connect("clicked", lambda _b: self.shift_note_page(1))
        nav_row.append(b_next_n)

        b_new_n = Gtk.Button(label="+"); b_new_n.add_css_class("mini-btn"); b_new_n.set_has_tooltip(False)
        b_new_n.connect("clicked", self.on_create_new_note_dialog)
        nav_row.append(b_new_n)

        b_del_n = Gtk.Button(label="✕"); b_del_n.add_css_class("del-btn"); b_del_n.set_has_tooltip(False)
        b_del_n.connect("clicked", self.on_delete_current_note_btn)
        rc_del_n = Gtk.GestureClick.new(); rc_del_n.set_button(3)
        rc_del_n.connect("pressed", lambda *_a: self.on_open_delete_old_notes_menu())
        b_del_n.add_controller(rc_del_n)
        nav_row.append(b_del_n)

        box.append(nav_row)

        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.set_hexpand(True)
        tv = Gtk.TextView(); tv.add_css_class("notes-view"); tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR); tv.set_has_tooltip(False)
        self.notes_buf = tv.get_buffer()
        self.notes_buf.connect("changed", self.on_notes_buffer_changed)
        sc.set_child(tv); box.append(sc)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        b_add = Gtk.Button(label="+ Задача"); b_add.add_css_class("mini-btn"); b_add.set_hexpand(True); b_add.set_has_tooltip(False)
        b_add.connect("clicked", lambda _b: self.notes_buf.insert(self.notes_buf.get_end_iter(), "\n[ ] "))
        b_cp = Gtk.Button(label="󰆏 Копировать"); b_cp.add_css_class("mini-btn"); b_cp.set_hexpand(True); b_cp.set_has_tooltip(False)
        b_cp.connect("clicked", lambda _b: subprocess.run(["wl-copy"], input=self.notes_buf.get_text(self.notes_buf.get_start_iter(), self.notes_buf.get_end_iter(), False), text=True))
        b_clr = Gtk.Button(label="󰩺"); b_clr.add_css_class("mini-btn"); b_clr.set_has_tooltip(False)
        b_clr.connect("clicked", lambda _b: self.notes_buf.set_text(""))
        row.append(b_add); row.append(b_cp); row.append(b_clr)
        box.append(row)

        self.refresh_note_page_ui()
        return box

    def on_delete_current_note_btn(self, _b):
        idx, _ = self.get_active_note_page()
        self._finish_delete_note(idx)

    def on_open_delete_old_notes_menu(self):
        def _worker():
            pages = self.notes_data.get("pages", [])
            cur_idx = int(self.notes_data.get("active_idx", 0))
            lines = ["🔥 Удалить ВСЕ старые вкладки заметок, кроме текущей"]
            for i, p in enumerate(pages):
                tag = " [ТЕКУЩАЯ]" if i == cur_idx else ""
                clean_t = re.sub(r"^[📑\s]+", "", p.get("title", "")).strip() or "Заметка"
                lines.append(f"{i+1}. 🗑 Удалить заметку «{clean_t}»{tag}")
            ch = rofi_prompt("🗑 УДАЛЕНИЕ СТАРЫХ ЗАМЕТОК", lines)
            if not ch:
                return
            if "Удалить ВСЕ старые" in ch:
                GLib.idle_add(self._finish_keep_only_current_note)
            elif "." in ch:
                try:
                    sel_i = int(ch.split(".", 1)[0]) - 1
                    if 0 <= sel_i < len(pages):
                        GLib.idle_add(self._finish_delete_note, sel_i)
                except Exception:
                    pass
        threading.Thread(target=_worker, daemon=True).start()

    def _finish_keep_only_current_note(self):
        _, cur_page = self.get_active_note_page()
        self.notes_data["pages"] = [cur_page]
        self.notes_data["active_idx"] = 0
        self.save_notes_db()
        self.refresh_note_page_ui()
        return False

    def on_notes_buffer_changed(self, buf):
        if self.updating_notes_ui: return
        _, page = self.get_active_note_page()
        txt = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        page["content"] = txt
        self.save_notes_db()
        try: open(NOTES_FILE, "w", encoding="utf-8").write(txt)
        except Exception: pass

    def refresh_note_page_ui(self):
        idx, page = self.get_active_note_page()
        total_p = len(self.notes_data.get("pages", []))
        clean_t = re.sub(r"^[📑\s]+", "", page.get("title", "")).strip() or "Заметка"
        if hasattr(self, "note_sel_btn"):
            self.note_sel_btn.set_label(f"📑 {clean_t[:16]} ({idx+1}/{total_p}) ▾")
        if hasattr(self, "notes_buf"):
            self.updating_notes_ui = True
            self.notes_buf.set_text(page.get("content", ""))
            self.updating_notes_ui = False

    def shift_note_page(self, delta):
        pages = self.notes_data.get("pages", [])
        if not pages: return
        self.notes_data["active_idx"] = (int(self.notes_data.get("active_idx", 0)) + delta) % len(pages)
        self.save_notes_db(); self.refresh_note_page_ui()

    def on_create_new_note_dialog(self, _b):
        def _worker():
            title = rofi_prompt("📑 Название новой заметки", ["🎮 Идеи для игры", "🖥 Команды", "📚 Конспект"])
            if title: GLib.idle_add(self._finish_create_note, title)
        threading.Thread(target=_worker, daemon=True).start()

    def _finish_create_note(self, title):
        clean_t = re.sub(r"^[📑\s]+", "", title).strip() or "Новая заметка"
        self.notes_data["pages"].append({"id": f"note-{int(time.time())}", "title": clean_t, "content": f"# {clean_t}\n[ ] "})
        self.notes_data["active_idx"] = len(self.notes_data["pages"]) - 1
        self.save_notes_db(); self.refresh_note_page_ui()
        return False

    def on_open_notes_rofi_menu(self, _b):
        def _worker():
            pages = self.notes_data.get("pages", [])
            cur_idx = int(self.notes_data.get("active_idx", 0))
            lines = []
            for i, p in enumerate(pages):
                clean_t = re.sub(r"^[📑\s]+", "", p.get("title", "")).strip() or "Заметка"
                lines.append(f"{i+1}. 📑 {clean_t}" + ("  [● АКТИВНА]" if i == cur_idx else ""))
            lines += [
                "➕ Создать новую вкладку заметок...",
                "✎ Переименовать текущую заметку...",
                "🗑 Выбрать и удалить старые заметки...",
                "🔥 Удалить все старые заметки, кроме текущей",
            ]
            ch = rofi_prompt("📑 ВКЛАДКИ ЗАМЕТОК", lines)
            if not ch: return
            if "Создать новую" in ch:
                new_t = rofi_prompt("📑 Название новой заметки", ["📌 Новая заметка"])
                if new_t: GLib.idle_add(self._finish_create_note, new_t)
            elif "Переименовать" in ch:
                ren_t = rofi_prompt("✎ Новое название заметки", [pages[cur_idx]["title"]])
                if ren_t: GLib.idle_add(self._finish_rename_note, cur_idx, ren_t)
            elif "Выбрать и удалить" in ch:
                self.on_open_delete_old_notes_menu()
            elif "Удалить все старые" in ch:
                GLib.idle_add(self._finish_keep_only_current_note)
            elif "." in ch:
                try:
                    sel_i = int(ch.split(".", 1)[0]) - 1
                    if 0 <= sel_i < len(pages): GLib.idle_add(self._finish_select_note, sel_i)
                except Exception: pass
        threading.Thread(target=_worker, daemon=True).start()

    def _finish_select_note(self, idx):
        self.notes_data["active_idx"] = idx
        self.save_notes_db(); self.refresh_note_page_ui()
        return False

    def _finish_rename_note(self, idx, new_title):
        clean_t = re.sub(r"^[📑\s]+", "", new_title).strip() or "Заметка"
        self.notes_data["pages"][idx]["title"] = clean_t
        self.save_notes_db(); self.refresh_note_page_ui()
        return False

    def _finish_delete_note(self, idx):
        if len(self.notes_data["pages"]) > 1:
            self.notes_data["pages"].pop(idx)
            self.notes_data["active_idx"] = max(0, min(idx, len(self.notes_data["pages"]) - 1))
        else:
            self.notes_data["pages"] = [{"id": f"note-{int(time.time())}", "title": "Основная заметка", "content": "[ ] "}]
            self.notes_data["active_idx"] = 0
        self.save_notes_db()
        self.refresh_note_page_ui()
        return False

    def build_calendar_widget(self, card):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_hexpand(True); box.set_vexpand(True)

        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.cal_title_lbl = Gtk.Label(label="", xalign=0, hexpand=True, css_classes=["widget-title"])
        nav.append(self.cal_title_lbl)
        for sym, d in [("◀", -1), ("●", 0), ("▶", 1)]:
            b = Gtk.Button(label=sym); b.add_css_class("mini-btn"); b.set_has_tooltip(False)
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
            b = Gtk.Button(label=lbl); b.add_css_class("mini-btn"); b.set_hexpand(True); b.set_has_tooltip(False)
            b.connect("clicked", lambda _b, c=cmd: self.spawn_raw(c))
            ctrl_r.append(b)
        meta_v.append(ctrl_r)
        top_h.append(meta_v)
        box.append(top_h)

        v_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        v_row.append(Gtk.Label(label="󰕾 Медиа", css_classes=["mono-sub"]))
        _, cur_mv = get_media_sink_inputs()
        init_v = cur_mv if cur_mv is not None else 85.0
        self.media_vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.media_vol_scale.set_draw_value(False); self.media_vol_scale.set_hexpand(True); self.media_vol_scale.set_value(init_v); self.media_vol_scale.set_has_tooltip(False)
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
        if self.updating_vol_ui: return
        val = int(scale.get_value())
        self.media_vol_lbl.set_label(f"{val}%")
        set_media_stream_only_volume(val)

    def build_notif_widget_body(self, _card):
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        body.set_hexpand(True); body.set_vexpand(True)
        sc = Gtk.ScrolledWindow(); sc.set_vexpand(True); sc.set_hexpand(True)
        self.notif_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        sc.set_child(self.notif_list_box)
        body.append(sc)
        return body

    def on_clear_all_notifications(self, *_args):
        try:
            raw = subprocess.check_output(["makoctl", "history"], text=True, stderr=subprocess.DEVNULL)
            for blk in raw.split("Notification "):
                if blk.strip():
                    nid = blk.strip().splitlines()[0].split(":", 1)[0].strip()
                    self.hidden_notifs.add(nid)
            self.save_hidden_notifs()
        except Exception: pass
        subprocess.run(["makoctl", "dismiss", "-a"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-x", "mako"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["mako"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.refresh_notif_list()

    def on_dismiss_single_notif(self, _b, nid):
        self.hidden_notifs.add(nid)
        self.save_hidden_notifs()
        subprocess.run(["makoctl", "dismiss", "-n", str(nid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.refresh_notif_list()

    def refresh_notif_list(self):
        if not hasattr(self, "notif_list_box"): return
        while True:
            c = self.notif_list_box.get_first_child()
            if c is None: break
            self.notif_list_box.remove(c)
        try: raw = subprocess.check_output(["makoctl", "history"], text=True, stderr=subprocess.DEVNULL)
        except Exception: raw = ""

        blocks = []
        for b in raw.split("Notification "):
            if not b.strip(): continue
            nid = b.strip().splitlines()[0].split(":", 1)[0].strip()
            if nid not in self.hidden_notifs:
                blocks.append((nid, b.strip()))

        if not blocks:
            lbl = Gtk.Label(label="󰂜  Список уведомлений чист", css_classes=["mono-sub"])
            lbl.set_valign(Gtk.Align.CENTER); lbl.set_vexpand(True)
            self.notif_list_box.append(lbl)
            return

        for nid, blk in blocks[:20]:
            lines = blk.splitlines()
            head = lines[0] if lines else "Уведомление"
            summary = head.split(":", 1)[1].strip() if ":" in head else head
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("notif-card")
            top_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            t_l = Gtk.Label(label=f"▣  {summary[:48]}", xalign=0, hexpand=True, css_classes=["notif-title"])
            t_l.set_ellipsize(Pango.EllipsizeMode.END)
            top_r.append(t_l)
            del_b = Gtk.Button(label="✕"); del_b.add_css_class("w-hdr-btn"); del_b.set_has_tooltip(False)
            del_b.connect("clicked", self.on_dismiss_single_notif, nid)
            top_r.append(del_b)
            card.append(top_r)
            for ln in lines[1:4]:
                if ln.strip():
                    b_l = Gtk.Label(label=ln.strip()[:70], xalign=0, css_classes=["notif-body"])
                    b_l.set_wrap(True); card.append(b_l)
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
            db = Gtk.Button(); db.add_css_class("dock-item"); db.set_has_tooltip(False)
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
            try: prov.load_from_string(open(css_p, "r", encoding="utf-8").read())
            except Exception: pass
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

        for wid, b_fn in builders.items():
            card = OverlayWidgetCard(self, wid, self.st, b_fn, is_standalone=False)
            self.cards[wid] = card
            overlay.add_overlay(card.frame)

        b_dnd = Gtk.Button(label="󰂛 DND"); b_dnd.add_css_class("w-hdr-btn"); b_dnd.set_has_tooltip(False)
        b_dnd.connect("clicked", lambda _b: self.spawn_raw("makoctl mode -t do-not-disturb"))

        b_clr_all = Gtk.Button(label="󰩺 Очистить всё"); b_clr_all.add_css_class("w-hdr-btn"); b_clr_all.set_has_tooltip(False)
        b_clr_all.connect("clicked", self.on_clear_all_notifications)

        b_hide_n = Gtk.Button(label="✕"); b_hide_n.add_css_class("w-hdr-btn"); b_hide_n.set_has_tooltip(False)
        b_hide_n.connect("clicked", lambda _b: self.notif_card.frame.set_visible(False))

        self.notif_card = OverlayWidgetCard(
            self, "notif", self.st, self.build_notif_widget_body,
            is_standalone=False, extra_hdr_btns=[b_dnd, b_clr_all, b_hide_n]
        )
        self.notif_card.frame.set_visible(False)
        overlay.add_overlay(self.notif_card.frame)

        dock_align = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dock_align.set_valign(Gtk.Align.END); dock_align.set_halign(Gtk.Align.CENTER)
        dock_align.set_margin_bottom(12)
        dock_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dock_wrap.add_css_class("bottom-dock")
        self.dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dock_wrap.append(self.dock_box)

        add_b = Gtk.Button(label="+"); add_b.add_css_class("dock-item"); add_b.set_has_tooltip(False)
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
            if self.notif_card:
                vis = not self.notif_card.frame.get_visible()
                if vis: self.refresh_notif_list()
                self.notif_card.frame.set_visible(vis)

        try:
            mt = os.path.getmtime(PIN_FILE) if os.path.isfile(PIN_FILE) else 0
            if mt != self.last_pin_mtime:
                self.pinned = self.load_pinned()
                self.populate_dock()
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
