import QtQuick
import QtQuick.Controls

TextField {
    id: field
    placeholderText: ""
    color: theme.text
    font.pixelSize: 11; font.family: theme.fontFamily
    background: Rectangle {
        radius: 8
        color: theme.panel
        border.width: field.activeFocus ? 2 : 1
        border.color: field.activeFocus ? theme.cyan : theme.border
        Behavior on border.color { ColorAnimation { duration: 200 } }
    }
    placeholderTextColor: theme.dim
    selectByMouse: true
    leftPadding: 12; rightPadding: 12
}
