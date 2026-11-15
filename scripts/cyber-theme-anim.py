#!/usr/bin/env python3
from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass

import os, sys, math, time, json, random, threading, subprocess
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell
import cairo

os.environ.pop("LD_PRELOAD", None)

OLD_ID = sys.argv[1] if len(sys.argv) > 1 else "cyber-deck"
NEW_ID = sys.argv[2] if len(sys.argv) > 2 else "arasaka-ronin"

PALETTES = {
    "cyber-deck":       {"name": "CYBER DECK // TACTICAL HUD",    "p": (0.298, 0.431, 0.961), "a": (0.133, 0.722, 0.812), "bg": (0.027, 0.035, 0.059)},
    "arasaka-ronin":    {"name": "ARASAKA RONIN // MECHA BLADE",  "p": (0.878, 0.192, 0.192), "a": (1.000, 0.769, 0.098), "bg": (0.043, 0.024, 0.031)},
    "matrix-construct": {"name": "MATRIX CONSTRUCT // NETRUNNER", "p": (0.047, 0.651, 0.471), "a": (0.251, 0.961, 0.620), "bg": (0.020, 0.043, 0.031)},
    "synth-outrun":     {"name": "SYNTH OUTRUN // HORIZON 2084",  "p": (0.941, 0.243, 0.596), "a": (0.000, 0.961, 0.831), "bg": (0.047, 0.024, 0.078)},
    "cryo-protocol":    {"name": "CRYO PROTOCOL // ORBITAL LAB",  "p": (0.200, 0.600, 1.000), "a": (0.580, 0.922, 1.000), "bg": (0.035, 0.059, 0.098)},
}

