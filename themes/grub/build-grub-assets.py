#!/usr/bin/python3
import sys, os, math, cairo

gt_dir = sys.argv[1] if len(sys.argv) > 1 else "/boot/grub/themes/cyberdeck-grub"
os.makedirs(os.path.join(gt_dir, "icons"), exist_ok=True)

W, H = 1920, 1080
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
cr = cairo.Context(surf)

BLUE  = (0.361, 0.384, 0.427)
GREEN = (0.580, 0.608, 0.655)
RED   = (0.450, 0.475, 0.515)

def rrect(x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi/2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    cr.arc(x + r, y + h - r, r, math.pi/2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3*math.pi/2)
    cr.close_path()

# 1. Фон 2D/3D Viewport с инженерной сеткой и координатными линейками
lg = cairo.LinearGradient(0, 0, W, H)
lg.add_color_stop_rgb(0.0, 0.067, 0.071, 0.082)
lg.add_color_stop_rgb(0.5, 0.082, 0.086, 0.098)
lg.add_color_stop_rgb(1.0, 0.063, 0.067, 0.078)
cr.set_source(lg); cr.paint()

rg = cairo.RadialGradient(W * 0.5, H * 0.52, 20, W * 0.5, H * 0.52, 620)
rg.add_color_stop_rgba(0.0, *BLUE, 0.16)
rg.add_color_stop_rgba(0.6, *GREEN, 0.06)
rg.add_color_stop_rgba(1.0, 0, 0, 0, 0)
cr.set_source(rg); cr.paint()

cr.set_line_width(0.8); cr.set_source_rgba(*BLUE, 0.05)
for x in range(32, W, 32): cr.move_to(x, 0); cr.line_to(x, H)
for y in range(32, H, 32): cr.move_to(0, y); cr.line_to(W, y)
cr.stroke()

cr.set_line_width(1.2); cr.set_source_rgba(*BLUE, 0.14)
for x in range(128, W, 128): cr.move_to(x, 0); cr.line_to(x, H)
for y in range(128, H, 128): cr.move_to(0, y); cr.line_to(W, y)
cr.stroke()

# Оси координат X/Y
cx, cy = W * 0.5, H * 0.52
cr.set_line_width(1.6)
cr.set_source_rgba(*RED, 0.40); cr.move_to(0, cy); cr.line_to(W, cy); cr.stroke()
cr.set_source_rgba(*GREEN, 0.40); cr.move_to(cx, 0); cr.line_to(cx, H); cr.stroke()

# 2. Боковые панели телеметрии загрузчика
cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
for bx, hdr, rows, col in [
    (64, "📂 BOOT_PIPELINE // STAGE_01", [("KERNEL_IMG", "LINUX-ZEN 64-BIT"), ("EARLY_KMS", "DRM WAYLAND READY"), ("SHADER_MEM", "10 GB RESERVED"), ("IOMMU_DMA", "ACTIVE // LOCKED")], BLUE),
    (W - 354, "🔍 ENGINE_INSPECTOR // TARGET", [("DISPLAY_HZ", "HIGH REFRESH RATE"), ("CPU_SCHED", "ADAPTIVE GOVERNOR"), ("AUDIO_PIPE", "LOW-LATENCY DSP"), ("OPERATOR", "ssOh-v1 // DEV")], GREEN),
]:
    by, bw, bh = int(cy - 105), 290, 210
    rrect(bx, by, bw, bh, 8)
    cr.set_source_rgba(0.090, 0.098, 0.114, 0.94); cr.fill_preserve()
    cr.set_line_width(1.4); cr.set_source_rgba(*col, 0.65); cr.stroke()
    cr.set_source_rgb(*col); cr.rectangle(bx, by, bw, 3); cr.fill()
    cr.set_font_size(11); cr.set_source_rgb(0.90, 0.95, 1.0)
    cr.move_to(bx + 16, by + 28); cr.show_text(hdr)
    cr.set_font_size(10.5)
    for idx, (k, v) in enumerate(rows):
        ry = by + 62 + idx * 36
        cr.set_source_rgb(0.55, 0.62, 0.72); cr.move_to(bx + 16, ry); cr.show_text(k)
        cr.set_source_rgb(*GREEN); cr.move_to(bx + 115, ry); cr.show_text(f"⟫ {v}")

# 3. Центральный контейнер меню ядер GRUB
mx, my, mw, mh = int(W * 0.27), int(H * 0.26), int(W * 0.46), int(H * 0.50)
rrect(mx, my, mw, mh, 10)
cr.set_source_rgba(0.082, 0.086, 0.098, 0.97); cr.fill_preserve()
cr.set_line_width(1.6); cr.set_source_rgba(*BLUE, 0.65); cr.stroke()
cr.set_source_rgb(*GREEN); cr.rectangle(mx + mw * 0.5 - 110, my, 220, 3); cr.fill()

# Угловые скобы Gizmo на окне выбора ядра
cr.set_line_width(2.6)
for x0, y0, dx, dy, col in [(mx, my, 1, 1, GREEN), (mx+mw, my, -1, 1, BLUE), (mx, my+mh, 1, -1, BLUE), (mx+mw, my+mh, -1, -1, RED)]:
    cr.set_source_rgb(*col)
    cr.move_to(x0 + dx * 26, y0); cr.line_to(x0, y0); cr.line_to(x0, y0 + dy * 26); cr.stroke()

surf.write_to_png(os.path.join(gt_dir, "background.png"))

# 4. Плашка активного пункта GRUB (с изумрудным индикатором Node2D слева)
S, R = 32, 6
pill = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S)
pc = cairo.Context(pill)
pc.new_sub_path()
pc.arc(S - R, R, R, -math.pi/2, 0); pc.arc(S - R, S - R, R, 0, math.pi/2)
pc.arc(R, S - R, R, math.pi/2, math.pi); pc.arc(R, R, R, math.pi, 3*math.pi/2); pc.close_path()
pc.set_source_rgba(0.14, 0.15, 0.18, 0.98); pc.fill_preserve()
pc.set_line_width(1.6); pc.set_source_rgba(*BLUE, 0.98); pc.stroke()
pc.set_source_rgba(*GREEN, 1.0); pc.rectangle(2, 5, 3.5, S - 10); pc.fill()

for name, (sx, sy, sw, sh) in {"nw":(0,0,8,8),"n":(8,0,16,8),"ne":(24,0,8,8),"w":(0,8,8,16),"c":(8,8,16,16),"e":(24,8,8,16),"sw":(0,24,8,8),"s":(8,24,16,8),"se":(24,24,8,8)}.items():
    sub = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
    sc = cairo.Context(sub)
    sc.set_source_surface(pill, -sx, -sy); sc.paint()
    sub.write_to_png(os.path.join(gt_dir, f"select_{name}.png"))
