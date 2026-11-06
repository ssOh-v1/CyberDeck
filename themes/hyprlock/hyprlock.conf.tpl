background {
    monitor =
    path = __HOME__/.cache/cyberdeck/lock_hud_bg.png
    blur_passes = 0
}

label {
    monitor =
    text = ◈ CYBER DECK // SECURITY LOCKDOWN
    color = rgb(102, 217, 232)
    font_size = 11
    font_family = Noto Sans Bold
    position = 0, 162
    halign = center
    valign = center
}

label {
    monitor =
    text = $TIME
    color = rgb(240, 244, 255)
    font_size = 76
    font_family = Noto Sans Bold
    position = 0, 86
    halign = center
    valign = center
}

label {
    monitor =
    text = cmd[update:30000] date +"%d.%m.%Y   •   %A"
    color = rgb(145, 167, 255)
    font_size = 13
    font_family = Noto Sans Bold
    position = 0, 20
    halign = center
    valign = center
}

label {
    monitor =
    text = ◈ OPERATOR // $USER   •   AES-256 ACTIVE
    color = rgb(99, 230, 190)
    font_size = 11
    font_family = Noto Sans Bold
    position = 0, -22
    halign = center
    valign = center
}

input-field {
    monitor =
    size = 360, 50
    outline_thickness = 2
    dots_size = 0.26
    dots_spacing = 0.22
    dots_center = true
    fade_on_empty = false
    font_color = rgb(229, 236, 255)
    inner_color = rgb(10, 15, 28)
    outer_color = rgb(34, 184, 207)
    check_color = rgb(76, 110, 245)
    fail_color = rgb(255, 107, 107)
    placeholder_text = <i>Введите ключ разблокировки...</i>
    rounding = 11
    position = 0, -82
    halign = center
    valign = center
}

label {
    monitor =
    text = cmd[update:5000] __HOME__/.local/bin/battery-status
    color = rgb(145, 167, 255)
    font_size = 12
    font_family = Noto Sans Bold
    position = 0, -158
    halign = center
    valign = center
}
