import QtQuick
import SddmComponents 2.0

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#121316"

    property int sessionIndex: (sessionModel && sessionModel.lastIndex >= 0) ? sessionModel.lastIndex : 0
    property string currentTime: Qt.formatTime(new Date(), "HH:mm")
    property string currentSec:  Qt.formatTime(new Date(), ":ss")
    property string currentDate: Qt.formatDate(new Date(), "dd.MM.yyyy")

    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: {
            var now = new Date()
            root.currentTime = Qt.formatTime(now, "HH:mm")
            root.currentSec  = Qt.formatTime(now, ":ss")
            root.currentDate = Qt.formatDate(now, "dd.MM.yyyy")
        }
    }

    Image {
        anchors.fill: parent
        source: "hud_bg.png"
        fillMode: Image.PreserveAspectCrop
    }

    function doLogin() {
        var uname = userField.text.trim()
        if (uname === "") uname = userModel.lastUser
        sddm.login(uname, passField.text, root.sessionIndex)
    }

    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_F2) {
            if (sessionModel && sessionModel.rowCount() > 0)
                root.sessionIndex = (root.sessionIndex + 1) % sessionModel.rowCount()
            event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            doLogin()
            event.accepted = true
        }
    }

    // 1. ВЕРХНИЙ ТУЛБАР ИГРОВОГО ДВИЖКА
    Rectangle {
        width: 760; height: 46
        anchors.top: parent.top; anchors.topMargin: 26
        anchors.horizontalCenter: parent.horizontalCenter
        radius: 8
        color: "#141619"
        border.color: "#2e3238"; border.width: 1

        Rectangle {
            width: parent.width; height: 2
            anchors.bottom: parent.bottom
            color: "#5c626d"
        }

        Row {
            anchors.centerIn: parent
            spacing: 16

            Rectangle {
                width: 9; height: 9; radius: 5
                color: "#9ea4b0"
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: "🎮 GAMEDEV ENGINE STUDIO // AUTHENTICATION VIEWPORT"
                color: "#e6edf3"
                font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: "•   " + root.currentDate + "   •"
                color: "#9ea4b0"
                font.family: "monospace"; font.pixelSize: 12; font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
                width: 165; height: 26; radius: 5
                color: "#1e2025"; border.color: "#454a52"; border.width: 1
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    anchors.centerIn: parent
                    text: "▶ 60.0 FPS // READY"
                    color: "#9ea4b0"
                    font.family: "monospace"; font.pixelSize: 11; font.bold: true
                }
            }
        }
    }

    // 2. КРУПНЫЕ ЧАСЫ С ИНДИКАТОРОМ КАДРА
    Row {
        anchors.top: parent.top; anchors.topMargin: 92
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 12

        Text {
            text: root.currentTime
            color: "#f0f6fc"
            font.family: "Noto Sans"; font.pixelSize: 78; font.bold: true
        }
        Rectangle {
            width: 56; height: 32; radius: 6
            color: "#1e2025"; border.color: "#5c626d"; border.width: 1
            anchors.bottom: parent.bottom; anchors.bottomMargin: 16
            Text {
                anchors.centerIn: parent
                text: root.currentSec
                color: "#9ea4b0"
                font.family: "monospace"; font.pixelSize: 15; font.bold: true
            }
        }
    }

    // 3. ВРАЩАЮЩИЙСЯ GIZMO-КОМПАС ЗА КАРТОЧКОЙ АВТОРИЗАЦИИ
    Item {
        width: 580; height: 580
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 42

        Rectangle {
            anchors.centerIn: parent
            width: 530; height: 530; radius: 265
            color: "transparent"
            border.color: "#5c626d"; border.width: 1
            opacity: 0.28
        }
        Item {
            anchors.fill: parent
            RotationAnimator on rotation { from: 0; to: 360; duration: 48000; loops: Animation.Infinite; running: true }
            Repeater {
                model: 12
                Item {
                    anchors.fill: parent
                    rotation: index * 30
                    Rectangle {
                        width: (index % 3 === 0) ? 20 : 9
                        height: 2.5
                        anchors.top: parent.top; anchors.topMargin: 24
                        anchors.horizontalCenter: parent.horizontalCenter
                        color: (index % 3 === 0) ? "#9ea4b0" : "#5c626d"
                        opacity: 0.75
                    }
                }
            }
        }
    }

    // 4. ЛЕВАЯ ПАНЕЛЬ: SCENETREE // ENGINE PIPELINE
    Rectangle {
        width: 280; height: 205
        anchors.left: parent.left; anchors.leftMargin: 56
        anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 42
        radius: 8
        color: "#181a1f"; opacity: 0.94
        border.color: "#2e3238"; border.width: 1

        Rectangle { width: parent.width; height: 3; anchors.top: parent.top; color: "#5c626d" }

        Column {
            anchors.fill: parent; anchors.margins: 18
            spacing: 11
            Text { text: "📂 SceneTree // System Nodes"; color: "#9ea4b0"; font.family: "monospace"; font.pixelSize: 11.5; font.bold: true }
            Rectangle { width: parent.width; height: 1; color: "#2b2e35" }
            Text { text: "├─ 🎮 Compositor  // Hyprland"; color: "#c9d1d9"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
            Text { text: "├─ ⚡ Render_API  // Vulkan DRM"; color: "#9ea4b0"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
            Text { text: "├─ 🐍 Runtime     // Python 3 + C#"; color: "#9ea4b0"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
            Text { text: "└─ 🔊 Audio_Bus   // PipeWire DSP"; color: "#c9d1d9"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
        }
    }

    // 5. ПРАВАЯ ПАНЕЛЬ: INSPECTOR // WORKSPACE MODES
    Rectangle {
        width: 280; height: 205
        anchors.right: parent.right; anchors.rightMargin: 56
        anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 42
        radius: 8
        color: "#181a1f"; opacity: 0.94
        border.color: "#2e3238"; border.width: 1

        Rectangle { width: parent.width; height: 3; anchors.top: parent.top; color: "#9ea4b0" }

        Column {
            anchors.fill: parent; anchors.margins: 18
            spacing: 11
            Text { text: "🔍 Inspector // Target Build"; color: "#9ea4b0"; font.family: "monospace"; font.pixelSize: 11.5; font.bold: true }
            Rectangle { width: parent.width; height: 1; color: "#2b2e35" }
            Text { text: "◈ hyprwork // Engine IDE + Eco"; color: "#9ea4b0"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
            Text { text: "◈ hyprgame // Scanout + Boost"; color: "#9ea4b0"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
            Text { text: "◈ Hotkey   // [F2] Смена сессии"; color: "#c9d1d9"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
            Text { text: "◈ Hotkey   // [Enter] Запуск"; color: "#c9d1d9"; font.family: "monospace"; font.pixelSize: 11; font.bold: true }
        }
    }

    // 6. ЦЕНТРАЛЬНЫЙ ИНСПЕКТОР АВТОРИЗАЦИИ
    Rectangle {
        id: loginCard
        width: 468; height: 348
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 42
        radius: 10
        color: "#141619"
        border.color: "#2e3238"; border.width: 1.5

        Rectangle {
            width: parent.width; height: 3
            anchors.top: parent.top
            color: "#5c626d"
        }

        // Угловые скобы Gizmo (X — красная, Y — изумрудная)
        Rectangle { width: 22; height: 2.5; anchors.top: parent.top; anchors.left: parent.left; color: "#9ea4b0" }
        Rectangle { width: 2.5; height: 22; anchors.top: parent.top; anchors.left: parent.left; color: "#9ea4b0" }
        Rectangle { width: 22; height: 2.5; anchors.bottom: parent.bottom; anchors.right: parent.right; color: "#6c727d" }
        Rectangle { width: 2.5; height: 22; anchors.bottom: parent.bottom; anchors.right: parent.right; color: "#6c727d" }

        Column {
            anchors.fill: parent; anchors.margins: 28
            spacing: 14

            Row {
                spacing: 8
                Rectangle { width: 4; height: 16; color: "#9ea4b0"; anchors.verticalCenter: parent.verticalCenter }
                Text {
                    text: "ЦЕЛЕВАЯ СЕССИЯ ДВИЖКА  •  [F2]"
                    color: "#8b949e"
                    font.family: "monospace"; font.pixelSize: 11; font.bold: true
                }
            }

            // Переключатель сессий (hyprwork / hyprgame)
            Row {
                spacing: 10
                Repeater {
                    model: sessionModel
                    Rectangle {
                        width: 196; height: 38; radius: 6
                        property bool isSel: (index === root.sessionIndex)
                        color: isSel ? "#25282f" : "#1e2025"
                        border.color: isSel ? "#9ea4b0" : "#2e3238"
                        border.width: isSel ? 1.6 : 1.0

                        Row {
                            anchors.centerIn: parent
                            spacing: 8
                            Rectangle {
                                width: 8; height: 8; radius: 4
                                color: parent.parent.isSel ? "#9ea4b0" : "#484f58"
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: model.name
                                color: parent.parent.isSel ? "#ffffff" : "#8b949e"
                                font.family: "monospace"; font.pixelSize: 12.5; font.bold: true
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                        MouseArea {
                            anchors.fill: parent
                            onClicked: root.sessionIndex = index
                        }
                    }
                }
            }

            // Поле оператора
            Rectangle {
                width: parent.width; height: 46; radius: 6
                color: "#1e2025"
                border.color: userField.activeFocus ? "#5c626d" : "#2e3238"; border.width: 1.4
                Rectangle { width: 3; height: parent.height; anchors.left: parent.left; color: "#5c626d" }

                TextInput {
                    id: userField
                    anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                    verticalAlignment: TextInput.AlignVCenter
                    text: userModel.lastUser
                    color: "#f0f6fc"
                    font.family: "monospace"; font.pixelSize: 14; font.bold: true
                    selectByMouse: true
                    KeyNavigation.tab: passField
                }
            }

            // Поле пароля
            Rectangle {
                width: parent.width; height: 46; radius: 6
                color: "#1e2025"
                border.color: passField.activeFocus ? "#9ea4b0" : "#2e3238"; border.width: 1.4
                Rectangle { width: 3; height: parent.height; anchors.left: parent.left; color: "#9ea4b0" }

                Text {
                    anchors.left: parent.left; anchors.leftMargin: 16
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Ключ доступа оператора..."
                    color: "#6e7681"
                    font.family: "Noto Sans"; font.pixelSize: 13
                    visible: passField.text.length === 0
                }

                TextInput {
                    id: passField
                    anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: TextInput.Password
                    passwordCharacter: "●"
                    color: "#9ea4b0"
                    font.family: "Noto Sans"; font.pixelSize: 15; font.bold: true
                    focus: true
                    onAccepted: root.doLogin()
                }
            }

            // Кнопка запуска сессии в стиле кнопки Play в Godot / IDE
            Rectangle {
                width: parent.width; height: 48; radius: 6
                color: loginArea.containsMouse ? "#454a52" : "#23262c"
                border.color: "#9ea4b0"; border.width: 1.5

                Text {
                    anchors.centerIn: parent
                    text: "▶ PLAY // ЗАПУСТИТЬ СЕССИЮ ДВИЖКА"
                    color: "#ffffff"
                    font.family: "Noto Sans"; font.pixelSize: 13; font.bold: true
                }
                MouseArea {
                    id: loginArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: root.doLogin()
                }
            }
        }
    }

    // 7. НИЖНИЙ ДОК ПИТАНИЯ SDDM
    Rectangle {
        width: 320; height: 46; radius: 8
        anchors.bottom: parent.bottom; anchors.bottomMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        color: "#141619"; border.color: "#2e3238"; border.width: 1

        Row {
            anchors.centerIn: parent
            spacing: 12

            Rectangle {
                width: 142; height: 32; radius: 6
                color: rebArea.containsMouse ? "#25282f" : "#1e2025"
                border.color: "#5c626d"; border.width: 1
                Text { anchors.centerIn: parent; text: "⟳ Перезагрузка"; color: "#9ea4b0"; font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true }
                MouseArea { id: rebArea; anchors.fill: parent; hoverEnabled: true; onClicked: sddm.reboot() }
            }
            Rectangle {
                width: 142; height: 32; radius: 6
                color: offArea.containsMouse ? "#2b2426" : "#1e2025"
                border.color: "#6c727d"; border.width: 1
                Text { anchors.centerIn: parent; text: "⏻ Выключение"; color: "#9ea4b0"; font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true }
                MouseArea { id: offArea; anchors.fill: parent; hoverEnabled: true; onClicked: sddm.powerOff() }
            }
        }
    }

    Component.onCompleted: passField.forceActiveFocus()
}
