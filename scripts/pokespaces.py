#!/usr/bin/env python3
import argparse
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
import zlib


ROOT = Path(__file__).resolve().parent.parent
CATALOG = json.loads((ROOT / "data/catalog.json").read_text())
POKEMON = {entry["id"]: entry for entry in CATALOG["pokemon"]}
BALLS = {entry["id"]: entry for entry in CATALOG["balls"]}
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "omarchy-pokespaces"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "omarchy-pokespaces" / CATALOG["revision"]
DEFAULT_TEAM = [
    {"pokemon": 94, "ball": "master-ball"},
    {"pokemon": 149, "ball": "dusk-ball"},
    {"pokemon": 551, "ball": "great-ball"},
    {"pokemon": 197, "ball": "net-ball"},
    {"pokemon": 25, "ball": "quick-ball"},
    {"pokemon": 133, "ball": "luxury-ball"},
]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".pokespaces-")
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def validate_team(value):
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError("A team must have exactly six slots.")
    result = []
    for slot in value:
        if not isinstance(slot, dict):
            raise ValueError("Invalid team slot.")
        pokemon = slot.get("pokemon")
        ball = slot.get("ball")
        if type(pokemon) is not int or pokemon not in POKEMON:
            raise ValueError("Choose a Pokémon from the available Gen V icons.")
        if ball not in BALLS:
            raise ValueError("Choose a ball from the available ball list.")
        result.append({"pokemon": pokemon, "ball": ball})
    return result


def read_team():
    path = CONFIG / "team.json"
    try:
        return validate_team(json.loads(path.read_text())["team"])
    except FileNotFoundError:
        return validate_team(DEFAULT_TEAM)
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("Cannot read your saved team: " + str(error)) from error


