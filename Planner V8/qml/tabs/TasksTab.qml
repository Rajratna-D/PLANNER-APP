import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as Components

ScrollView {
    id: tasksTab; clip: true
    property var tasks: []
    property string sortBy: "Priority"
    property string filterBy: ""
    property int _v: root.dataVersion
    on_VChanged: reload()
    Component.onCompleted: reload()
    onVisibleChanged: if (visible) reload()

    readonly property var priorityOrder: ["Immediate", "Important", "2nd Priority", "3rd Priority", "Someday"]
    readonly property var pColors: ({ "Immediate": "#EF4444", "Important": "#F59E0B", "2nd Priority": "#3B82F6", "3rd Priority": "#10B981", "Someday": "#94A3B8" })

    function reload() {
        var raw = JSON.parse(bridge.getTasks())
        var pending = raw.filter(function(t) { return !t.done })
        var done = raw.filter(function(t) { return t.done })
        if (filterBy) pending = pending.filter(function(t) { return t.priority === filterBy })
        if (sortBy === "Priority") pending.sort(function(a, b) { return priorityOrder.indexOf(a.priority || "Someday") - priorityOrder.indexOf(b.priority || "Someday") })
        else if (sortBy === "Due Date") pending.sort(function(a, b) { return (a.due || "9999").localeCompare(b.due || "9999") })
        else pending.sort(function(a, b) { return (b.added || "").localeCompare(a.added || "") })
        tasks = pending.concat([{ _separator: true, _doneCount: done.length }]).concat(done.slice(-8))
    }

    Column {
        width: tasksTab.width; spacing: 0

        // Header
        Item {
            width: parent.width; height: 80
            Column { x: 24; y: 20
                Row { spacing: 4
                    Text { text: "\u25A3 "; color: theme.orange; font.pixelSize: 24; font.family: theme.fontFamily }
                    Text { text: "TASKS"; color: theme.text; font.pixelSize: 24; font.bold: true; font.family: theme.fontFamily }
                }
                Text { text: "Priority-sorted tasks with recurrence"; color: theme.subtext; font.pixelSize: 11; font.family: theme.fontFamily; topPadding: 4 }
            }
            Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.orange }
            Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }

        // Form
        Rectangle {
            x: 24; width: parent.width - 48; height: 100; radius: 10; color: theme.card
            Column { anchors.fill: parent; spacing: 0
                Rectangle { width: parent.width; height: 2; color: theme.orange }
                Row { x: 14; y: 10; spacing: 8
                    Components.InputField { id: taEntry; placeholderText: "Task description"; width: 300; height: 34 }
                    ComboBox {
                        id: taPrio; model: priorityOrder; currentIndex: 0
                        width: 150; height: 34
                        background: Rectangle { radius: 8; color: theme.panel; border.width: 1; border.color: theme.border }
                        contentItem: Text { text: taPrio.currentText; color: theme.text; font.pixelSize: 11; font.family: theme.fontFamily; leftPadding: 12; verticalAlignment: Text.AlignVCenter }
                    }
                    Components.InputField { id: taDue; placeholderText: "Due YYYY-MM-DD"; width: 140; height: 34 }
                }
                Row { x: 14; y: 50; spacing: 8
                    Text { text: "Recurrence:"; color: theme.subtext; font.pixelSize: 10; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                    ComboBox {
                        id: taRecur; model: ["None", "Daily", "Weekly", "Monthly"]; currentIndex: 0
                        width: 110; height: 30
                        background: Rectangle { radius: 8; color: theme.panel; border.width: 1; border.color: theme.border }
                        contentItem: Text { text: taRecur.currentText; color: theme.text; font.pixelSize: 11; font.family: theme.fontFamily; leftPadding: 12; verticalAlignment: Text.AlignVCenter }
                    }
                    Components.ActionButton {
                        label: "\uFF0B  ADD TASK"; btnColor: theme.orange; textColor: theme.bg
                        width: 130; height: 32; fontSize: 10
                        onClicked: {
                            if (!taEntry.text.trim()) return
                            bridge.addTask(taEntry.text.trim(), taPrio.currentText, taDue.text.trim(), taRecur.currentText)
                            taEntry.text = ""; taDue.text = ""
                        }
                    }
                }
            }
        }

        // Sort/Filter controls
        Row {
            x: 24; y: 8; spacing: 4; topPadding: 8; bottomPadding: 8
            Text { text: "SORT:"; color: theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
            Repeater {
                model: ["Priority", "Due Date", "Added"]
                delegate: Components.ActionButton {
                    label: modelData; width: 80; height: 26; fontSize: 9
                    btnColor: sortBy === modelData ? theme.border2 : theme.border
                    textColor: sortBy === modelData ? theme.text : theme.subtext
                    onClicked: { sortBy = modelData; reload() }
                }
            }
            Item { width: 10; height: 1 }
            Text { text: "FILTER:"; color: theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
            Components.ActionButton {
                label: "ALL"; width: 46; height: 26; fontSize: 9
                btnColor: !filterBy ? theme.border2 : theme.border; textColor: !filterBy ? theme.text : theme.subtext
                onClicked: { filterBy = ""; reload() }
            }
            Repeater {
                model: priorityOrder
                delegate: Components.ActionButton {
                    label: modelData.substring(0, 3); width: 46; height: 26; fontSize: 9
                    btnColor: filterBy === modelData ? theme.border2 : theme.border
                    textColor: pColors[modelData] || theme.subtext
                    onClicked: { filterBy = modelData; reload() }
                }
            }
        }

        // Task list
        Repeater {
            model: tasks
            delegate: Loader {
                width: tasksTab.width
                sourceComponent: modelData._separator ? separatorComp : taskCardComp
                property var taskData: modelData
            }
        }
        Text { visible: tasks.length <= 1; x: 24; text: "No tasks yet."; color: theme.dim; font.pixelSize: 12; font.family: theme.fontFamily; topPadding: 30 }
        Item { width: 1; height: 24 }
    }

    Component {
        id: separatorComp
        Column {
            width: parent.width; visible: taskData._doneCount > 0
            Item { width: 1; height: 10 }
            Rectangle { x: 24; width: parent.width - 48; height: 1; color: theme.border }
            Text { x: 24; text: "\u2713  COMPLETED  (" + taskData._doneCount + ")"; color: theme.dim; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; topPadding: 6 }
        }
    }

    Component {
        id: taskCardComp
        Rectangle {
            x: 24; width: parent.width - 48; height: 70; radius: 12
            color: taskData.done ? "#0D0F18" : theme.card
            border.width: 2; border.color: taskMa.containsMouse ? (pColors[taskData.priority] || theme.border) : theme.border
            Behavior on border.color { ColorAnimation { duration: 200 } }
            MouseArea { id: taskMa; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; propagateComposedEvents: true }
            Column { anchors.fill: parent; spacing: 0
                Rectangle { width: parent.width; height: 3; color: taskData.done ? theme.border : (pColors[taskData.priority] || theme.border) }
                Item { height: 8; width: 1 }
                Row { x: 16; width: parent.width - 32; spacing: 8
                    CheckBox {
                        checked: taskData.done || false; width: 20; height: 20
                        anchors.verticalCenter: parent.verticalCenter
                        onToggled: bridge.toggleTask(taskData.id, checked)
                    }
                    Text {
                        text: taskData.text || ""; color: taskData.done ? theme.subtext : theme.text
                        font.pixelSize: 11; font.family: theme.fontFamily; font.strikeout: taskData.done || false
                        anchors.verticalCenter: parent.verticalCenter
                        elide: Text.ElideRight; width: parent.width - 200
                    }
                    Item { width: parent.width - parent.children[0].width - parent.children[1].width - parent.children[3].implicitWidth - parent.children[4].width - 32; height: 1 }
                    Text { text: taskData.priority || ""; color: pColors[taskData.priority] || theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                    Components.DeleteButton { anchors.verticalCenter: parent.verticalCenter; onDeleteConfirmed: bridge.deleteTask(taskData.id) }
                }
                Text {
                    x: 44; visible: !!(taskData.due) && !taskData.done
                    text: "Due " + (taskData.due || ""); color: theme.subtext
                    font.pixelSize: 10; font.family: theme.fontFamily
                }
            }
        }
    }
}
