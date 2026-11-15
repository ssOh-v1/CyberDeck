#!/usr/bin/env python3
from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass

import os, sys, math, time, random, threading, subprocess
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell
import cairo

os.environ.pop("LD_PRELOAD", None)

OLD_ID = sys.argv[1] if len(sys.argv) > 1 else "cyber-tactical"
NEW_ID = sys.argv[2] if len(sys.argv) > 2 else "ronin-os"

PALETTES = {
    "cyber-tactical": {"name": "CYBERDECK // TACTICAL WORKSPACE", "p": (0.298, 0.431, 0.961), "a": (0.133, 0.722, 0.812), "bg": (0.027, 0.035, 0.059)},
    "ronin-os":       {"name": "ARASAKA RONIN // COMMAND DECK",   "p": (0.878, 0.192, 0.192), "a": (0.988, 0.769, 0.098), "bg": (0.043, 0.024, 0.031)},
    "netrunner-os":   {"name": "NETRUNNER // CONSTRUCT MATRIX",   "p": (0.047, 0.651, 0.471), "a": (0.220, 0.851, 0.663), "bg": (0.020, 0.039, 0.031)},
    "cryo-studio":    {"name": "CRYO STUDIO // ORBITAL ISLAND",   "p": (0.110, 0.494, 0.839), "a": (0.455, 0.753, 0.988), "bg": (0.024, 0.043, 0.071)},
    "game-scanout":   {"name": "APEX SCANOUT // ESPORTS ARENA",   "p": (0.298, 0.431, 0.961), "a": (0.000, 0.961, 0.831), "bg": (0.024, 0.031, 0.055)},
    "game-redline":   {"name": "REDLINE OVERDRIVE // TURBO RIG",  "p": (0.941, 0.180, 0.240), "a": (1.000, 0.720, 0.000), "bg": (0.047, 0.020, 0.027)},
    "game-arcade":    {"name": "SYNTH ARCADE // HORIZON 2084",    "p": (0.839, 0.200, 0.518), "a": (0.000, 0.961, 0.831), "bg": (0.035, 0.020, 0.071)},
}

OLD_P = PALETTES.get(OLD_ID, PALETTES["cyber-tactical"])
NEW_P = PALETTES.get(NEW_ID, PALETTES["ronin-os"])

