import QtQuick

Item {
    id: root
    property var asset: null
    property bool animate: false
    property bool alignBottom: false
    readonly property var bounds: asset && asset.bounds ? asset.bounds : [0, 0, picture.implicitWidth, picture.implicitHeight]
    readonly property var canvas: asset && asset.canvas ? asset.canvas : [picture.implicitWidth, picture.implicitHeight]
    readonly property real pixelScale: Math.min(width / Math.max(1, canvas[0]), height / Math.max(1, canvas[1]))
    property int frame: 0
    readonly property bool ready: asset !== null && asset.frames && asset.frames.length > 0 && picture.status === Image.Ready
    onAssetChanged: frame = 0
    onAnimateChanged: if (!animate) frame = 0

    Image {
        id: picture
        width: root.alignBottom ? root.canvas[0] * root.pixelScale : root.width
        height: root.alignBottom ? root.canvas[1] * root.pixelScale : root.height
        x: root.alignBottom ? (root.width - root.bounds[2] * root.pixelScale) / 2 - root.bounds[0] * root.pixelScale : 0
        y: root.alignBottom ? root.height - (root.bounds[1] + root.bounds[3]) * root.pixelScale : 0
        source: root.asset && root.asset.frames ? root.asset.frames[root.frame] || "" : ""
        fillMode: Image.PreserveAspectFit
        smooth: false
        cache: true
    }

    Timer {
        running: root.animate && root.visible && root.asset !== null && root.asset.frames && root.asset.frames.length > 1
        repeat: true
        interval: root.asset && root.asset.delays ? root.asset.delays[root.frame] || 170 : 170
        onTriggered: root.frame = (root.frame + 1) % root.asset.frames.length
    }
}
