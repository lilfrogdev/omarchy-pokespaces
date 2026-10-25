import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ID = "lilfrogdev.pokespaces"
CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
SHELL_CONFIG = CONFIG_HOME / "omarchy/shell.json"
DESTINATION = CONFIG_HOME / "omarchy/plugins" / PLUGIN_ID


def copy_changed(source, destination):
    source = Path(source)
    destination = Path(destination)
    if not destination.exists() or source.read_bytes() != destination.read_bytes():
        shutil.copy2(source, destination)
    return str(destination)


def main():
    parser = argparse.ArgumentParser(description="Install Pokéspaces locally or restore the stock workspace widget.")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    source_config = SHELL_CONFIG if SHELL_CONFIG.exists() else Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "config/omarchy/shell.json"
    config = json.loads(source_config.read_text())
    layout = config["bar"]["layout"]
    replacing = PLUGIN_ID if args.restore else "omarchy.workspaces"
    replacement = "omarchy.workspaces" if args.restore else PLUGIN_ID
    target = None
    for wanted in (replacing, replacement):
        for section in ("left", "center", "right"):
            for index, item in enumerate(layout.get(section, [])):
                if item.get("id") == wanted and target is None:
                    target = (section, index)
    if target is None:
        raise SystemExit("No stock workspace widget found to replace. Add Pokéspaces with omarchy plugin enable " + PLUGIN_ID)
    for section in ("left", "center", "right"):
        items = []
        for index, item in enumerate(layout.get(section, [])):
            if item.get("id") not in (replacing, replacement):
                items.append(item)
            elif (section, index) == target:
                items.append(item if item.get("id") == replacement else {"id": replacement})
        layout[section] = items
    if not args.restore:
        subprocess.run(["omarchy", "plugin", "validate", str(ROOT)], check=True)
        launcher = Path.home() / ".local/bin/pokespaces"
        target = DESTINATION / "scripts/pokespaces.py"
        if (launcher.exists() or launcher.is_symlink()) and not (launcher.is_symlink() and launcher.resolve() == target.resolve()):
            raise SystemExit("Cannot install CLI: " + str(launcher) + " already exists.")
        if ROOT != DESTINATION.resolve():
            shutil.copytree(ROOT, DESTINATION, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "docs", "__pycache__", "*.pyc"), copy_function=copy_changed)
        launcher.parent.mkdir(parents=True, exist_ok=True)
        if not launcher.is_symlink():
            launcher.symlink_to(target)
        subprocess.run(["omarchy-shell", "shell", "rescanPlugins"], check=True)
    SHELL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if SHELL_CONFIG.exists():
        backup = SHELL_CONFIG.with_name("shell.json.before-pokespaces-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        shutil.copy2(SHELL_CONFIG, backup)
        print("Backed up shell settings to", backup)
    descriptor, temporary = tempfile.mkstemp(dir=SHELL_CONFIG.parent, prefix=".pokespaces-")
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(config, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.replace(temporary, SHELL_CONFIG)
    finally:
        Path(temporary).unlink(missing_ok=True)
    subprocess.run(["omarchy-shell", "shell", "reloadConfig"], check=True)
    print("Restored workspace numbers." if args.restore else "Installed Pokéspaces. Right-click a slot to edit your party.")


if __name__ == "__main__":
    main()
