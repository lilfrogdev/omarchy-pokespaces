function workspaceIds(workspaces) {
    var ids = [1, 2, 3, 4, 5, 6];
    for (var i = 0; i < workspaces.length; i++) {
        var id = workspaces[i].id;
        if (id > 6 && ids.indexOf(id) === -1) ids.push(id);
    }
    return ids.sort(function(a, b) { return a - b; });
}

function state(id, occupied, activeId) {
    if (id > 6) return "number";
    if (!occupied) return "empty";
    return id === activeId ? "pokemon" : "ball";
}

function pokemonKey(slot) {
    return slot ? "pokemon:" + slot.pokemon : "";
}

function matches(entry, query) {
    var text = query.toLowerCase().trim().replace(/^#/, "");
    return !text || String(entry.id).indexOf(text) === 0 || entry.name.toLowerCase().indexOf(text) >= 0;
}
