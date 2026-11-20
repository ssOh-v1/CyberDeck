#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
except Exception:
    pass

import os, sys, re, math, time, glob, signal, shutil, threading, subprocess

signal.signal(signal.SIGHUP, signal.SIG_IGN)

os.environ["XCURSOR_THEME"] = "GameDev-Cursor-Grey"
os.environ["XCURSOR_SIZE"] = "28"
os.environ["GTK_THEME"] = "Adwaita:dark"

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gio, Pango, GdkPixbuf, Gtk4LayerShell
import cairo

# Убираем LD_PRELOAD после инициализации LayerShell, чтобы дочерние команды (wl-copy, cliphist) запускались чисто
os.environ.pop("LD_PRELOAD", None)

UID = os.getuid()
THUMB_DIR = f"/tmp/studio_clip_thumbs_{UID}"
PID_FILE  = f"/tmp/studio_clipboard_{UID}.pid"
os.makedirs(THUMB_DIR, exist_ok=True)

IMG_EXTS = ("png", "jpg", "jpeg", "webp", "bmp", "gif")

CLIP_CSS = """
window.clip-win {
    background-color: transparent;
}
.clip-shell {
    background-color: rgba(18, 19, 22, 0.97);
    border: 1px solid #343842;
    border-radius: 10px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
}
.clip-header {
    background-color: #16181c;
    border-bottom: 1px solid #262932;
    border-radius: 9px 9px 0 0;
    padding: 9px 12px;
}
.clip-title {
    color: #e6e9ef;
    font-family: "JetBrainsMono Nerd Font", monospace;
    font-size: 12px;
    font-weight: 700;
}
.clip-count {
    color: #8c939e;
    font-family: "JetBrainsMono Nerd Font", monospace;
    font-size: 11px;
    font-weight: 600;
}
.clip-search-wrap {
    padding: 8px 12px 4px 12px;
}
entry.clip-search {
    background-color: #17191e;
    color: #e6e9ef;
    border: 1px solid #2c303a;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: "Inter", sans-serif;
    font-size: 12.5px;
    min-height: 28px;
}
entry.clip-search:focus {
    border-color: #6c727d;
    background-color: #1a1d23;
}
.clip-list-pad {
    padding: 6px 12px 12px 12px;
}
.clip-card {
    background-color: #17191e;
    border: 1px solid #252830;
    border-radius: 8px;
    padding: 4px;
    transition: background-color 120ms ease, border-color 120ms ease;
}
.clip-card:hover {
    background-color: #1e2128;
    border-color: #4b515e;
}
button.clip-main-btn {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 6px 8px;
    border-radius: 6px;
}
button.clip-main-btn:hover,
button.clip-main-btn:active {
    background: transparent;
}
.clip-text-preview {
    color: #d4d8de;
    font-family: "Inter", sans-serif;
    font-size: 12.5px;
}
.clip-meta {
    color: #7c828f;
    font-family: "JetBrainsMono Nerd Font", monospace;
    font-size: 10px;
    font-weight: 600;
}
button.clip-hdr-btn {
    background-color: #1f2229;
    color: #c8ccd2;
    border: 1px solid #323640;
    border-radius: 5px;
    padding: 3px 9px;
    min-height: 24px;
    font-family: "Inter", sans-serif;
    font-size: 11px;
    font-weight: 600;
}
button.clip-hdr-btn:hover {
    background-color: #2b303a;
    border-color: #6c727d;
    color: #ffffff;
}
button.clip-wipe-btn {
    background-color: #211a1d;
    color: #ccaab0;
    border: 1px solid #423035;
    border-radius: 5px;
    padding: 3px 9px;
    min-height: 24px;
    font-family: "Inter", sans-serif;
    font-size: 11px;
    font-weight: 600;
}
button.clip-wipe-btn:hover {
    background-color: #3d262b;
    border-color: #8a555f;
    color: #ffffff;
}
button.clip-del-btn {
    background-color: #1b191d;
    color: #9e8388;
    border: 1px solid #2e2629;
    border-radius: 6px;
    padding: 0px 8px;
    min-width: 28px;
    min-height: 28px;
    font-size: 11px;
    font-weight: 700;
}
button.clip-del-btn:hover {
    background-color: #3d262b;
    border-color: #8a555f;
    color: #ffffff;
}
.clip-empty {
    color: #7c828f;
    font-family: "JetBrainsMono Nerd Font", monospace;
    font-size: 12px;
}
tooltip, tooltip * {
    opacity: 0;
    background: transparent;
    border: none;
    box-shadow: none;
}
"""

