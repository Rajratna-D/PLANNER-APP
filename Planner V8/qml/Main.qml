import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import "components"
import "tabs"

ApplicationWindow {
    id: root
    width: 1280
    height: 780
    minimumWidth: 1024
    minimumHeight: 640
    title: "COMMAND PLANNER"
    visible: true
    color: theme.bg

    // ── Theme object ──────────────────────────────────────────────────
    QtObject {
        id: theme
        property bool isDark: bridge.currentTheme === "dark"

        property color bg:      isDark ? "#0B0E14" : "#F4F6F9"
        property color panel:   isDark ? "#131722" : "#EAEFF4"
        property color card:    isDark ? "#1A1F2C" : "#FFFFFF"
        property color card2:   isDark ? "#212836" : "#F8FAFC"
        property color hover:   isDark ? "#2A3345" : "#E2E8F0"
        property color border:  isDark ? "#273142" : "#CBD5E1"
        property color border2: isDark ? "#3B4A66" : "#94A3B8"

        property color text:    isDark ? "#F8FAFC" : "#0F172A"
        property color subtext: isDark ? "#94A3B8" : "#64748B"
        property color dim:     isDark ? "#475569" : "#94A3B8"

        property color cyan:    isDark ? "#06B6D4" : "#0891B2"
        property color blue:    isDark ? "#3B82F6" : "#2563EB"
        property color green:   isDark ? "#10B981" : "#059669"
        property color orange:  isDark ? "#F59E0B" : "#D97706"
        property color red:     isDark ? "#EF4444" : "#DC2626"
        property color gold:    isDark ? "#EAB308" : "#CA8A04"
        property color violet:  isDark ? "#8B5CF6" : "#7C3AED"
        property color pink:    isDark ? "#EC4899" : "#DB2777"

        property string fontFamily: "Segoe UI"
    }

    font.family: theme.fontFamily

    // ── State ─────────────────────────────────────────────────────────
    property int currentTabIndex: 0
    property bool sidebarExpanded: true
    property int dataVersion: 0  // bumped on dataChanged to refresh tabs

    Connections {
        target: bridge
        function onDataChanged() { root.dataVersion++ }
        function onThemeChanged() { /* theme bindings auto-update */ }
        function onToastRequested(message, color, icon) {
            toastPopup.show(message, color, icon)
        }
    }

    // ── Top Bar ───────────────────────────────────────────────────────
    Rectangle {
        id: topBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 56
        color: theme.panel
        z: 10

        // Cyan accent line
        Rectangle {
            width: 4; height: parent.height
            color: theme.cyan
            anchors.left: parent.left
        }

        // Sidebar toggle
        Rectangle {
            id: collapseBtn
            width: 40; height: parent.height
            anchors.left: parent.left; anchors.leftMargin: 4
            color: collapseMa.containsMouse ? theme.hover : "transparent"
            Text {
                anchors.centerIn: parent
                text: sidebarExpanded ? "\u25C0" : "\u25B6"
                color: theme.subtext; font.pixelSize: 14
            }
            MouseArea {
                id: collapseMa; anchors.fill: parent; hoverEnabled: true
                onClicked: sidebarExpanded = !sidebarExpanded
            }
        }

        // Title
        Row {
            anchors.left: collapseBtn.right; anchors.leftMargin: 16
            anchors.verticalCenter: parent.verticalCenter; spacing: 0
            Text { text: "COMMAND"; color: theme.text; font.pixelSize: 20; font.bold: true; font.family: theme.fontFamily }
            Text { text: " PLANNER"; color: theme.cyan; font.pixelSize: 20; font.bold: true; font.family: theme.fontFamily }
            Text { text: "  v3  //  PRINCEBLUE"; color: theme.subtext; font.pixelSize: 9; font.family: theme.fontFamily; anchors.bottom: parent.bottom; anchors.bottomMargin: 2 }
        }

        // Right buttons
        Row {
            anchors.right: parent.right; anchors.rightMargin: 16
            anchors.verticalCenter: parent.verticalCenter; spacing: 8

            Text {
                id: clockLabel
                color: theme.subtext; font.pixelSize: 10; font.family: theme.fontFamily
                anchors.verticalCenter: parent.verticalCenter
                Timer {
                    interval: 1000; running: true; repeat: true
                    onTriggered: clockLabel.text = new Date().toLocaleString(Qt.locale(), "ddd dd MMM yyyy  •  HH:mm:ss")
                }
                Component.onCompleted: text = new Date().toLocaleString(Qt.locale(), "ddd dd MMM yyyy  •  HH:mm:ss")
            }

            // Save button
            Rectangle {
                width: 90; height: 28; radius: 6; color: theme.border2
                border.width: 1; border.color: theme.border
                Text { anchors.centerIn: parent; text: "\uD83D\uDCBE SAVE"; color: theme.green; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: bridge.manualSave()
                }
            }
            // Backup button
            Rectangle {
                width: 100; height: 28; radius: 6; color: theme.border2
                border.width: 1; border.color: theme.border
                Text { anchors.centerIn: parent; text: "\uD83D\uDCE6 BACKUP"; color: theme.cyan; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var name = bridge.doBackup()
                        toastPopup.show("Backup saved: " + name, theme.cyan, "\uD83D\uDCE6")
                    }
                }
            }
            // Theme toggle
            Rectangle {
                width: 90; height: 28; radius: 6; color: theme.border2
                border.width: 1; border.color: theme.border
                Text {
                    anchors.centerIn: parent
                    text: theme.isDark ? "\u2600 LIGHT" : "\u263E DARK"
                    color: theme.gold; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily
                }
                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: bridge.toggleTheme()
                }
            }
        }

        // Bottom border
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: theme.border }
    }

    // ── Body ──────────────────────────────────────────────────────────
    Item {
        anchors.top: topBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        // Sidebar
        Rectangle {
            id: sidebar
            width: sidebarExpanded ? 200 : 56
            height: parent.height
            color: theme.panel
            z: 5
            clip: true

            Behavior on width { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

            // Sidebar separator
            Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: theme.border }

            Column {
                anchors.fill: parent; anchors.topMargin: 16

                // Navigation label
                Text {
                    text: "  NAVIGATION"; color: theme.subtext
                    font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily
                    leftPadding: 16; bottomPadding: 8
                    visible: sidebarExpanded; opacity: sidebarExpanded ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                }

                // Tab buttons
                Repeater {
                    model: ListModel {
                        ListElement { icon: "\u2B21"; name: "OVERVIEW";     idx: 0; clr: "#06B6D4" }
                        ListElement { icon: "\u25C8"; name: "TESTS";        idx: 1; clr: "#EAB308" }
                        ListElement { icon: "\u25A3"; name: "TASKS";        idx: 2; clr: "#F59E0B" }
                        ListElement { icon: "\u25EB"; name: "LISTS";        idx: 3; clr: "#3B82F6" }
                        ListElement { icon: "\u25E7"; name: "ASSIGNMENTS";  idx: 4; clr: "#EF4444" }
                        ListElement { icon: "\u25E9"; name: "PRACTICALS";   idx: 5; clr: "#10B981" }
                        ListElement { icon: "\u2B22"; name: "SYLLABUS";     idx: 6; clr: "#8B5CF6" }
                        ListElement { icon: "\u25CE"; name: "POMODORO";     idx: 7; clr: "#EC4899" }
                        ListElement { icon: "\u270E"; name: "NOTES";        idx: 8; clr: "#06B6D4" }
                        ListElement { icon: "\u25D0"; name: "PRODUCTIVITY"; idx: 9; clr: "#EC4899" }
                    }

                    delegate: Item {
                        width: sidebar.width; height: 44

                        property bool isActive: currentTabIndex === model.idx
                        property bool isHovered: tabMa.containsMouse

                        // Active indicator bar
                        Rectangle {
                            width: 4; height: 28; radius: 2
                            anchors.left: parent.left; anchors.leftMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            color: isActive ? model.clr : "transparent"
                            Behavior on color { ColorAnimation { duration: 200 } }
                        }

                        // Background
                        Rectangle {
                            anchors.left: parent.left; anchors.leftMargin: 20
                            anchors.right: parent.right; anchors.rightMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            height: 36; radius: 8
                            color: isActive ? theme.hover : (isHovered ? Qt.rgba(theme.hover.r, theme.hover.g, theme.hover.b, 0.5) : "transparent")
                            Behavior on color { ColorAnimation { duration: 150 } }

                            Row {
                                anchors.fill: parent; anchors.leftMargin: 12; spacing: 8
                                anchors.verticalCenter: parent.verticalCenter

                                Text {
                                    text: model.icon; color: model.clr
                                    font.pixelSize: 14; font.family: theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: model.name
                                    color: isActive ? theme.text : theme.subtext
                                    font.pixelSize: 11; font.family: theme.fontFamily
                                    anchors.verticalCenter: parent.verticalCenter
                                    visible: sidebarExpanded
                                    Behavior on color { ColorAnimation { duration: 150 } }
                                }
                            }
                        }

                        MouseArea {
                            id: tabMa; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: currentTabIndex = model.idx
                        }
                    }
                }

                // Divider
                Item { width: parent.width; height: 28
                    Rectangle { anchors.centerIn: parent; width: parent.width - 28; height: 1; color: theme.border }
                }

                // Backup label
                Text {
                    text: "  BACKUPS"; color: theme.subtext
                    font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily
                    leftPadding: 16; visible: sidebarExpanded
                }
                Text {
                    id: backupLbl; color: theme.dim
                    font.pixelSize: 9; font.family: theme.fontFamily
                    leftPadding: 16; topPadding: 2; visible: sidebarExpanded
                    text: bridge.getBackupLabel()
                }
            }
        }

        // Content area
        StackLayout {
            id: contentStack
            anchors.left: sidebar.right
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            currentIndex: currentTabIndex

            OverviewTab {}
            TestsTab {}
            TasksTab {}
            ListsTab {}
            AssignmentsTab {}
            PracticalsTab {}
            SyllabusTab {}
            PomodoroTab {}
            NotesTab {}
            ProductivityTab {}
        }
    }

    // ── Toast notification ────────────────────────────────────────────
    ToastPopup { id: toastPopup; z: 100 }
}
