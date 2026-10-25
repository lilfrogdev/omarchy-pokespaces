import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import qs.Commons
import qs.Commons as Commons
import qs.Ui as Ui
import "Model.js" as Model

Ui.Panel {
    id: root
    moduleName: "lilfrogdev.pokespaces"
    manageIpc: false
    property var anchorItem: null
    property var backend: null
    property var draft: []
    property int selectedIndex: 0
    property string selectionKind: "pokemon"
    property bool dirty: false
    property string message: ""
    readonly property var selected: draft[selectedIndex] || null
    readonly property var availablePokemon: backend ? backend.catalog.pokemon : []
    readonly property var availableBalls: backend ? backend.catalog.balls : []
    readonly property var searchResults: (selectionKind === "pokemon" ? availablePokemon : availableBalls).filter(function(entry) { return Model.matches(entry, search.text); })
    readonly property var selectedEntry: selected ? availablePokemon.find(function(entry) { return entry.id === root.selected.pokemon; }) || null : null
    readonly property var selectedBall: selected ? availableBalls.find(function(entry) { return entry.id === root.selected.ball; }) || null : null

    function resetDraft() {
        draft = backend ? JSON.parse(JSON.stringify(backend.team)) : [];
        dirty = false;
        message = "";
    }

    function open(slotIndex) {
        resetDraft();
        selectedIndex = typeof slotIndex === "number" && slotIndex >= 0 && slotIndex < 6 ? slotIndex : 0;
        selectionKind = "pokemon";
        search.text = "";
        root.controller.show();
        if (backend) backend.request({ action: "state" });
        Qt.callLater(function() { search.forceActiveFocus(); });
    }

    function close() {
        root.controller.hide();
        resetDraft();
    }

    function updateSlot(field, value) {
        if (!selected) return;
        var changed = JSON.parse(JSON.stringify(draft));
        changed[selectedIndex][field] = value;
        draft = changed;
        dirty = true;
        message = "";
        if (field === "ball") backend.request({ action: "preview", ball: value });
        else backend.request({ action: "preview", pokemon: value });
    }

    function chooseResult(index) {
        if (index >= 0 && index < searchResults.length)
            updateSlot(selectionKind === "pokemon" ? "pokemon" : "ball", searchResults[index].id);
    }

    onSelectionKindChanged: {
        search.text = "";
        Qt.callLater(function() { search.forceActiveFocus(); });
    }
    onSearchResultsChanged: results.currentIndex = searchResults.length > 0 ? 0 : -1

    Connections {
        target: root.backend
        function onCompleted(action, result) {
            if (action === "state" && !root.dirty) root.resetDraft();
            if (action === "save" && result.ok) {
                root.resetDraft();
                if (result.errors && result.errors.length > 0) root.message = "Team saved. Some sprites are unavailable.";
                else root.close();
            }
        }
    }

    Ui.KeyboardPanel {
        id: card
        anchorItem: root.anchorItem
        bar: root.bar
        owner: root
        open: root.opened
        focusTarget: search
        contentWidth: fittedContentWidth(Style.space(580), Style.space(640))
        contentHeight: fittedContentHeight(content.implicitHeight)

        Flickable {
            anchors.fill: parent
            contentWidth: width
            contentHeight: content.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Keys.onEscapePressed: root.close()

            ColumnLayout {
                id: content
                width: parent.width
                spacing: Style.spacing.xxl

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.spacing.md
                    Repeater {
                        model: root.draft
                        delegate: Ui.Button {
                            id: teamButton
                            required property int index
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: Style.space(70)
                            selected: root.selectedIndex === index
                            bordered: true
                            focusable: true
                            tooltipText: "Workspace " + (index + 1)
                            Accessible.name: "Edit slot " + (index + 1)
                            onClicked: root.selectedIndex = index
                            PixelSprite {
                                anchors.centerIn: parent
                                width: Style.space(32)
                                height: width
                                asset: root.backend ? root.backend.assets[Model.pokemonKey(teamButton.modelData)] || null : null
                                animate: root.opened && teamButton.selected
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.spacing.md
                    Ui.ButtonGroup {
                        options: [{ value: "pokemon", label: "Pokémon" }, { value: "ball", label: "Poké Balls" }]
                        value: root.selectionKind
                        onChanged: function(value) { root.selectionKind = value; }
                    }
                    Ui.TextField {
                        id: search
                        Layout.fillWidth: true
                        placeholderText: root.selectionKind === "pokemon" ? "Search by name or Pokédex number" : "Search Poké Balls"
                        Accessible.name: root.selectionKind === "pokemon" ? "Search Pokémon" : "Search Poké Balls"
                        Keys.onDownPressed: {
                            results.currentIndex = Math.min(results.count - 1, results.currentIndex + 1);
                            results.positionViewAtIndex(results.currentIndex, ListView.Contain);
                        }
                        Keys.onUpPressed: {
                            results.currentIndex = Math.max(0, results.currentIndex - 1);
                            results.positionViewAtIndex(results.currentIndex, ListView.Contain);
                        }
                        Keys.onReturnPressed: root.chooseResult(results.currentIndex)
                        Keys.onEnterPressed: root.chooseResult(results.currentIndex)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Style.spacing.huge

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.preferredWidth: Style.space(320)
                        spacing: Style.spacing.md

                        ListView {
                            id: results
                            Layout.fillWidth: true
                            Layout.preferredHeight: Style.space(154)
                            model: root.searchResults
                            clip: true
                            boundsBehavior: Flickable.StopAtBounds
                            Controls.ScrollBar.vertical: Controls.ScrollBar {}
                            delegate: Ui.Button {
                                required property var modelData
                                required property int index
                                width: ListView.view.width
                                height: Style.spacing.popupRowHeight
                                text: root.selectionKind === "pokemon" ? "#" + modelData.id + "  " + modelData.name : modelData.name
                                leftAlign: true
                                selected: root.selected !== null && (root.selectionKind === "pokemon" ? root.selected.pokemon : root.selected.ball) === modelData.id
                                hasCursor: search.activeFocus && results.currentIndex === index
                                focusable: true
                                onClicked: root.chooseResult(index)
                            }
                            Text {
                                anchors.centerIn: parent
                                visible: results.count === 0
                                text: "No matches."
                                color: Commons.Color.muted
                                font.family: Style.font.family
                                font.pixelSize: Style.font.body
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.preferredWidth: Style.space(180)
                        Layout.alignment: Qt.AlignTop
                        spacing: Style.spacing.lg
                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Style.space(100)
                            Row {
                                anchors.centerIn: parent
                                spacing: Style.spacing.huge
                                PixelSprite {
                                    width: Style.space(64)
                                    height: width
                                    alignBottom: true
                                    asset: root.backend && root.selected ? root.backend.assets[Model.pokemonKey(root.selected)] || null : null
                                    animate: root.opened
                                }
                                PixelSprite {
                                    anchors.bottom: parent.bottom
                                    width: Style.space(36)
                                    height: width
                                    alignBottom: true
                                    asset: root.backend && root.selected ? root.backend.assets["ball:" + root.selected.ball] || null : null
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: root.selectedEntry ? root.selectedEntry.name : "Loading…"
                            color: Commons.Color.popups.text
                            font.family: Style.font.family
                            font.pixelSize: Style.font.body
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: root.selectedBall ? root.selectedBall.name : ""
                            color: Commons.Color.muted
                            font.family: Style.font.family
                            font.pixelSize: Style.font.body
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: root.message || (root.backend ? root.backend.notice : "")
                    visible: text !== ""
                    wrapMode: Text.WordWrap
                    color: Commons.Color.muted
                    font.family: Style.font.family
                    font.pixelSize: Style.font.body
                }

                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    Ui.Button {
                        text: "Cancel"
                        focusable: true
                        onClicked: root.close()
                    }
                    Ui.Button {
                        text: "Save"
                        bordered: true
                        focusable: true
                        enabled: root.draft.length === 6 && root.dirty && root.backend !== null && !root.backend.busy
                        onClicked: root.backend.request({ action: "save", team: root.draft })
                    }
                }
            }
        }
    }
}
