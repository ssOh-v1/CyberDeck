#!/usr/bin/python3
from ctypes import CDLL, RTLD_GLOBAL
try:
    CDLL("/usr/lib/libgtk4-layer-shell.so", mode=RTLD_GLOBAL)
except Exception:
    pass

import os, sys, math, time, random, threading, subprocess
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell
import cairo

os.environ.pop("LD_PRELOAD", None)

OLD_ID = sys.argv[1] if len(sys.argv) > 1 else "cyberdeck"
NEW_ID = sys.argv[2] if len(sys.argv) > 2 else "dungeon-of-god"

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi/2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    cr.arc(x + r, y + h - r, r, math.pi/2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3*math.pi/2)
    cr.close_path()

def draw_3d_brushstroke(cr, x, y, w, h, ang, r, g, b, alpha=1.0):
    cr.save()
    cr.translate(x, y)
    cr.rotate(ang)
    # Тень под рельефным бугорком краски
    cr.set_source_rgba(r * 0.28, g * 0.26, b * 0.24, 0.82 * alpha)
    cr.rectangle(-w/2 + 3, -h/2 + 4, w, h); cr.fill()
    # Верхний световой гребень бугорка
    cr.set_source_rgba(min(1, r * 1.32 + 0.08), min(1, g * 1.28 + 0.06), min(1, b * 1.20 + 0.05), 0.94 * alpha)
    cr.rectangle(-w/2 - 2, -h/2 - 2, w, h * 0.45); cr.fill()
    # Основной слой масла
    cr.set_source_rgba(r, g, b, 0.98 * alpha)
    cr.rectangle(-w/2, -h/2, w, h); cr.fill()
    # Фактурные бороздки кисти
    cr.set_line_width(1.3)
    cr.set_source_rgba(min(1, r * 1.38 + 0.12), min(1, g * 1.32 + 0.10), min(1, b * 1.24 + 0.08), 0.45 * alpha)
    for by in (-h * 0.28, 0.0, h * 0.26):
        cr.move_to(-w * 0.45, by); cr.line_to(w * 0.45, by)
    cr.stroke()
    cr.restore()

