#!/bin/zsh
cd "${0:A:h}" || exit 1
if [[ -f .runtime/pid ]]; then
  app_pid=$(cat .runtime/pid)
  if [[ "$app_pid" == <-> ]] && ps -p "$app_pid" -o command= | /usr/bin/grep -Fq "$PWD/app.py"; then
    kill -TERM "$app_pid"
    echo 'Music Metadata stopped.'
  else
    echo 'Music Metadata is already stopped.'
  fi
  rm -f .runtime/pid .runtime/url
else
  echo 'Music Metadata is already stopped.'
fi
