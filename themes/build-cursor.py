#!/usr/bin/env python3
import os, math, shutil, tempfile, subprocess, cairo

theme_dir = os.path.expanduser("~/.local/share/icons/CyberDeck-Cursor")
cursors_dir = os.path.join(theme_dir, "cursors")
shutil.rmtree(theme_dir, ignore_errors=True)
os.makedirs(cursors_dir, exist_ok=True)
open(os.path.join(theme_dir, "index.theme"), "w", encoding="utf-8").write("[Icon Theme]\nName=CyberDeck-Cursor\nComment=Precision Cyber HUD Cursor Theme\nInherits=Adwaita\n")

INDIGO, CYAN, DARK, LIGHT, RED = (0.298,0.431,0.961), (0.133,0.722,0.812), (0.039,0.055,0.098), (0.898,0.925,1.0), (1.0,0.42,0.42)

def new_surf(sz):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, sz, sz)
    cr = cairo.Context(s); cr.scale(sz / 32.0, sz / 32.0)
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    return s, cr

def draw_arrow(cr):
    pts = [(3,2),(3,24),(8.8,19.2),(12.6,27.5),(16.0,25.8),(12.2,17.6),(19.8,17.6)]
    cr.save(); cr.translate(1.2, 1.5); cr.move_to(*pts[0])
    for p in pts[1:]: cr.line_to(*p)
    cr.close_path(); cr.set_source_rgba(0,0,0,0.48); cr.fill(); cr.restore()
    cr.move_to(*pts[0])
    for p in pts[1:]: cr.line_to(*p)
    cr.close_path(); cr.set_source_rgba(*DARK, 0.96); cr.fill_preserve()
    lg = cairo.LinearGradient(3,2,19,27)
    lg.add_color_stop_rgb(0.0, *CYAN); lg.add_color_stop_rgb(0.65, *INDIGO); lg.add_color_stop_rgb(1.0, *CYAN)
    cr.set_source(lg); cr.set_line_width(1.7); cr.stroke()
    cr.arc(4.3, 4.6, 1.2, 0, 2*math.pi); cr.set_source_rgb(*CYAN); cr.fill()

def draw_pointer(cr):
    pts = [(6,5),(6,23),(11.2,18.8),(15.5,26),(18.5,24.4),(14.2,17.2),(21,17.2)]
    cr.move_to(*pts[0])
    for p in pts[1:]: cr.line_to(*p)
    cr.close_path(); cr.set_source_rgba(*DARK, 0.96); cr.fill_preserve()
    cr.set_source_rgb(*CYAN); cr.set_line_width(1.8); cr.stroke()
    cx, cy, r = 6.0, 5.0, 3.6
    cr.move_to(cx, cy-r); cr.line_to(cx+r, cy); cr.line_to(cx, cy+r); cr.line_to(cx-r, cy); cr.close_path()
    cr.set_source_rgba(*DARK, 0.95); cr.fill_preserve(); cr.set_source_rgb(*LIGHT); cr.set_line_width(1.4); cr.stroke()

def draw_ibeam(cr):
    for w, col, al in [(4.2,(0,0,0),0.65), (1.9,CYAN,1.0)]:
        cr.set_line_width(w); cr.set_source_rgba(*col, al)
        cr.move_to(16,5); cr.line_to(16,27); cr.move_to(11.5,5); cr.line_to(20.5,5); cr.move_to(11.5,27); cr.line_to(20.5,27); cr.stroke()

def draw_cross(cr):
    cr.set_line_width(1.8); cr.set_source_rgb(*CYAN)
    for x1,y1,x2,y2 in [(16,3,16,11),(16,21,16,29),(3,16,11,16),(21,16,29,16)]: cr.move_to(x1,y1); cr.line_to(x2,y2)
    cr.stroke()
    cr.set_line_width(1.3); cr.set_source_rgba(*INDIGO, 0.9); cr.arc(16,16,6.5,0,2*math.pi); cr.stroke()

def draw_darrow(cr, ang):
    cr.save(); cr.translate(16,16); cr.rotate(math.radians(ang))
    for lw, col, al in [(4.2,(0,0,0),0.6), (2.0,CYAN,1.0)]:
        cr.set_line_width(lw); cr.set_source_rgba(*col, al)
        cr.move_to(-10,0); cr.line_to(10,0); cr.move_to(-6,-4.5); cr.line_to(-11,0); cr.line_to(-6,4.5); cr.move_to(6,-4.5); cr.line_to(11,0); cr.line_to(6,4.5); cr.stroke()
    cr.restore()

def draw_grab(cr, closed=False):
    r = 7.5 if closed else 9.5
    cr.arc(16,16,r,0,2*math.pi); cr.set_source_rgba(*DARK,0.95); cr.fill_preserve()
    cr.set_line_width(2.0); cr.set_source_rgb(*(CYAN if closed else INDIGO)); cr.stroke()

