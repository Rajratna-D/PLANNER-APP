import QtQuick
import QtQuick.Controls
import "../components" as Components

ScrollView {
    id: sylTab; clip: true
    property var syllabus: []
    property int _v: root.dataVersion
    on_VChanged: reload(); Component.onCompleted: reload(); onVisibleChanged: if (visible) reload()
    function reload() { syllabus = JSON.parse(bridge.getSyllabus()) }

    Column {
        width: sylTab.width; spacing: 0
        Item { width: parent.width; height: 80
            Column { x: 24; y: 20
                Row { Text { text: "\u2B22 "; color: theme.violet; font.pixelSize: 24 } Text { text: "SYLLABUS"; color: theme.text; font.pixelSize: 24; font.bold: true } }
                Text { text: "Track topics per subject \u2014 see your coverage"; color: theme.subtext; font.pixelSize: 11; topPadding: 4 }
            }
            Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.violet }
            Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }
        Rectangle { x: 24; width: parent.width - 48; height: 56; radius: 10; color: theme.card
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.violet }
                Row { x: 14; y: 12; spacing: 10
                    Components.InputField { id: sySubj; placeholderText: "Subject name (e.g. Engineering Physics)"; width: 300; height: 34 }
                    Components.ActionButton { label: "\uFF0B  ADD SUBJECT"; btnColor: theme.violet; textColor: theme.bg; width: 160; height: 34; fontSize: 10
                        onClicked: { if (!sySubj.text.trim()) return; bridge.addSubject(sySubj.text.trim()); sySubj.text = "" } }
                }
            }
        }
        Item { width: 1; height: 12 }
        Repeater {
            model: syllabus
            delegate: Rectangle {
                x: 24; width: sylTab.width - 48; radius: 10; color: theme.card
                height: sylCol.implicitHeight + 16; border.width: 1; border.color: theme.border
                Column { id: sylCol; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; spacing: 0
                    Rectangle { width: parent.width; height: 2; color: modelData._subject_color || theme.violet }
                    Item { height: 8; width: 1 }
                    Row { x: 16; width: parent.width - 32
                        property int topicsDone: { var t = modelData.topics || []; return t.filter(function(x){return x.done}).length }
                        property int topicsTotal: (modelData.topics || []).length
                        property int pct: topicsTotal > 0 ? Math.round(topicsDone / topicsTotal * 100) : 0
                        Text { text: modelData.name || ""; color: modelData._subject_color || theme.violet; font.pixelSize: 14; font.bold: true }
                        Text { text: "  " + parent.topicsDone + "/" + parent.topicsTotal + " topics  (" + parent.pct + "%)"; color: theme.subtext; font.pixelSize: 10; anchors.verticalCenter: parent.verticalCenter }
                        Item { width: parent.width - parent.children[0].implicitWidth - parent.children[1].implicitWidth - parent.children[3].width; height: 1 }
                        Components.DeleteButton { onDeleteConfirmed: bridge.deleteSubject(modelData.id) }
                    }
                    // Progress bar
                    Rectangle {
                        x: 16; width: parent.width - 32; height: 6; radius: 3; color: theme.border
                        Rectangle {
                            property int pct: { var t = modelData.topics || []; var total = t.length; return total > 0 ? Math.round(t.filter(function(x){return x.done}).length / total * 100) : 0 }
                            width: parent.width * pct / 100; height: parent.height; radius: 3; color: modelData._subject_color || theme.violet
                            Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
                        }
                    }
                    Item { height: 10; width: 1 }
                    // Topics grid (2 columns)
                    Grid { x: 16; width: parent.width - 32; columns: 2; spacing: 6
                        Repeater {
                            model: modelData.topics || []
                            delegate: Rectangle {
                                width: (sylCol.width - 38) / 2; height: 34; radius: 6; color: theme.card2
                                Row { anchors.fill: parent; anchors.leftMargin: 8; spacing: 4
                                    CheckBox { checked: modelData.done || false; width: 18; height: 18; anchors.verticalCenter: parent.verticalCenter
                                        onToggled: bridge.toggleTopic(syllabus[index].id, modelData.id, checked) }
                                    Text { text: modelData.name || ""; color: modelData.done ? theme.subtext : theme.text; font.pixelSize: 10; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight; width: parent.width - 60 }
                                    Components.DeleteButton { width: 22; height: 20; anchors.verticalCenter: parent.verticalCenter
                                        onDeleteConfirmed: bridge.deleteTopic(syllabus[index].id, modelData.id) }
                                }
                            }
                        }
                    }
                    // Add topic
                    Row { x: 16; spacing: 8; topPadding: 10; bottomPadding: 8
                        Components.InputField { id: topicEntry; placeholderText: "Add topic (e.g. Laser Principles)"; width: 340; height: 34; property string sid: modelData.id }
                        Components.ActionButton { label: "\uFF0B TOPIC"; btnColor: modelData._subject_color || theme.violet; textColor: theme.bg; width: 100; height: 34
                            onClicked: { if (!topicEntry.text.trim()) return; bridge.addTopic(topicEntry.sid, topicEntry.text.trim()); topicEntry.text = "" } }
                    }
                }
            }
        }
        Text { visible: syllabus.length === 0; x: 24; text: "No subjects added yet."; color: theme.dim; font.pixelSize: 12; topPadding: 30 }
        Item { width: 1; height: 24 }
    }
}
