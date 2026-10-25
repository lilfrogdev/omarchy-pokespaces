import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import qs.Commons
import qs.Ui
import "Model.js" as Model

BarWidget {
    id: root
    moduleName: "lilfrogdev.pokespaces"
    readonly property var hostScreen: root.QsWindow.window ? root.QsWindow.window.screen : null
    readonly property var monitor: hostScreen ? Hyprland.monitorFor(hostScreen) : null
    readonly property int activeId: monitor && monitor.activeWorkspace ? monitor.activeWorkspace.id : -1
    readonly property var ids: Model.workspaceIds(Hyprland.workspaces.values)
    readonly property real slotSize: Math.max(root.barSize, Style.space(30))
    readonly property bool opened: picker.opened

    function workspaceById(id) {
        var values = Hyprland.workspaces.values;
        for (var i = 0; i < values.length; i++) {
            if (values[i].id === id) return values[i];
        }
        return null;
    }

    function pokemonName(slot) {
        if (!slot) return "Loading";
        for (var i = 0; i < assetsBackend.catalog.pokemon.length; i++) {
            if (assetsBackend.catalog.pokemon[i].id === slot.pokemon) return assetsBackend.catalog.pokemon[i].name;
        }
        return "Pokémon " + slot.pokemon;
    }

    function focusWorkspace(id) {
        if (root.bar && root.ids.indexOf(id) >= 0)
            root.bar.run("hyprctl dispatch " + Util.shellQuote('hl.dsp.focus({ workspace = "' + id + '" })'));
    }

    function open() { picker.open(); }
    function close() { picker.close(); }

    implicitWidth: grid.implicitWidth
    implicitHeight: grid.implicitHeight

    Backend { id: assetsBackend }

    TeamPicker {
        id: picker
        bar: root.bar
        anchorItem: root
        backend: assetsBackend
    }

    GridLayout {
        id: grid
        anchors.fill: parent
        columns: root.vertical ? 1 : root.ids.length
        columnSpacing: 0
        rowSpacing: 0

        Repeater {
            model: root.ids
            WidgetButton {
                id: button
                required property int modelData
                readonly property var workspace: root.workspaceById(modelData)
                readonly property bool occupied: workspace !== null && workspace.toplevels.values.length > 0
                readonly property string displayState: Model.state(modelData, occupied, root.activeId)
                readonly property var slot: modelData <= 6 ? assetsBackend.team[modelData - 1] || null : null
                readonly property var pokemonAsset: slot ? assetsBackend.assets[Model.pokemonKey(slot)] || null : null
                readonly property var ballAsset: slot ? assetsBackend.assets["ball:" + slot.ball] || null : null

                bar: root.bar
                hasVisualContent: true
                labelVisible: displayState === "number"
                text: String(modelData)
                fixedWidth: root.vertical ? root.barSize : root.slotSize
                fixedHeight: root.vertical ? root.slotSize : root.barSize
                tooltipText: "Workspace " + modelData + (slot ? " · " + root.pokemonName(slot) : "") + "\nRight-click to edit your party"
                Accessible.role: Accessible.Button
                Accessible.name: tooltipText
                Accessible.onPressAction: root.focusWorkspace(modelData)
                onPressed: function(mouseButton) {
                    if (mouseButton === Qt.RightButton) picker.open(modelData <= 6 ? modelData - 1 : 0);
                    else if (mouseButton === Qt.LeftButton) root.focusWorkspace(modelData);
                }

                PixelSprite {
                    id: pokemonSprite
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: Math.max(2, (parent.height - 16) / 2)
                    alignBottom: true
                    width: Math.min(32, root.barSize)
                    height: width
                    asset: button.pokemonAsset
                    visible: button.displayState === "pokemon"
                    animate: visible
                }

                PixelSprite {
                    id: ballSprite
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: Math.max(2, (parent.height - 16) / 2)
                    alignBottom: true
                    width: Math.min(24, root.barSize - 2)
                    height: width
                    asset: button.ballAsset
                    visible: button.displayState === "ball" || (button.displayState === "pokemon" && !pokemonSprite.ready)
                }

                Rectangle {
                    anchors.centerIn: parent
                    width: Style.space(4)
                    height: width
                    radius: width / 2
                    color: "white"
                    visible: button.displayState === "empty" || (button.displayState !== "number" && !(pokemonSprite.visible && pokemonSprite.ready) && !ballSprite.ready)
                }
            }
        }
    }
}
