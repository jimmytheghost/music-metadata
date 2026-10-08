#!/bin/zsh
cd "${0:A:h}" || exit 1
mkdir -p .runtime
if [[ -f .runtime/pid ]]; then
  old_pid=$(cat .runtime/pid)
  if [[ "$old_pid" == <-> ]] && ps -p "$old_pid" -o command= | /usr/bin/grep -Fq "$PWD/app.py"; then
    [[ -f .runtime/url ]] && open "$(cat .runtime/url)"
    exit 0
  fi
fi
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv || { echo 'Python 3.9 or newer is required.'; read '?Press Return to close.'; exit 1; }
fi
if ! cmp -s requirements.txt .runtime/installed-requirements.txt; then
  .venv/bin/python -m pip install -r requirements.txt || { read '?Installation failed. Press Return to close.'; exit 1; }
  cp requirements.txt .runtime/installed-requirements.txt
fi
.venv/bin/python - <<'PYTHON'
import subprocess
import sys
from pathlib import Path
root = Path.cwd()
with (root / ".runtime/server.log").open("a") as log:
    process = subprocess.Popen([sys.executable, str(root / "app.py")], stdin=subprocess.DEVNULL,
                               stdout=log, stderr=log, start_new_session=True)
(root / ".runtime/pid").write_text(str(process.pid))
PYTHON
echo 'Music Metadata is starting in your browser. Use kill.command to stop it.'