def parse_entry(raw_line):
    parts = raw_line.split("\t", 1)
    cid = parts[0].strip()
    body = parts[1] if len(parts) > 1 else raw_line
    m = re.match(r"^\[\[\s*binary data\s+(.+?)\s*\]\]$", body.strip(), re.I)
    if m:
        info = m.group(1).strip()
        low = info.lower()
        img_ext = next((e for e in IMG_EXTS if re.search(rf"\b{e}\b", low)), None)
        if img_ext:
            return {"id": cid, "raw": raw_line, "kind": "image", "ext": img_ext, "info": info}
        return {"id": cid, "raw": raw_line, "kind": "binary", "ext": "", "info": info}
    return {"id": cid, "raw": raw_line, "kind": "text", "text": body.strip()}

def get_cliphist_entries():
    try:
        p = subprocess.run(["cliphist", "list"], capture_output=True, text=True, timeout=2.5)
        if p.returncode != 0:
            return []
        return [parse_entry(ln) for ln in p.stdout.splitlines() if ln.strip()]
    except Exception:
        return []

def copy_entry_to_wayland(entry):
    try:
        dec = subprocess.run(
            ["cliphist", "decode"],
            input=entry["raw"].encode("utf-8"),
            capture_output=True,
            timeout=3.0,
        )
        if dec.returncode != 0:
            return
        cmd = ["wl-copy"]
        if entry["kind"] == "image":
            ext = "jpeg" if entry["ext"] in ("jpg", "jpeg") else entry["ext"]
            cmd += ["--type", f"image/{ext}"]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if proc.stdin:
            proc.stdin.write(dec.stdout)
            proc.stdin.close()
        time.sleep(0.06)
    except Exception:
        pass

def draw_rounded_rect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()

class ImagePreviewArea(Gtk.DrawingArea):
    def __init__(self, max_w=368, max_h=175):
        super().__init__()
        self.max_w = max_w
        self.max_h = max_h
        self.pixbuf = None
        self.loading = True
        self.set_size_request(max_w, 110)
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_draw_func(self.on_draw)

    def set_pixbuf(self, pb):
        self.loading = False
        self.pixbuf = pb
        if pb is not None:
            h = max(68, min(self.max_h, pb.get_height()))
            self.set_size_request(self.max_w, h)
        self.queue_draw()

    def on_draw(self, _area, cr, w, h, *_args):
        r = 6.0
        draw_rounded_rect(cr, 0.5, 0.5, w - 1, h - 1, r)
        cr.save()
        cr.clip()
        cr.set_source_rgb(0.075, 0.082, 0.098)
        cr.paint()

        if self.pixbuf is not None:
            pw, ph = self.pixbuf.get_width(), self.pixbuf.get_height()
            dx = (w - pw) * 0.5
            dy = (h - ph) * 0.5
            Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, dx, dy)
            cr.paint()
        else:
            cr.select_font_face("JetBrainsMono Nerd Font", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(11)
            cr.set_source_rgba(0.55, 0.58, 0.65, 0.85)
            txt = "Загрузка превью..." if self.loading else "Изображение"
            ext = cr.text_extents(txt)
            cr.move_to((w - ext.width) * 0.5, (h + ext.height) * 0.5)
            cr.show_text(txt)
        cr.restore()

        draw_rounded_rect(cr, 0.5, 0.5, w - 1, h - 1, r)
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.24, 0.27, 0.33, 0.95)
        cr.stroke()

class StudioClipboardApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=f"org.studio.Clipboard.{os.getpid()}", flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.entries = []
        self.cards = []
        self.preview_areas = {}
        self.stop_loader = False

    def do_activate(self):
        try:
            open(PID_FILE, "w").write(str(os.getpid()))
        except Exception:
            pass

        prov = Gtk.CssProvider()
        prov.load_from_string(CLIP_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 40
        )

        self.win = Gtk.ApplicationWindow(application=self, title="StudioClipboard")
        self.win.add_css_class("clip-win")
        self.win.set_default_size(465, 580)

        Gtk4LayerShell.init_for_window(self.win)
        Gtk4LayerShell.set_namespace(self.win, "studio-clipboard")
        Gtk4LayerShell.set_layer(self.win, Gtk4LayerShell.Layer.OVERLAY)
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.TOP, False)
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.BOTTOM, False)
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.LEFT, False)
        Gtk4LayerShell.set_anchor(self.win, Gtk4LayerShell.Edge.RIGHT, False)
        Gtk4LayerShell.set_exclusive_zone(self.win, -1)
        Gtk4LayerShell.set_keyboard_mode(self.win, Gtk4LayerShell.KeyboardMode.EXCLUSIVE)

        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self.on_key_pressed)
        self.win.add_controller(key_ctrl)

        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        shell.add_css_class("clip-shell")
        shell.set_size_request(465, 580)

        # 1. Шапка окна
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hdr.add_css_class("clip-header")

        title_lbl = Gtk.Label(label="󰅌  БУФЕР ОБМЕНА", xalign=0)
        title_lbl.add_css_class("clip-title")
        hdr.append(title_lbl)

        self.count_lbl = Gtk.Label(label="", xalign=0, hexpand=True)
        self.count_lbl.add_css_class("clip-count")
        hdr.append(self.count_lbl)

        btn_wipe = Gtk.Button(label="󰩺 Очистить всё")
        btn_wipe.add_css_class("clip-wipe-btn")
        btn_wipe.set_has_tooltip(False)
        btn_wipe.connect("clicked", self.on_wipe_all)
        hdr.append(btn_wipe)

        btn_close = Gtk.Button(label="✕")
        btn_close.add_css_class("clip-hdr-btn")
        btn_close.set_has_tooltip(False)
        btn_close.connect("clicked", lambda _b: self.close_app())
        hdr.append(btn_close)

        shell.append(hdr)

        # 2. Поиск по истории
        search_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        search_wrap.add_css_class("clip-search-wrap")
        self.search_entry = Gtk.Entry()
        self.search_entry.add_css_class("clip-search")
        self.search_entry.set_hexpand(True)
        self.search_entry.set_has_tooltip(False)
        self.search_entry.set_placeholder_text("Поиск по тексту или «скрин» / «png» (Esc — закрыть)...")
        self.search_entry.connect("changed", self.on_filter_changed)
        self.search_entry.connect("activate", self.on_copy_first_visible)
        search_wrap.append(self.search_entry)
        shell.append(search_wrap)

        # 3. Прокручиваемый список карточек
        sc = Gtk.ScrolledWindow()
        sc.set_vexpand(True)
        sc.set_hexpand(True)
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        self.list_box.add_css_class("clip-list-pad")
        sc.set_child(self.list_box)
        shell.append(sc)

        self.win.set_child(shell)
        self.load_and_render()
        self.win.present()
        self.search_entry.grab_focus()

    def close_app(self):
        self.stop_loader = True
        try:
            if os.path.isfile(PID_FILE):
                os.remove(PID_FILE)
        except Exception:
            pass
        self.quit()

    def on_key_pressed(self, _ctrl, keyval, _keycode, _state):
        if keyval == Gdk.KEY_Escape:
            self.close_app()
            return True
        return False

    def update_count(self):
        n = len(self.entries)
        self.count_lbl.set_label(f"•  {n} шт.")

    def show_empty_placeholder(self):
        lbl = Gtk.Label(label="󰅌  История буфера обмена пуста")
        lbl.add_css_class("clip-empty")
        lbl.set_vexpand(True)
        lbl.set_valign(Gtk.Align.CENTER)
        lbl.set_margin_top(60)
        self.list_box.append(lbl)

    def load_and_render(self):
        self.entries = get_cliphist_entries()[:60]
        self.cards = []
        self.preview_areas = {}
        self.update_count()

        while True:
            c = self.list_box.get_first_child()
            if c is None:
                break
            self.list_box.remove(c)

        if not self.entries:
            self.show_empty_placeholder()
            return

        img_queue = []
        for entry in self.entries:
            card_row = self.build_card(entry)
            self.cards.append((entry, card_row))
            self.list_box.append(card_row)
            if entry["kind"] == "image":
                img_queue.append(entry)

        if img_queue:
            threading.Thread(target=self._decode_thumbs_worker, args=(img_queue,), daemon=True).start()

    def build_card(self, entry):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.add_css_class("clip-card")

        main_btn = Gtk.Button()
        main_btn.add_css_class("clip-main-btn")
        main_btn.set_hexpand(True)
        main_btn.set_has_tooltip(False)
        main_btn.connect("clicked", lambda _b, e=entry: self.on_select_entry(e))

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.set_hexpand(True)

        if entry["kind"] == "image":
            preview = ImagePreviewArea(max_w=368, max_h=175)
            self.preview_areas[entry["id"]] = preview
            content.append(preview)

            meta = Gtk.Label(label=f"󰋩  СКРИНШОТ / КАРТИНКА  •  {entry['info'].upper()}", xalign=0)
            meta.add_css_class("clip-meta")
            meta.set_ellipsize(Pango.EllipsizeMode.END)
            content.append(meta)
        elif entry["kind"] == "binary":
            lbl = Gtk.Label(label=f"󰈔  Бинарные данные ({entry['info']})", xalign=0)
            lbl.add_css_class("clip-text-preview")
            content.append(lbl)
        else:
            raw_txt = entry["text"]
            compact = "\n".join(ln.rstrip() for ln in raw_txt.splitlines()[:4])[:260]
            lbl = Gtk.Label(label=compact, xalign=0)
            lbl.add_css_class("clip-text-preview")
            lbl.set_wrap(True)
            lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
            lbl.set_lines(3)
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            lbl.set_max_width_chars(44)
            content.append(lbl)

            kind_tag = "󰌹  ССЫЛКА" if raw_txt.startswith(("http://", "https://")) else "󰦨  ТЕКСТ"
            meta = Gtk.Label(label=f"{kind_tag}  •  {len(raw_txt)} симв.", xalign=0)
            meta.add_css_class("clip-meta")
            content.append(meta)

        main_btn.set_child(content)
        row.append(main_btn)

        del_btn = Gtk.Button(label="✕")
        del_btn.add_css_class("clip-del-btn")
        del_btn.set_valign(Gtk.Align.START)
        del_btn.set_margin_top(4)
        del_btn.set_margin_end(2)
        del_btn.set_has_tooltip(False)
        del_btn.connect("clicked", lambda _b, e=entry, r=row: self.on_delete_entry(e, r))
        row.append(del_btn)

        return row

    def _decode_thumbs_worker(self, img_entries):
        for entry in img_entries:
            if self.stop_loader:
                return
            cid = entry["id"]
            cache_path = os.path.join(THUMB_DIR, f"clip_{cid}.{entry['ext']}")
            try:
                if not (os.path.isfile(cache_path) and os.path.getsize(cache_path) > 0):
                    dec = subprocess.run(
                        ["cliphist", "decode"],
                        input=entry["raw"].encode("utf-8"),
                        capture_output=True,
                        timeout=3.5,
                    )
                    if dec.returncode == 0 and dec.stdout:
                        with open(cache_path, "wb") as f:
                            f.write(dec.stdout)
                if os.path.isfile(cache_path) and os.path.getsize(cache_path) > 0:
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(cache_path, 368, 175, True)
                    GLib.idle_add(self._apply_thumb, cid, pb)
                else:
                    GLib.idle_add(self._apply_thumb, cid, None)
            except Exception:
                GLib.idle_add(self._apply_thumb, cid, None)

    def _apply_thumb(self, cid, pb):
        area = self.preview_areas.get(cid)
        if area is not None:
            area.set_pixbuf(pb)
        return False

    def on_filter_changed(self, entry_w):
        q = entry_w.get_text().strip().lower()
        for entry, row in self.cards:
            if not q:
                row.set_visible(True)
                continue
            if entry["kind"] == "image":
                hay = f"скриншот картинка изображение image photo {entry['info'].lower()}"
            elif entry["kind"] == "binary":
                hay = entry["info"].lower()
            else:
                hay = entry["text"].lower()
            row.set_visible(q in hay)

    def on_copy_first_visible(self, _entry_w):
        for entry, row in self.cards:
            if row.get_visible():
                self.on_select_entry(entry)
                return

    def on_select_entry(self, entry):
        copy_entry_to_wayland(entry)
        self.close_app()

    def on_delete_entry(self, entry, row):
        try:
            subprocess.run(
                ["cliphist", "delete"],
                input=entry["raw"] + "\n",
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
        except Exception:
            pass
        if entry["kind"] == "image":
            for f in glob.glob(os.path.join(THUMB_DIR, f"clip_{entry['id']}.*")):
                try: os.remove(f)
                except Exception: pass
        self.entries = [e for e in self.entries if e["id"] != entry["id"]]
        self.cards = [(e, r) for (e, r) in self.cards if e["id"] != entry["id"]]
        self.list_box.remove(row)
        self.update_count()
        if not self.entries:
            self.show_empty_placeholder()

    def on_wipe_all(self, _b):
        subprocess.run(["cliphist", "wipe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["wl-copy", "--clear"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.rmtree(THUMB_DIR, ignore_errors=True)
        os.makedirs(THUMB_DIR, exist_ok=True)
        self.entries = []
        self.cards = []
        self.preview_areas = {}
        while True:
            c = self.list_box.get_first_child()
            if c is None:
                break
            self.list_box.remove(c)
        self.update_count()
        self.show_empty_placeholder()

if __name__ == "__main__":
    StudioClipboardApp().run(None)
