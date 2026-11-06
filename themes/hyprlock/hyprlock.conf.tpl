background {
    monitor =
    path = __HOME__/.cache/cyberdeck/cyberdeck_hud_bg.png
    blur_passes = 0
}

input-field {
    monitor =
    size = 360, 50
    outline_thickness = 2
    dots_size = 0.25
    dots_spacing = 0.20
    dots_center = true
    fade_on_empty = false
    font_color = rgb(219, 228, 255)
    inner_color = rgb(13, 17, 28)
    outer_color = rgb(76, 110, 245)
    check_color = rgb(34, 184, 207)
    fail_color = rgb(224, 49, 49)
    placeholder_text = <i>Введите ключ доступа...</i>
    rounding = 12
    position = 0, -45
    halign = center
    valign = center
}

label {
    monitor =
    text = $TIME
    color = rgb(229, 236, 255)
    font_size = 80
    font_family = Noto Sans Bold
    position = 0, 125
    halign = center
    valign = center
}

label {
    monitor =
    text = ◈ CYBER DECK // SECURITY TERMINAL
    color = rgb(34, 184, 207)
    font_size = 13
    font_family = Noto Sans Bold
    position = 0, 42
    halign = center
    valign = center
}

label {
    monitor =
    text = cmd[update:5000] __HOME__/.local/bin/battery-status
    color = rgb(145, 167, 255)
    font_size = 13
    font_family = Noto Sans Bold
    position = 0, -118
    halign = center
    valign = center
}
