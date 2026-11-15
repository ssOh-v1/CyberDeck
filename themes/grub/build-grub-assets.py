#!/usr/bin/env python3
import sys, os, math, cairo

gt_dir = sys.argv[1]
prim_hex = sys.argv[2] if len(sys.argv) > 2 else "#4c6ef5"
acc_hex  = sys.argv[3] if len(sys.argv) > 3 else "#22b8cf"

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

PRIM = hex_rgb(prim_hex)
ACC  = hex_rgb(acc_hex)

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

for cx, cy, rad, col, al in [
    (W * 0.50, H * 0.52, 540, PRIM, 0.12),
    (W * 0.14, H * 0.16, 520, ACC,  0.09),
    (W * 0.86, H * 0.84, 520, PRIM, 0.09),
]:
    rg = cairo.RadialGradient(cx, cy, 10, cx, cy, rad)
    rg.add_color_stop_rgba(0.0, *col, al)
    rg.add_color_stop_rgba(1.0, *col, 0.0)
    cr.set_source(rg); cr.paint()

cr.set_line_width(1.0); cr.set_source_rgba(*PRIM, 0.055)
for x in range(96, W, 96): cr.move_to(x, 0); cr.line_to(x, H)
for y in range(96, H, 96): cr.move_to(0, y); cr.line_to(W, y)
cr.stroke()

m, ln = 16, 54
cr.set_line_width(2.4); cr.set_source_rgba(*PRIM, 0.78)
for x1, y1, x2, y2, x3, y3 in [
    (m, m + ln, m, m, m + ln, m), (W - m - ln, m, W - m, m, W - m, m + ln),
    (m, H - m - ln, m, H - m, m + ln, H - m), (W - m - ln, H - m, W - m, H - m, W - m, H - m - ln),
]:
    cr.move_to(x1, y1); cr.line_to(x2, y2); cr.line_to(x3, y3)
cr.stroke()

ocx, ocy = W * 0.50, H * 0.53
cr.set_line_width(1.4); cr.set_source_rgba(*PRIM, 0.24)
cr.arc(ocx, ocy, 330, 0, 2 * math.pi); cr.stroke()
cr.set_line_width(2.6); cr.set_source_rgba(*ACC, 0.42)
cr.arc(ocx, ocy, 344, -0.55, 0.55); cr.stroke()
cr.arc(ocx, ocy, 344, math.pi - 0.55, math.pi + 0.55); cr.stroke()

mx, my, mw, mh = int(W * 0.27), int(H * 0.26), int(W * 0.46), int(H * 0.50)
rrect(mx, my, mw, mh, 16)
cr.set_source_rgba(0.051, 0.067, 0.110, 0.96); cr.fill_preserve()
cr.set_line_width(1.5); cr.set_source_rgba(*PRIM, 0.45); cr.stroke()
cr.set_source_rgb(*ACC); cr.rectangle(mx + mw / 2 - 90, my, 180, 2.5); cr.fill()

cr.set_line_width(2.5)
for bx, by, dx, dy, col in [
    (mx, my, 1, 1, ACC), (mx+mw, my, -1, 1, ACC),
    (mx, my+mh, 1, -1, PRIM), (mx+mw, my+mh, -1, -1, PRIM)
]:
    cr.set_source_rgb(*col)
    cr.move_to(bx + dx * 26, by); cr.line_to(bx, by); cr.line_to(bx, by + dy * 26); cr.stroke()

surf.write_to_png(os.path.join(gt_dir, "background.png"))

S, R = 32, 8
pill = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); pc = cairo.Context(pill)
pc.new_sub_path()
pc.arc(S - R, R, R, -math.pi/2, 0); pc.arc(S - R, S - R, R, 0, math.pi/2)
pc.arc(R, S - R, R, math.pi/2, math.pi); pc.arc(R, R, R, math.pi, 3*math.pi/2); pc.close_path()
pc.set_source_rgba(0.086, 0.141, 0.251, 0.98); pc.fill_preserve()
pc.set_line_width(1.6); pc.set_source_rgba(*PRIM, 0.98); pc.stroke()
pc.set_source_rgba(*ACC, 1.0); pc.rectangle(2, 5, 3.5, S - 10); pc.fill()

for name, (sx, sy, sw, sh) in {"nw":(0,0,8,8),"n":(8,0,16,8),"ne":(24,0,8,8),"w":(0,8,8,16),"c":(8,8,16,16),"e":(24,8,8,16),"sw":(0,24,8,8),"s":(8,24,16,8),"se":(24,24,8,8)}.items():
    sub = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh); sc = cairo.Context(sub)
    sc.set_source_surface(pill, -sx, -sy); sc.paint()
    sub.write_to_png(os.path.join(gt_dir, f"select_{name}.png"))
