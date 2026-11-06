#!/usr/bin/env python3
import os, math, cairo

HOME = os.path.expanduser("~")
ASSETS = os.path.join(HOME, ".config/hypr/assets")
UI = os.path.join(ASSETS, "ui")
CACHE = os.path.join(HOME, ".cache/cyberdeck")
os.makedirs(UI, exist_ok=True); os.makedirs(CACHE, exist_ok=True)

ui_svgs = {
    "bolt.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M9.5 1.5 L3.5 9 H8 L6.5 14.5 L12.5 7 H8 Z" fill="#22b8cf"/></svg>',
    "eco.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M13.5 2.5 C7 2.5 3 6.5 3 11.5 C3 12.5 3.5 13 4.5 13 C9.5 13 13.5 9 13.5 2.5 Z" fill="none" stroke="#63e6be" stroke-width="1.8"/><path d="M3.5 12.5 L9.5 6.5" stroke="#63e6be" stroke-width="1.6" stroke-linecap="round"/></svg>',
    "turbo.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><polygon points="8,1.5 14,13.5 8,10.8 2,13.5" fill="none" stroke="#ff6b6b" stroke-width="1.7" stroke-linejoin="round"/></svg>',
    "audio.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M2.5 6 H5.2 L8.8 3 V13 L5.2 10 H2.5 Z" fill="#66d9e8"/><path d="M11 5.5 C12.2 6.8 12.2 9.2 11 10.5 M12.8 3.8 C14.8 6 14.8 10 12.8 12.2" fill="none" stroke="#4c6ef5" stroke-width="1.6" stroke-linecap="round"/></svg>',
    "lock.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><rect x="3.5" y="7" width="9" height="7" rx="2" fill="none" stroke="#91a7ff" stroke-width="1.7"/><path d="M5.5 7 V5 C5.5 3.5 6.6 2.5 8 2.5 C9.4 2.5 10.5 3.5 10.5 5 V7" fill="none" stroke="#22b8cf" stroke-width="1.7" stroke-linecap="round"/></svg>',
    "reboot.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path d="M12.5 8 A4.5 4.5 0 1 1 11.2 4.8" fill="none" stroke="#9da8c4" stroke-width="1.8" stroke-linecap="round"/><polyline points="11.5,2.2 11.5,5.2 8.5,5.2" fill="none" stroke="#22b8cf" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "power.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><line x1="8" y1="2.2" x2="8" y2="8" stroke="#ff8787" stroke-width="1.9" stroke-linecap="round"/><path d="M4.6 4.5 A5 5 0 1 0 11.4 4.5" fill="none" stroke="#ff8787" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "wifi-high.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18"><path d="M2.2 6.4 C5.9 3.2 12.1 3.2 15.8 6.4" fill="none" stroke="#22b8cf" stroke-width="1.8" stroke-linecap="round"/><path d="M4.6 9.3 C7.1 7.2 10.9 7.2 13.4 9.3" fill="none" stroke="#4c6ef5" stroke-width="1.8" stroke-linecap="round"/><path d="M7.0 12.1 C8.2 11.1 9.8 11.1 11.0 12.1" fill="none" stroke="#66d9e8" stroke-width="1.8" stroke-linecap="round"/><circle cx="9" cy="14.6" r="1.4" fill="#e5ecff"/></svg>',
    "wifi-mid.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18"><path d="M4.6 9.3 C7.1 7.2 10.9 7.2 13.4 9.3" fill="none" stroke="#22b8cf" stroke-width="1.8" stroke-linecap="round"/><circle cx="9" cy="14.6" r="1.4" fill="#e5ecff"/></svg>',
    "wifi-low.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="14.6" r="1.4" fill="#fcc419"/></svg>',
    "wifi-off.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="14.6" r="1.3" fill="#495678"/><line x1="3.5" y1="3.5" x2="14.5" y2="14.5" stroke="#ff6b6b" stroke-width="1.9" stroke-linecap="round"/></svg>',
    "lan.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18"><rect x="6" y="2" width="6" height="4.5" rx="1" fill="none" stroke="#22b8cf" stroke-width="1.6"/><rect x="2" y="11.5" width="5" height="4.5" rx="1" fill="none" stroke="#4c6ef5" stroke-width="1.6"/><rect x="11" y="11.5" width="5" height="4.5" rx="1" fill="none" stroke="#4c6ef5" stroke-width="1.6"/><path d="M9 6.5 V9 M4.5 9 H13.5 M4.5 9 V11.5 M13.5 9 V11.5" stroke="#66d9e8" stroke-width="1.6" stroke-linecap="round"/></svg>',
    "kb.svg": '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><rect x="2" y="5" width="28" height="22" rx="6" fill="#10182b" stroke="#22b8cf" stroke-width="2"/><rect x="9" y="20" width="14" height="3" rx="1.2" fill="#e5ecff"/></svg>',
}
for fn, svg in ui_svgs.items(): open(os.path.join(UI, fn), "w", encoding="utf-8").write(svg)

