import QtQuick
import QtQuick.Controls
import "../components" as Components

ScrollView {
    id: assignTab; clip: true
    property var assignments: []
    property int _v: root.dataVersion
    on_VChanged: reload(); Component.onCompleted: reload(); onVisibleChanged: if (visible) reload()
    function reload() { assignments = JSON.parse(bridge.getAssignments()) }

    Column {
        width: assignTab.width; spacing: 0
        Item { width: parent.width; height: 80
            Column { x: 24; y: 20
                Row { Text { text: "\u25E7 "; color: theme.red; font.pixelSize: 24 } Text { text: "ASSIGNMENTS"; color: theme.text; font.pixelSize: 24; font.bold: true } }
                Text { text: "Track submissions and deadlines"; color: theme.subtext; font.pixelSize: 11; topPadding: 4 }
            }
            Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.red }
            Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }
        Rectangle { x: 24; width: parent.width - 48; height: 56; radius: 10; color: theme.card
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.red }
                Row { x: 14; y: 12; spacing: 8
                    Components.InputField { id: asSubj; placeholderText: "Subject"; width: 130; height: 34 }
                    Components.InputField { id: asTitle; placeholderText: "Assignment title"; width: 240; height: 34 }
                    Components.InputField { id: asDue; placeholderText: "YYYY-MM-DD"; width: 130; height: 34 }
                    Components.InputField { id: asMarks; placeholderText: "Marks"; width: 70; height: 34 }
                    Components.ActionButton { label: "\uFF0B  ADD"; btnColor: theme.red; textColor: theme.text; width: 100; height: 34; fontSize: 10
                        onClicked: {
                            if (!asSubj.text.trim() || !asTitle.text.trim()) return
                            bridge.addAssignment(asSubj.text.trim(), asTitle.text.trim(), asDue.text.trim(), asMarks.text.trim())
                            asSubj.text = ""; asTitle.text = ""; asDue.text = ""; asMarks.text = ""
                        }
                    }
                }
            }
        }
        Item { width: 1; height: 12 }
        Repeater {
            model: assignments
            delegate: Rectangle {
                x: 24; width: assignTab.width - 48; height: 80; radius: 12
                color: modelData.submitted ? "#0D0F18" : theme.card
                border.width: 2; border.color: aMa.containsMouse ? (modelData._subject_color || theme.red) : theme.border
                Behavior on border.color { ColorAnimation { duration: 200 } }
                MouseArea { id: aMa; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; propagateComposedEvents: true }
                Column { anchors.fill: parent; spacing: 0
                    Rectangle { width: parent.width; height: 3; color: modelData.submitted ? theme.border : (modelData._subject_color || theme.red) }
                    Item { height: 10; width: 1 }
                    Row { x: 16; width: parent.width - 32; spacing: 4
                        Text { text: "[" + (modelData.subject || "") + "]"; color: modelData.submitted ? theme.subtext : (modelData._subject_color || theme.red); font.pixelSize: 12; font.bold: true }
                        Text { text: " " + (modelData.title || ""); color: modelData.submitted ? theme.subtext : theme.text; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight; width: parent.width - 300 }
                        Item { width: parent.width - parent.children[0].implicitWidth - parent.children[1].width - parent.children[3].implicitWidth - parent.children[4].width - (modelData.submitted ? 0 : parent.children[5].width) - 24; height: 1 }
                        Text { text: modelData.submitted ? "" : (modelData._urgency_lbl || ""); color: modelData._urgency_color || theme.subtext; font.pixelSize: 9; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                        Components.ActionButton {
                            visible: !modelData.submitted; label: "\u2713 SUBMITTED"; btnColor: theme.green; textColor: theme.bg; width: 120; height: 28; fontSize: 9
                            onClicked: bridge.submitAssignment(modelData.id); anchors.verticalCenter: parent.verticalCenter
                        }
                        Components.DeleteButton { anchors.verticalCenter: parent.verticalCenter; onDeleteConfirmed: bridge.deleteAssignment(modelData.id) }
                    }
                    Text { x: 16; visible: !!(modelData.marks); text: "Marks: " + (modelData.marks || ""); color: theme.subtext; font.pixelSize: 10 }
                }
            }
        }
        Text { visible: assignments.length === 0; x: 24; text: "No assignments added."; color: theme.dim; font.pixelSize: 12; topPadding: 30 }
        Item { width: 1; height: 24 }
    }
}
