#!/usr/bin/env python3
import sys, os, math, cairo

gt_dir = sys.argv[1]
os.makedirs(os.path.join(gt_dir, "icons"), exist_ok=True)

W, H = 1920, 1080
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
cr = cairo.Context(surf)

def rrect(x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi/2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi/2)
    cr.arc(x + r, y + h - r, r, math.pi/2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3*math.pi/2)
    cr.close_path()

lg = cairo.LinearGradient(0, 0, W, H)
lg.add_color_stop_rgb(0.0, 0.024, 0.031, 0.052)
lg.add_color_stop_rgb(0.5, 0.030, 0.039, 0.066)
lg.add_color_stop_rgb(1.0, 0.020, 0.026, 0.045)
cr.set_source(lg); cr.paint()

for cx, cy, rad, r, g, b, al in [
    (W * 0.50, H * 0.52, 540, 0.25, 0.40, 0.95, 0.11),
    (W * 0.14, H * 0.16, 520, 0.13, 0.72, 0.81, 0.08),
    (W * 0.86, H * 0.84, 520, 0.30, 0.43, 0.96, 0.08),
]:
    rg = cairo.RadialGradient(cx, cy, 10, cx, cy, rad)
    rg.add_color_stop_rgba(0.0, r, g, b, al)
    rg.add_color_stop_rgba(1.0, r, g, b, 0.0)
    cr.set_source(rg); cr.paint()

cr.set_line_width(1.0); cr.set_source_rgba(0.32, 0.44, 0.76, 0.048)
for x in range(96, W, 96): cr.move_to(x, 0); cr.line_to(x, H)
for y in range(96, H, 96): cr.move_to(0, y); cr.line_to(W, y)
cr.stroke()

m, ln = 16, 54
cr.set_line_width(2.4); cr.set_source_rgba(0.30, 0.43, 0.96, 0.72)
for x1, y1, x2, y2, x3, y3 in [
    (m, m + ln, m, m, m + ln, m), (W - m - ln, m, W - m, m, W - m, m + ln),
    (m, H - m - ln, m, H - m, m + ln, H - m), (W - m - ln, H - m, W - m, H - m, W - m, H - m - ln),
]:
    cr.move_to(x1, y1); cr.line_to(x2, y2); cr.line_to(x3, y3)
cr.stroke()

ocx, ocy = W * 0.50, H * 0.53
cr.set_line_width(1.4); cr.set_source_rgba(0.30, 0.43, 0.96, 0.22)
cr.arc(ocx, ocy, 330, 0, 2 * math.pi); cr.stroke()
cr.set_line_width(2.6); cr.set_source_rgba(0.13, 0.72, 0.81, 0.35)
cr.arc(ocx, ocy, 344, -0.55, 0.55); cr.stroke()
cr.arc(ocx, ocy, 344, math.pi - 0.55, math.pi + 0.55); cr.stroke()

cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
tw, th = 640, 46
tx, ty = (W - tw) / 2, 32
rrect(tx, ty, tw, th, 12)
cr.set_source_rgba(0.047, 0.063, 0.106, 0.94); cr.fill_preserve()
cr.set_line_width(1.4); cr.set_source_rgba(0.145, 0.196, 0.314, 1.0); cr.stroke()
cr.set_font_size(12); cr.set_source_rgb(0.90, 0.93, 1.0)
cr.move_to(tx + 38, ty + 27); cr.show_text("◈ CYBER DECK // UEFI BOOT GATE   •   ARCH X86_64   •   DRM READY")

wings = [
    (70, "◈ KERNEL & BOOT MATRIX", True, [("STAGE_01", "UEFI GPT DISPATCH", False), ("STAGE_02", "LINUX KERNEL IMAGE", True), ("INITRAMFS", "EARLY KMS // ZSTD", False), ("DISPLAY", "1920x1080 GFXTERM", False)]),
    (W - 350, "◈ TARGET ENVIRONMENTS", False, [("PROFILE_A", "CYBERDECK // AUTO", True), ("HARDWARE", "PC & LAPTOP ENGINE", True), ("SECURITY", "PAM + HYPRLOCK", False), ("CURSOR", "CYBERDECK 28PX", False)]),
]
for wx, wtitle, is_left, rows in wings:
    wy, ww, wh = int(H * 0.39), 280, 210
    rrect(wx, wy, ww, wh, 14)
    cr.set_source_rgba(0.047, 0.063, 0.106, 0.90); cr.fill_preserve()
    cr.set_line_width(1.3); cr.set_source_rgba(0.14, 0.20, 0.33, 0.95); cr.stroke()
    cr.set_source_rgb(*( (0.30, 0.43, 0.96) if is_left else (0.13, 0.72, 0.81) ))
    cr.rectangle(wx if is_left else wx + ww - 3.5, wy + 18, 3.5, 30); cr.fill()
    cr.set_font_size(12); cr.set_source_rgb(0.88, 0.92, 1.0)
    cr.move_to(wx + 18, wy + 34); cr.show_text(wtitle)
    cr.set_font_size(11)
    for idx, (k, v, hi) in enumerate(rows):
        ry = wy + 76 + idx * 34
        cr.set_source_rgb(0.46, 0.54, 0.72); cr.move_to(wx + 18, ry); cr.show_text(k)
        cr.set_source_rgb(*( (0.13, 0.72, 0.81) if hi else (0.76, 0.82, 0.95) ))
        cr.move_to(wx + 108, ry); cr.show_text(f"// {v}")

