import QtQuick

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#07090f"

    property int sessionIndex: (sessionModel && sessionModel.lastIndex >= 0) ? sessionModel.lastIndex : 0
    property string errorText: ""
    property bool loggingIn: false
    property string batStatus: (typeof config !== "undefined" && config.battery) ? config.battery : "⚡ СЕТЬ AC"

    function startLogin() {
        if (root.loggingIn) return
        root.errorText = ""
        root.loggingIn = true
        loginTimer.start()
    }

    Image {
        anchors.fill: parent
        source: "hud_bg.png"
        fillMode: Image.PreserveAspectCrop
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.loggingIn = false
            root.errorText = "ОШИБКА ДОСТУПА // НЕВЕРНЫЙ ПАРОЛЬ"
            passInput.text = ""
            passInput.forceActiveFocus()
        }
    }

    Timer {
        id: loginTimer
        interval: 260
        repeat: false
        onTriggered: sddm.login(userInput.text, passInput.text, root.sessionIndex)
    }

    // Вращающееся орбитальное прицельное кольцо за карточкой входа
    Item {
        width: 560; height: 560
        anchors.centerIn: deckCard
        opacity: 0.45

        RotationAnimation on rotation {
            from: 0; to: 360; duration: 64000
            loops: Animation.Infinite; running: true
        }

        Repeater {
            model: 12
            Item {
                anchors.fill: parent
                rotation: index * 30
                Rectangle {
                    width: index % 3 === 0 ? 18 : 8
                    height: 2
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: index % 3 === 0 ? "#22b8cf" : "#4c6ef5"
                }
            }
        }
    }

    // Верхняя командная телеметрическая дека SDDM (с отображением заряда батареи)
    Rectangle {
        width: topRow.implicitWidth + 44
        height: 46
        anchors.top: parent.top
        anchors.topMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        radius: 12
        color: "#ea0c101b"
        border.width: 1
        border.color: "#253250"

        Row {
            id: topRow
            anchors.centerIn: parent
            spacing: 16

            Row {
                spacing: 8
                Rectangle {
                    width: 8; height: 8; radius: 4
                    anchors.verticalCenter: parent.verticalCenter
                    color: "#22b8cf"
                    SequentialAnimation on opacity {
                        loops: Animation.Infinite; running: true
                        NumberAnimation { from: 0.35; to: 1.0; duration: 1100 }
                        NumberAnimation { from: 1.0; to: 0.35; duration: 1100 }
                    }
                }
                Text {
                    text: "◈ CYBER DECK // ACCESS GATE"
                    color: "#e5ecff"
                    font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true
                }
            }

            Rectangle { width: 1; height: 16; color: "#25314d" }

            Text {
                id: dateLabel
                color: "#748ffc"
                font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true
                text: Qt.formatDateTime(new Date(), "dd.MM.yyyy  •  dddd")
            }

            Rectangle { width: 1; height: 16; color: "#25314d" }

            Rectangle {
                height: 26
                width: batText.implicitWidth + 20
                radius: 7
                color: "#0e1a18"
                border.width: 1
                border.color: "#1c3d35"

                Text {
                    id: batText
                    anchors.centerIn: parent
                    text: root.batStatus
                    color: "#63e6be"
                    font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true
                }
            }
        }
    }

    // Блок часов с живым секундным индикатором
    Row {
        anchors.top: parent.top
        anchors.topMargin: 92
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 12

        Text {
            id: clockLabel
            color: "#e5ecff"
            font.family: "Noto Sans"; font.pixelSize: 78; font.bold: true
            text: Qt.formatDateTime(new Date(), "HH:mm")
        }

        Rectangle {
            width: 52; height: 30; radius: 8
            anchors.bottom: clockLabel.bottom
            anchors.bottomMargin: 14
            color: "#121b2f"
            border.width: 1
            border.color: "#364fc7"

            Text {
                id: secLabel
                anchors.centerIn: parent
                color: "#66d9e8"
                font.family: "Noto Sans"; font.pixelSize: 14; font.bold: true
                text: Qt.formatDateTime(new Date(), ":ss")
            }
        }
    }

    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: {
            var now = new Date()
            clockLabel.text = Qt.formatDateTime(now, "HH:mm")
            secLabel.text = Qt.formatDateTime(now, ":ss")
            dateLabel.text = Qt.formatDateTime(now, "dd.MM.yyyy  •  dddd")
        }
    }

    // Левое тактическое крыло телеметрии
    Rectangle {
        width: 250; height: 170
        anchors.left: parent.left; anchors.leftMargin: 64
        anchors.verticalCenter: deckCard.verticalCenter
        radius: 12
        color: "#cc0c101b"
        border.width: 1; border.color: "#1f2a44"
        visible: parent.width >= 1360

        Rectangle { width: 3; height: 28; x: 0; y: 16; color: "#4c6ef5" }

        Column {
            anchors.fill: parent; anchors.margins: 18; spacing: 10
            Text { text: "◈ SYSTEM TELEMETRY"; color: "#dbe4ff"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Rectangle { width: parent.width; height: 1; color: "#1d2740" }
            Text { text: "COMPOSITOR  // HYPRLAND"; color: "#7f8db0"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Text { text: "GRAPHICS    // WAYLAND DRM"; color: "#7f8db0"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Text { text: "NET BYPASS  // ZAPRET NFQWS"; color: "#22b8cf"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Text { text: "AUTH ENGINE // PAM SECURE"; color: "#7f8db0"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
        }
    }

    // Правое тактическое крыло сессий
    Rectangle {
        width: 250; height: 170
        anchors.right: parent.right; anchors.rightMargin: 64
        anchors.verticalCenter: deckCard.verticalCenter
        radius: 12
        color: "#cc0c101b"
        border.width: 1; border.color: "#1f2a44"
        visible: parent.width >= 1360

        Rectangle { width: 3; height: 28; anchors.right: parent.right; y: 16; color: "#22b8cf" }

        Column {
            anchors.fill: parent; anchors.margins: 18; spacing: 10
            Text { text: "◈ ACTIVE ARCHITECTURE"; color: "#dbe4ff"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Rectangle { width: parent.width; height: 1; color: "#1d2740" }
            Text { text: "WORK   // FREE-WS + VPN"; color: "#748ffc"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Text { text: "GAMING // DIRECT SCANOUT"; color: "#63e6be"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Text { text: "HOTKEY // [F2] СМЕНА СЕССИИ"; color: "#7f8db0"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
            Text { text: "HOTKEY // [ENTER] СТАРТ"; color: "#7f8db0"; font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true }
        }
    }

    // Центральная боевая дека авторизации с угловыми скобами и сканером
    Rectangle {
        id: deckCard
        width: 456
        height: formCol.implicitHeight + 64
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 42
        color: "#f00d111c"
        radius: 16
        border.width: 1
        border.color: "#263352"

        // Бегущий световой сканер по верхней грани карточки
        Item {
            width: parent.width - 32; height: 2
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            clip: true

            Rectangle {
                id: scanBeam
                width: 110; height: 2
                color: "#22b8cf"
                SequentialAnimation on x {
                    loops: Animation.Infinite; running: true
                    NumberAnimation { from: -110; to: 420; duration: 2600; easing.type: Easing.InOutSine }
                    NumberAnimation { from: 420; to: -110; duration: 2600; easing.type: Easing.InOutSine }
                }
            }
        }

        // Угловые HUD-скобы на самой карточке входа
        Rectangle { width: 22; height: 2; x: -1; y: -1; color: "#22b8cf" }
        Rectangle { width: 2; height: 22; x: -1; y: -1; color: "#22b8cf" }
        Rectangle { width: 22; height: 2; anchors.right: parent.right; anchors.rightMargin: -1; y: -1; color: "#22b8cf" }
        Rectangle { width: 2; height: 22; anchors.right: parent.right; anchors.rightMargin: -1; y: -1; color: "#22b8cf" }
        Rectangle { width: 22; height: 2; x: -1; anchors.bottom: parent.bottom; anchors.bottomMargin: -1; color: "#4c6ef5" }
        Rectangle { width: 2; height: 22; x: -1; anchors.bottom: parent.bottom; anchors.bottomMargin: -1; color: "#4c6ef5" }
        Rectangle { width: 22; height: 2; anchors.right: parent.right; anchors.rightMargin: -1; anchors.bottom: parent.bottom; anchors.bottomMargin: -1; color: "#4c6ef5" }
        Rectangle { width: 2; height: 22; anchors.right: parent.right; anchors.rightMargin: -1; anchors.bottom: parent.bottom; anchors.bottomMargin: -1; color: "#4c6ef5" }

        Column {
            id: formCol
            width: parent.width - 56
            anchors.centerIn: parent
            spacing: 14

            Row {
                spacing: 8
                Rectangle { width: 4; height: 16; radius: 2; color: "#22b8cf" }
                Text {
                    text: "ПРОФИЛЬ СЕССИИ  •  КЛАВИША [F2]"
                    color: "#9aa8c7"
                    font.family: "Noto Sans"; font.pixelSize: 11; font.bold: true
                }
            }

            Flow {
                width: parent.width
                spacing: 8

                Repeater {
                    id: sessionRepeater
                    model: sessionModel
                    delegate: Rectangle {
                        height: 36
                        width: sessRow.implicitWidth + 24
                        radius: 9
                        color: index === root.sessionIndex ? "#162440" : (sMouse.containsMouse ? "#12192b" : "#0f1422")
                        border.width: 1
                        border.color: index === root.sessionIndex ? "#4c6ef5" : "#212b42"

                        Behavior on color { ColorAnimation { duration: 130 } }

                        Row {
                            id: sessRow
                            anchors.centerIn: parent
                            spacing: 8

                            Rectangle {
                                width: 7; height: 7; radius: 4
                                anchors.verticalCenter: parent.verticalCenter
                                color: index === root.sessionIndex ? "#22b8cf" : "#495470"
                            }

                            Text {
                                text: model.name
                                color: index === root.sessionIndex ? "#e5ecff" : "#8d99b8"
                                font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true
                            }
                        }

                        MouseArea {
                            id: sMouse
                            anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.sessionIndex = index
                        }
                    }
                }
            }

            Rectangle {
                width: parent.width; height: 45; radius: 10
                color: userInput.activeFocus ? "#131b2e" : "#0e1320"
                border.width: 1
                border.color: userInput.activeFocus ? "#4c6ef5" : "#222c44"

                TextInput {
                    id: userInput
                    anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14
                    verticalAlignment: TextInput.AlignVCenter
                    color: "#e2e8f8"; font.family: "Noto Sans"; font.pixelSize: 14
                    text: userModel.lastUser; selectByMouse: true
                    KeyNavigation.tab: passInput
                    Keys.onReturnPressed: root.startLogin()
                    Keys.onEnterPressed: root.startLogin()
                }
            }

            Rectangle {
                width: parent.width; height: 45; radius: 10
                color: passInput.activeFocus ? "#131b2e" : "#0e1320"
                border.width: 1
                border.color: passInput.activeFocus ? "#22b8cf" : "#222c44"

                Text {
                    anchors.left: parent.left; anchors.leftMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Ключ авторизации..."
                    color: "#677391"; font.family: "Noto Sans"; font.pixelSize: 14
                    visible: passInput.text.length === 0
                }

                TextInput {
                    id: passInput
                    anchors.fill: parent; anchors.leftMargin: 14; anchors.rightMargin: 14
                    verticalAlignment: TextInput.AlignVCenter
                    color: "#e2e8f8"; font.family: "Noto Sans"; font.pixelSize: 14
                    echoMode: TextInput.Password; focus: true; selectByMouse: true
                    Component.onCompleted: passInput.forceActiveFocus()
                    Keys.onReturnPressed: root.startLogin()
                    Keys.onEnterPressed: root.startLogin()
                    Keys.onPressed: function(event) {
                        if (event.key === Qt.Key_F2 && sessionRepeater.count > 0) {
                            root.sessionIndex = (root.sessionIndex + 1) % sessionRepeater.count
                            event.accepted = true
                        }
                    }
                }
            }

            Rectangle {
                width: parent.width; height: 46; radius: 10
                color: lMouse.containsMouse ? "#1f3257" : "#16233d"
                border.width: 1
                border.color: lMouse.containsMouse ? "#22b8cf" : "#4c6ef5"

                Behavior on color { ColorAnimation { duration: 130 } }

                Text {
                    anchors.centerIn: parent
                    text: "◈ ИНИЦИИРОВАТЬ СЕССИЮ  ⟫"
                    color: "#e5ecff"
                    font.family: "Noto Sans"; font.pixelSize: 13; font.bold: true
                }

                MouseArea {
                    id: lMouse
                    anchors.fill: parent; hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.startLogin()
                }
            }

            Text {
                visible: root.errorText.length > 0
                text: root.errorText
                color: "#ff8787"
                font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    // Нижняя приборная панель управления питанием
    Rectangle {
        height: 46
        width: pwrRow.implicitWidth + 28
        anchors.bottom: parent.bottom; anchors.bottomMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        radius: 12
        color: "#ea0d111c"
        border.width: 1; border.color: "#24304d"

        Row {
            id: pwrRow
            anchors.centerIn: parent
            spacing: 12

            Rectangle {
                height: 30; width: 136; radius: 8
                color: rMouse.containsMouse ? "#1a243b" : "#121827"
                border.width: 1; border.color: "#263352"
                Text { anchors.centerIn: parent; text: "⟳ Перезагрузка"; color: "#b8c4e0"; font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true }
                MouseArea { id: rMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sddm.reboot() }
            }

            Rectangle {
                height: 30; width: 136; radius: 8
                color: pMouse.containsMouse ? "#2e1a22" : "#1f1318"
                border.width: 1; border.color: "#4a2631"
                Text { anchors.centerIn: parent; text: "⏻ Выключение"; color: "#f098a6"; font.family: "Noto Sans"; font.pixelSize: 12; font.bold: true }
                MouseArea { id: pMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: sddm.powerOff() }
            }
        }
    }

    // Выдвижная стена перехода в сессию
    Rectangle {
        id: transitionWall
        x: 0; y: 0
        height: parent.height
        width: root.loggingIn ? parent.width : 0
        color: "#07090f"
        Behavior on width { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }

        Rectangle {
            width: 3; height: parent.height
            anchors.right: parent.right
            visible: transitionWall.width > 0
            color: "#22b8cf"
        }
    }
}
