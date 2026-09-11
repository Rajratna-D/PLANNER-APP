import QtQuick
import QtQuick.Controls
import "../components" as Components

ScrollView {
    id: pomoTab; clip: true
    property var pomoState: ({})
    property int _v: root.dataVersion

    Connections {
        target: bridge
        function onPomoStateChanged() { refreshState() }
        function onDataChanged() { refreshLog() }
    }
    Component.onCompleted: { refreshState(); refreshLog() }
    onVisibleChanged: if (visible) { refreshState(); refreshLog() }

    function refreshState() { pomoState = JSON.parse(bridge.getPomoState()) }
    function refreshLog() {
        var raw = JSON.parse(bridge.getPomodoroLog())
        var today = new Date().toISOString().substring(0, 10)
        var todayLog = raw.filter(function(p) { return p.date === today })
        todayLog.reverse()
        logRepeater.model = todayLog
    }

    Column {
        width: pomoTab.width; spacing: 0

        // Header
        Item { width: parent.width; height: 80
            Column { x: 24; y: 20
                Row { Text { text: "\u25CE "; color: theme.pink; font.pixelSize: 24 } Text { text: "POMODORO"; color: theme.text; font.pixelSize: 24; font.bold: true } }
                Text { text: "Focused work sessions with built-in timer"; color: theme.subtext; font.pixelSize: 11; topPadding: 4 }
            }
            Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.pink }
            Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }

        // Timer card
        Item { width: parent.width; height: 320
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 420; height: 300; radius: 16; color: theme.card
                border.width: 1; border.color: theme.border
                Column { anchors.fill: parent; spacing: 0
                    Rectangle { width: parent.width; height: 3; color: theme.pink }
                    Item { height: 20; width: 1 }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: pomoState.mode === "work" ? "FOCUS SESSION" : (pomoState.mode === "long_break" ? "LONG BREAK" : "SHORT BREAK")
                        color: pomoState.mode === "work" ? theme.pink : (pomoState.mode === "long_break" ? theme.green : theme.cyan)
                        font.pixelSize: 13; font.bold: true; font.family: theme.fontFamily
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: pomoState.timeStr || "25:00"
                        color: theme.text; font.pixelSize: 52; font.bold: true; font.family: "Consolas"
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: "Session " + (pomoState.sessions || 0) + "  \u2022  Today: " + (pomoState.todayCount || 0)
                        color: theme.subtext; font.pixelSize: 10; font.family: theme.fontFamily
                    }
                    Item { height: 10; width: 1 }
                    // Progress bar
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 340; height: 6; radius: 3; color: theme.border
                        Rectangle {
                            width: parent.width * (pomoState.progress || 0); height: parent.height; radius: 3; color: theme.pink
                            Behavior on width { NumberAnimation { duration: 800; easing.type: Easing.OutCubic } }
                        }
                    }
                    Item { height: 16; width: 1 }
                    // Buttons
                    Row { anchors.horizontalCenter: parent.horizontalCenter; spacing: 8
                        Components.ActionButton {
                            label: pomoState.running ? "\u23F8  PAUSE" : "\u25B6  START"
                            btnColor: theme.pink; textColor: theme.bg; width: 130; height: 40; fontSize: 13
                            onClicked: bridge.pomoStartStop()
                        }
                        Components.ActionButton {
                            label: "\u21BA  RESET"; btnColor: theme.border2; textColor: theme.text; width: 110; height: 40; fontSize: 12
                            onClicked: bridge.pomoReset()
                        }
                    }
                }
            }
        }

        // Settings
        Rectangle {
            x: 60; width: parent.width - 120; height: 90; radius: 10; color: theme.card
            border.width: 1; border.color: theme.border
            Column { anchors.fill: parent; spacing: 0
                Rectangle { width: parent.width; height: 1; color: theme.border2 }
                Row { x: 20; y: 12; spacing: 6
                    Text { text: "Work (min):"; color: theme.subtext; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                    Components.InputField { id: pomoWork; placeholderText: "25"; width: 60; height: 28; text: "25" }
                    Item { width: 10; height: 1 }
                    Text { text: "Short break:"; color: theme.subtext; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                    Components.InputField { id: pomoShort; placeholderText: "5"; width: 60; height: 28; text: "5" }
                    Item { width: 10; height: 1 }
                    Text { text: "Long break:"; color: theme.subtext; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                    Components.InputField { id: pomoLong; placeholderText: "15"; width: 60; height: 28; text: "15" }
                    Item { width: 10; height: 1 }
                    Components.ActionButton { label: "APPLY"; btnColor: theme.border2; textColor: theme.cyan; width: 70; height: 28; fontSize: 9
                        onClicked: bridge.pomoApplySettings(parseInt(pomoWork.text) || 25, parseInt(pomoShort.text) || 5, parseInt(pomoLong.text) || 15) }
                }
                Row { x: 20; y: 50; spacing: 6
                    Text { text: "Working on:"; color: theme.subtext; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                    ComboBox {
                        id: pomoTaskCombo; width: 320; height: 28
                        model: JSON.parse(bridge.pomoGetTasks())
                        background: Rectangle { radius: 8; color: theme.panel; border.width: 1; border.color: theme.border }
                        contentItem: Text { text: pomoTaskCombo.currentText; color: theme.text; font.pixelSize: 11; leftPadding: 12; verticalAlignment: Text.AlignVCenter }
                        onCurrentTextChanged: bridge.pomoSetTask(currentText)
                    }
                }
            }
        }

        Item { width: 1; height: 12 }

        // Today's log header
        Item { width: parent.width; height: 30
            Text { x: 44; text: "\u25CE  TODAY'S LOG"; color: theme.pink; font.pixelSize: 12; font.bold: true }
            Rectangle { y: 28; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }

        Repeater {
            id: logRepeater; model: []
            delegate: Rectangle {
                x: 24; width: pomoTab.width - 48; height: 36; radius: 8; color: theme.card
                border.width: 1; border.color: theme.border
                Row { x: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 8
                    Rectangle { width: 8; height: 8; radius: 4; color: modelData.type === "work" ? theme.pink : theme.cyan }
                    Text { text: modelData.time || ""; color: theme.subtext; font.pixelSize: 10 }
                    Text { text: modelData.type === "work" ? "Focus" : "Break"; color: modelData.type === "work" ? theme.pink : theme.cyan; font.pixelSize: 10; font.bold: true }
                    Text { text: (modelData.duration_min || 0) + " min"; color: theme.dim; font.pixelSize: 10 }
                    Text { text: modelData.task || ""; color: theme.subtext; font.pixelSize: 10; elide: Text.ElideRight; width: 200 }
                }
            }
        }
        Item { width: 1; height: 24 }
    }
}
