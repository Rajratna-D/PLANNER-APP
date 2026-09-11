import QtQuick
import QtQuick.Controls
import "../components" as Components

ScrollView {
    id: prodTab; clip: true
    property var prodData: ({})
    property int _v: root.dataVersion
    on_VChanged: reload(); Component.onCompleted: reload(); onVisibleChanged: if (visible) reload()
    function reload() { prodData = JSON.parse(bridge.getProductivityData()) }

    function scoreColor(s) { return s >= 80 ? theme.gold : (s >= 60 ? theme.cyan : (s >= 40 ? theme.orange : (s > 0 ? theme.red : theme.dim))) }
    function scoreGrade(s) { return s >= 80 ? "EXCELLENT" : (s >= 60 ? "GOOD" : (s >= 40 ? "AVERAGE" : (s > 0 ? "NEEDS WORK" : "NO DATA"))) }

    Column {
        width: prodTab.width; spacing: 0

        // Header
        Item { width: parent.width; height: 80
            Column { x: 24; y: 20
                Row { Text { text: "\u25D0 "; color: theme.pink; font.pixelSize: 24 } Text { text: "PRODUCTIVITY"; color: theme.text; font.pixelSize: 24; font.bold: true } }
                Text { text: "Focus analytics \u2014 scores, streaks, heatmap"; color: theme.subtext; font.pixelSize: 11; topPadding: 4 }
            }
            Rectangle { y: 70; x: 24; width: parent.width - 48; height: 2; color: theme.pink }
            Rectangle { y: 73; x: 24; width: parent.width - 48; height: 1; color: theme.border }
        }

        // Goal setter
        Rectangle { x: 24; width: parent.width - 48; height: 50; radius: 12; color: theme.card; border.width: 1; border.color: theme.border
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.pink }
                Row { x: 18; y: 12; spacing: 8
                    Text { text: "\u2699  DAILY SESSION GOAL"; color: theme.subtext; font.pixelSize: 10; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                    Components.InputField { id: goalEntry; width: 60; height: 28; text: "" + (prodData.goal || 6) }
                    Components.ActionButton { label: "SET"; btnColor: theme.pink; textColor: theme.bg; width: 56; height: 28; fontSize: 10
                        onClicked: bridge.setDailyGoal(parseInt(goalEntry.text) || 6) }
                    Text { text: "sessions / day"; color: theme.subtext; font.pixelSize: 10; anchors.verticalCenter: parent.verticalCenter }
                    Item { width: 40; height: 1 }
                    Text { text: "\uD83D\uDD25 " + (prodData.streak || 0) + " day streak"; color: theme.orange; font.pixelSize: 10; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
                }
            }
        }

        // PERFORMANCE SCORES
        Item { width: 1; height: 10 }
        Text { x: 28; text: "  PERFORMANCE SCORES"; color: theme.subtext; font.pixelSize: 9; font.bold: true }
        Item { width: 1; height: 4 }
        Row { x: 24; spacing: 10; width: parent.width - 48
            Repeater {
                model: [
                    { period: "TODAY", score: prodData.score_today || 0, sessions: prodData.sessions_today || 0, sub: prodData.today_str || "" },
                    { period: "YESTERDAY", score: prodData.score_yesterday || 0, sessions: prodData.sessions_yesterday || 0, sub: prodData.yesterday_str || "" },
                    { period: "THIS WEEK", score: prodData.score_week || 0, sessions: prodData.sessions_week || 0, sub: prodData.week_str || "" },
                    { period: "THIS MONTH", score: prodData.score_month || 0, sessions: prodData.sessions_month || 0, sub: prodData.month_str || "" },
                ]
                delegate: Rectangle {
                    width: (prodTab.width - 78) / 4; height: 140; radius: 12; color: theme.card; border.width: 1; border.color: theme.border
                    Column { anchors.fill: parent; spacing: 0
                        Rectangle { width: parent.width; height: 2; color: scoreColor(modelData.score) }
                        Item { height: 10; width: 1 }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.period; color: theme.subtext; font.pixelSize: 9; font.bold: true }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "" + modelData.score; color: scoreColor(modelData.score); font.pixelSize: 34; font.bold: true }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "/ 100"; color: theme.subtext; font.pixelSize: 9 }
                        Rectangle { x: 14; width: parent.width - 28; height: 5; radius: 3; color: theme.border
                            Rectangle { width: parent.width * modelData.score / 100; height: parent.height; radius: 3; color: scoreColor(modelData.score); Behavior on width { NumberAnimation { duration: 600 } } }
                        }
                        Item { height: 2; width: 1 }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: scoreGrade(modelData.score); color: scoreColor(modelData.score); font.pixelSize: 9; font.bold: true }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.sessions + " sessions  \u2022  " + modelData.sub; color: theme.dim; font.pixelSize: 8 }
                    }
                }
            }
        }

        // WEEKLY REPORT CARD
        Item { width: 1; height: 6 }
        Text { x: 28; text: "  WEEKLY REPORT CARD"; color: theme.subtext; font.pixelSize: 9; font.bold: true }
        Item { width: 1; height: 4 }
        Rectangle { x: 24; width: parent.width - 48; radius: 12; color: theme.card; border.width: 1; border.color: theme.border
            height: 200
            Column { anchors.fill: parent; spacing: 0
                Rectangle { width: parent.width; height: 2; color: theme.gold }
                Item { height: 12; width: 1 }
                // Stats grid
                Grid { x: 18; width: parent.width - 36; columns: 3; spacing: 8
                    Repeater {
                        model: {
                            var tw = prodData.this_week || [0,0,0,0,0,0,0]
                            var labels = prodData.day_labels || ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
                            return [
                                { lbl: "BEST DAY", val: prodData.best_day || labels[0], col: theme.gold },
                                { lbl: "GOAL HIT", val: (prodData.goal_hit || 0) + "/7 days", col: theme.cyan },
                                { lbl: "TOTAL SESSIONS", val: "" + (prodData.sessions_week || 0), col: theme.pink },
                                { lbl: "TOTAL FOCUS TIME", val: (prodData.total_focus_min || 0) + " min", col: theme.violet },
                                { lbl: "WEEK SCORE", val: (prodData.score_week || 0) + "/100", col: scoreColor(prodData.score_week || 0) },
                                { lbl: "VS LAST WEEK", val: (prodData.vs_last_week >= 0 ? "+" : "") + (prodData.vs_last_week || 0), col: (prodData.vs_last_week || 0) >= 0 ? theme.gold : theme.red },
                            ]
                        }
                        delegate: Rectangle {
                            width: (parent.width - 16) / 3; height: 56; radius: 8; color: theme.card2
                            Column { anchors.centerIn: parent
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.lbl; color: theme.subtext; font.pixelSize: 8; font.bold: true }
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.val; color: modelData.col; font.pixelSize: 16; font.bold: true }
                            }
                        }
                    }
                }
                Item { height: 10; width: 1 }
                // Per-day bar chart
                Row { x: 18; spacing: 3; width: parent.width - 36
                    Repeater {
                        model: {
                            var tw = prodData.this_week || [0,0,0,0,0,0,0]
                            var labels = prodData.day_labels || ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
                            var goal = prodData.goal || 6
                            var result = []
                            for (var i = 0; i < 7; i++) {
                                result.push({ day: labels[i], cnt: tw[i], hit: tw[i] >= goal })
                            }
                            return result
                        }
                        delegate: Column { width: (parent.width - 18) / 7; spacing: 0
                            Item { width: 1; height: Math.max(0, 50 - Math.min(50, modelData.cnt / Math.max(1, prodData.goal || 6) * 50)) }
                            Rectangle { anchors.horizontalCenter: parent.horizontalCenter; width: 22; height: Math.max(6, Math.min(50, modelData.cnt / Math.max(1, prodData.goal || 6) * 50)); radius: 4; color: modelData.hit ? theme.gold : (modelData.cnt > 0 ? theme.cyan : theme.border) }
                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.day; color: modelData.hit ? theme.text : theme.subtext; font.pixelSize: 8 }
                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: "" + modelData.cnt; color: modelData.hit ? theme.gold : (modelData.cnt > 0 ? theme.cyan : theme.border); font.pixelSize: 8; font.bold: true }
                        }
                    }
                }
            }
        }

        // SPIDER CHART (FOCUS BALANCE)
        Item { width: 1; height: 6 }
        Text { x: 28; text: "  FOCUS BALANCE (SPIDER CHART)"; color: theme.subtext; font.pixelSize: 9; font.bold: true }
        Item { width: 1; height: 4 }
        Rectangle { x: 24; width: parent.width - 48; height: 220; radius: 12; color: theme.card; border.width: 1; border.color: theme.border
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.pink }
                Components.SpiderChart {
                    width: parent.width; height: 200
                    thisWeek: prodData.this_week || [0,0,0,0,0,0,0]
                    lastWeek: prodData.last_week || [0,0,0,0,0,0,0]
                    dailyGoal: prodData.goal || 6
                }
            }
        }

        // PEAK FOCUS HOURS
        Item { width: 1; height: 6 }
        Text { x: 28; text: "  PEAK FOCUS HOURS"; color: theme.subtext; font.pixelSize: 9; font.bold: true }
        Item { width: 1; height: 4 }
        Rectangle { x: 24; width: parent.width - 48; height: 180; radius: 12; color: theme.card; border.width: 1; border.color: theme.border
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.cyan }
                Canvas {
                    id: hourChart; width: parent.width; height: 160; y: 10
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        var counts = prodData.hour_counts || []
                        var labels = prodData.hour_labels || []
                        if (counts.length === 0) return
                        var maxC = Math.max.apply(null, counts.concat([1]))
                        var barW = (width - 60) / counts.length
                        var chartH = height - 30
                        for (var i = 0; i < counts.length; i++) {
                            var x = 30 + i * barW
                            var h = (counts[i] / maxC) * chartH
                            var r = counts[i] / maxC
                            ctx.fillStyle = r >= 0.75 ? theme.pink : (r >= 0.5 ? theme.violet : (r >= 0.25 ? theme.blue : theme.border2))
                            ctx.fillRect(x + 2, chartH - h + 5, barW - 4, h)
                            if (counts[i] > 0) {
                                ctx.fillStyle = theme.text
                                ctx.font = "7px " + theme.fontFamily
                                ctx.fillText("" + counts[i], x + barW/2 - 4, chartH - h)
                            }
                            ctx.fillStyle = theme.subtext
                            ctx.font = "7px " + theme.fontFamily
                            ctx.fillText("" + labels[i], x + barW/2 - 4, chartH + 18)
                        }
                    }
                }
            }
        }

        // CONTRIBUTION HEATMAP
        Item { width: 1; height: 6 }
        Text { x: 28; text: "  CONTRIBUTION HEATMAP"; color: theme.subtext; font.pixelSize: 9; font.bold: true }
        Item { width: 1; height: 4 }
        Rectangle { x: 24; width: parent.width - 48; height: 200; radius: 12; color: theme.card; border.width: 1; border.color: theme.border
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.gold }
                Components.GitHubHeatmap { width: parent.width - 20; height: 180; x: 10 }
            }
        }

        // 30-DAY SCORE HISTORY
        Item { width: 1; height: 6 }
        Text { x: 28; text: "  30-DAY SCORE HISTORY"; color: theme.subtext; font.pixelSize: 9; font.bold: true }
        Item { width: 1; height: 4 }
        Rectangle { x: 24; width: parent.width - 48; height: 180; radius: 12; color: theme.card; border.width: 1; border.color: theme.border
            Column { anchors.fill: parent
                Rectangle { width: parent.width; height: 2; color: theme.cyan }
                Canvas {
                    id: lineChart; width: parent.width; height: 160; y: 10
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        var scores = prodData.scores_30 || []
                        if (scores.length === 0) return
                        var chartW = width - 60; var chartH = height - 30
                        var stepX = chartW / 29

                        // Zone fills
                        var zones = [
                            { y1: 0, y2: 40, col: "rgba(239,68,68,0.04)" },
                            { y1: 40, y2: 60, col: "rgba(245,158,11,0.05)" },
                            { y1: 60, y2: 80, col: "rgba(6,182,212,0.05)" },
                            { y1: 80, y2: 100, col: "rgba(234,179,8,0.06)" },
                        ]
                        for (var z = 0; z < zones.length; z++) {
                            ctx.fillStyle = zones[z].col
                            var zy1 = chartH - (zones[z].y2 / 100) * chartH + 5
                            var zy2 = chartH - (zones[z].y1 / 100) * chartH + 5
                            ctx.fillRect(30, zy1, chartW, zy2 - zy1)
                        }

                        // Line
                        ctx.strokeStyle = theme.cyan; ctx.lineWidth = 2
                        ctx.beginPath()
                        for (var i = 0; i < scores.length; i++) {
                            var x = 30 + i * stepX
                            var y = chartH - (scores[i] / 100) * chartH + 5
                            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
                        }
                        ctx.stroke()

                        // Fill under
                        ctx.globalAlpha = 0.12; ctx.fillStyle = theme.cyan
                        ctx.lineTo(30 + 29 * stepX, chartH + 5); ctx.lineTo(30, chartH + 5); ctx.fill()
                        ctx.globalAlpha = 1

                        // Dots
                        for (var j = 0; j < scores.length; j++) {
                            var dx = 30 + j * stepX
                            var dy = chartH - (scores[j] / 100) * chartH + 5
                            ctx.fillStyle = scoreColor(scores[j])
                            ctx.beginPath(); ctx.arc(dx, dy, 3, 0, 2 * Math.PI); ctx.fill()
                        }

                        // Y axis labels
                        ctx.fillStyle = theme.subtext; ctx.font = "7px " + theme.fontFamily
                        for (var yl of [0, 40, 60, 80, 100]) {
                            var yy = chartH - (yl / 100) * chartH + 5
                            ctx.fillText("" + yl, 6, yy + 3)
                        }

                        // X axis labels (every 5th)
                        var dates = prodData.dates_30 || []
                        for (var xi = 0; xi < 30; xi += 5) {
                            var xx = 30 + xi * stepX
                            ctx.fillText(dates[xi] ? dates[xi].substring(5) : "", xx - 8, chartH + 20)
                        }
                    }
                }
            }
        }

        Item { width: 1; height: 24 }
    }
}
