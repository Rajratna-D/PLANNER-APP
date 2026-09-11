import QtQuick

Item {
    id: toastRoot
    anchors.fill: parent

    property string message: ""
    property color accentColor: "#06B6D4"
    property string icon: "\u2713"
    property bool showing: false

    function show(msg, color, icn) {
        message = msg
        accentColor = color || "#06B6D4"
        icon = icn || "\u2713"
        showing = true
        hideTimer.restart()
    }

    Timer {
        id: hideTimer; interval: 2800
        onTriggered: showing = false
    }

    Rectangle {
        id: toastCard
        width: 300; height: 56
        anchors.right: parent.right; anchors.rightMargin: 20
        anchors.bottom: parent.bottom; anchors.bottomMargin: showing ? 20 : -70
        radius: 10
        color: theme.card
        border.width: 1; border.color: toastRoot.accentColor
        opacity: showing ? 1 : 0
        visible: opacity > 0

        Behavior on anchors.bottomMargin { NumberAnimation { duration: 300; easing.type: Easing.OutBack } }
        Behavior on opacity { NumberAnimation { duration: 200 } }

        // Accent bar left
        Rectangle {
            width: 4; height: parent.height; radius: 2
            color: toastRoot.accentColor
            anchors.left: parent.left; anchors.leftMargin: 0
        }

        Row {
            anchors.fill: parent; anchors.leftMargin: 14; spacing: 8
            anchors.verticalCenter: parent.verticalCenter

            Text {
                text: toastRoot.icon; color: toastRoot.accentColor
                font.pixelSize: 16; font.bold: true; font.family: theme.fontFamily
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: toastRoot.message; color: theme.text
                font.pixelSize: 11; font.family: theme.fontFamily
                anchors.verticalCenter: parent.verticalCenter
                width: 240; wrapMode: Text.WordWrap
            }
        }

        MouseArea {
            anchors.fill: parent
            onClicked: showing = false
        }
    }
}