def draw_deny(cr):
    cr.arc(16,16,10.5,0,2*math.pi); cr.set_source_rgba(*DARK,0.92); cr.fill_preserve()
    cr.set_line_width(2.4); cr.set_source_rgb(*RED); cr.stroke()
    cr.move_to(9.2,9.2); cr.line_to(22.8,22.8); cr.stroke()

def draw_spin(cr, ph, mini=False):
    cx, cy, r = (22.5, 21.5, 6.2) if mini else (16.0, 16.0, 10.5)
    cr.arc(cx,cy,r,0,2*math.pi); cr.set_source_rgba(*DARK,0.85); cr.fill_preserve()
    cr.set_line_width(2.0); cr.set_source_rgba(*INDIGO,0.35); cr.stroke()
    a0 = ph * 2 * math.pi
    cr.set_line_width(2.4); cr.set_source_rgb(*CYAN); cr.arc(cx,cy,r,a0,a0+math.pi*0.9); cr.stroke()
    cr.set_source_rgb(*INDIGO); cr.arc(cx,cy,r,a0+math.pi,a0+math.pi*1.55); cr.stroke()

tmp = tempfile.mkdtemp(prefix="cd_cur_")
try:
    sizes = [24, 32, 48]
    def b_static(name, hx32, hy32, fn):
        lines = []
        for sz in sizes:
            s, cr = new_surf(sz); fn(cr)
            png = os.path.join(tmp, f"{name}_{sz}.png"); s.write_to_png(png)
            lines.append(f"{sz} {int(round(hx32*sz/32.0))} {int(round(hy32*sz/32.0))} {png}")
        cfg = os.path.join(tmp, f"{name}.cfg"); open(cfg,"w").write("\n".join(lines)+"\n")
        subprocess.run(["xcursorgen", cfg, os.path.join(cursors_dir, name)], check=True)
    def b_anim(name, hx32, hy32, mini=False):
        lines = []
        for sz in sizes:
            for fr in range(12):
                s, cr = new_surf(sz)
                if mini: draw_arrow(cr)
                draw_spin(cr, fr/12.0, mini)
                png = os.path.join(tmp, f"{name}_{sz}_{fr}.png"); s.write_to_png(png)
                lines.append(f"{sz} {int(round(hx32*sz/32.0))} {int(round(hy32*sz/32.0))} {png} 55")
        cfg = os.path.join(tmp, f"{name}.cfg"); open(cfg,"w").write("\n".join(lines)+"\n")
        subprocess.run(["xcursorgen", cfg, os.path.join(cursors_dir, name)], check=True)

    b_static("left_ptr", 3, 2, draw_arrow)
    b_static("hand2", 6, 5, draw_pointer)
    b_static("xterm", 16, 16, draw_ibeam)
    b_static("crosshair", 16, 16, draw_cross)
    b_static("fleur", 16, 16, lambda cr: (draw_darrow(cr,0), draw_darrow(cr,90)))
    b_static("sb_h_double_arrow", 16, 16, lambda cr: draw_darrow(cr,0))
    b_static("sb_v_double_arrow", 16, 16, lambda cr: draw_darrow(cr,90))
    b_static("bd_double_arrow", 16, 16, lambda cr: draw_darrow(cr,45))
    b_static("fd_double_arrow", 16, 16, lambda cr: draw_darrow(cr,-45))
    b_static("grab", 16, 16, lambda cr: draw_grab(cr,False))
    b_static("grabbing", 16, 16, lambda cr: draw_grab(cr,True))
    b_static("not_allowed", 16, 16, draw_deny)
    b_anim("watch", 16, 16, False)
    b_anim("left_ptr_watch", 3, 2, True)

    aliases = {
        "left_ptr": ["default","arrow","top_left_arrow","right_ptr","help","context-menu","copy"],
        "hand2": ["pointer","hand1","pointing_hand"],
        "xterm": ["text","ibeam"],
        "crosshair": ["cross","tcross","plus","color-picker"],
        "fleur": ["move","size_all","all-scroll"],
        "sb_h_double_arrow": ["ew-resize","col-resize","size_hor","left_side","right_side","e-resize","w-resize"],
        "sb_v_double_arrow": ["ns-resize","row-resize","size_ver","top_side","bottom_side","n-resize","s-resize"],
        "bd_double_arrow": ["nwse-resize","size_fdiag","top_left_corner","bottom_right_corner","nw-resize","se-resize"],
        "fd_double_arrow": ["nesw-resize","size_bdiag","top_right_corner","bottom_left_corner","ne-resize","sw-resize"],
        "grab": ["openhand"],
        "grabbing": ["closedhand","dnd-move","dnd-copy"],
        "not_allowed": ["not-allowed","crossed_circle","no-drop","forbidden"],
        "watch": ["wait"],
        "left_ptr_watch": ["progress","half-busy"],
    }
    for tgt, lks in aliases.items():
        for lk in lks:
            lp = os.path.join(cursors_dir, lk)
            if not os.path.exists(lp): os.symlink(tgt, lp)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
