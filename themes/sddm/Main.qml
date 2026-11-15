import QtQuick 2.15
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
        interval: 1000
        running: true
        repeat: true
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

    Keys.onPressed: {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            root.doLogin()
            event.accepted = true
        }
    }

    // 1. ВЕРХНЯЯ ПАНЕЛЬ СТАТУСА СТУДИИ
    Rectangle {
        width: 680
        height: 44
        anchors.top: parent.top
        anchors.topMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        radius: 8
        color: "#15171b"
        border.color: "#2c3038"
        border.width: 1

        Row {
            anchors.centerIn: parent
            spacing: 18

            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: "#9ea4b0"
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: "▣ STUDIO WORKSTATION // AUTHENTICATION"
                color: "#e6e9ef"
                font.family: "Inter"
                font.pixelSize: 12
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: "•   " + root.currentDate + "   •"
                color: "#8c939e"
                font.family: "monospace"
                font.pixelSize: 12
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
                width: 130
                height: 24
                radius: 5
                color: "#1e2127"
                border.color: "#454a54"
                border.width: 1
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    anchors.centerIn: parent
                    text: "WAYLAND // READY"
                    color: "#c8ccd2"
                    font.family: "monospace"
                    font.pixelSize: 10
                    font.bold: true
                }
            }
        }
    }

    // 2. КРУПНЫЕ ЧАСЫ
    Row {
        anchors.top: parent.top
        anchors.topMargin: 96
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 12

        Text {
            text: root.currentTime
            color: "#e6e9ef"
            font.family: "Inter"
            font.pixelSize: 78
            font.bold: true
        }
        Rectangle {
            width: 54
            height: 30
            radius: 6
            color: "#1b1e24"
            border.color: "#454a54"
            border.width: 1
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 16
            Text {
                anchors.centerIn: parent
                text: root.currentSec
                color: "#9ea4b0"
                font.family: "monospace"
                font.pixelSize: 14
                font.bold: true
            }
        }
    }

    // 3. ЦЕНТРАЛЬНАЯ КАРТОЧКА ВХОДА В СИСТЕМУ
    Rectangle {
        id: loginCard
        width: 440
        height: 320
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 40
        radius: 10
        color: "#14161a"
        border.color: "#343842"
        border.width: 1

        Rectangle {
            width: parent.width
            height: 2
            anchors.top: parent.top
            color: "#6c727d"
        }

        Column {
            anchors.fill: parent
            anchors.margins: 28
            spacing: 14

            Row {
                spacing: 8
                Rectangle {
                    width: 4
                    height: 15
                    color: "#8c939e"
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "АВТОРИЗАЦИЯ ОПЕРАТОРА // STUDIO OS"
                    color: "#9ea4b0"
                    font.family: "monospace"
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            // Индикатор сессии
            Rectangle {
                width: parent.width
                height: 36
                radius: 6
                color: "#1b1e24"
                border.color: "#383c46"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "▣  Сессия: Studio Workstation (Hyprland)"
                    color: "#d4d8de"
                    font.family: "Inter"
                    font.pixelSize: 12
                    font.bold: true
                }
            }

            // Поле логина
            Rectangle {
                width: parent.width
                height: 44
                radius: 6
                color: "#191b20"
                border.color: userField.activeFocus ? "#8c939e" : "#2c3038"
                border.width: 1

                TextInput {
                    id: userField
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    verticalAlignment: TextInput.AlignVCenter
                    text: userModel.lastUser
                    color: "#e6e9ef"
                    font.family: "monospace"
                    font.pixelSize: 13
                    font.bold: true
                    selectByMouse: true
                    KeyNavigation.tab: passField
                }
            }

            // Поле пароля
            Rectangle {
                width: parent.width
                height: 44
                radius: 6
                color: "#191b20"
                border.color: passField.activeFocus ? "#9ea4b0" : "#2c3038"
                border.width: 1

                Text {
                    anchors.left: parent.left
                    anchors.leftMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Введите пароль..."
                    color: "#6c727d"
                    font.family: "Inter"
                    font.pixelSize: 13
                    visible: passField.text.length === 0
                }

                TextInput {
                    id: passField
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    verticalAlignment: TextInput.AlignVCenter
                    echoMode: TextInput.Password
                    passwordCharacter: "●"
                    color: "#e6e9ef"
                    font.family: "Inter"
                    font.pixelSize: 14
                    font.bold: true
                    focus: true
                    Keys.onReturnPressed: root.doLogin()
                    Keys.onEnterPressed: root.doLogin()
                }
            }

            // Кнопка входа
            Rectangle {
                width: parent.width
                height: 44
                radius: 6
                color: loginArea.containsMouse ? "#2f343e" : "#23272f"
                border.color: "#6c727d"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: "▶  ВОЙТИ В РАБОЧУЮ СТАНЦИЮ"
                    color: "#ffffff"
                    font.family: "Inter"
                    font.pixelSize: 12
                    font.bold: true
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

    // 4. НИЖНЯЯ ПАНЕЛЬ ПИТАНИЯ
    Rectangle {
        width: 310
        height: 44
        radius: 8
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        color: "#15171b"
        border.color: "#2c3038"
        border.width: 1

        Row {
            anchors.centerIn: parent
            spacing: 12

            Rectangle {
                width: 138
                height: 30
                radius: 5
                color: rebArea.containsMouse ? "#262a32" : "#1c1f25"
                border.color: "#3e434d"
                border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: "⟳ Перезагрузка"
                    color: "#d4d8de"
                    font.family: "Inter"
                    font.pixelSize: 11
                    font.bold: true
                }
                MouseArea {
                    id: rebArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: sddm.reboot()
                }
            }
            Rectangle {
                width: 138
                height: 30
                radius: 5
                color: offArea.containsMouse ? "#382629" : "#1c1f25"
                border.color: "#523b3e"
                border.width: 1
                Text {
                    anchors.centerIn: parent
                    text: "⏻ Выключение"
                    color: "#e0b8bc"
                    font.family: "Inter"
                    font.pixelSize: 11
                    font.bold: true
                }
                MouseArea {
                    id: offArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: sddm.powerOff()
                }
            }
        }
    }

    Component.onCompleted: passField.forceActiveFocus()
}