mx, my, mw, mh = int(W * 0.27), int(H * 0.26), int(W * 0.46), int(H * 0.50)
rrect(mx, my, mw, mh, 16)
cr.set_source_rgba(0.051, 0.067, 0.110, 0.96); cr.fill_preserve()
cr.set_line_width(1.5); cr.set_source_rgba(0.15, 0.20, 0.33, 1.0); cr.stroke()
cr.set_source_rgb(0.13, 0.72, 0.81); cr.rectangle(mx + mw / 2 - 90, my, 180, 2.5); cr.fill()

cr.set_line_width(2.5)
for bx, by, dx, dy, col in [
    (mx, my, 1, 1, (0.13,0.72,0.81)), (mx+mw, my, -1, 1, (0.13,0.72,0.81)),
    (mx, my+mh, 1, -1, (0.30,0.43,0.96)), (mx+mw, my+mh, -1, -1, (0.30,0.43,0.96))
]:
    cr.set_source_rgb(*col)
    cr.move_to(bx + dx * 26, by); cr.line_to(bx, by); cr.line_to(bx, by + dy * 26); cr.stroke()

rrect(int(W * 0.23), int(H * 0.855), int(W * 0.54), 46, 12)
cr.set_source_rgba(0.051, 0.067, 0.110, 0.94); cr.fill_preserve()
cr.set_line_width(1.3); cr.set_source_rgba(0.15, 0.20, 0.33, 1.0); cr.stroke()
surf.write_to_png(os.path.join(gt_dir, "background.png"))

S, R = 32, 8
pill = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); pc = cairo.Context(pill)
pc.new_sub_path()
pc.arc(S - R, R, R, -math.pi/2, 0); pc.arc(S - R, S - R, R, 0, math.pi/2)
pc.arc(R, S - R, R, math.pi/2, math.pi); pc.arc(R, R, R, math.pi, 3*math.pi/2); pc.close_path()
pc.set_source_rgba(0.086, 0.141, 0.251, 0.98); pc.fill_preserve()
pc.set_line_width(1.6); pc.set_source_rgba(0.30, 0.43, 0.96, 0.98); pc.stroke()
pc.set_source_rgba(0.13, 0.72, 0.81, 1.0); pc.rectangle(2, 5, 3.5, S - 10); pc.fill()

for name, (sx, sy, sw, sh) in {"nw":(0,0,8,8),"n":(8,0,16,8),"ne":(24,0,8,8),"w":(0,8,8,16),"c":(8,8,16,16),"e":(24,8,8,16),"sw":(0,24,8,8),"s":(8,24,16,8),"se":(24,24,8,8)}.items():
    sub = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh); sc = cairo.Context(sub)
    sc.set_source_surface(pill, -sx, -sy); sc.paint()
    sub.write_to_png(os.path.join(gt_dir, f"select_{name}.png"))

def make_icon(fname, kind):
    ic = cairo.ImageSurface(cairo.FORMAT_ARGB32, 32, 32); k = cairo.Context(ic); k.set_line_width(2.2)
    if kind == "arch":
        k.set_source_rgb(0.13, 0.72, 0.81)
        k.move_to(16, 4); k.line_to(27, 27); k.line_to(20, 27); k.line_to(16, 19); k.line_to(12, 27); k.line_to(5, 27); k.close_path(); k.fill()
    elif kind == "win":
        k.set_source_rgb(0.30, 0.43, 0.96)
        for bx, by in [(5,5),(17,5),(5,17),(17,17)]: k.rectangle(bx, by, 10, 10); k.fill()
    else:
        k.set_source_rgb(0.66, 0.74, 0.92); k.arc(16, 16, 10, 0, 2*math.pi); k.stroke()
    ic.write_to_png(os.path.join(gt_dir, "icons", fname))

for fn in ("arch.png", "gnu-linux.png", "linux.png", "os.png", "cachyos.png", "endeavouros.png"):
    make_icon(fn, "arch")
make_icon("windows.png", "win")
make_icon("efi.png", "efi")
make_icon("recovery.png", "efi")
