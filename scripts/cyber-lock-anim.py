#!/usr/bin/env python3
import os, sys, math, time, random, datetime, subprocess
from ctypes import CDLL
try:
    CDLL("libgtk4-layer-shell.so")
except Exception:
    pass
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib
import cairo

HAS_LAYER = False
try:
    gi.require_version("Gtk4LayerShell", "1.0")
    from gi.repository import Gtk4LayerShell
    HAS_LAYER = True
except Exception:
    HAS_LAYER = False

os.environ.pop("LD_PRELOAD", None)

MODE = sys.argv[1] if len(sys.argv) > 1 else "lock"  # lock | unlock | demo
HOME = os.path.expanduser("~")
LOCK_BG = os.path.join(HOME, ".cache/cyberdeck/lock_hud_bg.png")
USER_NAME = os.environ.get("USER", "operator")

try:
    BAT_TXT = subprocess.check_output([os.path.join(HOME, ".local/bin/battery-status")], text=True, stderr=subprocess.DEVNULL).strip()
except Exception:
    BAT_TXT = "⚡ SYSTEM READY"

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi/2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    cr.arc(x + r, y + h - r, r, math.pi/2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3*math.pi/2)
    cr.close_path()

class LockBlastDoors(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=f"org.cyberdeck.LockAnim.{MODE}.{os.getpid()}")
        self.t0 = None
        self.door_l = None
        self.door_r = None
        self.lock_bg = cairo.ImageSurface.create_from_png(LOCK_BG) if os.path.isfile(LOCK_BG) else None
        random.seed(19)
        self.sparks = [(random.uniform(0.08, 0.92), random.uniform(45, 190), random.uniform(-35, 35), random.uniform(1.6, 3.0), random.random()) for _ in range(32)]

    def build_doors(self, w, h):
        hw = w // 2 + 4
        self.door_l = cairo.ImageSurface(cairo.FORMAT_ARGB32, hw, h)
        self.door_r = cairo.ImageSurface(cairo.FORMAT_ARGB32, hw, h)

        for is_left, surf in [(True, self.door_l), (False, self.door_r)]:
            cr = cairo.Context(surf)
            lg = cairo.LinearGradient(0, 0, hw, h)
            lg.add_color_stop_rgb(0.0, 0.022, 0.030, 0.055)
            lg.add_color_stop_rgb(1.0, 0.035, 0.048, 0.085)
            cr.set_source(lg); cr.paint()

            # Сотовая бронеструктура и сетка на створках
            cr.set_line_width(1.0); cr.set_source_rgba(0.30, 0.43, 0.96, 0.08)
            for x in range(48, hw, 48): cr.move_to(x, 0); cr.line_to(x, h)
            for y in range(48, h, 48): cr.move_to(0, y); cr.line_to(hw, y)
            cr.stroke()

            # Диагональные предупреждающие шевроны вдоль внутренней кромки смыкания
            seam_x = hw - 28 if is_left else 4
            cr.set_source_rgba(0.06, 0.09, 0.17, 0.96)
            cr.rectangle(seam_x, 0, 24, h); cr.fill()
            cr.set_line_width(2.6); cr.set_source_rgba(0.13, 0.72, 0.81, 0.48)
            for y in range(20, h - 20, 26):
                cr.move_to(seam_x + 3, y); cr.line_to(seam_x + 21, y + 12)
            cr.stroke()

            # Бронеплита сектора на створке
            px = 54 if is_left else hw - 334
            py = int(h * 0.5 - 95)
            rrect(cr, px, py, 280, 190, 12)
            cr.set_source_rgba(0.04, 0.055, 0.10, 0.92); cr.fill_preserve()
            cr.set_line_width(1.5); cr.set_source_rgba(0.22, 0.34, 0.62, 0.9); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(11); cr.set_source_rgb(0.88, 0.93, 1.0)
            cr.move_to(px + 18, py + 32)
            cr.show_text("◈ BLAST DOOR // PORT_L" if is_left else "◈ BLAST DOOR // STBD_R")
            cr.set_font_size(10.5); cr.set_source_rgb(0.40, 0.86, 0.94)
            for idx, line in enumerate(
                ["HYDRAULIC_SEAL // ARMED", "PAM_SHIELD     // READY", "LAYER_LOCK     // OVERLAY", "CIPHER_BUS     // 256_BIT"]
                if is_left else
                ["OPTIC_SENSOR   // ACTIVE", "MEMORY_FENCE   // LOCKED", "WAYLAND_GATE   // SECURE", "KEY_VERIFIER   // STANDBY"]
            ):
                cr.move_to(px + 18, py + 68 + idx * 30); cr.show_text(f"⟫ {line}")

    def do_activate(self):
        prov = Gtk.CssProvider()
        css = "window { background-color: transparent; }"
        if hasattr(prov, "load_from_string"): prov.load_from_string(css)
        else: prov.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER + 20)

        win = Gtk.ApplicationWindow(application=self)
        if HAS_LAYER and Gtk4LayerShell.is_supported():
            Gtk4LayerShell.init_for_window(win)
            Gtk4LayerShell.set_namespace(win, "cyberdeck-lock-doors")
            Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.OVERLAY)
            for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
                Gtk4LayerShell.set_anchor(win, edge, True)
            Gtk4LayerShell.set_exclusive_zone(win, -1)
            Gtk4LayerShell.set_keyboard_mode(win, Gtk4LayerShell.KeyboardMode.NONE)
        else:
            win.fullscreen()

        area = Gtk.DrawingArea()
        area.set_hexpand(True); area.set_vexpand(True)
        area.set_draw_func(self.on_draw)
        win.set_child(area)

        self.t0 = time.monotonic()
        GLib.timeout_add(15, self.on_tick, area)
        win.present()

    def total_duration(self):
        if MODE == "lock": return 0.95
        if MODE == "unlock": return 0.95
        return 7.40  # demo: смыкание -> экран блокировки + ввод ключа -> размыкание

    def on_tick(self, area):
        if (time.monotonic() - self.t0) >= self.total_duration():
            self.quit()
            return False
        area.queue_draw()
        return True

    def draw_blast_doors(self, cr, w, h, close_frac, dt, is_unlock=False):
        hw = w // 2
        lx = int(round(-hw * (1.0 - close_frac)))
        rx = int(round(w - hw * close_frac))

        cr.save()
        cr.set_source_surface(self.door_l, lx, 0); cr.paint()
        cr.set_source_surface(self.door_r, rx, 0); cr.paint()

        seam_l = lx + hw
        seam_r = rx
        accent = (0.125, 0.788, 0.592) if is_unlock else (0.133, 0.722, 0.812)

        # Светящиеся плазменные кромки гермостворок
        cr.set_line_width(3.0); cr.set_source_rgba(*accent, 0.96)
        cr.move_to(seam_l, 0); cr.line_to(seam_l, h)
        cr.move_to(seam_r, 0); cr.line_to(seam_r, h); cr.stroke()

        # Искры при движении створок
        if 0.04 < close_frac < 0.98:
            for y_rel, spd, vy, sz, ph in self.sparks:
                cyc = ((dt * 3.6) + ph) % 1.0
                sy = y_rel * h + cyc * vy
                cr.set_line_width(sz); cr.set_source_rgba(*accent, (1.0 - cyc) * 0.9)
                cr.move_to(seam_l - cyc * spd * 0.6, sy); cr.line_to(seam_l - cyc * spd * 0.6 + 9, sy)
                cr.move_to(seam_r + cyc * spd * 0.6, sy); cr.line_to(seam_r + cyc * spd * 0.6 - 9, sy)
                cr.stroke()

        # Центральный замок, силовые ригели и голограмма статуса при сомкнутых створках
        if close_frac > 0.82:
            lock_a = min(1.0, (close_frac - 0.82) / 0.18)
            cx, cy = w * 0.5, h * 0.5

            # Горизонтальные гидравлические ригели через центральный шов
            for ry in (cy - 210, cy + 210):
                rrect(cr, cx - 72, ry - 10, 144, 20, 5)
                cr.set_source_rgba(0.06, 0.10, 0.19, 0.96 * lock_a); cr.fill_preserve()
                cr.set_line_width(1.8); cr.set_source_rgba(*accent, 0.95 * lock_a); cr.stroke()

            # Центральный вращающийся гексагональный щит замка
            rrect(cr, cx - 220, cy - 82, 440, 164, 16)
            cr.set_source_rgba(0.04, 0.06, 0.11, 0.96 * lock_a); cr.fill_preserve()
            cr.set_line_width(2.2); cr.set_source_rgba(*accent, 0.95 * lock_a); cr.stroke()

            cr.set_line_width(2.4); cr.set_source_rgba(*accent, 0.85 * lock_a)
            cr.arc(cx, cy - 16, 36, dt * 3.2, dt * 3.2 + 2.1); cr.stroke()
            cr.arc(cx, cy - 16, 36, dt * 3.2 + math.pi, dt * 3.2 + math.pi + 2.1); cr.stroke()

            # Символ замка в ядре
            rrect(cr, cx - 12, cy - 18, 24, 19, 4)
            cr.set_source_rgba(*accent, lock_a); cr.fill()
            cr.set_line_width(2.8); cr.set_source_rgba(0.92, 0.96, 1.0, lock_a)
            shackle_dy = -6 if is_unlock else 0
            cr.arc(cx, cy - 18 + shackle_dy, 7.5, math.pi, 0); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14)
            msg = "◈ ACCESS GRANTED // TERMINAL UNLOCKED" if is_unlock else "◈ SECURITY PROTOCOL // ENGAGING LOCKDOWN"
            ext = cr.text_extents(msg)
            cr.set_source_rgba(0.92, 0.96, 1.0, lock_a)
            cr.move_to(cx - ext.width / 2, cy + 52); cr.show_text(msg)
        cr.restore()

    def draw_demo_lockscreen(self, cr, w, h, lt):
        cr.save()
        cr.scale(w / 1920.0, h / 1080.0)
        W, H = 1920, 1080
        cx, cy = W * 0.5, H * 0.5

        if self.lock_bg:
            cr.set_source_surface(self.lock_bg, 0, 0); cr.paint()

        # Вращающаяся дуга сканера вокруг центрального кольца блокировки
        cr.set_line_width(2.8); cr.set_source_rgba(0.13, 0.72, 0.81, 0.75)
        cr.arc(cx, cy, 292, lt * 1.1, lt * 1.1 + 0.95); cr.stroke()
        cr.arc(cx, cy, 292, lt * 1.1 + math.pi, lt * 1.1 + math.pi + 0.95); cr.stroke()

        now = datetime.datetime.now()
        cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

        def center_txt(txt, y_off, fsize, col):
            cr.set_font_size(fsize)
            e = cr.text_extents(txt)
            cr.set_source_rgb(*col)
            cr.move_to(cx - e.width / 2, cy - y_off + fsize * 0.36)
            cr.show_text(txt)

        center_txt("◈ CYBER DECK // SECURITY LOCKDOWN", 162, 11.5, (0.40, 0.85, 0.91))
        center_txt(now.strftime("%H:%M"), 86, 76, (0.94, 0.96, 1.0))
        center_txt(now.strftime("%d.%m.%Y   •   %A"), 20, 13, (0.57, 0.65, 1.0))
        center_txt(f"◈ OPERATOR // {USER_NAME}   •   AES-256 ACTIVE", -22, 11.5, (0.39, 0.90, 0.75))

        # Поле ввода ключа разблокировки (неспешный ввод с 1.2с по 3.6с)
        verified = (lt >= 3.85)
        iw, ih = 360, 50
        ix, iy = cx - iw / 2, cy + 82 - ih / 2
        rrect(cr, ix, iy, iw, ih, 11)
        cr.set_source_rgb(0.039, 0.059, 0.110); cr.fill_preserve()
        cr.set_line_width(2.2)
        cr.set_source_rgb(*( (0.125, 0.788, 0.592) if verified else (0.133, 0.722, 0.812) )); cr.stroke()

        typed = int(min(9, max(0, (lt - 1.25) / 0.24)))
        if verified:
            center_txt("◈ КЛЮЧ ПОДТВЕРЖДЁН // ДОСТУП РАЗРЕШЁН", -82, 12, (0.39, 0.90, 0.75))
        elif typed == 0:
            center_txt("Введите ключ разблокировки...", -82, 13, (0.42, 0.48, 0.62))
        else:
            start_x = cx - ((typed - 1) * 16) / 2.0
            for i in range(typed):
                cr.arc(start_x + i * 16, cy + 82, 4.5, 0, 2 * math.pi)
                cr.set_source_rgb(0.90, 0.94, 1.0); cr.fill()

        center_txt(BAT_TXT, -158, 12, (0.57, 0.65, 1.0))
        cr.restore()

    def on_draw(self, _area, cr, w, h, *_args):
        if self.door_l is None:
            self.build_doors(w, h)
        dt = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        if MODE == "lock":
            u = min(1.0, dt / 0.46)
            cf = 1.0 - math.pow(1.0 - u, 3)
            self.draw_blast_doors(cr, w, h, cf, dt, False)
        elif MODE == "unlock":
            if dt < 0.30:
                cf = 1.0
            else:
                u = min(1.0, (dt - 0.30) / 0.62)
                cf = 1.0 - math.pow(u, 3)
            self.draw_blast_doors(cr, w, h, cf, dt, True)
        else:
            # Режим demo (7.4с): 0..0.95 закрытие -> 0.95..5.90 экран блокировки -> 5.90..7.40 открытие
            if dt < 0.55:
                u = dt / 0.55
                self.draw_blast_doors(cr, w, h, 1.0 - math.pow(1.0 - u, 3), dt, False)
            elif dt < 1.05:
                self.draw_demo_lockscreen(cr, w, h, 0.0)
                u = (dt - 0.55) / 0.50
                self.draw_blast_doors(cr, w, h, 1.0 - math.pow(u, 3), dt, False)
            elif dt < 5.55:
                self.draw_demo_lockscreen(cr, w, h, dt - 1.05)
            elif dt < 6.05:
                self.draw_demo_lockscreen(cr, w, h, 4.50)
                u = (dt - 5.55) / 0.50
                self.draw_blast_doors(cr, w, h, 1.0 - math.pow(1.0 - u, 3), dt, True)
            else:
                u = min(1.0, (dt - 6.05) / 1.25)
                if u < 0.25:
                    cf = 1.0
                else:
                    su = (u - 0.25) / 0.75
                    cf = 1.0 - math.pow(su, 3)
                self.draw_blast_doors(cr, w, h, cf, dt, True)

if __name__ == "__main__":
    LockBlastDoors().run(None)
