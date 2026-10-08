"""MP3 inspection and atomic, audio-preserving ID3 edits."""
import io
import os
import re
import shutil
import tempfile
from pathlib import Path

from mutagen.id3 import ID3, APIC, TALB, TPE1, TPE2, TIT2, TRCK, TDRC, TCON, TPOS, TCMP
from mutagen.mp3 import MP3
from PIL import Image, ImageOps


def inferred_track(filename):
    stem = Path(filename).stem
    match = re.match(r"^(\d{1,3})[\s._-]+(.+)$", stem)
    number, title = (int(match[1]), match[2]) if match else (None, stem)
    title = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", title.replace("_", " "))
    return number, title.strip()


def inspect_track(path):
    audio = MP3(path)
    tags = audio.tags or ID3()
    number, title = inferred_track(path.name)
    def value(key):
        return str(tags.get(key, ""))
    stored_number = value("TRCK").split("/")[0]
    return dict(file=path.name, title=value("TIT2") or title,
                number=int(stored_number) if stored_number.isdigit() else number,
                artist=value("TPE1"), album=value("TALB"), album_artist=value("TPE2"),
                year=value("TDRC")[:4], genre=value("TCON"),
                compilation=value("TCMP") == "1", seconds=round(audio.info.length))


def prepare_artwork(data):
    with Image.open(io.BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((2000, 2000))
        if image.mode != "RGB":
            canvas = Image.new("RGB", image.size, "white")
            if "A" in image.getbands():
                canvas.paste(image, mask=image.getchannel("A"))
            else:
                canvas.paste(image.convert("RGB"))
            image = canvas
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=92)
        return output.getvalue()


def write_track(path, track, album, artwork, total):
    # Stage a full copy beside the source, then atomically replace after verification.
    fd, name = tempfile.mkstemp(prefix=".music-metadata-", suffix=".mp3", dir=path.parent)
    os.close(fd)
    staged = Path(name)
    try:
        shutil.copy2(path, staged)
        audio = MP3(staged)
        if audio.tags is None:
            audio.add_tags()
        tags = audio.tags
        fields = [("TIT2", TIT2, track["title"]), ("TALB", TALB, album["album"]),
                  ("TPE1", TPE1, track["artist"]), ("TPE2", TPE2, album["album_artist"]),
                  ("TRCK", TRCK, f'{track["number"]}/{total}'),
                  ("TDRC", TDRC, album["year"]), ("TCON", TCON, album["genre"]),
                  ("TPOS", TPOS, "1/1"), ("TCMP", TCMP, "1" if album["compilation"] else "0")]
        for key, frame, value in fields:
            tags.delall(key)
            if value:
                tags.add(frame(encoding=3, text=[value]))
        if artwork is not None:
            tags.delall("APIC")
            tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=artwork))
        tags.save(staged, v2_version=3, v1=0)
        verified = MP3(staged)
        if str(verified.tags["TIT2"]) != track["title"]:
            raise ValueError("Saved title failed verification")
        if artwork is not None and not verified.tags.getall("APIC"):
            raise ValueError("Saved artwork failed verification")
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)
