import QtQuick
import QtQuick.Controls

Rectangle {
    id: card
    property color accentColor: theme.border
    property alias body: bodyContent

    color: theme.card
    radius: 12
    border.width: 2
    border.color: hovered ? accentColor : theme.border

    property bool hovered: cardMa.containsMouse

    Behavior on border.color { ColorAnimation { duration: 200 } }

    MouseArea {
        id: cardMa; anchors.fill: parent; hoverEnabled: true
        propagateComposedEvents: true; acceptedButtons: Qt.NoButton
    }

    Column {
        anchors.fill: parent; spacing: 0

        // Accent bar
        Rectangle {
            width: parent.width; height: 3; color: card.accentColor
            radius: 0
            Rectangle {
                anchors.top: parent.top; width: parent.width; height: 1.5
                color: card.accentColor
            }
        }

        // Body content
        Item {
            id: bodyContent
            width: parent.width
            height: card.height - 3
        }
    }
}