OLD_P = PALETTES.get(OLD_ID, PALETTES["cyber-deck"])
NEW_P = PALETTES.get(NEW_ID, PALETTES["arasaka-ronin"])

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_col(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi/2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    cr.arc(x + r, y + h - r, r, math.pi/2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3*math.pi/2)
    cr.close_path()

class ThemeMorphOverlay(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=f"org.cyberdeck.ThemeMorph.{os.getpid()}")
        self.t0 = None
        self.worker_started = False
        self.worker_done = False
        self.open_start_t = None
        random.seed(11)
        self.sparks = [(random.uniform(0.05, 0.95), random.uniform(60, 220), random.uniform(-40, 40), random.uniform(1.8, 3.2), random.random()) for _ in range(36)]

    def run_backend_swap(self):
        try:
            subprocess.run([os.path.expanduser("~/.local/bin/cyber-theme"), "--apply-backend", NEW_ID], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            self.worker_done = True

    def do_activate(self):
        prov = Gtk.CssProvider()
        prov.load_from_string("window { background-color: transparent; }")
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 30)

        win = Gtk.ApplicationWindow(application=self)
        Gtk4LayerShell.init_for_window(win)
        Gtk4LayerShell.set_namespace(win, "cyberdeck-theme-morph")
        Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.OVERLAY)
        for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
            Gtk4LayerShell.set_anchor(win, edge, True)
        Gtk4LayerShell.set_exclusive_zone(win, -1)
        Gtk4LayerShell.set_keyboard_mode(win, Gtk4LayerShell.KeyboardMode.NONE)

        area = Gtk.DrawingArea()
        area.set_hexpand(True); area.set_vexpand(True)
        area.set_draw_func(self.on_draw)
        area.add_tick_callback(self.on_tick)
        win.set_child(area)
        self.t0 = time.monotonic()
        win.present()

    def on_tick(self, widget, _clock):
        dt = time.monotonic() - self.t0
        # Когда створки полностью сомкнулись (0.42с) и закрыли экран — запускаем пересборку темы и перезапуск стола позади них!
        if dt >= 0.42 and not self.worker_started:
            self.worker_started = True
            threading.Thread(target=self.run_backend_swap, daemon=True).start()

        if self.worker_done and dt >= 1.95 and self.open_start_t is None:
            self.open_start_t = dt

        if self.open_start_t is not None and (dt - self.open_start_t) >= 0.55:
            self.quit()
            return GLib.SOURCE_REMOVE

        widget.queue_draw()
        return GLib.SOURCE_CONTINUE

    def on_draw(self, _area, cr, w, h, *_args):
        dt = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # Коэффициент закрытия створок (0.0 -> 1.0 -> 0.0)
        if dt < 0.40:
            u = dt / 0.40
            close_f = 1.0 - math.pow(1.0 - u, 3)
        elif self.open_start_t is None:
            close_f = 1.0
        else:
            u = min(1.0, (dt - self.open_start_t) / 0.52)
            close_f = 1.0 - math.pow(u, 3)

        # Коэффициент морфинга старой темы в новую (0.0 -> 1.0)
        morph_t = min(1.0, max(0.0, (dt - 0.35) / 1.35))
        sm_morph = morph_t * morph_t * (3.0 - 2.0 * morph_t)

        col_p  = lerp_col(OLD_P["p"],  NEW_P["p"],  sm_morph)
        col_a  = lerp_col(OLD_P["a"],  NEW_P["a"],  sm_morph)
        col_bg = lerp_col(OLD_P["bg"], NEW_P["bg"], sm_morph)

        hw = w // 2 + 2
        lx = int(round(-hw * (1.0 - close_f)))
        rx = int(round(w - hw * close_f))

        # Левая и правая бронестворки морфинга
        for sx in (lx, rx):
            cr.save()
            cr.rectangle(sx, 0, hw, h); cr.clip()
            cr.set_source_rgb(*col_bg); cr.paint()

            cr.set_line_width(1.0); cr.set_source_rgba(*col_p, 0.09)
            for gx in range(sx, sx + hw, 56): cr.move_to(gx, 0); cr.line_to(gx, h)
            for gy in range(0, h, 56): cr.move_to(sx, gy); cr.line_to(sx + hw, gy)
            cr.stroke()
            cr.restore()

        seam_l, seam_r = lx + hw, rx
        cr.set_line_width(3.2); cr.set_source_rgba(*col_a, 0.95)
        cr.move_to(seam_l, 0); cr.line_to(seam_l, h)
        cr.move_to(seam_r, 0); cr.line_to(seam_r, h); cr.stroke()

        # Лазерная волна перековки сверху вниз, пока створки закрыты
        if close_f > 0.85:
            panel_a = min(1.0, (close_f - 0.85) / 0.15)
            cx, cy = w * 0.5, h * 0.5

            scan_y = h * morph_t
            sg = cairo.LinearGradient(0, scan_y - 60, 0, scan_y + 12)
            sg.add_color_stop_rgba(0.0, *col_a, 0.0)
            sg.add_color_stop_rgba(0.8, *col_a, 0.22 * panel_a)
            sg.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.65 * panel_a)
            cr.set_source(sg); cr.rectangle(0, scan_y - 60, w, 72); cr.fill()

            # Центральное ядро перекалибровки темы
            rrect(cr, cx - 290, cy - 115, 580, 230, 14 if NEW_ID != "arasaka-ronin" else 2)
            cr.set_source_rgba(col_bg[0]*1.2, col_bg[1]*1.2, col_bg[2]*1.2, 0.96 * panel_a); cr.fill_preserve()
            cr.set_line_width(2.2); cr.set_source_rgba(*col_a, 0.95 * panel_a); cr.stroke()

            # Вращающиеся кольца вокруг ядра
            cr.set_line_width(2.6); cr.set_source_rgba(*col_p, 0.85 * panel_a)
            cr.arc(cx, cy - 26, 42, dt * 3.0, dt * 3.0 + 2.0); cr.stroke()
            cr.arc(cx, cy - 26, 42, dt * 3.0 + math.pi, dt * 3.0 + math.pi + 2.0); cr.stroke()

            cr.set_line_width(2.2); cr.set_source_rgba(*col_a, 0.95 * panel_a)
            cr.arc(cx, cy - 26, 30, -dt * 3.8, -dt * 3.8 + 1.6); cr.stroke()
            cr.arc(cx, cy - 26, 30, -dt * 3.8 + math.pi, -dt * 3.8 + math.pi + 1.6); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14)
            title = f"◈ АРХИТЕКТУРА ТЕМЫ // {NEW_P['name']}"
            ext = cr.text_extents(title)
            cr.set_source_rgba(0.95, 0.97, 1.0, panel_a)
            cr.move_to(cx - ext.width / 2, cy + 44); cr.show_text(title)

            # Сегментированный прогресс-бар перековки модулей
            segs = 22
            sw, sgap = 18, 4
            bx0 = cx - (segs * sw + (segs - 1) * sgap) / 2
            by0 = cy + 62
            act_s = int(round(morph_t * segs))
            for i in range(segs):
                cr.set_source_rgba(*( (*col_a, 0.95 * panel_a) if i < act_s else (0.15, 0.20, 0.30, 0.65 * panel_a) ))
                cr.rectangle(bx0 + i * (sw + sgap), by0, sw, 8); cr.fill()

            cr.set_font_size(10.5)
            steps_txt = ["[OK] GEOMETRY_CSS", "[OK] CURSOR_X11", "[OK] FIREFOX_HUD", "[OK] SDDM_GRUB", "[OK] LAYER_READY"]
            shown = "   •   ".join(steps_txt[:max(1, int(morph_t * 5.2))])
            se = cr.text_extents(shown)
            cr.set_source_rgba(*col_a, 0.92 * panel_a)
            cr.move_to(cx - se.width / 2, cy + 92); cr.show_text(shown)

if __name__ == "__main__":
    ThemeMorphOverlay().run(None)
