import os, json, subprocess

BG_DAEMONS = [
    ("steam",            "Steam",    "steam steam://open/main",       "steam",           "steam"),
    ("discord",          "Discord",  "~/.local/bin/gaming-discord",   "discord",         "discord"),
    ("vesktop",          "Vesktop",  "~/.local/bin/gaming-discord",   "vesktop",         "vesktop"),
    ("legcord",          "Legcord",  "~/.local/bin/gaming-discord",   "legcord",         "legcord"),
    ("telegram-deskto",  "Telegram", "telegram-desktop",              "telegram",        "telegram"),
    ("ayugram-desktop",  "AyuGram",  "ayugram-desktop",               "ayugram-desktop", "telegram"),
    ("obs",              "OBS",      "obs",                           "obs",             "obs"),
    ("spotify",          "Spotify",  "spotify",                       "spotify",         "spotify"),
    ("qbittorrent",      "qBit",     "qbittorrent",                   "qbittorrent",     "qbittorrent"),
    ("vlc",              "VLC",      "vlc",                           "vlc",             "vlc"),
    ("nekoray",          "NekoRay",  "nekoray",                       "nekoray",         "nekoray"),
    ("hiddify",          "Hiddify",  "hiddify",                       "hiddify",         "hiddify"),
]

def get_bg_and_open_items():
    grouped = {}
    order = []
    try:
        clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"], text=True, stderr=subprocess.DEVNULL))
    except Exception:
        clients = []

    active_addr = ""
    try:
        active_addr = json.loads(subprocess.check_output(["hyprctl", "activewindow", "-j"], text=True, stderr=subprocess.DEVNULL)).get("address", "")
    except Exception:
        pass

    for cl in clients:
        addr = cl.get("address", "")
        cls = cl.get("class") or cl.get("initialClass") or cl.get("title") or "App"
        if cls in ("WorkHubDesktop", "GamingHubDesktop", "CyberDeckHubDesktop"):
            continue
        key = cls.lower()
        ws_name = cl.get("workspace", {}).get("name", "")
        ws_id = cl.get("workspace", {}).get("id", 1)
        pinned = bool(cl.get("pinned", False))
        in_bg = (ws_name == "special:bg" or ws_id < 0)

        if key not in grouped:
            order.append(key)
            grouped[key] = {
                "name": cls,
                "icon_spec": cls,
                "count": 0,
                "windows": [],
                "has_bg": False,
                "has_pinned": False,
            }
        grouped[key]["count"] += 1
        grouped[key]["windows"].append((addr, ws_id, in_bg))
        if in_bg:
            grouped[key]["has_bg"] = True
        if pinned:
            grouped[key]["has_pinned"] = True

    items = []
    for key in order:
        g = grouped[key]
        wins = g["windows"]
        # Выбираем следующее окно группы при повторном клике
        target_addr, target_ws, target_bg = wins[0]
        if len(wins) > 1:
            addrs = [w[0] for w in wins]
            if active_addr in addrs:
                nxt = (addrs.index(active_addr) + 1) % len(wins)
                target_addr, target_ws, target_bg = wins[nxt]

        if target_bg:
            lclick = f'CUR=$(hyprctl activeworkspace -j | jq -r ".id // 1"); hyprctl --batch "dispatch movetoworkspace $CUR,address:{target_addr}; dispatch focuswindow address:{target_addr}"'
            rclick = f"hyprctl dispatch closewindow address:{target_addr}"
            style = "bg-pill-hidden"
            state_txt = "В ФОНЕ"
        else:
            lclick = f'hyprctl --batch "dispatch workspace {target_ws}; dispatch focuswindow address:{target_addr}"'
            rclick = f'hyprctl dispatch movetoworkspacesilent "special:bg,address:{target_addr}"'
            style = "bg-pill-pinned" if g["has_pinned"] else "bg-pill-ws"
            state_txt = "ПОВЕРХ" if g["has_pinned"] else f"СТОЛ {target_ws}"

        short = g["name"][:14]
        cnt = g["count"]
        items.append({
            "name": g["name"],
            "icon_spec": g["icon_spec"],
            "count": cnt,
            "is_bg": g["has_bg"],
            "is_pinned": g["has_pinned"],
            "is_daemon": False,
            "lclick": lclick,
            "rclick": rclick,
            "label": f"◈ {short} ×{cnt} [{state_txt}]" if cnt > 1 else f"◈ {short} [{state_txt}]",
            "style": style,
        })

    comms = set()
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                comms.add(open(f"/proc/{pid}/comm").read().strip().lower())
            except Exception:
                pass

    for comm, title, open_cmd, kill_pat, icon_key in BG_DAEMONS:
        if comm in comms and not any(comm[:6] in k for k in grouped):
            items.append({
                "name": title,
                "icon_spec": icon_key,
                "count": 1,
                "is_bg": True,
                "is_pinned": False,
                "is_daemon": True,
                "lclick": open_cmd,
                "rclick": f"pkill -TERM -f '{kill_pat}'",
                "label": f"● {title} [ТРЕЙ]",
                "style": "bg-pill-daemon",
            })

    return items
