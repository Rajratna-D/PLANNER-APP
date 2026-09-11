import QtQuick
import QtQuick.Controls

Item {
    id: spiderChart
    property var thisWeek: [0,0,0,0,0,0,0]
    property var lastWeek: [0,0,0,0,0,0,0]
    property int dailyGoal: 6
    property var dayLabels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    // We expect this to be bound to data from the backend
    function refresh() {
        canvas.requestPaint()
    }

    onThisWeekChanged: refresh()
    onLastWeekChanged: refresh()
    onDailyGoalChanged: refresh()

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            var cx = width / 2
            var cy = height / 2 + 6
            var radius = Math.min(width, height) / 2 - 20
            var maxVal = Math.max(dailyGoal, 1)
            for (var i = 0; i < 7; i++) {
                if (thisWeek[i] > maxVal) maxVal = thisWeek[i]
                if (lastWeek[i] > maxVal) maxVal = lastWeek[i]
            }

            // Draw concentric background heptagons
            ctx.lineWidth = 1
            ctx.strokeStyle = theme.border
            for (var level = 1; level <= 4; level++) {
                var r = radius * (level / 4)
                ctx.beginPath()
                for (var j = 0; j < 7; j++) {
                    var angle = j * (2 * Math.PI / 7) - Math.PI / 2
                    var x = cx + r * Math.cos(angle)
                    var y = cy + r * Math.sin(angle)
                    if (j === 0) ctx.moveTo(x, y)
                    else ctx.lineTo(x, y)
                }
                ctx.closePath()
                ctx.stroke()
            }

            // Draw axes and labels
            ctx.fillStyle = theme.subtext
            ctx.font = "9px " + theme.fontFamily
            ctx.textAlign = "center"
            ctx.textBaseline = "middle"
            for (var k = 0; k < 7; k++) {
                var angleAxis = k * (2 * Math.PI / 7) - Math.PI / 2
                var endX = cx + radius * Math.cos(angleAxis)
                var endY = cy + radius * Math.sin(angleAxis)
                
                // Axis line
                ctx.beginPath()
                ctx.moveTo(cx, cy)
                ctx.lineTo(endX, endY)
                ctx.stroke()
                
                // Label
                var lblX = cx + (radius + 12) * Math.cos(angleAxis)
                var lblY = cy + (radius + 12) * Math.sin(angleAxis)
                ctx.fillText(dayLabels[k], lblX, lblY)
            }

            // Draw last week (dashed/faded)
            ctx.beginPath()
            for (var m = 0; m < 7; m++) {
                var angleLw = m * (2 * Math.PI / 7) - Math.PI / 2
                var radLw = radius * (lastWeek[m] / maxVal)
                var lwX = cx + radLw * Math.cos(angleLw)
                var lwY = cy + radLw * Math.sin(angleLw)
                if (m === 0) ctx.moveTo(lwX, lwY)
                else ctx.lineTo(lwX, lwY)
            }
            ctx.closePath()
            ctx.setLineDash([4, 4])
            ctx.strokeStyle = theme.subtext
            ctx.lineWidth = 1.5
            ctx.stroke()
            ctx.fillStyle = "rgba(148, 163, 184, 0.1)"
            ctx.fill()
            ctx.setLineDash([]) // reset

            // Draw this week (solid accent color)
            ctx.beginPath()
            for (var n = 0; n < 7; n++) {
                var angleTw = n * (2 * Math.PI / 7) - Math.PI / 2
                var radTw = radius * (thisWeek[n] / maxVal)
                var twX = cx + radTw * Math.cos(angleTw)
                var twY = cy + radTw * Math.sin(angleTw)
                if (n === 0) ctx.moveTo(twX, twY)
                else ctx.lineTo(twX, twY)
            }
            ctx.closePath()
            ctx.strokeStyle = theme.pink
            ctx.lineWidth = 2
            ctx.stroke()
            ctx.fillStyle = Qt.rgba(theme.pink.r, theme.pink.g, theme.pink.b, 0.25)
            ctx.fill()

            // Draw points for this week
            ctx.fillStyle = theme.pink
            for (var p = 0; p < 7; p++) {
                var anglePt = p * (2 * Math.PI / 7) - Math.PI / 2
                var radPt = radius * (thisWeek[p] / maxVal)
                var ptX = cx + radPt * Math.cos(anglePt)
                var ptY = cy + radPt * Math.sin(anglePt)
                ctx.beginPath()
                ctx.arc(ptX, ptY, 3, 0, 2 * Math.PI)
                ctx.fill()
            }
        }
    }

    // Legend
    Row {
        x: 8; y: 4; spacing: 12
        Row { spacing: 4
            Rectangle { width: 10; height: 10; radius: 5; color: theme.pink; anchors.verticalCenter: parent.verticalCenter }
            Text { text: "This week"; color: theme.text; font.pixelSize: 9; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
        }
        Row { spacing: 4
            Rectangle { width: 10; height: 10; radius: 5; color: "transparent"; border.width: 1; border.color: theme.subtext; anchors.verticalCenter: parent.verticalCenter }
            Text { text: "Last week"; color: theme.subtext; font.pixelSize: 9; font.family: theme.fontFamily; anchors.verticalCenter: parent.verticalCenter }
        }
    }
}
