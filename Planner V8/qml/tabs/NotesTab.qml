import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as Components

Item {
    id: notesTab
    property var notes: []
    property string selectedNoteId: ""
    property int _v: root.dataVersion
    on_VChanged: reloadList()
    Component.onCompleted: reloadList()
    onVisibleChanged: if (visible) reloadList()
    function reloadList() { notes = JSON.parse(bridge.getNotes()) }

    // Header
    Item { id: header; width: parent.width; height: 80
        Column { x: 24; y: 20
            Row { Text { text: "\u270E "; color: theme.cyan; font.pixelSize: 24 } Text { text: "NOTES"; color: theme.text; font.pixelSize: 24; font.bold: true } }
            Text { text: "Quick notes, ideas, and references"; color: theme.subtext; font.pixelSize: 11; topPadding: 4 }
        }
        Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.cyan }
        Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
    }

    // New note button
    Row { id: newNoteRow; anchors.top: header.bottom; x: 24; spacing: 10; topPadding: 4; bottomPadding: 10
        Components.ActionButton { label: "\uFF0B  NEW NOTE"; btnColor: theme.cyan; textColor: theme.bg; width: 130; height: 34; fontSize: 10
            onClicked: { selectedNoteId = bridge.newNote(); reloadList(); loadNote(selectedNoteId) } }
    }

    // Two-panel layout
    Row {
        anchors.top: newNoteRow.bottom; anchors.topMargin: 4; x: 24; spacing: 10
        width: parent.width - 48; height: parent.height - header.height - newNoteRow.height - 24

        // Left: note list
        Rectangle {
            width: parent.width * 0.28; height: parent.height; radius: 10; color: theme.card
            border.width: 1; border.color: theme.border
            Column { anchors.fill: parent; spacing: 0
                Rectangle { width: parent.width; height: 2; color: theme.cyan }
                Text { x: 12; text: "  ALL NOTES"; color: theme.subtext; font.pixelSize: 10; font.bold: true; topPadding: 8; bottomPadding: 4 }
                ScrollView { width: parent.width; height: parent.height - 30; clip: true
                    Column { width: parent.width; spacing: 2
                        Repeater {
                            model: notes
                            delegate: Rectangle {
                                width: parent.width - 8; height: 72; radius: 6; x: 4
                                color: selectedNoteId === modelData.id ? theme.hover : (nlMa.containsMouse ? Qt.rgba(theme.hover.r, theme.hover.g, theme.hover.b, 0.5) : "transparent")
                                Behavior on color { ColorAnimation { duration: 120 } }
                                MouseArea { id: nlMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: { selectedNoteId = modelData.id; loadNote(modelData.id) } }
                                Column { anchors.fill: parent; anchors.leftMargin: 8; anchors.topMargin: 6; spacing: 1
                                    Text { text: modelData.title || "Untitled"; color: selectedNoteId === modelData.id ? theme.cyan : theme.text; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight; width: parent.width - 16 }
                                    Text { text: "\u25CF " + (modelData.subject || "General"); color: theme.subtext; font.pixelSize: 9; font.bold: true }
                                    Text { text: (modelData.updated || "").substring(0, 10); color: theme.subtext; font.pixelSize: 9 }
                                    Text { text: (modelData.body || "").substring(0, 50).replace(/\n/g, " "); color: theme.dim; font.pixelSize: 9; elide: Text.ElideRight; width: parent.width - 16 }
                                }
                            }
                        }
                        Text { visible: notes.length === 0; x: 8; text: "No notes yet."; color: theme.dim; font.pixelSize: 10; topPadding: 20 }
                    }
                }
            }
        }

        // Right: editor
        Rectangle {
            width: parent.width * 0.72 - 10; height: parent.height; radius: 10; color: theme.card
            border.width: 1; border.color: theme.border
            Column { anchors.fill: parent; spacing: 0
                Rectangle { width: parent.width; height: 2; color: theme.cyan }
                Row { x: 14; y: 10; spacing: 8
                    Components.InputField { id: noteTitleEntry; placeholderText: "Note title\u2026"; width: 300; height: 34 }
                    Components.InputField { id: noteSubjectEntry; placeholderText: "Subject"; width: 160; height: 34 }
                    Components.ActionButton { label: "\uD83D\uDCBE SAVE NOTE"; btnColor: theme.cyan; textColor: theme.bg; width: 120; height: 34
                        onClicked: {
                            if (!selectedNoteId) { selectedNoteId = bridge.newNote() }
                            bridge.saveNote(selectedNoteId, noteTitleEntry.text, noteSubjectEntry.text, noteBody.text)
                            reloadList()
                        }
                    }
                    Components.DeleteButton { width: 80; height: 34; onDeleteConfirmed: {
                        if (selectedNoteId) { bridge.deleteNote(selectedNoteId); selectedNoteId = ""; noteBody.text = ""; noteTitleEntry.text = ""; reloadList() }
                    } }
                }
                Text { id: noteTs; x: 16; topPadding: 4; color: theme.subtext; font.pixelSize: 9 }
                ScrollView {
                    x: 14; width: parent.width - 28; height: parent.height - 80; clip: true; topPadding: 6
                    TextArea {
                        id: noteBody; width: parent.width; wrapMode: TextEdit.Wrap
                        color: theme.text; font.pixelSize: 12; font.family: theme.fontFamily
                        placeholderText: "Select a note or click + NEW NOTE..."
                        placeholderTextColor: theme.dim
                        background: Rectangle { radius: 8; color: theme.card2; border.width: 1; border.color: theme.border2 }
                        selectByMouse: true
                    }
                }
            }
        }
    }

    function loadNote(nid) {
        for (var i = 0; i < notes.length; i++) {
            if (notes[i].id === nid) {
                noteTitleEntry.text = notes[i].title || ""
                noteSubjectEntry.text = notes[i].subject || "General"
                noteBody.text = notes[i].body || ""
                noteTs.text = "  Last edited: " + (notes[i].updated || "")
                return
            }
        }
    }
}
