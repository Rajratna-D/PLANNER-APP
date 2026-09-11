import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as Components

ScrollView {
    id: overviewTab
    clip: true
    ScrollBar.vertical.policy: ScrollBar.AsNeeded

    property var ovData: ({})
    property int _v: root.dataVersion

    on_VChanged: reload()
    Component.onCompleted: reload()
    onVisibleChanged: if (visible) reload()

    function reload() {
        ovData = JSON.parse(bridge.getOverviewData())
    }

    Column {
        width: overviewTab.width
        spacing: 0

        // ── Greeting + Streak ────────────────────────────────────────
        Item { width: 1; height: 20 }
        Row {
            x: 24; spacing: 0; width: parent.width - 48
            Text {
                text: (ovData.greeting || "HELLO") + ", PRINCEBLUE"
                color: theme.cyan; font.pixelSize: 22; font.bold: true; font.family: theme.fontFamily
            }
            Item { Layout.fillWidth: true; width: 20 }
            Rectangle {
                visible: (ovData.streak || 0) > 0
                anchors.verticalCenter: parent.verticalCenter
                width: streakText.implicitWidth + 24; height: 30; radius: 8
                color: "#2C1E0A"
                Text {
                    id: streakText; anchors.centerIn: parent
                    text: "\uD83D\uDD25 " + (ovData.streak || 0) + " day streak"
                    color: theme.orange; font.pixelSize: 11; font.bold: true; font.family: theme.fontFamily
                }
            }
        }
        Text {
            x: 26; text: "  " + (ovData.dateStr || "")
            color: theme.subtext; font.pixelSize: 11; font.family: theme.fontFamily
        }
        Item { width: 1; height: 8 }
        Text {
            x: 26; text: "  " + (ovData.motivational || "Make it count.")
            color: theme.dim; font.pixelSize: 10; font.family: theme.fontFamily; font.italic: true
        }

        // Divider
        Item { width: 1; height: 12 }
        Rectangle { x: 24; width: parent.width - 48; height: 1; color: theme.border }
        Item { width: 1; height: 12 }

        // ── Stat Cards ───────────────────────────────────────────────
        Row {
            x: 24; spacing: 10; width: parent.width - 48

            Repeater {
                model: ListModel {
                    ListElement { key: "tests_up";  label: "TESTS DUE";   clr: "#EAB308" }
                    ListElement { key: "tasks_p";   label: "TASKS LEFT";  clr: "#F59E0B" }
                    ListElement { key: "asgn_p";    label: "ASSIGNMENTS"; clr: "#EF4444" }
                    ListElement { key: "prac_p";    label: "PRACTICALS";  clr: "#10B981" }
                    ListElement { key: "subj_c";    label: "SUBJECTS";    clr: "#8B5CF6" }
                    ListElement { key: "pomo_today"; label: "POMODOROS\nTODAY"; clr: "#EC4899" }
                }
                delegate: Rectangle {
                    width: (overviewTab.width - 48 - 50) / 6
                    height: 90; radius: 10; color: theme.card
                    Column {
                        anchors.fill: parent; spacing: 0
                        Rectangle { width: parent.width; height: 2; color: model.clr }
                        Item { width: 1; height: 8 }
                        Text {
                            x: 14; text: ovData.stats ? (ovData.stats[model.key] || 0) : "0"
                            color: model.clr; font.pixelSize: 28; font.bold: true; font.family: theme.fontFamily
                        }
                        Text {
                            x: 14; text: model.label
                            color: theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily
                        }
                    }
                }
            }
        }

        Item { width: 1; height: 16 }

        // ── Two-column layout ────────────────────────────────────────
        Row {
            x: 20; spacing: 16; width: parent.width - 40

            // LEFT COLUMN
            Column {
                width: (parent.width - 16) / 2; spacing: 0

                // UPCOMING TESTS
                SectionHeader { title: "\u25C8  UPCOMING TESTS"; accentColor: theme.gold }
                Repeater {
                    model: ovData.upcoming_tests || []
                    delegate: Rectangle {
                        width: parent.width - 40; height: 70; radius: 10; color: theme.card
                        x: 20; border.width: 1; border.color: theme.border
                        Column {
                            anchors.fill: parent; spacing: 0
                            Rectangle { width: parent.width; height: 3; color: modelData._urgency_color || theme.border }
                            Item { height: 8; width: 1 }
                            Row {
                                x: 14; width: parent.width - 28
                                Text { text: modelData.subject || ""; color: theme.text; font.pixelSize: 12; font.bold: true; font.family: theme.fontFamily }
                                Item { width: parent.width - parent.children[0].implicitWidth - parent.children[2].implicitWidth; height: 1 }
                                Text { text: modelData._urgency_lbl || ""; color: modelData._urgency_color || theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                            }
                            Text { x: 14; text: (modelData.date || "") + "  " + (modelData.time || ""); color: theme.subtext; font.pixelSize: 10; font.family: theme.fontFamily }
                        }
                    }
                }
                Text { visible: !(ovData.upcoming_tests && ovData.upcoming_tests.length > 0); x: 24; text: "  No upcoming tests"; color: theme.dim; font.pixelSize: 11; font.family: theme.fontFamily; topPadding: 6 }

                Item { width: 1; height: 8 }

                // TOP TASKS
                SectionHeader { title: "\u25A3  TOP TASKS"; accentColor: theme.orange }
                Repeater {
                    model: ovData.top_tasks || []
                    delegate: Rectangle {
                        width: parent.width - 40; height: 60; radius: 10; color: theme.card
                        x: 20; border.width: 1; border.color: theme.border
                        Column {
                            anchors.fill: parent; spacing: 0
                            Rectangle { width: parent.width; height: 3; color: modelData._priority_color || theme.border }
                            Item { height: 8; width: 1 }
                            Row {
                                x: 14; width: parent.width - 28
                                Text { text: modelData.text || ""; color: theme.text; font.pixelSize: 11; font.family: theme.fontFamily; elide: Text.ElideRight; width: parent.width - 80 }
                                Item { width: parent.width - parent.children[0].width - parent.children[2].implicitWidth; height: 1 }
                                Text { text: modelData.priority || ""; color: modelData._priority_color || theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                            }
                        }
                    }
                }
                Text { visible: !(ovData.top_tasks && ovData.top_tasks.length > 0); x: 24; text: "  No pending tasks"; color: theme.dim; font.pixelSize: 11; font.family: theme.fontFamily; topPadding: 6 }

                Item { width: 1; height: 8 }

                // SYLLABUS PROGRESS
                SectionHeader { title: "\u2B22  SYLLABUS PROGRESS"; accentColor: theme.violet }
                Repeater {
                    model: ovData.syllabus_items || []
                    delegate: Rectangle {
                        width: parent.width - 40; height: 72; radius: 10; color: theme.card
                        x: 20; border.width: 1; border.color: theme.border
                        Column {
                            anchors.fill: parent; spacing: 0
                            Rectangle { width: parent.width; height: 3; color: modelData.color || theme.violet }
                            Item { height: 8; width: 1 }
                            Row {
                                x: 14; width: parent.width - 28
                                Text { text: modelData.name || ""; color: modelData.color || theme.text; font.pixelSize: 11; font.bold: true; font.family: theme.fontFamily }
                                Item { width: parent.width - parent.children[0].implicitWidth - parent.children[2].implicitWidth; height: 1 }
                                Text { text: (modelData.pct || 0) + "%"; color: theme.violet; font.pixelSize: 11; font.bold: true; font.family: theme.fontFamily }
                            }
                            Item { height: 6; width: 1 }
                            Rectangle {
                                x: 14; width: parent.parent.width - 28; height: 6; radius: 3; color: theme.border
                                Rectangle {
                                    width: parent.width * (modelData.pct || 0) / 100; height: parent.height; radius: 3
                                    color: modelData.color || theme.violet
                                    Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
                                }
                            }
                        }
                    }
                }
                Text { visible: !(ovData.syllabus_items && ovData.syllabus_items.length > 0); x: 24; text: "  No subjects added"; color: theme.dim; font.pixelSize: 11; font.family: theme.fontFamily; topPadding: 6 }
            }

            // RIGHT COLUMN
            Column {
                width: (parent.width - 16) / 2; spacing: 0

                // ASSIGNMENTS DUE
                SectionHeader { title: "\u25E7  ASSIGNMENTS DUE"; accentColor: theme.red }
                Repeater {
                    model: ovData.pending_asgns || []
                    delegate: Rectangle {
                        width: parent.width - 40; height: 60; radius: 10; color: theme.card
                        x: 20; border.width: 1; border.color: theme.border
                        Column {
                            anchors.fill: parent; spacing: 0
                            Rectangle { width: parent.width; height: 3; color: modelData._urgency_color || theme.border }
                            Item { height: 8; width: 1 }
                            Row {
                                x: 14; width: parent.width - 28
                                Text { text: "[" + (modelData.subject || "") + "] " + (modelData.title || ""); color: theme.text; font.pixelSize: 11; font.family: theme.fontFamily; elide: Text.ElideRight; width: parent.width - 60 }
                                Item { width: parent.width - parent.children[0].width - parent.children[2].implicitWidth; height: 1 }
                                Text { text: modelData._urgency_lbl || ""; color: modelData._urgency_color || theme.subtext; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                            }
                        }
                    }
                }
                Text { visible: !(ovData.pending_asgns && ovData.pending_asgns.length > 0); x: 24; text: "  No pending assignments"; color: theme.dim; font.pixelSize: 11; font.family: theme.fontFamily; topPadding: 6 }

                Item { width: 1; height: 8 }

                // PRACTICALS
                SectionHeader { title: "\u25E9  PRACTICALS"; accentColor: theme.green }
                Repeater {
                    model: ovData.pending_pracs || []
                    delegate: Rectangle {
                        width: parent.width - 40; height: 60; radius: 10; color: theme.card
                        x: 20; border.width: 1; border.color: theme.border
                        Column {
                            anchors.fill: parent; spacing: 0
                            Rectangle { width: parent.width; height: 3; color: theme.green }
                            Item { height: 8; width: 1 }
                            Row {
                                x: 14; width: parent.width - 28
                                Text {
                                    text: "Exp " + (modelData.num || "?") + " \u2014 " + (modelData.title || "")
                                    color: theme.text; font.pixelSize: 11; font.family: theme.fontFamily
                                    elide: Text.ElideRight; width: parent.width - 80
                                }
                                Item { width: parent.width - parent.children[0].width - parent.children[2].implicitWidth; height: 1 }
                                Row { spacing: 4
                                    Text { text: "P"; color: modelData.performed ? theme.green : theme.dim; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                                    Text { text: "W"; color: modelData.writeup ? theme.green : theme.dim; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                                    Text { text: "S"; color: modelData.submitted ? theme.green : theme.dim; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily }
                                }
                            }
                        }
                    }
                }
                Text { visible: !(ovData.pending_pracs && ovData.pending_pracs.length > 0); x: 24; text: "  No pending practicals"; color: theme.dim; font.pixelSize: 11; font.family: theme.fontFamily; topPadding: 6 }

                Item { width: 1; height: 8 }

                // GITHUB HEATMAP
                SectionHeader { title: "\u25C8  CONTRIBUTION HEATMAP"; accentColor: theme.gold }
                Rectangle {
                    x: 20; width: parent.width - 40; height: 180; radius: 10; color: theme.card
                    border.width: 1; border.color: theme.border
                    Column {
                        anchors.fill: parent; spacing: 0
                        Rectangle { width: parent.width; height: 2; color: theme.gold }
                        Components.GitHubHeatmap {
                            width: parent.width - 20; height: 160
                            x: 10
                        }
                    }
                }

                Item { width: 1; height: 16 }

                // ── Spider Chart ─────────────────────────────────────────────
                SectionHeader { title: "\u25CE  FOCUS BALANCE (SPIDER CHART)"; accentColor: theme.pink }
                Rectangle {
                    width: parent.width - 40; height: 220; radius: 10; color: theme.card
                    x: 20; border.width: 1; border.color: theme.border
                    Column {
                        anchors.fill: parent; spacing: 0
                        Rectangle { width: parent.width; height: 2; color: theme.pink }
                        Components.SpiderChart {
                            width: parent.width; height: 200
                            thisWeek: ovData.this_week || [0,0,0,0,0,0,0]
                            lastWeek: ovData.last_week || [0,0,0,0,0,0,0]
                            dailyGoal: ovData.daily_goal || 6
                        }
                    }
                }
            } // end of RIGHT COLUMN
        } // end of Row



        // ── Pending Today / Tomorrow ─────────────────────────────────
        Rectangle { x: 24; width: parent.width - 48; height: 1; color: theme.border }
        Item { width: 1; height: 12 }

        Row {
            x: 20; spacing: 16; width: parent.width - 40

            // Due Today & Overdue
            Rectangle {
                width: (parent.width - 16) / 2; height: pendTodayCol.implicitHeight + 16
                radius: 10; color: theme.card
                Column {
                    id: pendTodayCol; anchors.fill: parent; spacing: 0
                    Rectangle { width: parent.width; height: 2; color: theme.red }
                    Item { height: 8; width: 1 }
                    Row {
                        x: 14; width: parent.width - 28
                        Text { text: "\uD83D\uDD34  DUE TODAY & OVERDUE"; color: theme.red; font.pixelSize: 11; font.bold: true; font.family: theme.fontFamily }
                        Item { width: parent.width - parent.children[0].implicitWidth - parent.children[2].implicitWidth; height: 1 }
                        Text { text: "" + ((ovData.today_due || []).length + (ovData.overdue || []).length); color: theme.red; font.pixelSize: 11; font.bold: true; font.family: theme.fontFamily }
                    }
                    Item { height: 4; width: 1 }
                    Repeater {
                        model: (ovData.today_due || []).concat(ovData.overdue || []).slice(0, 8)
                        delegate: Row {
                            x: 14; width: parent.width - 28; height: 22; spacing: 6
                            Text { text: modelData.type || ""; color: modelData.color || theme.red; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                            Text { text: modelData.name || ""; color: theme.text; font.pixelSize: 10; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter; elide: Text.ElideRight; width: parent.width - 140 }
                            Item { width: parent.width - parent.children[0].implicitWidth - parent.children[1].width - parent.children[3].implicitWidth - 12; height: 1 }
                            Text { text: modelData.label || ""; color: modelData.color || theme.red; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                        }
                    }
                    Text {
                        visible: (ovData.today_due || []).length + (ovData.overdue || []).length === 0
                        x: 14; text: "  Nothing due today \u2014 great!"; color: theme.green
                        font.pixelSize: 10; font.family: theme.fontFamily; topPadding: 4
                    }
                    Item { height: 8; width: 1 }
                }
            }

            // Due Tomorrow
            Rectangle {
                width: (parent.width - 16) / 2; height: pendTmrwCol.implicitHeight + 16
                radius: 10; color: theme.card
                Column {
                    id: pendTmrwCol; anchors.fill: parent; spacing: 0
                    Rectangle { width: parent.width; height: 2; color: theme.orange }
                    Item { height: 8; width: 1 }
                    Row {
                        x: 14; width: parent.width - 28
                        Text { text: "\uD83D\uDFE1  DUE TOMORROW"; color: theme.orange; font.pixelSize: 11; font.bold: true; font.family: theme.fontFamily }
                        Item { width: parent.width - parent.children[0].implicitWidth - parent.children[2].implicitWidth; height: 1 }
                        Text { text: "" + (ovData.tomorrow_due || []).length; color: theme.orange; font.pixelSize: 11; font.bold: true; font.family: theme.fontFamily }
                    }
                    Item { height: 4; width: 1 }
                    Repeater {
                        model: (ovData.tomorrow_due || []).slice(0, 8)
                        delegate: Row {
                            x: 14; width: parent.width - 28; height: 22; spacing: 6
                            Text { text: modelData.type || ""; color: modelData.color || theme.orange; font.pixelSize: 9; font.bold: true; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                            Text { text: modelData.name || ""; color: theme.text; font.pixelSize: 10; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
                        }
                    }
                    Text {
                        visible: (ovData.tomorrow_due || []).length === 0
                        x: 14; text: "  Nothing due tomorrow."; color: theme.subtext
                        font.pixelSize: 10; font.family: theme.fontFamily; topPadding: 4
                    }
                    Item { height: 8; width: 1 }
                }
            }
        }

        Item { width: 1; height: 24 }
    }

    // Section header helper component
    component SectionHeader: Item {
        property string title: ""
        property color accentColor: theme.cyan
        width: parent.width; height: 40
        Column {
            anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20
            Item { width: 1; height: 16 }
            Text { text: title; color: accentColor; font.pixelSize: 12; font.bold: true; font.family: theme.fontFamily }
            Item { width: 1; height: 4 }
            Rectangle { width: parent.width; height: 1; color: theme.border }
        }
    }
}
