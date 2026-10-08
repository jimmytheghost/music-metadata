# Music Metadata

A personal, local Mac tool for embedding album artwork and ID3 metadata directly into MP3 deliverables. No AI, account, or cloud service is involved in tagging.

## Run

Double-click **launch.command**. On first launch it creates a local Python environment and downloads dependencies; later launches reuse it. Requires Python 3.9 or newer. The browser opens automatically. Double-click **kill.command** to stop the server. Closing the browser does not stop it.

If macOS asks which app should open a `.command` file, select Terminal. If the browser does not open, the local address is in `.runtime/url`, and startup errors are in `.runtime/server.log`.

## Workflow

1. Browse for a folder, or paste its path, then load the MP3s. Subfolders and symbolic links are excluded.
2. Enter the album title, track artist, album artist, release year, and optional genre. Album artist defaults to track artist when saving.
3. For compilations, enable the checkbox, supply an album artist such as “Various Artists,” and edit each track’s artist. Blank per-track artists fall back to the shared track artist.
4. Select a JPEG, PNG, or WebP cover image. Uploaded artwork replaces existing cover images. Without a new image, each MP3 keeps its existing artwork.
5. Review titles and numbers, then click **Save to MP3s**. The result reports successful and failed files individually.

**Saving modifies the source MP3s.** Your WAV masters are never edited. Filenames stay the same. Existing tags populate the form; untagged files use filename suggestions such as `01-Crazy.mp3` → track 1, “Crazy” and `03-4thWave.mp3` → track 3, “4th Wave.” Suggestions remain editable.

The app writes ID3v2.3 tags, including album, title, artist, album artist, track number/total, release year, genre, disc 1/1, compilation status, and cover artwork. Audio is not re-encoded. Artwork is converted to JPEG with a maximum dimension of 2000 pixels. Each file is staged and verified before atomic replacement; a failed file leaves its original intact. A batch is not an all-or-nothing transaction: successfully saved files remain saved if another file fails. No undo history or persistent backup is created.

The server listens only on your Mac at an automatically selected local port. One browser session and one album at a time are supported. Music apps may need to re-import previously cached files to display updated tags.

## Development

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
```

Integration tests generate a tiny MP3 with the development-only LAME encoder. Your music files, virtual environment, and server runtime files are excluded from Git.

## Scope

Initial version: personal Mac workflow, direct MP3 tagging, editable filename suggestions, one album per batch, optional compilation artists, and imported cover artwork. Future options can include pasted track lists, additional audio formats, and native app packaging.
