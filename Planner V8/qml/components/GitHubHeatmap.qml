import QtQuick
import QtQuick.Controls

Item {
    id: heatmap
    property var heatmapData: []
    property int cellSize: 14
    property int cellSpacing: 3
    implicitHeight: (cellSize + cellSpacing) * 7 + 60

    // GitHub green palette
    readonly property var levelColors: [
        theme.isDark ? "#161B22" : "#ebedf0",   // 0 — no activity
        theme.isDark ? "#0e4429" : "#9be9a8",   // 1 — low
        theme.isDark ? "#006d32" : "#40c463",   // 2 — medium
        theme.isDark ? "#26a641" : "#30a14e",   // 3 — high
        theme.isDark ? "#39d353" : "#216e39",   // 4 — max
    ]

    function refresh() {
        var raw = bridge.getHeatmapData()
        heatmapData = JSON.parse(raw)
        canvas.requestPaint()
    }

    Component.onCompleted: refresh()

    // Re-render when data changes
    Connections {
        target: bridge
        function onDataChanged() { heatmap.refresh() }
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            if (heatmapData.length === 0) return

            var cs = cellSize
            var sp = cellSpacing
            var leftPad = 36   // space for day labels
            var topPad = 24    // space for month labels

            // Day-of-week labels (Mon, Wed, Fri)
            ctx.fillStyle = Qt.binding(function() { return theme.subtext })
            ctx.font = "9px " + theme.fontFamily
            var dayLabels = ["", "Mon", "", "Wed", "", "Fri", ""]
            for (var d = 0; d < 7; d++) {
                if (dayLabels[d]) {
                    ctx.fillText(dayLabels[d], 0, topPad + d * (cs + sp) + cs - 2)
                }
            }

            // Group data by week
            var weeks = []
            var currentWeek = []
            for (var i = 0; i < heatmapData.length; i++) {
                var item = heatmapData[i]
                var wd = item.weekday
                // Sunday = 6 in Python, but GitHub starts weeks on Sunday
                // Our data has weekday 0=Mon..6=Sun
                // We map: Mon=0→row0, Tue=1→row1, ..., Sun=6→row6
                currentWeek.push(item)
                if (wd === 6 || i === heatmapData.length - 1) {
                    weeks.push(currentWeek)
                    currentWeek = []
                }
            }

            // Month labels
            ctx.fillStyle = Qt.binding(function() { return theme.subtext })
            ctx.font = "9px " + theme.fontFamily
            var lastMonth = -1
            var monthNames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            for (var w = 0; w < weeks.length; w++) {
                if (weeks[w].length > 0) {
                    var dateStr = weeks[w][0].date
                    var month = parseInt(dateStr.substring(5, 7)) - 1
                    if (month !== lastMonth) {
                        lastMonth = month
                        var x = leftPad + w * (cs + sp)
                        ctx.fillText(monthNames[month], x, topPad - 8)
                    }
                }
            }

            // Draw cells
            for (var wi = 0; wi < weeks.length; wi++) {
                for (var di = 0; di < weeks[wi].length; di++) {
                    var cell = weeks[wi][di]
                    var cx = leftPad + wi * (cs + sp)
                    var cy = topPad + cell.weekday * (cs + sp)
                    var level = Math.min(4, Math.max(0, cell.level))
                    ctx.fillStyle = levelColors[level]
                    ctx.beginPath()
                    roundRect(ctx, cx, cy, cs, cs, 2)
                    ctx.fill()
                }
            }

            // Legend — "Less ... More"
            var legendY = topPad + 7 * (cs + sp) + 10
            var legendX = width - 160
            ctx.fillStyle = Qt.binding(function() { return theme.subtext })
            ctx.font = "9px " + theme.fontFamily
            ctx.fillText("Less", legendX, legendY + cs - 2)
            legendX += 30
            for (var li = 0; li < 5; li++) {
                ctx.fillStyle = levelColors[li]
                ctx.beginPath()
                roundRect(ctx, legendX + li * (cs + sp), legendY, cs, cs, 2)
                ctx.fill()
            }
            ctx.fillStyle = Qt.binding(function() { return theme.subtext })
            ctx.fillText("More", legendX + 5 * (cs + sp) + 4, legendY + cs - 2)
        }

        function roundRect(ctx, x, y, w, h, r) {
            ctx.moveTo(x + r, y)
            ctx.lineTo(x + w - r, y)
            ctx.arcTo(x + w, y, x + w, y + r, r)
            ctx.lineTo(x + w, y + h - r)
            ctx.arcTo(x + w, y + h, x + w - r, y + h, r)
            ctx.lineTo(x + r, y + h)
            ctx.arcTo(x, y + h, x, y + h - r, r)
            ctx.lineTo(x, y + r)
            ctx.arcTo(x, y, x + r, y, r)
            ctx.closePath()
        }
    }

    // Tooltip on hover
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        property string tooltipText: ""

        onPositionChanged: function(mouse) {
            var leftPad = 36
            var topPad = 24
            var cs = cellSize
            var sp = cellSpacing

            // Determine which week column
            var col = Math.floor((mouse.x - leftPad) / (cs + sp))
            var row = Math.floor((mouse.y - topPad) / (cs + sp))

            if (row >= 0 && row < 7 && col >= 0) {
                // Find the cell
                var weeks = []
                var currentWeek = []
                for (var i = 0; i < heatmapData.length; i++) {
                    currentWeek.push(heatmapData[i])
                    if (heatmapData[i].weekday === 6 || i === heatmapData.length - 1) {
                        weeks.push(currentWeek)
                        currentWeek = []
                    }
                }
                if (col < weeks.length) {
                    for (var j = 0; j < weeks[col].length; j++) {
                        if (weeks[col][j].weekday === row) {
                            var cell = weeks[col][j]
                            tooltip.text = cell.count + " sessions on " + cell.date
                            tooltip.x = mouse.x + 10
                            tooltip.y = mouse.y - 30
                            tooltip.visible = true
                            return
                        }
                    }
                }
            }
            tooltip.visible = false
        }
        onExited: tooltip.visible = false
    }

    Rectangle {
        id: tooltip
        visible: false
        width: tooltipText.implicitWidth + 16
        height: 24; radius: 4
        color: theme.card2; border.width: 1; border.color: theme.border

        property alias text: tooltipText.text

        Text {
            id: tooltipText; anchors.centerIn: parent
            color: theme.text; font.pixelSize: 10; font.family: theme.fontFamily
        }
    }
}
