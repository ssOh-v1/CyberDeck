#!/usr/bin/python3
from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass

import os, sys, math, time, threading, subprocess
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell
import cairo

os.environ.pop("LD_PRELOAD", None)

OLD_ID = sys.argv[1] if len(sys.argv) > 1 else "cyberdeck"
NEW_ID = sys.argv[2] if len(sys.argv) > 2 else "dungeon-of-god"

WORLDS = {
    "cyberdeck":         {"name": "CYBERDECK // TACTICAL OS",         "p": (0.298, 0.431, 0.961), "a": (0.133, 0.722, 0.812), "bg": (0.027, 0.035, 0.059)},
    "dungeon-of-god":    {"name": "THE DUNGEON OF GOD // ssOh-v1",    "p": (0.850, 0.220, 0.160), "a": (0.980, 0.780, 0.220), "bg": (0.045, 0.028, 0.024)},
    "forest-stream":     {"name": "FOREST STREAM // ZEN WAYBAR",      "p": (0.180, 0.545, 0.341), "a": (0.502, 0.898, 0.698), "bg": (0.035, 0.075, 0.055)},
    "impasto-landscape": {"name": "IMPASTO LANDSCAPE // OIL CANVAS",  "p": (0.878, 0.478, 0.373), "a": (0.949, 0.800, 0.561), "bg": (0.095, 0.070, 0.062)},
    "gamedev-studio":    {"name": "GAMEDEV STUDIO // ENGINE IDE",     "p": (0.278, 0.549, 0.749), "a": (0.388, 0.851, 0.580), "bg": (0.055, 0.067, 0.086)},
}

OLD_W = WORLDS.get(OLD_ID, WORLDS["cyberdeck"])
NEW_W = WORLDS.get(NEW_ID, WORLDS["dungeon-of-god"])

def lerp(a, b, t): return a + (b - a) * t
def lerp_col(c1, c2, t): return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi/2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    cr.arc(x + r, y + h - r, r, math.pi/2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3*math.pi/2)
    cr.close_path()

class WorldTransition(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=f"org.cyberdeck.WorldMorph.{os.getpid()}")
        self.t0 = None
        self.worker_started = False
        self.worker_done = False
        self.open_t = None

    def run_swap(self):
        try:
            subprocess.run(["/usr/bin/python3", os.path.expanduser("~/.local/bin/cyber-theme"), "--apply-backend", NEW_ID], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            self.worker_done = True

    def do_activate(self):
        prov = Gtk.CssProvider()
        prov.load_from_string("window { background-color: transparent; }")
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 30)

        win = Gtk.ApplicationWindow(application=self)
        Gtk4LayerShell.init_for_window(win)
        Gtk4LayerShell.set_namespace(win, "cyberdeck-world-morph")
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
        if dt >= 0.36 and not self.worker_started:
            self.worker_started = True
            threading.Thread(target=self.run_swap, daemon=True).start()
        if self.worker_done and dt >= 1.75 and self.open_t is None:
            self.open_t = dt
        if self.open_t is not None and (dt - self.open_t) >= 0.48:
            self.quit()
            return GLib.SOURCE_REMOVE
        widget.queue_draw()
        return GLib.SOURCE_CONTINUE

    def on_draw(self, _area, cr, w, h, *_args):
        dt = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        if dt < 0.35:
            cf = 1.0 - math.pow(1.0 - (dt / 0.35), 3)
        elif self.open_t is None:
            cf = 1.0
        else:
            cf = 1.0 - math.pow(min(1.0, (dt - self.open_t) / 0.46), 3)

        mt = min(1.0, max(0.0, (dt - 0.30) / 1.25))
        sm = mt * mt * (3.0 - 2.0 * mt)
        cp = lerp_col(OLD_W["p"], NEW_W["p"], sm)
        ca = lerp_col(OLD_W["a"], NEW_W["a"], sm)
        cbg = lerp_col(OLD_W["bg"], NEW_W["bg"], sm)

        hw = w // 2 + 2
        lx = int(round(-hw * (1.0 - cf)))
        rx = int(round(w - hw * cf))

        for sx in (lx, rx):
            cr.save()
            cr.rectangle(sx, 0, hw, h); cr.clip()
            cr.set_source_rgb(*cbg); cr.paint()
            cr.set_line_width(1.0); cr.set_source_rgba(*cp, 0.12)
            for gx in range(sx, sx + hw, 56): cr.move_to(gx, 0); cr.line_to(gx, h)
            for gy in range(0, h, 56): cr.move_to(sx, gy); cr.line_to(sx + hw, gy)
            cr.stroke()
            cr.restore()

        cr.set_line_width(3.2); cr.set_source_rgba(*ca, 0.96)
        cr.move_to(lx + hw, 0); cr.line_to(lx + hw, h)
        cr.move_to(rx, 0); cr.line_to(rx, h); cr.stroke()

        if cf > 0.85:
            pa = min(1.0, (cf - 0.85) / 0.15)
            cx, cy = w * 0.5, h * 0.5
            rrect(cr, cx - 310, cy - 105, 620, 210, 14)
            cr.set_source_rgba(cbg[0]*1.2, cbg[1]*1.2, cbg[2]*1.2, 0.96 * pa); cr.fill_preserve()
            cr.set_line_width(2.2); cr.set_source_rgba(*ca, 0.95 * pa); cr.stroke()

            cr.set_line_width(2.8); cr.set_source_rgba(*cp, 0.88 * pa)
            cr.arc(cx, cy - 22, 38, dt * 3.2, dt * 3.2 + 2.0); cr.stroke()
            cr.arc(cx, cy - 22, 38, dt * 3.2 + math.pi, dt * 3.2 + math.pi + 2.0); cr.stroke()

            cr.set_line_width(2.2); cr.set_source_rgba(*ca, 0.95 * pa)
            cr.arc(cx, cy - 22, 26, -dt * 4.2, -dt * 4.2 + 1.7); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14)
            ttl = f"◈ ЗАГРУЗКА МИРА // {NEW_W['name']}"
            ext = cr.text_extents(ttl)
            cr.set_source_rgba(0.96, 0.97, 1.0, pa)
            cr.move_to(cx - ext.width / 2, cy + 44); cr.show_text(ttl)

            segs, sw, sgap = 22, 18, 4
            bx0, by0 = cx - (segs * sw + (segs - 1) * sgap) / 2, cy + 62
            for i in range(segs):
                cr.set_source_rgba(*( (*ca, 0.95 * pa) if i < int(round(mt * segs)) else (0.18, 0.20, 0.26, 0.65 * pa) ))
                cr.rectangle(bx0 + i * (sw + sgap), by0, sw, 8); cr.fill()