def lerp(a, b, t): return a + (b - a) * t
def lerp_col(c1, c2, t): return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))

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
        if dt >= 0.38 and not self.worker_started:
            self.worker_started = True
            threading.Thread(target=self.run_backend_swap, daemon=True).start()
        if self.worker_done and dt >= 1.80 and self.open_start_t is None:
            self.open_start_t = dt
        if self.open_start_t is not None and (dt - self.open_start_t) >= 0.50:
            self.quit()
            return GLib.SOURCE_REMOVE
        widget.queue_draw()
        return GLib.SOURCE_CONTINUE

    def on_draw(self, _area, cr, w, h, *_args):
        dt = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        if dt < 0.36:
            close_f = 1.0 - math.pow(1.0 - (dt / 0.36), 3)
        elif self.open_start_t is None:
            close_f = 1.0
        else:
            close_f = 1.0 - math.pow(min(1.0, (dt - self.open_start_t) / 0.48), 3)

        morph_t = min(1.0, max(0.0, (dt - 0.32) / 1.25))
        sm = morph_t * morph_t * (3.0 - 2.0 * morph_t)
        col_p  = lerp_col(OLD_P["p"],  NEW_P["p"],  sm)
        col_a  = lerp_col(OLD_P["a"],  NEW_P["a"],  sm)
        col_bg = lerp_col(OLD_P["bg"], NEW_P["bg"], sm)

        hw = w // 2 + 2
        lx = int(round(-hw * (1.0 - close_f)))
        rx = int(round(w - hw * close_f))

        for sx in (lx, rx):
            cr.save()
            cr.rectangle(sx, 0, hw, h); cr.clip()
            cr.set_source_rgb(*col_bg); cr.paint()
            cr.set_line_width(1.0); cr.set_source_rgba(*col_p, 0.10)
            for gx in range(sx, sx + hw, 56): cr.move_to(gx, 0); cr.line_to(gx, h)
            for gy in range(0, h, 56): cr.move_to(sx, gy); cr.line_to(sx + hw, gy)
            cr.stroke()
            cr.restore()

        cr.set_line_width(3.2); cr.set_source_rgba(*col_a, 0.96)
        cr.move_to(lx + hw, 0); cr.line_to(lx + hw, h)
        cr.move_to(rx, 0); cr.line_to(rx, h); cr.stroke()

        if close_f > 0.85:
            pa = min(1.0, (close_f - 0.85) / 0.15)
            cx, cy = w * 0.5, h * 0.5
            scan_y = h * morph_t
            sg = cairo.LinearGradient(0, scan_y - 50, 0, scan_y + 10)
            sg.add_color_stop_rgba(0.0, *col_a, 0.0)
            sg.add_color_stop_rgba(0.8, *col_a, 0.25 * pa)
            sg.add_color_stop_rgba(1.0, 1.0, 1.0, 1.0, 0.70 * pa)
            cr.set_source(sg); cr.rectangle(0, scan_y - 50, w, 60); cr.fill()

            rrect(cr, cx - 300, cy - 110, 600, 220, 12)
            cr.set_source_rgba(col_bg[0]*1.2, col_bg[1]*1.2, col_bg[2]*1.2, 0.96 * pa); cr.fill_preserve()
            cr.set_line_width(2.2); cr.set_source_rgba(*col_a, 0.95 * pa); cr.stroke()

            cr.set_line_width(2.6); cr.set_source_rgba(*col_p, 0.88 * pa)
            cr.arc(cx, cy - 24, 40, dt * 3.2, dt * 3.2 + 2.0); cr.stroke()
            cr.arc(cx, cy - 24, 40, dt * 3.2 + math.pi, dt * 3.2 + math.pi + 2.0); cr.stroke()

            cr.set_line_width(2.2); cr.set_source_rgba(*col_a, 0.95 * pa)
            cr.arc(cx, cy - 24, 28, -dt * 4.0, -dt * 4.0 + 1.6); cr.stroke()
            cr.arc(cx, cy - 24, 28, -dt * 4.0 + math.pi, -dt * 4.0 + math.pi + 1.6); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14)
            ttl = f"◈ ЗАГРУЗКА НОВОГО ОКРУЖЕНИЯ // {NEW_P['name']}"
            ext = cr.text_extents(ttl)
            cr.set_source_rgba(0.95, 0.97, 1.0, pa)
            cr.move_to(cx - ext.width / 2, cy + 44); cr.show_text(ttl)

            segs, sw, sgap = 22, 18, 4
            bx0, by0 = cx - (segs * sw + (segs - 1) * sgap) / 2, cy + 62
            for i in range(segs):
                cr.set_source_rgba(*( (*col_a, 0.95 * pa) if i < int(round(morph_t * segs)) else (0.15, 0.20, 0.30, 0.65 * pa) ))
                cr.rectangle(bx0 + i * (sw + sgap), by0, sw, 8); cr.fill()

            cr.set_font_size(10.5)
            steps = ["[OK] WORKSPACE_LAYOUT", "[OK] WIDGET_ENGINE", "[OK] XCURSOR_SHAPE", "[OK] FIREFOX_SDDM_GRUB"]
            st_txt = "   •   ".join(steps[:max(1, int(morph_t * 4.3))])
            se = cr.text_extents(st_txt)
            cr.set_source_rgba(*col_a, 0.92 * pa)
            cr.move_to(cx - se.width / 2, cy + 92); cr.show_text(st_txt)

if __name__ == "__main__":
    ThemeMorphOverlay().run(None)
