#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
except Exception:
    pass

import os, sys, math, time, subprocess
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell
import cairo

os.environ.pop("LD_PRELOAD", None)
MODE = sys.argv[1] if len(sys.argv) > 1 else "lock"

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()

class StudioLockTransition(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=f"org.studio.LockAnim.{os.getpid()}")
        self.t0 = None
        self.hyprlock_spawned = False

    def do_activate(self):
        prov = Gtk.CssProvider()
        prov.load_from_string("window { background-color: transparent; }")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 40
        )

        win = Gtk.ApplicationWindow(application=self)
        Gtk4LayerShell.init_for_window(win)
        Gtk4LayerShell.set_namespace(win, "studio-lock-anim")
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
        if MODE == "lock":
            # Когда створки сомкнулись (0.40с) — запускаем hyprlock под ними
            if dt >= 0.40 and not self.hyprlock_spawned:
                self.hyprlock_spawned = True
                subprocess.Popen(["hyprlock"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if dt >= 0.78:
                self.quit()
                return GLib.SOURCE_REMOVE
        else:
            # Режим unlock: плавное раскрытие створок на рабочий стол за 0.55с
            if dt >= 0.56:
                self.quit()
                return GLib.SOURCE_REMOVE

        widget.queue_draw()
        return GLib.SOURCE_CONTINUE

    def on_draw(self, _area, cr, w, h, *_args):
        dt = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        if MODE == "lock":
            # Фаза закрытия створок (0..0.38с), затем плавное растворение над hyprlock (0.48..0.78с)
            p_close = min(1.0, dt / 0.38)
            cf = 1.0 - math.pow(1.0 - p_close, 3)
            fade = 1.0 if dt < 0.48 else max(0.0, 1.0 - (dt - 0.48) / 0.30)
            status_txt = "▣ БЛОКИРОВКА СИСТЕМЫ // ЗАЩИТНЫЙ КОНТУР АКТИВЕН"
            sub_txt    = "STUDIO SECURITY VAULT  •  LOCKED"
        else:
            # Фаза открытия створок после успешного ввода пароля (0..0.55с)
            p_open = min(1.0, dt / 0.54)
            cf = 1.0 - math.pow(p_open, 3)
            fade = 1.0
            status_txt = "▣ ДОСТУП РАЗРЕШЁН // РАБОЧАЯ СТАНЦИЯ РАЗБЛОКИРОВАНА"
            sub_txt    = "WELCOME BACK, OPERATOR  •  STUDIO READY"

        hh = int(h // 2 + 4)
        top_y = int(round(-hh * (1.0 - cf)))
        bot_y = int(round(h - hh * cf))

        # Верхняя и нижняя матово-графитовые бронестворки
        for sy in (top_y, bot_y):
            cr.save()
            cr.rectangle(0, sy, w, hh)
            cr.clip()
            cr.set_source_rgba(0.071, 0.075, 0.090, 0.98 * fade)
            cr.paint()
            cr.set_line_width(1.0)
            cr.set_source_rgba(0.45, 0.48, 0.54, 0.08 * fade)
            for gx in range(0, w, 64):
                cr.move_to(gx, sy); cr.line_to(gx, sy + hh)
            for gy in range(sy, sy + hh, 64):
                cr.move_to(0, gy); cr.line_to(w, gy)
            cr.stroke()
            cr.restore()

        # Стальная кромка смыкания створок
        cr.set_line_width(2.5)
        cr.set_source_rgba(0.62, 0.66, 0.72, 0.90 * fade)
        cr.move_to(0, top_y + hh); cr.line_to(w, top_y + hh)
        cr.move_to(0, bot_y);      cr.line_to(w, bot_y)
        cr.stroke()

        # Центральный механический затвор и карточка статуса
        if cf > 0.35:
            pa = min(1.0, (cf - 0.35) / 0.65) * fade
            cx, cy = w * 0.5, h * 0.5

            rrect(cr, cx - 285, cy - 82, 570, 164, 10)
            cr.set_source_rgba(0.09, 0.10, 0.12, 0.96 * pa)
            cr.fill_preserve()
            cr.set_line_width(1.6)
            cr.set_source_rgba(0.55, 0.58, 0.65, 0.85 * pa)
            cr.stroke()

            # Вращающееся кольцо затвора
            cr.set_line_width(2.4)
            cr.set_source_rgba(0.75, 0.78, 0.84, 0.90 * pa)
            ang0 = dt * (4.5 if MODE == "lock" else -5.0)
            cr.arc(cx, cy - 22, 26, ang0, ang0 + 2.0); cr.stroke()
            cr.arc(cx, cy - 22, 26, ang0 + math.pi, ang0 + math.pi + 2.0); cr.stroke()

            cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(13.5)
            ext = cr.text_extents(status_txt)
            cr.set_source_rgba(0.92, 0.94, 0.97, pa)
            cr.move_to(cx - ext.width * 0.5, cy + 32)
            cr.show_text(status_txt)

            cr.select_font_face("JetBrainsMono Nerd Font", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(10.5)
            se = cr.text_extents(sub_txt)
            cr.set_source_rgba(0.60, 0.64, 0.70, pa)
            cr.move_to(cx - se.width * 0.5, cy + 54)
            cr.show_text(sub_txt)

if __name__ == "__main__":
    StudioLockTransition().run(None)
