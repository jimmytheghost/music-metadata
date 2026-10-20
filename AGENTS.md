# Music Metadata — project continuity

## Status and purpose

As of 2026-10-08, the first working version is complete. The owner has tried it and confirmed: “Looks great. Works well!” No outstanding feature request or known reported bug remains. Future work should start with the owner's next request, rather than rebuilding or expanding the app unsolicited.

Music Metadata is a personal Mac tool for embedding metadata and cover artwork into MP3 deliverables. The owner's WAV files are the masters; MP3s are the deliverables and are intentionally modified in place. The tool exists because editing songs in Apple Music did not update the owner's original MP3 files as expected.

GitHub repository: https://github.com/jimmytheghost/music-metadata
Default branch: `main`. Inspect actual Git state before working; do not assume it is clean or synchronized.

On 2026-10-20, the owner requested public-release preparation using the Agentic Toolkit. The README now follows its personal-tool sharing process, with an MIT license and an actual interface screenshot. Source-only sharing is the chosen preparation scope; no binary, release tag, or hosted site is required. Preparation alone does not authorize changing repository visibility or publishing a GitHub Release. Check actual visibility before describing the repository as public. The owner subsequently authorized publication on 2026-10-20. Repository visibility was changed to public and anonymous access to the repository and README was verified. No GitHub Release or binary was published.

## Owner preferences and agreed scope

- Keep this simple and procedural. No generative AI, model hosting, external tagging service, or cloud processing is needed.
- This is for the owner's personal workflow, almost always single-artist albums. Do not introduce commercial product infrastructure without a request.
- A local browser UI launched by double-clicking `launch.command` is the chosen format. `kill.command` stops the server. Native Mac packaging and a menu-bar app are not current requirements.
- Update the selected MP3s directly. Do not change this into an output-copy workflow or add mandatory backups/confirmation dialogs without a request.
- Keep artwork and music local and out of Git. Never test tagging against the owner's actual music unless explicitly asked.
- Explain results in plain language and keep routine implementation details out of the UI.

## Behavior to preserve

- Load MP3s directly from one selected folder; skip subfolders and symbolic links. Native Mac folder selection and pasted paths are supported.
- Prefer existing tags when loading. Infer editable track numbers and titles for untagged files: `01-Crazy.mp3` becomes track 1, “Crazy”; `03-4thWave.mp3` becomes track 3, “4th Wave.” The numeric prefix is authoritative as a starting suggestion; do not silently renumber it.
- Album details contain album title, **Album Artist**, release year, optional genre, and an optional compilation checkbox. There is **no shared Track Artist field**.
- Section 04 always has three columns: track number, song title/source filename, and track artist.
- Track artists default to Album Artist and follow subsequent changes to it until individually overridden. Preserve existing distinct track credits when loading tagged files.
- Editing a track artist changes only that song. Artist overrides work regardless of the compilation checkbox. A blank artist falls back to Album Artist on save.
- Compilation is an independent metadata tag, not a switch for showing artist inputs.
- **Loading tracks must preserve entered album fields, selected artwork, and the user's compilation choice.** Fields the user deliberately clears must stay cleared. Empty, untouched album fields can populate from MP3 tags.
- Reloading the same folder preserves existing track edits matched by filename. Loading a different folder loads that folder's track list while keeping the album form and selected artwork.
- JPEG, PNG, and WebP artwork is converted to JPEG, with a maximum dimension of 2000 pixels. A selected image replaces embedded artwork; no selected image preserves each file's existing cover.
- Save embeds ID3v2.3 metadata and artwork without re-encoding audio or renaming files. WAVs are untouched.
- Stage and verify each file beside its original before atomic replacement. Report success/failure per file. A batch is not transactional; successful files remain saved if another fails. No persistent backup or undo feature exists.

## Implementation map

- `app.py`: Flask routes, local-only access checks, request token, folder/session state, save validation, native folder picker, and server startup.
- `metadata.py`: filename inference, MP3 inspection, image conversion, and atomic ID3 updates with Mutagen.
- `templates/index.html`: four-section interface and form layout.
- `static/app.js`: form state, track editing, album artist inheritance/overrides, upload preview, and API requests. `editedAlbumFields` protects manual edits; `loadedFolder` and filenames preserve same-folder track edits; `artistOverride` tracks independent credits.
- `static/style.css`: responsive dark green interface.
- `launch.command` / `kill.command`: executable zsh scripts for the Mac lifecycle. Launch creates/reuses `.venv`, installs dependencies as needed, and starts a detached process.
- `requirements.txt`: Flask, Mutagen, Pillow. Python 3.9 or newer.
- `requirements-dev.txt`: runtime requirements plus LAME encoder for generating test MP3s.
- `tests/test_metadata.py`: generated MP3 integration tests for parsing, tags/artwork, audio preservation, failed-write preservation, API validation, compilation, and independent artist overrides/defaults.
- `README.md`: user instructions and current limitations. Keep it aligned with behavior changes.

## Run and verify

```sh
./launch.command
# Read .runtime/url for the current local URL.
./kill.command

.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
node --check static/app.js
zsh -n launch.command kill.command
git diff --check
```

Public-release preparation on 2026-10-20: all six Python tests passed with Python 3.9.6; JavaScript and zsh syntax, README local links, ignore rules, and diff whitespace checks passed. The documentation screenshot shows an isolated instance of the actual app with no music loaded. A focused review covered tracked files and all 19 file versions reachable from the four existing commits; it found no credentials, private absolute paths, music, uploads, or runtime artifacts. This was a publication-material review, not a comprehensive security audit.

At handoff all six Python tests passed. Artist inheritance and load-state preservation also received JavaScript smoke checks. There is no committed browser test suite; use focused UI verification for interaction changes rather than relying only on backend tests.

Use temporary, generated MP3s for verification. On macOS resolve temporary folder paths before assigning `SESSION['folder']`; `/var` and `/private/var` can refer to the same place, while containment checks compare resolved paths.

The server binds only to `127.0.0.1`, on an automatically assigned port. Never hardcode a previous chat's port: read `.runtime/url`. Runtime files and logs live in `.runtime/` and are ignored by Git. There is one shared in-memory folder session; multiple simultaneous browser sessions are not supported.

Python changes need a server restart. Static changes need a browser refresh. Refreshing currently clears unsaved browser form state, and restarting clears the server's loaded folder state. Avoid restarting or refreshing while the owner is working without explaining the effect. The launch script opens the browser automatically; avoid creating redundant tabs.

## Future sessions

Read this file and the relevant implementation before editing. Check Git status and preserve unrelated local changes. Treat the latest owner instruction as authoritative over these notes. Keep fixes focused, run checks appropriate to the changed behavior, and update these continuity notes when decisions change. The project has been kept synchronized with its GitHub repository; preserve that workflow for requested project changes. Do not commit music, artwork uploads, credentials, virtual environments, or runtime artifacts.

Possible future ideas such as pasted track lists, more audio formats, or native app packaging are unapproved options, not a backlog to implement automatically.
