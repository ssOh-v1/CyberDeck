#!/usr/bin/python3
import os, glob

HOME = os.path.expanduser("~")

STEAM_CSS = """/* Studio Monochrome Matte-Grey Theme for Steam */
:root {
    --studio-bg: #121316 !important;
    --studio-panel: #17191e !important;
    --studio-card: #1d2026 !important;
    --studio-hover: #282c34 !important;
    --studio-border: #2e323b !important;
    --studio-accent: #8c939e !important;
    --studio-text: #e6e9ef !important;
    --studio-muted: #9ea4b0 !important;
}

body, html, #root, .main-window, .DesktopUI, .steamdesktop_OuterFrame_3mz8w,
.steamdesktop_TopBar_3Z7VQ, .steamdesktop_BottomBar_3vCzS, .library_Container_3xRRJ,
.gamelistbar_Container_3x1Hk, .gamelistbar_GameListHomeAndSearch_2TKEa,
.libraryhome_Container_2gSXC, .libraryhome_UpdatesContainer_17uEB,
.libraryhome_LibraryHome_3Sb2o, .appdetails_ScrollContainer_2l416,
.friendsui-container, .friendlist, .chatWindow {
    background: #121316 !important;
    background-color: #121316 !important;
    background-image: none !important;
    color: #d4d8de !important;
    font-family: "Inter", "JetBrainsMono Nerd Font", sans-serif !important;
}

/* Левая панель списка игр и верхний бар */
.gamelistbar_Container_3x1Hk, .steamdesktop_TopBar_3Z7VQ, .steamdesktop_BottomBar_3vCzS {
    background-color: #15171b !important;
    border-color: #262930 !important;
}

/* Элементы списка игр */
.gamelistentry_Container_2-O4Z {
    border-radius: 5px !important;
    margin: 1px 6px !important;
    color: #b8bec8 !important;
}
.gamelistentry_Container_2-O4Z:hover {
    background-color: #20232a !important;
    color: #ffffff !important;
}
.gamelistentry_Selected_1UBpA, .gamelistentry_Container_2-O4Z.gamelistentry_Selected_1UBpA {
    background: #282c34 !important;
    background-color: #282c34 !important;
    border-left: 3px solid #9ea4b0 !important;
    color: #ffffff !important;
}

/* Поле поиска в библиотеке и чате */
input, .gamelistsearchbar_SearchInput_12vo5, .DialogTextInputBase {
    background-color: #111215 !important;
    border: 1px solid #2c3038 !important;
    border-radius: 6px !important;
    color: #e6e9ef !important;
    box-shadow: none !important;
}

/* Кнопка ИГРАТЬ / УСТАНОВИТЬ в сером студийном стиле */
.appactionbutton_PlayButton_3ydig, .appactionbutton_ButtonChild_2AzIX {
    background: #282c35 !important;
    background-color: #282c35 !important;
    background-image: none !important;
    border: 1px solid #6c727d !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    box-shadow: none !important;
}
.appactionbutton_PlayButton_3ydig:hover, .appactionbutton_ButtonChild_2AzIX:hover {
    background: #363b46 !important;
    border-color: #b0b6c0 !important;
}

/* Убираем синие/цветные градиенты и размытия Steam */
.appdetails_Glassy_3Fmxx, .libraryhome_UpdatesContainer_17uEB,
.appdetailssection_AppDetailsSectionContainer_31ptF {
    background: #17191e !important;
    background-image: none !important;
    border: 1px solid #282c34 !important;
    border-radius: 7px !important;
    backdrop-filter: none !important;
}
"""

steam_roots = [
    os.path.join(HOME, ".local/share/Steam"),
    os.path.join(HOME, ".steam/steam"),
    os.path.join(HOME, ".var/app/com.valvesoftware.Steam/.local/share/Steam"),
]

for sroot in steam_roots:
    sui = os.path.join(sroot, "steamui")
    if not os.path.isdir(sui):
        continue
    # 1. Записываем кастомные таблицы стилей Steam
    for cname in ("libraryroot.custom.css", "friends.custom.css", "webkit.css"):
        open(os.path.join(sui, cname), "w", encoding="utf-8").write(STEAM_CSS)

    # 2. Включаем поддержку CEF-отладки и кастомных стилей
    open(os.path.join(sroot, ".cef-enable-remote-debugging"), "w").write("")

    # 3. Безопасный патч с сохранением ТОЧНОГО размера файла в байтах (чтобы Steam не перезаписал CSS при запуске!)
    lib_css = os.path.join(sui, "css/libraryroot.css")
    if os.path.isfile(lib_css):
        bak_css = lib_css + ".orig_bak"
        if not os.path.isfile(bak_css):
            open(bak_css, "wb").write(open(lib_css, "rb").read())
        orig_bytes = open(bak_css, "rb").read()
        imp_stmt = b'@import url("../libraryroot.custom.css");'
        if imp_stmt not in orig_bytes and len(orig_bytes) > 256:
            # Находим конец первого CSS-правила '}' и заменяем его на @import с пробелами ровно той же длины!
            first_brace = orig_bytes.find(b"}")
            if first_brace >= len(imp_stmt):
                pad_len = (first_brace + 1) - len(imp_stmt)
                patched = imp_stmt + (b" " * pad_len) + orig_bytes[first_brace + 1:]
                if len(patched) == len(orig_bytes):
                    open(lib_css, "wb").write(patched)