class WorldTransition(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=f"org.cyberdeck.WorldMorph.{os.getpid()}")
        self.t0 = None
        self.worker_started = False
        self.worker_done = False
        self.open_t = None

        random.seed(42)
        # Частицы для огня подземелья, листьев леса и мазков импасто
        self.embers = [(random.uniform(0.05, 0.95), random.uniform(0.4, 1.3), random.uniform(-35, 35), random.uniform(2.2, 5.0), random.random()) for _ in range(55)]
        self.leaves = [(random.uniform(0.05, 0.95), random.uniform(0.1, 0.9), random.uniform(0.6, 1.4), random.uniform(8, 16), random.random()) for _ in range(36)]

        palette_impasto = [
            (0.88, 0.48, 0.37), (0.95, 0.80, 0.56), (0.24, 0.25, 0.36),
            (0.51, 0.70, 0.60), (0.91, 0.44, 0.32), (0.18, 0.32, 0.45)
        ]
        self.strokes = []
        for idx in range(68):
            col = palette_impasto[idx % len(palette_impasto)]
            self.strokes.append((
                random.uniform(0.0, 1.0),
                random.uniform(0.0, 1.0),
                random.uniform(280, 520),
                random.uniform(95, 160),
                random.uniform(-0.35, 0.35),
                col[0], col[1], col[2],
                idx / 68.0 * 0.65
            ))

    def run_swap(self):
        try:
            subprocess.run(
                ["/usr/bin/python3", os.path.expanduser("~/.local/bin/cyber-theme"), "--apply-backend", NEW_ID],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
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
        # Когда заслон закрыл экран (0.42с) — запускаем переключение фонового окружения
        if dt >= 0.42 and not self.worker_started:
            self.worker_started = True
            threading.Thread(target=self.run_swap, daemon=True).start()

        if self.worker_done and dt >= 2.15 and self.open_t is None:
            self.open_t = dt

        if self.open_t is not None and (dt - self.open_t) >= 0.55:
            self.quit()
            return GLib.SOURCE_REMOVE

        widget.queue_draw()
        return GLib.SOURCE_CONTINUE

    # --------------------------------------------------------------------------
    # 1. АНИМАЦИЯ CYBERDECK CLASSIC: Бронестворки, плазменный шов и лазерный радар
    # --------------------------------------------------------------------------
    def draw_cyberdeck_anim(self, cr, w, h, dt, cf, prog):
        hw = w // 2 + 2
        lx = int(round(-hw * (1.0 - cf)))
        rx = int(round(w - hw * cf))

        for sx in (lx, rx):
            cr.save()
            cr.rectangle(sx, 0, hw, h); cr.clip()
            cr.set_source_rgb(0.027, 0.035, 0.059); cr.paint()
            cr.set_line_width(1.0); cr.set_source_rgba(0.30, 0.43, 0.96, 0.10)
            for gx in range(sx, sx + hw, 64): cr.move_to(gx, 0); cr.line_to(gx, h)
            for gy in range(0, h, 64): cr.move_to(sx, gy); cr.line_to(sx + hw, gy)
            cr.stroke()
            cr.restore()

        cr.set_line_width(3.2); cr.set_source_rgba(0.13, 0.72, 0.81, 0.96)
        cr.move_to(lx + hw, 0); cr.line_to(lx + hw, h)
        cr.move_to(rx, 0); cr.line_to(rx, h); cr.stroke()

        if cf > 0.82:
            pa = min(1.0, (cf - 0.82) / 0.18)
            cx, cy = w * 0.5, h * 0.5
            scan_y = (dt * 650.0) % h
            cr.set_source_rgba(0.13, 0.72, 0.81, 0.25 * pa)
            cr.rectangle(0, scan_y - 18, w, 24); cr.fill()

            rrect(cr, cx - 290, cy - 105, 580, 210, 14)
            cr.set_source_rgba(0.04, 0.06, 0.11, 0.96 * pa); cr.fill_preserve()
            cr.set_line_width(2.2); cr.set_source_rgba(0.13, 0.72, 0.81, 0.95 * pa); cr.stroke()

            cr.set_line_width(2.8); cr.set_source_rgba(0.30, 0.43, 0.96, 0.9 * pa)
            cr.arc(cx, cy - 22, 42, dt * 3.0, dt * 3.0 + 2.1); cr.stroke()
            cr.arc(cx, cy - 22, 42, dt * 3.0 + math.pi, dt * 3.0 + math.pi + 2.1); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(15); ttl = "◈ CYBERDECK CLASSIC // TACTICAL MATRIX ENGAGED"
            ext = cr.text_extents(ttl); cr.set_source_rgba(0.92, 0.96, 1.0, pa)
            cr.move_to(cx - ext.width / 2, cy + 46); cr.show_text(ttl)

            rrect(cr, cx - 200, cy + 64, 400 * prog, 10, 4)
            cr.set_source_rgba(0.13, 0.72, 0.81, 0.95 * pa); cr.fill()

    # --------------------------------------------------------------------------
    # 2. АНИМАЦИЯ THE DUNGEON OF GOD: Каменные врата, руническая печать и угли
    # --------------------------------------------------------------------------
    def draw_dungeon_anim(self, cr, w, h, dt, cf, prog):
        hh = h // 2 + 4
        ty = int(round(-hh * (1.0 - cf)))
        by = int(round(h - hh * cf))

        # Верхняя и нижняя каменные плиты подземелья
        for sy in (ty, by):
            cr.save()
            cr.rectangle(0, sy, w, hh); cr.clip()
            cr.set_source_rgb(0.055, 0.032, 0.026); cr.paint()
            for r_i, y_b in enumerate(range(sy, sy + hh, 64)):
                ox = 48 if (r_i % 2) else 0
                for x_b in range(-48, w, 96):
                    cr.set_source_rgba(0.11, 0.065, 0.055, 0.90)
                    cr.rectangle(x_b + ox + 2, y_b + 2, 92, 60); cr.fill_preserve()
                    cr.set_line_width(1.2); cr.set_source_rgba(0.26, 0.15, 0.11, 0.55); cr.stroke()
            cr.restore()

        # Раскалённый лавовый шов смыкания каменных врат
        cr.set_line_width(4.0); cr.set_source_rgba(0.96, 0.68, 0.18, 0.95)
        cr.move_to(0, ty + hh); cr.line_to(w, ty + hh)
        cr.move_to(0, by); cr.line_to(w, by); cr.stroke()

        # Взлетающие искры пламени и огненная печать Бога Подземелья
        if cf > 0.75:
            pa = min(1.0, (cf - 0.75) / 0.25)
            cx, cy = w * 0.5, h * 0.5

            rg = cairo.RadialGradient(cx, cy, 10, cx, cy, 420)
            rg.add_color_stop_rgba(0.0, 0.92, 0.28, 0.14, 0.38 * pa)
            rg.add_color_stop_rgba(0.6, 0.96, 0.65, 0.15, 0.14 * pa)
            rg.add_color_stop_rgba(1.0, 0, 0, 0, 0)
            cr.set_source(rg); cr.paint()

            for x0, spd, vx, sz, ph in self.embers:
                cyc = ((dt * spd) + ph) % 1.0
                ex = (x0 * w + cyc * vx * 3.0) % w
                ey = h - cyc * h
                cr.set_source_rgba(0.98, 0.72, 0.20, (1.0 - cyc) * pa)
                cr.arc(ex, ey, sz, 0, 2 * math.pi); cr.fill()

            # Вращающаяся древняя руническая печать
            cr.save(); cr.translate(cx, cy - 18); cr.rotate(dt * 1.1)
            cr.set_line_width(2.8); cr.set_source_rgba(0.96, 0.74, 0.22, 0.95 * pa)
            cr.arc(0, 0, 88, 0, 2 * math.pi); cr.stroke()
            cr.arc(0, 0, 72, 0, 2 * math.pi); cr.stroke()
            # 8-конечная звезда рун внутри кольца
            for k in range(2):
                cr.save(); cr.rotate(k * math.pi / 4.0)
                cr.set_source_rgba(0.88, 0.24, 0.18, 0.92 * pa)
                cr.rectangle(-50, -50, 100, 100); cr.stroke()
                cr.restore()
            cr.restore()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(18); ttl = "⚔ THE DUNGEON OF GOD // ВРАТА ПОДЗЕМЕЛЬЯ ОТКРЫТЫ"
            ext = cr.text_extents(ttl); cr.set_source_rgba(0.99, 0.92, 0.78, pa)
            cr.move_to(cx - ext.width / 2, cy + 108); cr.show_text(ttl)

            cr.set_font_size(12); sub = "by ssOh-v1   •   ЗАГРУЗКА АЛТАРЯ АРТЕФАКТОВ И ЖИВЫХ ФАКЕЛОВ..."
            se = cr.text_extents(sub); cr.set_source_rgba(0.96, 0.74, 0.22, 0.9 * pa)
            cr.move_to(cx - se.width / 2, cy + 132); cr.show_text(sub)

            rrect(cr, cx - 220, cy + 148, 440, 12, 4)
            cr.set_source_rgba(0.16, 0.08, 0.06, 0.9 * pa); cr.fill_preserve()
            cr.set_line_width(1.4); cr.set_source_rgba(0.96, 0.74, 0.22, 0.9 * pa); cr.stroke()
            rrect(cr, cx - 218, cy + 150, 436 * prog, 8, 3)
            cr.set_source_rgba(0.88, 0.24, 0.18, 0.98 * pa); cr.fill()

    # --------------------------------------------------------------------------
    # 3. АНИМАЦИЯ ЛЕСНОГО РУЧЬЯ: Изумрудный туман, течение воды и кружащаяся листва
    # --------------------------------------------------------------------------
    def draw_forest_anim(self, cr, w, h, dt, cf, prog):
        hw = w // 2 + 20
        lx = int(round(-hw * (1.0 - cf)))
        rx = int(round(w - hw * cf))

        # Мягкий лесной полог слева и справа
        for sx in (lx, rx):
            cr.save()
            cr.rectangle(sx, 0, hw, h); cr.clip()
            lg = cairo.LinearGradient(0, 0, 0, h)
            lg.add_color_stop_rgb(0.0, 0.03, 0.09, 0.06)
            lg.add_color_stop_rgb(0.5, 0.06, 0.16, 0.11)
            lg.add_color_stop_rgb(1.0, 0.04, 0.11, 0.08)
            cr.set_source(lg); cr.paint()
            cr.restore()

        if cf > 0.70:
            pa = min(1.0, (cf - 0.70) / 0.30)
            cx, cy = w * 0.5, h * 0.5

            # Живые волны лесного ручья через экран
            for wave_i in range(5):
                cr.set_line_width(3.0 if wave_i == 2 else 1.8)
                cr.set_source_rgba(0.45, 0.85, 0.65, (0.22 + 0.08 * wave_i) * pa)
                cr.move_to(0, cy + (wave_i - 2) * 32)
                for x in range(0, w + 40, 40):
                    wy = cy + (wave_i - 2) * 32 + math.sin(x * 0.008 + dt * 4.5 + wave_i) * 18
                    cr.line_to(x, wy)
                cr.stroke()

            # Парящие изумрудные листья и светлячки
            for x0, y0, spd, sz, ph in self.leaves:
                lx_p = ((x0 + dt * spd * 0.22) % 1.0) * w
                ly_p = y0 * h + math.sin(dt * 3.0 + ph * 6.28) * 26
                cr.save()
                cr.translate(lx_p, ly_p)
                cr.rotate(dt * 1.8 + ph * 6.28)
                cr.set_source_rgba(0.55, 0.92, 0.72, 0.75 * pa)
                cr.move_to(-sz, 0); cr.curve_to(-sz*0.3, -sz*0.6, sz*0.3, -sz*0.6, sz, 0)
                cr.curve_to(sz*0.3, sz*0.6, -sz*0.3, sz*0.6, -sz, 0)
                cr.fill()
                cr.restore()

            rrect(cr, cx - 280, cy - 85, 560, 170, 22)
            cr.set_source_rgba(0.04, 0.11, 0.08, 0.94 * pa); cr.fill_preserve()
            cr.set_line_width(2.0); cr.set_source_rgba(0.45, 0.85, 0.65, 0.90 * pa); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(16); ttl = "🌿 ЛЕСНОЙ РУЧЕЙ // ГАРМОНИЯ И ФОКУС"
            ext = cr.text_extents(ttl); cr.set_source_rgba(0.92, 0.99, 0.95, pa)
            cr.move_to(cx - ext.width / 2, cy - 12); cr.show_text(ttl)

            rrect(cr, cx - 190, cy + 24, 380 * prog, 10, 5)
            cr.set_source_rgba(0.45, 0.85, 0.65, 0.95 * pa); cr.fill()

    # --------------------------------------------------------------------------
    # 4. АНИМАЦИЯ ИМПАСТО ПЕЙЗАЖА: Живое закрашивание экрана 3D-мазками масла
    # --------------------------------------------------------------------------
    def draw_impasto_anim(self, cr, w, h, dt, cf, prog):
        # Каждый рельефный мазок вылетает на холст в своё время
        for rx, ry, sw, sh, ang, r, g, b, delay in self.strokes:
            local_u = min(1.0, max(0.0, (cf - delay * 0.55) / 0.45))
            if local_u <= 0.01:
                continue
            cur_w = sw * local_u
            draw_3d_brushstroke(cr, rx * w, ry * h, cur_w, sh, ang, r, g, b, local_u)

        if cf > 0.78:
            pa = min(1.0, (cf - 0.78) / 0.22)
            cx, cy = w * 0.5, h * 0.5
            rrect(cr, cx - 290, cy - 90, 580, 180, 14)
            cr.set_source_rgba(0.12, 0.09, 0.08, 0.95 * pa); cr.fill_preserve()
            cr.set_line_width(3.0); cr.set_source_rgba(0.95, 0.80, 0.56, 0.95 * pa); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(16); ttl = "🎨 МАСТЕРСКАЯ ИМПАСТО // НАНЕСЕНИЕ 3D-МАЗКОВ МАСЛА"
            ext = cr.text_extents(ttl); cr.set_source_rgba(0.99, 0.95, 0.89, pa)
            cr.move_to(cx - ext.width / 2, cy - 14); cr.show_text(ttl)

            cr.set_font_size(12); sub = "Подготовка мольберта, палитры красок и рельефного пейзажа..."
            se = cr.text_extents(sub); cr.set_source_rgba(0.95, 0.80, 0.56, 0.9 * pa)
            cr.move_to(cx - se.width / 2, cy + 16); cr.show_text(sub)

            rrect(cr, cx - 200, cy + 42, 400 * prog, 12, 6)
            cr.set_source_rgba(0.88, 0.48, 0.37, 0.98 * pa); cr.fill()

    # --------------------------------------------------------------------------
    # 5. АНИМАЦИЯ GAMEDEV ENGINE STUDIO: Viewport 2D/3D, Gizmo и сборка шейдеров
    # --------------------------------------------------------------------------
    def draw_gamedev_anim(self, cr, w, h, dt, cf, prog):
        hw = w // 2 + 2
        lx = int(round(-hw * (1.0 - cf)))
        rx = int(round(w - hw * cf))

        for sx in (lx, rx):
            cr.save()
            cr.rectangle(sx, 0, hw, h); cr.clip()
            cr.set_source_rgb(0.05, 0.067, 0.090); cr.paint()
            cr.set_line_width(1.0); cr.set_source_rgba(0.28, 0.55, 0.75, 0.14)
            for gx in range(sx, sx + hw, 48): cr.move_to(gx, 0); cr.line_to(gx, h)
            for gy in range(0, h, 48): cr.move_to(sx, gy); cr.line_to(sx + hw, gy)
            cr.stroke()
            cr.restore()

        if cf > 0.80:
            pa = min(1.0, (cf - 0.80) / 0.20)
            cx, cy = w * 0.5, h * 0.5

            # Оси координат X (красная) и Y (зелёная) игрового движка
            cr.set_line_width(2.2)
            cr.set_source_rgba(0.92, 0.32, 0.36, 0.65 * pa); cr.move_to(0, cy); cr.line_to(w, cy); cr.stroke()
            cr.set_source_rgba(0.39, 0.85, 0.58, 0.65 * pa); cr.move_to(cx, 0); cr.line_to(cx, h); cr.stroke()

            rrect(cr, cx - 310, cy - 115, 620, 230, 8)
            cr.set_source_rgba(0.08, 0.10, 0.14, 0.97 * pa); cr.fill_preserve()
            cr.set_line_width(2.0); cr.set_source_rgba(0.28, 0.55, 0.75, 0.95 * pa); cr.stroke()

            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(15); ttl = "🎮 GAMEDEV ENGINE STUDIO // BUILDING SCENE TREE"
            ext = cr.text_extents(ttl); cr.set_source_rgba(0.90, 0.95, 1.0, pa)
            cr.move_to(cx - ext.width / 2, cy - 72); cr.show_text(ttl)

            logs = [
                "[OK] Initializing Wayland 2D/3D Viewport & Coordinate Gizmo...",
                "[OK] Compiling GLSL / Vulkan Shaders & Sprite Atlases...",
                "[OK] Mounting SceneTree Dock, Node2D Registry & Python Inspector...",
                "[OK] Engine IDE Ready (60.0 FPS Locked).",
            ]
            cr.set_font_size(11.5)
            shown_n = max(1, min(len(logs), int(prog * 4.5) + 1))
            for idx, line in enumerate(logs[:shown_n]):
                cr.set_source_rgba(0.39, 0.85, 0.58, 0.95 * pa)
                cr.move_to(cx - 275, cy - 32 + idx * 24); cr.show_text(line)

            rrect(cr, cx - 275, cy + 72, 550 * prog, 12, 4)
            cr.set_source_rgba(0.28, 0.55, 0.75, 0.98 * pa); cr.fill()

    def on_draw(self, _area, cr, w, h, *_args):
        dt = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        if dt < 0.40:
            cf = 1.0 - math.pow(1.0 - (dt / 0.40), 3)
        elif self.open_t is None:
            cf = 1.0
        else:
            cf = 1.0 - math.pow(min(1.0, (dt - self.open_t) / 0.52), 3)

        prog = min(1.0, max(0.0, (dt - 0.35) / 1.55))

        if NEW_ID == "dungeon-of-god":
            self.draw_dungeon_anim(cr, w, h, dt, cf, prog)
        elif NEW_ID == "forest-stream":
            self.draw_forest_anim(cr, w, h, dt, cf, prog)
        elif NEW_ID == "impasto-landscape":
            self.draw_impasto_anim(cr, w, h, dt, cf, prog)
        elif NEW_ID == "gamedev-studio":
            self.draw_gamedev_anim(cr, w, h, dt, cf, prog)
        else:
            self.draw_cyberdeck_anim(cr, w, h, dt, cf, prog)

if __name__ == "__main__":
    WorldTransition().run(None)
