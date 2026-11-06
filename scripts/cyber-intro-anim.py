#!/usr/bin/env python3
import os, sys, math, time, random
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

MODE = sys.argv[1] if len(sys.argv) > 1 else "work"
LOGO_PATH = os.path.expanduser(f"~/.config/hypr/assets/{MODE}_logo.png")
TITLE_TXT = "◈ GAMING DECK // DIRECT SCANOUT ENGAGED" if MODE == "gaming" else ("◈ CYBER DECK // ADAPTIVE HARDWARE MATRIX ENGAGED" if MODE == "cyberdeck" else "◈ WORK DECK // FREE-WORKSPACE MATRIX ENGAGED")
LEFT_SPECS = (
    [("PROFILE", "GAMING // MAX_FPS"), ("SCANOUT", "DRM DIRECT BYPASS"), ("GOVERNOR", "PERFORMANCE LOCK"), ("SHADERS", "10GB CACHE READY"), ("NET_DPI", "ZAPRET NFQWS ON")]
    if MODE == "gaming" else
    [("PROFILE", "HYPRWORK // CLEAN"), ("WORKSPACES", "UNLIMITED ENGINE"), ("TUNNEL", "ISOLATED VPN ON"), ("OSD_CORE", "MAKO + XKB LIVE"), ("POWER", "BALANCED // ECO")]
)
RIGHT_SPECS = [
    ("COMPOSITOR", "HYPRLAND WAYLAND"),
    ("LAYER_SHELL", "OVERLAY // LOCK"),
    ("CURSOR_DRV", "ALPORA CYBER 28PX"),
    ("ICON_PACK", "VECTOR HUD SVG"),
    ("AUDIO_DSP", "PIPEWIRE // READY"),
]
SUB_MODULES = (
    ["[OK] DRM_SCANOUT", "[OK] GAME_BOOST", "[OK] PIPEWIRE_DSP", "[OK] LAYER_HUD"]
    if MODE == "gaming" else
    ["[OK] VPN_ISOLATION", "[OK] FREE_WS_CORE", "[OK] MAKO_DAEMON", "[OK] CYBER_HUD"]
)

def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()

def chamfer_rect(cr, x, y, w, h, c):
    cr.new_sub_path()
    cr.move_to(x + c, y)
    cr.line_to(x + w - c, y)
    cr.line_to(x + w, y + c)
    cr.line_to(x + w, y + h - c)
    cr.line_to(x + w - c, y + h)
    cr.line_to(x + c, y + h)
    cr.line_to(x, y + h - c)
    cr.line_to(x, y + c)
    cr.close_path()

class IntroApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=f"org.alpora.Intro.{MODE}")
        self.t0 = None
        self.wall_surf = None
        self.wall_dims = (0, 0)
        self.circuits = []
        self.logo = cairo.ImageSurface.create_from_png(LOGO_PATH) if os.path.isfile(LOGO_PATH) else None
        random.seed(42)
        self.sparks = [
            (random.uniform(0.06, 0.94), random.uniform(45.0, 210.0), random.uniform(-38.0, 38.0), random.uniform(1.6, 3.4), random.random())
            for _ in range(36)
        ]

    def do_activate(self):
        prov = Gtk.CssProvider()
        css = "window { background-color: transparent; }"
        if hasattr(prov, "load_from_string"):
            prov.load_from_string(css)
        else:
            prov.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        win = Gtk.ApplicationWindow(application=self)
        if HAS_LAYER and Gtk4LayerShell.is_supported():
            Gtk4LayerShell.init_for_window(win)
            Gtk4LayerShell.set_namespace(win, "alpora-intro-overlay")
            Gtk4LayerShell.set_layer(win, Gtk4LayerShell.Layer.OVERLAY)
            for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT, Gtk4LayerShell.Edge.RIGHT):
                Gtk4LayerShell.set_anchor(win, edge, True)
            Gtk4LayerShell.set_exclusive_zone(win, -1)
            Gtk4LayerShell.set_keyboard_mode(win, Gtk4LayerShell.KeyboardMode.NONE)
        else:
            win.fullscreen()

        area = Gtk.DrawingArea()
        area.set_hexpand(True)
        area.set_vexpand(True)
        area.set_draw_func(self.on_draw)
        win.set_child(area)

        self.t0 = time.monotonic()
        GLib.timeout_add(14, self.on_tick, area)
        win.present()

    def build_wall_surface(self, w, h):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surf)
        cx, cy = w * 0.5, h * 0.48

        # 1. Бронированная матовая основа стенки
        lg = cairo.LinearGradient(0, 0, w, h)
        lg.add_color_stop_rgb(0.0, 0.022, 0.029, 0.050)
        lg.add_color_stop_rgb(0.5, 0.031, 0.041, 0.072)
        lg.add_color_stop_rgb(1.0, 0.019, 0.025, 0.044)
        cr.set_source(lg)
        cr.paint()

        # Радиальные неоновые подсветки на самой бронеплите
        for gx, gy, grad, r, g, b, al in [
            (cx, cy, 460, 0.13, 0.72, 0.81, 0.16),
            (w * 0.16, h * 0.25, 420, 0.30, 0.43, 0.96, 0.11),
            (w * 0.84, h * 0.75, 420, 0.30, 0.43, 0.96, 0.11),
        ]:
            rg = cairo.RadialGradient(gx, gy, 12, gx, gy, grad)
            rg.add_color_stop_rgba(0.0, r, g, b, al)
            rg.add_color_stop_rgba(1.0, r, g, b, 0.0)
            cr.set_source(rg)
            cr.paint()

        # 2. Рельефные секционные бронелисты и диагональные швы обшивки
        for px, py, pw, ph in [
            (36, 72, int(w * 0.27), h - 144),
            (w - 36 - int(w * 0.27), 72, int(w * 0.27), h - 144),
        ]:
            chamfer_rect(cr, px, py, pw, ph, 22)
            cr.set_source_rgba(0.043, 0.058, 0.102, 0.78)
            cr.fill_preserve()
            cr.set_line_width(1.4)
            cr.set_source_rgba(0.20, 0.29, 0.50, 0.85)
            cr.stroke()

            # Заклёпки / силовые болты по углам бронеплит
            for rx, ry in [(px + 16, py + 16), (px + pw - 16, py + 16), (px + 16, py + ph - 16), (px + pw - 16, py + ph - 16)]:
                cr.arc(rx, ry, 3.2, 0, 2 * math.pi)
                cr.set_source_rgba(0.13, 0.72, 0.81, 0.65)
                cr.fill()

        # 3. Гексагональные соты на левом и правом крыле стенки
        hex_r = 22
        dx = hex_r * 1.732
        dy = hex_r * 1.5
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.30, 0.44, 0.86, 0.085)
        for wing_x0, wing_x1 in [(56, int(w * 0.29)), (int(w * 0.71), w - 56)]:
            row = 0
            y = 105.0
            while y < h - 105:
                x = wing_x0 + (dx * 0.5 if row % 2 else 0.0)
                while x < wing_x1:
                    cr.new_sub_path()
                    for i in range(6):
                        ang = math.pi / 3 * i + math.pi / 6
                        vx, vy = x + (hex_r - 2) * math.cos(ang), y + (hex_r - 2) * math.sin(ang)
                        if i == 0: cr.move_to(vx, vy)
                        else: cr.line_to(vx, vy)
                    cr.close_path()
                    cr.stroke()
                    x += dx
                y += dy
                row += 1

        # 4. Инженерная координатная сетка и прицельные перекрестия по центру
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.32, 0.45, 0.82, 0.065)
        for x in range(64, w, 64):
            cr.move_to(x, 52); cr.line_to(x, h - 52)
        for y in range(64, h - 52, 64):
            cr.move_to(0, y); cr.line_to(w, y)
        cr.stroke()

        cr.set_source_rgba(0.13, 0.72, 0.81, 0.22)
        for x in range(192, w - 120, 192):
            for y in range(192, h - 120, 192):
                cr.move_to(x - 5, y); cr.line_to(x + 5, y)
                cr.move_to(x, y - 5); cr.line_to(x, y + 5)
        cr.stroke()

        # 5. Схемотехнические магистрали от краёв стенки к центральному магнитному гнезду
        self.circuits = [
            [(70, cy - 150), (w * 0.26, cy - 150), (w * 0.33, cy - 75), (cx - 195, cy - 75)],
            [(70, cy),       (w * 0.28, cy),       (cx - 205, cy)],
            [(70, cy + 150), (w * 0.26, cy + 150), (w * 0.33, cy + 75), (cx - 195, cy + 75)],
            [(w - 70, cy - 150), (w * 0.74, cy - 150), (w * 0.67, cy - 75), (cx + 195, cy - 75)],
            [(w - 70, cy),       (w * 0.72, cy),       (cx + 205, cy)],
            [(w - 70, cy + 150), (w * 0.74, cy + 150), (w * 0.67, cy + 75), (cx + 195, cy + 75)],
        ]
        cr.set_line_width(2.0)
        for path in self.circuits:
            cr.set_source_rgba(0.30, 0.43, 0.96, 0.34)
            cr.move_to(*path[0])
            for px, py in path[1:]:
                cr.line_to(px, py)
            cr.stroke()
            for px, py in path:
                cr.arc(px, py, 3.8, 0, 2 * math.pi)
                cr.set_source_rgba(0.13, 0.72, 0.81, 0.65)
                cr.fill()

        # 6. Встроенные в стенку тактические терминалы телеметрии (слева и справа)
        cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for bx, hdr, specs, accent_col in [
            (66, "◈ BULKHEAD // SECTOR_A", LEFT_SPECS, (0.13, 0.72, 0.81)),
            (w - 366, "◈ TELEMETRY // SECTOR_B", RIGHT_SPECS, (0.30, 0.43, 0.96)),
        ]:
            by, bw, bh = int(cy - 122), 300, 244
            chamfer_rect(cr, bx, by, bw, bh, 14)
            cr.set_source_rgba(0.035, 0.048, 0.086, 0.92)
            cr.fill_preserve()
            cr.set_line_width(1.5)
            cr.set_source_rgba(*accent_col, 0.75)
            cr.stroke()

            cr.set_source_rgba(*accent_col, 0.18)
            cr.rectangle(bx + 10, by + 10, bw - 20, 28)
            cr.fill()

            cr.set_font_size(11)
            cr.set_source_rgb(0.90, 0.94, 1.0)
            cr.move_to(bx + 20, by + 28)
            cr.show_text(hdr)

            cr.set_font_size(10.5)
            for idx, (k, v) in enumerate(specs):
                ry = by + 64 + idx * 36
                cr.set_source_rgba(0.50, 0.60, 0.82, 0.9)
                cr.move_to(bx + 20, ry)
                cr.show_text(k)
                cr.set_source_rgb(0.40, 0.86, 0.94)
                cr.move_to(bx + 126, ry)
                cr.show_text(f"⟫ {v}")
                cr.set_source_rgba(0.18, 0.25, 0.42, 0.55)
                cr.rectangle(bx + 20, ry + 8, bw - 40, 1)
                cr.fill()

        # 7. Верхняя и нижняя силовые рельсы бронестворки + зубцы замка на правой кромке
        cr.set_source_rgba(0.05, 0.07, 0.13, 0.96)
        cr.rectangle(0, 0, w, 52)
        cr.rectangle(0, h - 52, w, 52)
        cr.fill()

        cr.set_line_width(2.0)
        cr.set_source_rgba(0.30, 0.43, 0.96, 0.75)
        cr.move_to(0, 52); cr.line_to(w, 52)
        cr.move_to(0, h - 52); cr.line_to(w, h - 52)
        cr.stroke()

        # Тактические предупреждающие шевроны на рельсах
        cr.set_line_width(3.0)
        cr.set_source_rgba(0.13, 0.72, 0.81, 0.42)
        for x in range(24, w - 24, 22):
            cr.move_to(x, 14); cr.line_to(x + 11, 38)
            cr.move_to(x + 11, h - 38); cr.line_to(x, h - 14)
        cr.stroke()

        # Механические замковые зубцы вдоль передней движущейся кромки стенки (x = w)
        cr.set_source_rgba(0.09, 0.14, 0.25, 0.98)
        for y in range(72, h - 90, 64):
            cr.rectangle(w - 18, y, 18, 34)
        cr.fill()

        # 8. Тонкие кибер-сканлайны по всей поверхности стенки
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.20)
        for y in range(0, h, 4):
            cr.move_to(0, y); cr.line_to(w, y)
        cr.stroke()

        self.wall_surf = surf
        self.wall_dims = (w, h)

    def on_tick(self, area):
        if (time.monotonic() - self.t0) >= 1.95:
            self.quit()
            return False
        area.queue_draw()
        return True

    def on_draw(self, _area, cr, w, h, *_args):
        if self.wall_surf is None or self.wall_dims != (w, h):
            self.build_wall_surface(w, h)

        dt = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        # Фаза 1 (0..0.46с): бронестена выезжает слева; Фаза 2 (0.46..1.38с): замок и эффекты; Фаза 3 (1.38..1.95с): уход влево
        moving = True
        if dt < 0.46:
            u = dt / 0.46
            wall_frac = 1.0 - math.pow(1.0 - u, 3)
        elif dt < 1.38:
            wall_frac = 1.0
            moving = False
        else:
            u = min(1.0, (dt - 1.38) / 0.57)
            wall_frac = 1.0 - math.pow(u, 3)

        wall_w = max(2, int(w * wall_frac))
        offset_x = wall_w - w
        cx, cy = w * 0.5, h * 0.48

        # Отрисовка физически сдвигающейся бронестенки (все декорации едут вместе со стенкой!)
        cr.save()
        cr.rectangle(0, 0, wall_w, h)
        cr.clip()
        cr.translate(offset_x, 0)

        cr.set_source_surface(self.wall_surf, 0, 0)
        cr.paint()

        # Эффект 1: Бегущие энергетические импульсы по дорожкам платы к центру стенки
        pulse_pos = (dt * 1.9) % 1.0
        for path in self.circuits:
            segs = list(zip(path[:-1], path[1:]))
            idx = min(len(segs) - 1, int(pulse_pos * len(segs)))
            local_t = (pulse_pos * len(segs)) - idx
            (x1, y1), (x2, y2) = segs[idx]
            px, py = x1 + (x2 - x1) * local_t, y1 + (y2 - y1) * local_t
            rg = cairo.RadialGradient(px, py, 1, px, py, 16)
            rg.add_color_stop_rgba(0.0, 0.55, 0.96, 1.0, 0.95)
            rg.add_color_stop_rgba(1.0, 0.13, 0.72, 0.81, 0.0)
            cr.set_source(rg)
            cr.arc(px, py, 16, 0, 2 * math.pi)
            cr.fill()

        # Эффект 2: Вертикальный лазерный луч сканирования по поверхности стенки
        scan_y = 54 + ((dt * 620.0) % max(1, (h - 108)))
        sg = cairo.LinearGradient(0, scan_y - 26, 0, scan_y + 6)
        sg.add_color_stop_rgba(0.0, 0.13, 0.72, 0.81, 0.0)
        sg.add_color_stop_rgba(0.85, 0.13, 0.72, 0.81, 0.14)
        sg.add_color_stop_rgba(1.0, 0.45, 0.92, 1.0, 0.32)
        cr.set_source(sg)
        cr.rectangle(0, scan_y - 26, w, 32)
        cr.fill()

        # Эффект 3: Встречные сегментированные радарные кольца и силовые зажимы гнезда
        a1, a2 = dt * 1.8, -dt * 2.4
        cr.set_line_width(2.6)
        cr.set_source_rgba(0.30, 0.43, 0.96, 0.75)
        for off in (0, math.pi * 0.66, math.pi * 1.33):
            cr.arc(cx, cy, 174, a1 + off, a1 + off + 0.75)
            cr.stroke()

        cr.set_line_width(2.2)
        cr.set_source_rgba(0.13, 0.72, 0.81, 0.85)
        for off in (0, math.pi):
            cr.arc(cx, cy, 152, a2 + off, a2 + off + 1.35)
            cr.stroke()

        # 4 гидравлических силовых зажима, смыкающихся вокруг логотипа в момент примагничивания
        clamp_u = min(1.0, max(0.0, (dt - 0.26) / 0.28))
        clamp_dist = 198 - 28 * (1.0 - math.pow(1.0 - clamp_u, 3))
        cr.set_line_width(3.2)
        cr.set_source_rgba(0.66, 0.85, 1.0, 0.90)
        for ang_deg in (45, 135, 225, 315):
            rad = math.radians(ang_deg)
            jx, jy = cx + clamp_dist * math.cos(rad), cy + clamp_dist * math.sin(rad)
            p_rad = rad + math.pi / 2
            cr.move_to(jx + 14 * math.cos(p_rad) + 8 * math.cos(rad), jy + 14 * math.sin(p_rad) + 8 * math.sin(rad))
            cr.line_to(jx + 14 * math.cos(p_rad), jy + 14 * math.sin(p_rad))
            cr.line_to(jx - 14 * math.cos(p_rad), jy - 14 * math.sin(p_rad))
            cr.line_to(jx - 14 * math.cos(p_rad) + 8 * math.cos(rad), jy - 14 * math.sin(p_rad) + 8 * math.sin(rad))
            cr.stroke()

        # Эффект 4: Примагничивание логотипа + вспышка фиксации + двойная ударная волна
        if self.logo and dt > 0.08:
            lu = min(1.0, (dt - 0.08) / 0.50)
            damped = 1.0 - math.exp(-7.5 * lu) * math.cos(12.0 * lu)
            scale = 0.68 + 0.32 * damped
            alpha = min(1.0, lu * 2.5)

            # Энергетическая вспышка и ударные волны при защёлкивании магнита
            if 0.28 < lu < 1.0:
                sh = (lu - 0.28) / 0.72
                flash_a = max(0.0, (1.0 - sh * 2.2) * 0.35)
                if flash_a > 0:
                    fg = cairo.RadialGradient(cx, cy, 5, cx, cy, 260)
                    fg.add_color_stop_rgba(0.0, 0.85, 0.97, 1.0, flash_a)
                    fg.add_color_stop_rgba(1.0, 0.13, 0.72, 0.81, 0.0)
                    cr.set_source(fg)
                    cr.arc(cx, cy, 260, 0, 2 * math.pi)
                    cr.fill()

                for mult, col in [(1.0, (0.13, 0.72, 0.81)), (0.62, (0.30, 0.43, 0.96))]:
                    ring_r = 118 + sh * 230 * mult
                    cr.set_line_width(2.6)
                    cr.set_source_rgba(*col, max(0.0, (1.0 - sh) * 0.9))
                    cr.arc(cx, cy, ring_r, 0, 2 * math.pi)
                    cr.stroke()

            lw, lh = self.logo.get_width(), self.logo.get_height()
            cr.save()
            cr.translate(cx, cy)
            cr.scale(scale, scale)
            cr.translate(-lw / 2, -lh / 2)
            cr.set_source_surface(self.logo, 0, 0)
            cr.paint_with_alpha(alpha)
            cr.restore()

            # Нижний HUD-блок синхронизации на стенке
            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(15)
            ext = cr.text_extents(TITLE_TXT)
            cr.set_source_rgba(0.90, 0.94, 1.0, alpha)
            cr.move_to(cx - ext.width / 2, cy + 218)
            cr.show_text(TITLE_TXT)

            # Сегментированный индикатор заряда/инициализации
            prog = min(1.0, max(0.0, (dt - 0.12) / 1.05))
            segs_n = 20
            sb_w, sb_gap = 17, 4
            total_bw = segs_n * sb_w + (segs_n - 1) * sb_gap
            bx0, by0 = cx - total_bw / 2, cy + 232
            active_segs = int(round(prog * segs_n))
            for s_i in range(segs_n):
                sx = bx0 + s_i * (sb_w + sb_gap)
                if s_i < active_segs:
                    cr.set_source_rgba(0.13, 0.72, 0.81, 0.95)
                else:
                    cr.set_source_rgba(0.10, 0.15, 0.26, 0.85)
                cr.rectangle(sx, by0, sb_w, 9)
                cr.fill()

            cr.set_font_size(11)
            m_txt = "   •   ".join(SUB_MODULES[:max(1, int(prog * 4.3))])
            m_ext = cr.text_extents(m_txt)
            cr.set_source_rgba(0.39, 0.90, 0.75, alpha * 0.95)
            cr.move_to(cx - m_ext.width / 2, cy + 262)
            cr.show_text(m_txt)

        cr.restore()

        # Эффект 5: Плазменная режущая кромка и разлетающиеся искры на границе движения стены
        if wall_w < w - 2:
            eg = cairo.LinearGradient(wall_w - 28, 0, wall_w + 18, 0)
            eg.add_color_stop_rgba(0.0, 0.30, 0.43, 0.96, 0.0)
            eg.add_color_stop_rgba(0.65, 0.13, 0.72, 0.81, 0.55)
            eg.add_color_stop_rgba(0.82, 0.92, 0.97, 1.00, 0.98)
            eg.add_color_stop_rgba(1.0, 0.30, 0.43, 0.96, 0.0)
            cr.set_source(eg)
            cr.rectangle(wall_w - 28, 0, 46, h)
            cr.fill()

            cr.set_line_width(2.6)
            cr.set_source_rgba(0.92, 0.98, 1.0, 0.98)
            cr.move_to(wall_w, 0)
            cr.line_to(wall_w, h)
            cr.stroke()

            if moving:
                for y_rel, spd, vy, sz, ph in self.sparks:
                    cyc = ((dt * 3.4) + ph) % 1.0
                    sx = wall_w - cyc * spd
                    sy = y_rel * h + cyc * vy
                    sp_a = (1.0 - cyc) * 0.95
                    cr.set_line_width(sz)
                    cr.set_source_rgba(0.45, 0.92, 1.0, sp_a)
                    cr.move_to(sx, sy)
                    cr.line_to(sx + 12 * (1.0 - cyc * 0.5), sy - vy * 0.06)
                    cr.stroke()

if __name__ == "__main__":
    IntroApp().run(None)