def save_team(team=None, slot=None, pokemon=None, ball=None):
    CONFIG.mkdir(parents=True, exist_ok=True)
    with (CONFIG / ".team.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if team is None:
            team = read_team()
        if slot is not None:
            if pokemon is not None:
                team[slot - 1]["pokemon"] = pokemon
            if ball is not None:
                team[slot - 1]["ball"] = ball
        team = validate_team(team)
        atomic_write(CONFIG / "team.json", (json.dumps({"version": 1, "team": team}, indent=2) + "\n").encode())
    return team


def frame_geometry(files):
    left, top, right, bottom = 256, 256, 0, 0
    for name in files:
        chunks = list(png_chunks(Path(name).read_bytes()))
        header = next(payload for kind, payload in chunks if kind == b"IHDR")
        width, height, depth, color, _, _, _ = struct.unpack(">IIBBBBB", header)
        palette = next((payload for kind, payload in chunks if kind == b"PLTE"), b"")
        transparency = next((payload for kind, payload in chunks if kind == b"tRNS"), b"")
        pixels = decode_rgba([payload for kind, payload in chunks if kind == b"IDAT"], width, height, depth, color, palette, transparency)
        for y in range(height):
            for x in range(width):
                if pixels[(y * width + x) * 4 + 3]:
                    left, top = min(left, x), min(top, y)
                    right, bottom = max(right, x + 1), max(bottom, y + 1)
    return {"canvas": [width, height], "bounds": [left, top, right - left, bottom - top]} if right > left else {"canvas": [width, height], "bounds": [0, 0, width, height]}


def asset_response(saved):
    return {"frames": [Path(name).as_uri() for name in saved["files"]], "delays": saved["delays"], "canvas": saved["canvas"], "bounds": saved["bounds"]}


def png_chunks(data):
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("The downloaded asset is not a PNG image.")
    position = 8
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError("Truncated PNG image.")
        size = struct.unpack(">I", data[position:position + 4])[0]
        end = position + size + 12
        if end > len(data):
            raise ValueError("Truncated PNG chunk.")
        kind = data[position + 4:position + 8]
        payload = data[position + 8:end - 4]
        crc = struct.unpack(">I", data[end - 4:end])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError("Invalid PNG checksum.")
        yield kind, payload
        position = end
        if kind == b"IEND":
            return
    raise ValueError("Missing PNG end marker.")


def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def decode_rgba(pixels, width, height, depth, color, palette, transparency):
    raw = zlib.decompress(b"".join(pixels))
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    stride = (width * channels * depth + 7) // 8
    bpp = max(1, (channels * depth + 7) // 8)
    if len(raw) != height * (stride + 1):
        raise ValueError("Unexpected PNG pixel data size.")
    decoded = bytearray()
    previous = bytearray(stride)
    for y in range(height):
        offset = y * (stride + 1)
        mode = raw[offset]
        row = bytearray(raw[offset + 1:offset + 1 + stride])
        for x in range(stride):
            left = row[x - bpp] if x >= bpp else 0
            above = previous[x]
            corner = previous[x - bpp] if x >= bpp else 0
            if mode == 1:
                predictor = left
            elif mode == 2:
                predictor = above
            elif mode == 3:
                predictor = (left + above) // 2
            elif mode == 4:
                estimate = left + above - corner
                distances = (abs(estimate - left), abs(estimate - above), abs(estimate - corner))
                predictor = (left, above, corner)[distances.index(min(distances))]
            elif mode == 0:
                predictor = 0
            else:
                raise ValueError("Unsupported PNG filter.")
            row[x] = (row[x] + predictor) & 255
        for x in range(width):
            if color == 3:
                shift = 8 - depth - (x * depth % 8)
                index = (row[x * depth // 8] >> shift) & ((1 << depth) - 1)
                if index * 3 + 3 > len(palette):
                    raise ValueError("Invalid PNG palette index.")
                decoded.extend(palette[index * 3:index * 3 + 3])
                decoded.append(transparency[index] if index < len(transparency) else 255)
            elif color == 6:
                decoded.extend(row[x * 4:x * 4 + 4])
            elif color == 2:
                rgb = row[x * 3:x * 3 + 3]
                decoded.extend(rgb)
                transparent = len(transparency) == 6 and tuple(rgb) == struct.unpack(">HHH", transparency)
                decoded.append(0 if transparent else 255)
            else:
                gray = row[x * channels]
                alpha = row[x * channels + 1] if color == 4 else (0 if transparency == struct.pack(">H", gray) else 255)
                decoded.extend((gray, gray, gray, alpha))
        previous = row
    return decoded


def encode_rgba(pixels, width, height):
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    stride = width * 4
    raw = b"".join(b"\x00" + pixels[y * stride:(y + 1) * stride] for y in range(height))
    return PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def extract_animation(data):
    chunks = list(png_chunks(data))
    header = next(payload for kind, payload in chunks if kind == b"IHDR")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", header)
    if not 1 <= width <= 256 or not 1 <= height <= 256 or color not in (0, 2, 3, 4, 6) or (depth not in (1, 2, 4, 8) if color == 3 else depth != 8) or (compression, filtering, interlace) != (0, 0, 0):
        raise ValueError("Unexpected party icon pixel format.")
    palette = next((payload for kind, payload in chunks if kind == b"PLTE"), b"")
    transparency = next((payload for kind, payload in chunks if kind == b"tRNS"), b"")
    frames = []
    control = None
    pixels = []
    canvas = bytearray(width * height * 4)

    def finish():
        if not pixels or control is None:
            return
        _, fw, fh, x, y, delay_n, delay_d, dispose, blend = control
        if fw < 1 or fh < 1 or x + fw > width or y + fh > height or dispose > 2 or blend > 1:
            raise ValueError("Invalid APNG frame geometry.")
        previous = canvas[:]
        frame = decode_rgba(pixels, fw, fh, depth, color, palette, transparency)
        for fy in range(fh):
            for fx in range(fw):
                source = (fy * fw + fx) * 4
                target = ((y + fy) * width + x + fx) * 4
                sa = frame[source + 3]
                if blend == 0 or sa == 255:
                    canvas[target:target + 4] = frame[source:source + 4]
                elif sa:
                    da = canvas[target + 3]
                    alpha = sa * 255 + da * (255 - sa)
                    for channel in range(3):
                        numerator = frame[source + channel] * sa * 255 + canvas[target + channel] * da * (255 - sa)
                        canvas[target + channel] = (numerator + alpha // 2) // alpha
                    canvas[target + 3] = (alpha + 127) // 255
        delay = max(20, min(10000, round(1000 * delay_n / (delay_d or 100))))
        frames.append((encode_rgba(canvas, width, height), delay))
        if dispose == 1:
            for row in range(y, y + fh):
                start = (row * width + x) * 4
                canvas[start:start + fw * 4] = b"\x00" * (fw * 4)
        elif dispose == 2:
            canvas[:] = previous

    for kind, payload in chunks:
        if kind == b"fcTL":
            finish()
            control = struct.unpack(">IIIIIHHBB", payload)
            pixels = []
        elif kind == b"IDAT":
            pixels.append(payload)
        elif kind == b"fdAT":
            pixels.append(payload[4:])
    finish()
    if len(frames) < 2:
        raise ValueError("The selected party icon has no animation.")
    return frames


def fetch(path):
    url = "https://raw.githubusercontent.com/PokeAPI/sprites/" + CATALOG["revision"] + "/" + path
    request = urllib.request.Request(url, headers={"User-Agent": "omarchy-pokespaces/0.1"})
    with urllib.request.urlopen(request, timeout=12) as response:
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("The sprite exceeds the expected download size.")
    return data


def asset_key(pokemon=None, ball=None):
    return "ball:" + ball if ball is not None else "pokemon:" + str(pokemon)


def ensure_asset(pokemon=None, ball=None):
    key = asset_key(pokemon=pokemon, ball=ball)
    if ball is not None:
        if ball not in BALLS:
            raise ValueError("Unknown ball.")
        path = BALLS[ball]["path"]
    else:
        if type(pokemon) is not int or pokemon not in POKEMON:
            raise ValueError("Unknown Pokémon.")
        path = POKEMON[pokemon]["path"]
    directory = CACHE / key.replace(":", "-")
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        metadata = directory / "asset.json"
        if metadata.exists():
            try:
                saved = json.loads(metadata.read_text())
                files = saved["files"]
                if files and all(Path(name).is_file() and Path(name).parent == directory for name in files) and len(files) == len(saved["delays"]):
                    if "bounds" not in saved or "canvas" not in saved:
                        saved.update(frame_geometry(files))
                        atomic_write(metadata, json.dumps(saved).encode())
                    return key, asset_response(saved)
            except (ValueError, KeyError, TypeError):
                metadata.unlink(missing_ok=True)
        data = fetch(path)
        frames = [(data, 1000)] if ball is not None else extract_animation(data)
        if ball is not None:
            list(png_chunks(data))
        files = []
        for index, (image, delay) in enumerate(frames):
            target = directory / (str(index) + ".png")
            atomic_write(target, image)
            files.append(str(target))
        saved = {"files": files, "delays": [delay for image, delay in frames], **frame_geometry(files)}
        atomic_write(metadata, json.dumps(saved).encode())
        return key, asset_response(saved)


def assets_for(team):
    requests = {}
    for slot in team:
        requests[asset_key(pokemon=slot["pokemon"])] = {"pokemon": slot["pokemon"]}
        requests[asset_key(ball=slot["ball"])] = {"ball": slot["ball"]}
    assets, errors = {}, []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        pending = {executor.submit(ensure_asset, **args): key for key, args in requests.items()}
        for future in concurrent.futures.as_completed(pending):
            try:
                key, value = future.result()
                assets[key] = value
            except (OSError, ValueError, urllib.error.URLError) as error:
                errors.append(pending[future] + ": " + str(error))
    return assets, errors


def handle(request):
    action = request.get("action")
    if action == "preview":
        args = {"ball": request["ball"]} if "ball" in request else {"pokemon": request.get("pokemon")}
        key, value = ensure_asset(**args)
        return {"assets": {key: value}}
    if action not in ("state", "save"):
        raise ValueError("Unknown request.")
    team = validate_team(request.get("team")) if action == "save" else read_team()
    if action == "save" or not (CONFIG / "team.json").exists():
        team = save_team(team if action == "save" else None)
    assets, errors = assets_for(team)
    return {"team": team, "assets": assets, "errors": errors, "catalog": CATALOG, "configPath": str(CONFIG / "team.json")}


def helper_main():
    try:
        request = json.loads(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read(65536))
        result = {"ok": True, **handle(request)}
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as error:
        result = {"ok": False, "error": str(error)}
    print(json.dumps(result, ensure_ascii=False))


class CliParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFKD", str(value).replace("♀", " female ").replace("♂", " male ")).casefold() if c.isalnum())


def resolve_entry(value, entries, kind):
    matches = [entry for entry in entries if normalized(value) in (normalized(entry["id"]), normalized(entry["name"]))]
    if len(matches) != 1:
        raise ValueError("Unknown " + kind + ": " + str(value))
    return matches[0]["id"]


def cli_main():
    as_json = "--json" in sys.argv[1:]
    parser = CliParser(prog="pokespaces", description="Inspect and configure the Pokéspaces team.")
    output = argparse.ArgumentParser(add_help=False)
    output.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=CliParser)
    team_parser = commands.add_parser("team", parents=[output])
    teams = team_parser.add_subparsers(dest="operation", required=True, parser_class=CliParser)
    teams.add_parser("show", parents=[output])
    setter = teams.add_parser("set", parents=[output])
    setter.add_argument("--slot", type=int, choices=range(1, 7), required=True)
    setter.add_argument("--pokemon")
    setter.add_argument("--ball")
    apply = teams.add_parser("apply", parents=[output])
    apply.add_argument("--file", required=True, help="Team JSON file, or - for stdin")
    pokemon_parser = commands.add_parser("pokemon", parents=[output])
    pokemon_commands = pokemon_parser.add_subparsers(dest="operation", required=True, parser_class=CliParser)
    search = pokemon_commands.add_parser("search", parents=[output])
    search.add_argument("query", nargs="?", default="")
    ball_parser = commands.add_parser("balls", parents=[output])
    ball_commands = ball_parser.add_subparsers(dest="operation", required=True, parser_class=CliParser)
    ball_commands.add_parser("list", parents=[output])
    try:
        args = parser.parse_args()
    except ValueError as error:
        if as_json:
            print(json.dumps({"ok": False, "error": str(error)}))
        else:
            print("pokespaces: " + str(error), file=sys.stderr)
        return 2
    try:
        if args.command == "pokemon":
            query = normalized(args.query.lstrip("#"))
            result = {"pokemon": [{"id": e["id"], "name": e["name"]} for e in CATALOG["pokemon"] if not query or query in normalized(e["name"]) or str(e["id"]).startswith(query)]}
        elif args.command == "balls":
            result = {"balls": [{"id": e["id"], "name": e["name"]} for e in CATALOG["balls"]]}
        elif args.operation == "show":
            result = {"version": 1, "team": read_team()}
        else:
            if args.operation == "set":
                if args.pokemon is None and args.ball is None:
                    raise ValueError("Provide --pokemon, --ball, or both.")
                pokemon = resolve_entry(args.pokemon, CATALOG["pokemon"], "Pokémon") if args.pokemon is not None else None
                ball = resolve_entry(args.ball, CATALOG["balls"], "ball") if args.ball is not None else None
                team = save_team(slot=args.slot, pokemon=pokemon, ball=ball)
            else:
                payload = json.loads(sys.stdin.read() if args.file == "-" else Path(args.file).read_text())
                team = save_team(validate_team(payload.get("team") if isinstance(payload, dict) else payload))
            assets, errors = assets_for(team)
            result = {"version": 1, "team": team, "warnings": errors}
        if as_json:
            print(json.dumps({"ok": True, **result}, ensure_ascii=False))
        elif "team" in result:
            for index, slot in enumerate(result["team"], 1):
                print(str(index) + ": " + POKEMON[slot["pokemon"]]["name"] + " / " + BALLS[slot["ball"]]["name"])
            for warning in result.get("warnings", []):
                print("Warning: " + warning, file=sys.stderr)
        else:
            for entry in result.get("pokemon", result.get("balls", [])):
                print(str(entry["id"]) + "\t" + entry["name"])
        return 0
    except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as error:
        if as_json:
            print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        else:
            print("pokespaces: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if (len(sys.argv) == 1 and Path(sys.argv[0]).name != "pokespaces") or (len(sys.argv) > 1 and sys.argv[1].lstrip().startswith("{")):
        helper_main()
    else:
        sys.exit(cli_main())
