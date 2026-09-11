import QtQuick
import QtQuick.Controls

Rectangle {
    id: btn
    property string label: ""
    property color btnColor: theme.border2
    property color textColor: theme.text
    property color hoverColor: theme.hover
    property int fontSize: 11
    signal clicked()

    width: 120; height: 32; radius: 8
    color: ma.containsMouse ? hoverColor : btnColor
    border.width: 1; border.color: theme.border

    Behavior on color { ColorAnimation { duration: 120 } }

    Text {
        anchors.centerIn: parent; text: btn.label
        color: btn.textColor
        font.pixelSize: btn.fontSize; font.bold: true; font.family: theme.fontFamily
    }

    MouseArea {
        id: ma; anchors.fill: parent; hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: btn.clicked()
    }
}