S = 260
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); cr = cairo.Context(surf); cx, cy = S/2, S/2
cr.new_sub_path()
for i in range(6):
    ang = math.pi / 3 * i + math.pi / 6
    px, py = cx + 108 * math.cos(ang), cy + 108 * math.sin(ang)
    if i == 0: cr.move_to(px, py)
    else: cr.line_to(px, py)
cr.close_path(); cr.set_source_rgba(0.05, 0.07, 0.12, 0.96); cr.fill_preserve()
cr.set_line_width(2.5); cr.set_source_rgba(0.30, 0.43, 0.96, 0.9); cr.stroke()
cr.set_line_width(4.5); cr.set_source_rgb(0.13, 0.72, 0.81)
cr.move_to(cx - 20, cy - 14); cr.line_to(cx - 34, cy); cr.line_to(cx - 20, cy + 14); cr.stroke()
cr.move_to(cx + 20, cy - 14); cr.line_to(cx + 34, cy); cr.line_to(cx + 20, cy + 14); cr.stroke()
for nm in ("cyberdeck_logo.png", "work_logo.png"): surf.write_to_png(os.path.join(ASSETS, nm))

def make_hud_canvas(out_png, grub_card=False):
    W, H = 1920, 1080
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    lg = cairo.LinearGradient(0, 0, W, H)
    lg.add_color_stop_rgb(0.0, 0.024, 0.031, 0.052); lg.add_color_stop_rgb(0.5, 0.030, 0.039, 0.066); lg.add_color_stop_rgb(1.0, 0.020, 0.026, 0.045)
    c.set_source(lg); c.paint()
    c.set_line_width(1.0); c.set_source_rgba(0.34, 0.46, 0.78, 0.055)
    for x in range(96, W, 96): c.move_to(x, 0); c.line_to(x, H)
    for y in range(96, H, 96): c.move_to(0, y); c.line_to(W, y)
    c.stroke()
    m, ln = 16, 54
    c.set_line_width(2.4); c.set_source_rgba(0.30, 0.43, 0.96, 0.72)
    for x1, y1, x2, y2, x3, y3 in [(m,m+ln,m,m,m+ln,m),(W-m-ln,m,W-m,m,W-m,m+ln),(m,H-m-ln,m,H-m,m+ln,H-m),(W-m-ln,H-m,W-m,H-m,W-m,H-m-ln)]:
        c.move_to(x1, y1); c.line_to(x2, y2); c.line_to(x3, y3)
    c.stroke()
    if grub_card:
        mx, my, mw, mh = int(W * 0.27), int(H * 0.26), int(W * 0.46), int(H * 0.50)
        c.set_source_rgba(0.051, 0.067, 0.110, 0.96); c.rectangle(mx, my, mw, mh); c.fill_preserve()
        c.set_line_width(1.6); c.set_source_rgba(0.13, 0.72, 0.81, 0.85); c.stroke()
    s.write_to_png(out_png)

make_hud_canvas(os.path.join(ASSETS, "terminal_hud_bg.png"), False)
make_hud_canvas(os.path.join(CACHE, "sddm_bg.png"), False)
make_hud_canvas(os.path.join(CACHE, "grub_bg.png"), True)
