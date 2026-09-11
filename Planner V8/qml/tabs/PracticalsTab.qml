import QtQuick
import QtQuick.Controls
import "../components" as Components

ScrollView {
    id: pracTab; clip: true
    property var practicals: []
    property int _v: root.dataVersion
    on_VChanged: reload(); Component.onCompleted: reload(); onVisibleChanged: if (visible) reload()
    function reload() { practicals = JSON.parse(bridge.getPracticals()) }

    Column {
        width: pracTab.width; spacing: 0
        Item { width: parent.width; height: 80
            Column { x: 24; y: 20
                Row { Text { text: "\u25E9 "; color: theme.green; font.pixelSize: 24 } Text { text: "PRACTICALS"; color: theme.text; font.pixelSize: 24; font.bold: true } }
                Text { text: "Track lab experiments and writeup progress"; color: theme.subtext; font.pixelSize: 11; topPadding: 4 }
            }
            Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.green }
            Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }
        Rectangle { x: 24; width: parent.width - 48; height: 56; radius: 10; color: theme.card
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.green }
                Row { x: 14; y: 12; spacing: 8
                    Components.InputField { id: prSubj; placeholderText: "Subject"; width: 130; height: 34 }
                    Components.InputField { id: prNum; placeholderText: "Exp No"; width: 70; height: 34 }
                    Components.InputField { id: prTitle; placeholderText: "Experiment title"; width: 260; height: 34 }
                    Components.InputField { id: prDate; placeholderText: "YYYY-MM-DD"; width: 130; height: 34 }
                    Components.ActionButton { label: "\uFF0B  ADD"; btnColor: theme.green; textColor: theme.bg; width: 100; height: 34; fontSize: 10
                        onClicked: {
                            if (!prSubj.text.trim() || !prTitle.text.trim()) return
                            bridge.addPractical(prSubj.text.trim(), prNum.text.trim(), prTitle.text.trim(), prDate.text.trim())
                            prSubj.text = ""; prNum.text = ""; prTitle.text = ""; prDate.text = ""
                        }
                    }
                }
            }
        }
        Item { width: 1; height: 12 }
        Repeater {
            model: practicals
            delegate: Rectangle {
                x: 24; width: pracTab.width - 48; height: 110; radius: 12
                color: modelData.done ? "#0D0F18" : theme.card
                border.width: 2; border.color: pMa.containsMouse ? (modelData._subject_color || theme.green) : theme.border
                Behavior on border.color { ColorAnimation { duration: 200 } }
                MouseArea { id: pMa; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; propagateComposedEvents: true }
                Column { anchors.fill: parent; spacing: 0
                    Rectangle { width: parent.width; height: 3; color: modelData.done ? theme.border : (modelData._subject_color || theme.green) }
                    Item { height: 8; width: 1 }
                    Row { x: 16; width: parent.width - 32
                        Text { text: "Exp " + (modelData.num || "?") + " \u2014 " + (modelData.title || ""); color: modelData.done ? theme.subtext : theme.text; font.pixelSize: 12; font.bold: true }
                        Item { width: parent.width - parent.children[0].implicitWidth - parent.children[2].width; height: 1 }
                        Components.DeleteButton { onDeleteConfirmed: bridge.deletePractical(modelData.id) }
                    }
                    Text { x: 16; text: "Subject: " + (modelData.subject || "") + "   Date: " + (modelData.date || ""); color: theme.subtext; font.pixelSize: 10 }
                    Item { height: 6; width: 1 }
                    Row { x: 16; spacing: 6
                        Repeater {
                            model: [
                                { label: "PERFORMED", key: "performed", col: "#10B981" },
                                { label: "WRITEUP DONE", key: "writeup", col: "#3B82F6" },
                                { label: "SUBMITTED", key: "submitted", col: "#EAB308" }
                            ]
                            delegate: Components.ActionButton {
                                label: (practicals[index] && practicals[index][modelData.key] ? "\u2713 " : "\u25CB ") + modelData.label
                                btnColor: practicals[index] && practicals[index][modelData.key] ? modelData.col : theme.border
                                textColor: practicals[index] && practicals[index][modelData.key] ? theme.bg : theme.subtext
                                width: 130; height: 30; fontSize: 9
                                onClicked: bridge.togglePractical(practicals[index].id, modelData.key)
                            }
                        }
                    }
                }
            }
        }
        Text { visible: practicals.length === 0; x: 24; text: "No practicals added."; color: theme.dim; font.pixelSize: 12; topPadding: 30 }
        Item { width: 1; height: 24 }
    }
}
