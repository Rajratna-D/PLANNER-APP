import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as Components

ScrollView {
    id: testsTab; clip: true
    property var tests: []
    property int _v: root.dataVersion
    on_VChanged: reload()
    Component.onCompleted: reload()
    onVisibleChanged: if (visible) reload()
    function reload() { tests = JSON.parse(bridge.getTests()) }

    Column {
        width: testsTab.width; spacing: 0

        // Header
        TabHeader { icon: "\u25C8"; title: "TESTS"; subtitle: "Schedule exams and track countdown"; accentColor: theme.gold }

        // Form
        Rectangle {
            x: 24; width: parent.width - 48; height: 56; radius: 10; color: theme.card
            Column { anchors.fill: parent; spacing: 0
                Rectangle { width: parent.width; height: 2; color: theme.gold }
                Row { x: 14; y: 12; spacing: 8
                    Components.InputField { id: teSubj; placeholderText: "Subject"; width: 160; height: 34 }
                    Components.InputField { id: teDate; placeholderText: "YYYY-MM-DD"; width: 130; height: 34 }
                    Components.InputField { id: teTime; placeholderText: "HH:MM"; width: 90; height: 34 }
                    Components.InputField { id: teNote; placeholderText: "Note (optional)"; width: 200; height: 34 }
                    Components.ActionButton {
                        label: "\uFF0B  ADD TEST"; btnColor: theme.gold; textColor: theme.bg
                        width: 130; height: 34; fontSize: 10
                        onClicked: {
                            if (!teSubj.text.trim() || !teDate.text.trim()) return
                            bridge.addTest(teSubj.text.trim(), teDate.text.trim(), teTime.text.trim(), teNote.text.trim())
                            teSubj.text = ""; teDate.text = ""; teTime.text = ""; teNote.text = ""
                        }
                    }
                }
            }
        }

        Item { width: 1; height: 12 }

        // List
        Repeater {
            model: tests
            delegate: Rectangle {
                x: 24; width: testsTab.width - 48; height: 80; radius: 12; color: theme.card
                border.width: 2; border.color: testCardMa.containsMouse ? (modelData._subject_color || theme.gold) : theme.border
                Behavior on border.color { ColorAnimation { duration: 200 } }
                MouseArea { id: testCardMa; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; propagateComposedEvents: true }
                Column { anchors.fill: parent; spacing: 0
                    Rectangle { width: parent.width; height: 3; color: modelData._subject_color || theme.gold }
                    Item { height: 10; width: 1 }
                    Row {
                        x: 16; width: parent.width - 32
                        Text { text: modelData.subject || ""; color: modelData._subject_color || theme.gold; font.pixelSize: 13; font.bold: true; font.family: theme.fontFamily }
                        Item { width: parent.width - parent.children[0].implicitWidth - parent.children[2].implicitWidth - parent.children[3].width - 8; height: 1 }
                        Text { text: modelData._urgency_lbl || ""; color: modelData._urgency_color || theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                        Components.DeleteButton { anchors.verticalCenter: parent.verticalCenter; onDeleteConfirmed: bridge.deleteTest(modelData.id) }
                    }
                    Text { x: 16; text: "\uD83D\uDCC5 " + (modelData.date || "") + "  \u23F0 " + (modelData.time || ""); color: theme.subtext; font.pixelSize: 10; font.family: theme.fontFamily }
                    Text { x: 16; text: modelData.note || ""; color: theme.dim; font.pixelSize: 10; font.family: theme.fontFamily; visible: !!modelData.note }
                }
            }
        }
        Text { visible: tests.length === 0; x: 24; text: "No tests scheduled."; color: theme.dim; font.pixelSize: 12; font.family: theme.fontFamily; topPadding: 30 }
        Item { width: 1; height: 24 }
    }

    component TabHeader: Item {
        property string icon: ""
        property string title: ""
        property string subtitle: ""
        property color accentColor: theme.cyan
        width: parent.width; height: 80
        Column {
            x: 24; y: 20; spacing: 0
            Row { spacing: 4
                Text { text: icon + " "; color: accentColor; font.pixelSize: 24; font.family: theme.fontFamily }
                Text { text: title; color: theme.text; font.pixelSize: 24; font.bold: true; font.family: theme.fontFamily }
            }
            Text { text: subtitle; color: theme.subtext; font.pixelSize: 11; font.family: theme.fontFamily; topPadding: 4 }
        }
        Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: accentColor }
        Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
    }
}
