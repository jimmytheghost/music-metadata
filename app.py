"""Local Music Metadata UI. Bind only to loopback; never expose on a network."""
import json
import secrets
import subprocess
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from werkzeug.serving import make_server

from metadata import inspect_track, prepare_artwork, write_track

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
TOKEN = secrets.token_urlsafe(32)
SESSION = {"folder": None, "files": set()}
LOCK = threading.Lock()


@app.before_request
def local_only():
    if request.host.split(":")[0] not in {"127.0.0.1", "localhost"}:
        return jsonify(error="Local access only"), 403
    if request.method == "POST" and not secrets.compare_digest(request.headers.get("X-App-Token", ""), TOKEN):
        return jsonify(error="Reload this page and try again"), 403


@app.errorhandler(Exception)
def error(exc):
    return jsonify(error=str(exc)), exc.code if isinstance(exc, HTTPException) else 400


@app.get("/")
def index():
    return render_template("index.html", token=TOKEN)


@app.post("/api/browse")
def browse():
    result = subprocess.run(["osascript", "-e", 'POSIX path of (choose folder with prompt "Choose your MP3 folder")'], capture_output=True, text=True)
    return jsonify(folder=result.stdout.strip() if result.returncode == 0 else "")


@app.post("/api/load")
def load():
    with LOCK:
        folder = Path(request.get_json()["folder"]).expanduser().resolve(strict=True)
        if not folder.is_dir():
            raise ValueError("Choose a folder")
        tracks, errors = [], []
        for path in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if path.suffix.lower() != ".mp3" or path.is_symlink() or not path.is_file():
                continue
            try:
                tracks.append(inspect_track(path))
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")
        tracks.sort(key=lambda t: (t["number"] is None, t["number"] or 0, t["file"].lower()))
        for index, track in enumerate(tracks, 1):
            if track["number"] is None:
                track["number"] = index
        SESSION.update(folder=folder, files={t["file"] for t in tracks})
        return jsonify(folder=str(folder), tracks=tracks, errors=errors)


@app.post("/api/save")
def save():
    with LOCK:
        if SESSION["folder"] is None:
            raise ValueError("Load a folder first")
        payload = json.loads(request.form["metadata"])
        album = payload["album"]
        for field in ("album", "album_artist", "year", "genre"):
            album[field] = str(album.get(field, "")).strip()
        album["compilation"] = bool(album.get("compilation"))
        if not album["album"] or not album["album_artist"]:
            raise ValueError("Album title and album artist are required")
        if album["year"] and (len(album["year"]) != 4 or not album["year"].isdigit()):
            raise ValueError("Enter a four-digit release year")
        tracks = payload["tracks"]
        if not tracks or {t["file"] for t in tracks} != SESSION["files"] or len(tracks) != len(SESSION["files"]):
            raise ValueError("Track list changed. Reload the folder before saving")
        numbers = set()
        for track in tracks:
            track["title"] = str(track["title"]).strip()
            track["artist"] = str(track.get("artist", "")).strip() or album["album_artist"]
            track["number"] = int(track["number"])
            path = SESSION["folder"] / track["file"]
            if path.is_symlink() or path.resolve().parent != SESSION["folder"] or not path.is_file():
                raise ValueError("A source file moved or changed. Reload the folder")
            if not track["title"] or not track["artist"] or track["number"] < 1 or track["number"] in numbers:
                raise ValueError("Each track needs a title, artist, and unique positive track number")
            numbers.add(track["number"])
        upload = request.files.get("artwork")
        artwork = prepare_artwork(upload.read()) if upload and upload.filename else None
        results = []
        for track in tracks:
            try:
                write_track(SESSION["folder"] / track["file"], track, album, artwork, len(tracks))
                results.append(dict(file=track["file"], ok=True))
            except Exception as exc:
                results.append(dict(file=track["file"], ok=False, error=str(exc)))
        return jsonify(results=results)


if __name__ == "__main__":
    runtime = Path(__file__).parent / ".runtime"
    runtime.mkdir(exist_ok=True)
    server = make_server("127.0.0.1", 0, app, threaded=True)
    url = f"http://127.0.0.1:{server.server_port}"
    (runtime / "url").write_text(url)
    print(f"Music Metadata: {url}", flush=True)
    threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    server.serve_forever()
