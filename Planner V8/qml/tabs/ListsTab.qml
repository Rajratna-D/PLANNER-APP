import QtQuick
import QtQuick.Controls
import "../components" as Components

ScrollView {
    id: listsTab; clip: true
    property var lists: []
    property int _v: root.dataVersion
    on_VChanged: reload()
    Component.onCompleted: reload()
    onVisibleChanged: if (visible) reload()
    function reload() { lists = JSON.parse(bridge.getLists()) }

    Column {
        width: listsTab.width; spacing: 0
        Item { width: parent.width; height: 80
            Column { x: 24; y: 20
                Row { Text { text: "\u25EB "; color: theme.blue; font.pixelSize: 24 } Text { text: "LISTS"; color: theme.text; font.pixelSize: 24; font.bold: true } }
                Text { text: "Running master lists of work to do"; color: theme.subtext; font.pixelSize: 11; topPadding: 4 }
            }
            Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.blue }
            Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }
        Row { x: 24; spacing: 10; topPadding: 4; bottomPadding: 10
            Components.InputField { id: liName; placeholderText: "New list name"; width: 260; height: 34 }
            Components.ActionButton { label: "\uFF0B  CREATE LIST"; btnColor: theme.blue; textColor: theme.bg; width: 150; height: 34; fontSize: 10
                onClicked: { if (!liName.text.trim()) return; bridge.addList(liName.text.trim()); liName.text = "" } }
        }
        Repeater {
            model: lists
            delegate: Rectangle {
                x: 24; width: listsTab.width - 48; radius: 10; color: theme.card
                height: listCol.implicitHeight + 16
                border.width: 1; border.color: theme.border
                Column { id: listCol; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; spacing: 0
                    Rectangle { width: parent.width; height: 2; color: theme.blue }
                    Item { height: 8; width: 1 }
                    Row { x: 16; width: parent.width - 32
                        Text { text: modelData.name || ""; color: theme.blue; font.pixelSize: 14; font.bold: true }
                        Item { width: 10; height: 1 }
                        Text { text: modelData.items ? modelData.items.filter(function(i){return i.done}).length + "/" + modelData.items.length : "0/0"; color: theme.subtext; font.pixelSize: 10; anchors.verticalCenter: parent.verticalCenter }
                        Item { width: parent.width - parent.children[0].implicitWidth - parent.children[1].width - parent.children[2].implicitWidth - parent.children[4].width - 10; height: 1 }
                        Components.DeleteButton { anchors.verticalCenter: parent.verticalCenter; onDeleteConfirmed: bridge.deleteList(modelData.id) }
                    }
                    // Progress bar
                    Rectangle {
                        x: 16; width: parent.width - 32; height: 4; radius: 2; color: theme.border; visible: modelData.items && modelData.items.length > 0
                        Rectangle { width: parent.width * (modelData.items ? modelData.items.filter(function(i){return i.done}).length / Math.max(1, modelData.items.length) : 0); height: parent.height; radius: 2; color: theme.blue; Behavior on width { NumberAnimation { duration: 400 } } }
                    }
                    Item { height: 6; width: 1 }
                    // Items
                    Repeater {
                        model: modelData.items || []
                        delegate: Row { x: 16; width: parent.width - 32; height: 28; spacing: 4
                            CheckBox { checked: modelData.done || false; width: 18; height: 18; anchors.verticalCenter: parent.verticalCenter
                                onToggled: bridge.toggleListItem(lists[index] ? lists[index].id : "", modelData.id, checked) }
                            Text { text: modelData.text || ""; color: modelData.done ? theme.subtext : theme.text; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                            Item { width: parent.width - parent.children[0].width - parent.children[1].implicitWidth - parent.children[3].width - 12; height: 1 }
                            Components.DeleteButton { width: 24; height: 22; anchors.verticalCenter: parent.verticalCenter
                                onDeleteConfirmed: bridge.deleteListItem(lists[index] ? lists[index].id : "", modelData.id) }
                        }
                    }
                    // Add item
                    Row { x: 16; spacing: 8; topPadding: 8; bottomPadding: 8
                        Components.InputField { id: liItemEntry; placeholderText: "Add item\u2026"; width: 300; height: 34
                            property string listId: modelData.id }
                        Components.ActionButton { label: "\uFF0B"; btnColor: theme.blue; textColor: theme.bg; width: 40; height: 34
                            onClicked: { if (!liItemEntry.text.trim()) return; bridge.addListItem(liItemEntry.listId, liItemEntry.text.trim()); liItemEntry.text = "" } }
                    }
                }
            }
        }
        Text { visible: lists.length === 0; x: 24; text: "No lists created yet."; color: theme.dim; font.pixelSize: 12; topPadding: 30 }
        Item { width: 1; height: 24 }
    }
}
