#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "◈ Установка адаптивного окружения CyberDeck..."

if command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed --noconfirm \
        hyprland hyprlock gtk4 gtk4-layer-shell python-gobject python-cairo \
        rofi mako libnotify pamixer jq foot fastfetch btop \
        grim slurp wl-clipboard brightnessctl power-profiles-daemon \
        xorg-xcursorgen xorg-xrdb librsvg gtk-update-icon-cache \
        sddm qt6-declarative qt6-svg fontconfig freetype2
fi

mkdir -p ~/.local/bin ~/.config/{cyberdeck,hypr/assets/ui,foot,kitty,btop/themes,fastfetch,mako} \
         ~/.cache/cyberdeck ~/.local/share/icons/default ~/.icons/default \
         ~/.config/{gtk-3.0,gtk-4.0,environment.d} ~/.local/share/dbus-1/services

install -m 0755 "$REPO_ROOT"/scripts/* ~/.local/bin/
cp -f ~/.local/bin/cyber-intro ~/.local/bin/alpora-intro
sudo install -m 0755 "$REPO_ROOT/scripts/battery-status" /usr/local/bin/cyberdeck-power-status
sudo install -m 0755 "$REPO_ROOT/session/start-cyberdeck" /usr/local/bin/start-cyberdeck
sudo install -m 0644 "$REPO_ROOT/session/cyberdeck.desktop" /usr/share/wayland-sessions/cyberdeck.desktop

python3 "$REPO_ROOT/themes/build-assets.py"
python3 "$REPO_ROOT/themes/build-cursor.py"
python3 "$REPO_ROOT/themes/sync-icons.py"
python3 "$REPO_ROOT/themes/sync-firefox.py" || true

sudo rm -rf /usr/share/icons/CyberDeck-Cursor
sudo cp -r ~/.local/share/icons/CyberDeck-Cursor /usr/share/icons/CyberDeck-Cursor
sudo mkdir -p /usr/share/icons/default
printf "[Icon Theme]\nName=Default\nInherits=CyberDeck-Cursor\n" | sudo tee /usr/share/icons/default/index.theme >/dev/null
cp /usr/share/icons/default/index.theme ~/.icons/default/index.theme
cp /usr/share/icons/default/index.theme ~/.local/share/icons/default/index.theme
printf "Xcursor.theme: CyberDeck-Cursor\nXcursor.size: 28\n" > ~/.Xresources

for gdir in ~/.config/gtk-3.0 ~/.config/gtk-4.0; do
    printf "[Settings]\ngtk-application-prefer-dark-theme=1\ngtk-cursor-theme-name=CyberDeck-Cursor\ngtk-cursor-theme-size=28\ngtk-icon-theme-name=CyberDeck-Icons\ngtk-font-name=Noto Sans 10\n" > "$gdir/settings.ini"
done
printf "XCURSOR_THEME=CyberDeck-Cursor\nXCURSOR_SIZE=28\n" > ~/.config/environment.d/99-cyberdeck.conf

cp "$REPO_ROOT/themes/foot/foot.ini" ~/.config/foot/foot.ini
cp "$REPO_ROOT/themes/kitty/cyber-deck.conf" ~/.config/kitty/cyber-deck.conf
touch ~/.config/kitty/kitty.conf
sed -i '/include cyber-deck\.conf/d' ~/.config/kitty/kitty.conf
echo "include cyber-deck.conf" >> ~/.config/kitty/kitty.conf

cp "$REPO_ROOT/themes/btop/cyber-deck.theme" ~/.config/btop/themes/cyber-deck.theme
cp "$REPO_ROOT/themes/fastfetch/cyber_logo.txt" ~/.config/fastfetch/cyber_logo.txt
cp "$REPO_ROOT/themes/fastfetch/config.jsonc" ~/.config/fastfetch/config.jsonc
cp "$REPO_ROOT/themes/rofi/gaming_launcher.rasi" ~/.config/hypr/gaming_launcher.rasi
cp "$REPO_ROOT/themes/rofi/cyber_wifi.rasi" ~/.config/hypr/cyber_wifi.rasi
sed "s|__HOME__|$HOME|g" "$REPO_ROOT/themes/mako/config.tpl" > ~/.config/mako/config
sed "s|__HOME__|$HOME|g" "$REPO_ROOT/themes/hyprlock/hyprlock.conf.tpl" > ~/.config/hypr/hyprlock.conf
printf "[D-BUS Service]\nName=org.freedesktop.Notifications\nExec=/usr/bin/mako\n" > ~/.local/share/dbus-1/services/org.freedesktop.Notifications.service

cp "$REPO_ROOT/themes/shell/cyber-shell.sh" ~/.config/cyberdeck/cyber-shell.sh
for rc in ~/.bashrc ~/.zshrc; do
    [ -f "$rc" ] || touch "$rc"
    sed -i '/# >>> CYBERDECK SHELL >>>/,/# <<< CYBERDECK SHELL <<</d' "$rc"
    printf '# >>> CYBERDECK SHELL >>>\n[ -f "$HOME/.config/cyberdeck/cyber-shell.sh" ] && source "$HOME/.config/cyberdeck/cyber-shell.sh"\n# <<< CYBERDECK SHELL <<<\n' >> "$rc"
done

SDDM_DIR="/usr/share/sddm/themes/cyberdeck-sddm"
sudo mkdir -p "$SDDM_DIR" /etc/sddm.conf.d
sudo cp ~/.cache/cyberdeck/sddm_bg.png "$SDDM_DIR/hud_bg.png"
sudo cp "$REPO_ROOT/themes/sddm/Main.qml" "$SDDM_DIR/Main.qml"
sudo cp "$REPO_ROOT/themes/sddm/metadata.desktop" "$SDDM_DIR/metadata.desktop"
printf "[General]\nbackground=hud_bg.png\nbattery=⚡ SYSTEM READY\n" | sudo tee "$SDDM_DIR/theme.conf" >/dev/null
sudo chmod -R a+rX "$SDDM_DIR"
printf "[Theme]\nCurrent=cyberdeck-sddm\nCursorTheme=CyberDeck-Cursor\nCursorSize=28\n" | sudo tee /etc/sddm.conf.d/zz-cyberdeck.conf >/dev/null
sudo install -m 0755 "$REPO_ROOT/themes/sddm/cyberdeck-sddm-sync" /usr/local/bin/cyberdeck-sddm-sync
sudo /usr/local/bin/cyberdeck-sddm-sync || true

if sudo test -d /boot/grub && command -v grub-mkconfig >/dev/null 2>&1; then
    GT_DIR="/boot/grub/themes/cyberdeck-grub"
    sudo mkdir -p "$GT_DIR/icons"
    sudo python3 "$REPO_ROOT/themes/grub/build-grub-assets.py" "$GT_DIR"
    sudo cp "$REPO_ROOT/themes/grub/theme.txt" "$GT_DIR/theme.txt"
    FONT_REG=$(fc-match -f '%{file}' 'sans-serif' 2>/dev/null || true)
    if [ -f "$FONT_REG" ] && command -v grub-mkfont >/dev/null 2>&1; then
        sudo grub-mkfont -s 14 -n "Alpora Regular" -o "$GT_DIR/alpora_reg_14.pf2" "$FONT_REG" 2>/dev/null || true
        sudo grub-mkfont -s 20 -n "Alpora Regular" -o "$GT_DIR/alpora_reg_20.pf2" "$FONT_REG" 2>/dev/null || true
        sudo grub-mkfont -s 20 -b -n "Alpora Bold" -o "$GT_DIR/alpora_bold_20.pf2" "$FONT_REG" 2>/dev/null || true
        sudo grub-mkfont -s 28 -b -n "Alpora Bold" -o "$GT_DIR/alpora_bold_28.pf2" "$FONT_REG" 2>/dev/null || true
    fi
    sudo sed -i '/^[[:space:]]*GRUB_THEME=/d; /^[[:space:]]*GRUB_GFXMODE=/d; /^[[:space:]]*GRUB_TERMINAL_OUTPUT=/d' /etc/default/grub
    printf 'GRUB_TERMINAL_OUTPUT="gfxterm"\nGRUB_GFXMODE="1920x1080,auto"\nGRUB_THEME="/boot/grub/themes/cyberdeck-grub/theme.txt"\n' | sudo tee -a /etc/default/grub >/dev/null
    sudo grub-mkconfig -o /boot/grub/grub.cfg
fi

~/.local/bin/cyberdeck-hw-detect
echo "◈ CyberDeck установлен! Выберите сессию cyberdeck на экране входа SDDM."
