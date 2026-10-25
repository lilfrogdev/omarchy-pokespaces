import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: root
    property var team: []
    property var catalog: ({ pokemon: [], balls: [] })
    property var assets: ({})
    property var queue: []
    property var current: null
    property string notice: "Loading your party…"
    property string configPath: ""
    property string lastTeam: ""
    readonly property bool busy: current !== null || queue.length > 0
    signal completed(string action, var result)

    function request(job) {
        var pending = queue.slice();
        if (job.action === "preview") {
            pending = pending.filter(function(item) {
                return item.action !== "preview" || (item.pokemon !== undefined) !== (job.pokemon !== undefined);
            });
        }
        if (job.action === "state" && pending.some(function(item) { return item.action === "state"; })) return;
        pending.push(job);
        queue = pending;
        Qt.callLater(pump);
    }

    function pump() {
        if (current !== null || queue.length === 0 || worker.running) return;
        current = queue[0];
        queue = queue.slice(1);
        worker.command = ["python3", decodeURIComponent(Qt.resolvedUrl("scripts/pokespaces.py").toString().slice(7)), JSON.stringify(current)];
        worker.running = true;
    }

    function accept(result) {
        if (result.ok) {
            if (result.team) {
                lastTeam = JSON.stringify(result.team);
                team = result.team;
            }
            if (result.catalog) catalog = result.catalog;
            if (result.assets) assets = Object.assign({}, assets, result.assets);
            if (result.configPath) configPath = result.configPath;
            notice = result.errors && result.errors.length > 0
                ? "Some sprites could not download. Cached sprites and fallback icons remain available."
                : "";
        } else {
            notice = result.error || "Could not load Pokéspaces.";
        }
        completed(current ? current.action : "", result);
    }

    Component.onCompleted: request({ action: "state" })

    FileView {
        id: teamFile
        path: root.configPath
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            try {
                var saved = JSON.parse(text());
                if (JSON.stringify(saved.team) !== root.lastTeam) root.request({ action: "state" });
            } catch (error) {
                root.notice = "Your team file could not be read.";
            }
        }
    }

    Process {
        id: worker
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.accept(JSON.parse(text)); }
                catch (error) { root.notice = "Could not read the asset helper response: " + error; }
            }
        }
        stderr: StdioCollector {}
        onExited: function(code, status) {
            if (code !== 0) root.notice = "The asset helper failed. Python 3 is required.";
            root.current = null;
            Qt.callLater(root.pump);
        }
    }
}
