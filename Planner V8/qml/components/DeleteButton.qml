import QtQuick
import QtQuick.Controls

Rectangle {
    id: delBtn
    width: 28; height: 26; radius: 6
    color: armed ? theme.red : (delMa.containsMouse ? "#2C1216" : "transparent")
    property bool armed: false
    signal deleteConfirmed()

    Behavior on color { ColorAnimation { duration: 150 } }

    Text {
        anchors.centerIn: parent
        text: armed ? "Sure?" : "\u2715"
        color: armed ? theme.bg : theme.red
        font.pixelSize: armed ? 9 : 10; font.bold: true; font.family: theme.fontFamily
    }

    Timer {
        id: resetTimer; interval: 2000
        onTriggered: delBtn.armed = false
    }

    MouseArea {
        id: delMa; anchors.fill: parent; hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            if (!armed) {
                armed = true
                resetTimer.restart()
            } else {
                armed = false
                delBtn.deleteConfirmed()
            }
        }
    }
}
