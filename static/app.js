const $ = id => document.getElementById(id);
let tracks = [], busy = false, previewURL, loadedFolder;
const editedAlbumFields = new Set();
['album','album_artist','year','genre','compilation'].forEach(field => {
  $(field).addEventListener('input', () => editedAlbumFields.add(field));
});
function status(message, error = false) { $('status').textContent = message; $('status').classList.toggle('error', error); }
function setBusy(value) { busy = value; document.querySelectorAll('button,input').forEach(el => el.disabled = value); $('save').disabled = value || !tracks.length; }
async function api(path, body) {
  const headers = {'X-App-Token': window.APP_TOKEN};
  if (!(body instanceof FormData)) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(body); }
  const response = await fetch(path, {method: 'POST', headers, body});
  const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Request failed'); return data;
}
function render() {
  $('tracks').replaceChildren();
  tracks.forEach(track => {
    const row = document.createElement('tr');
    function cell(field, type) {
      const td = document.createElement('td'), input = document.createElement('input'); input.type = type; input.value = track[field]; input.setAttribute('aria-label', `${field} for ${track.file}`);
      if (type === 'number') { input.min = 1; input.step = 1; }
      input.addEventListener('input', () => {
        track[field] = input.value;
        if (field === 'artist') track.artistOverride = !!input.value.trim() && input.value.trim() !== $('album_artist').value.trim();
      }); td.append(input); row.append(td); return td;
    }
    cell('number','number'); const title = cell('title','text'); const filename = document.createElement('small'); filename.textContent = track.file; title.append(filename);
    const artist = cell('artist','text'); artist.className = 'track-artist';
    $('tracks').append(row);
  });
  if (!tracks.length) { const row = $('tracks').insertRow(); const cell = row.insertCell(); cell.colSpan = 3; cell.className = 'empty'; cell.textContent = 'No readable MP3s in this folder.'; }
  $('count').textContent = `${tracks.length} track${tracks.length === 1 ? '' : 's'}`;
  $('save').disabled = !tracks.length;

}
$('browse').onclick = async () => { setBusy(true); try { const data = await api('/api/browse', {}); if (data.folder) $('folder').value = data.folder; } catch (e) { status(e.message,true); } finally { setBusy(false); } };
$('load').onclick = async () => {
  setBusy(true); status('Reading MP3s…');
  try {
    const data = await api('/api/load', {folder:$('folder').value});
    const previousTracks = new Map(loadedFolder === data.folder ? tracks.map(track => [track.file, track]) : []);
    tracks = data.tracks.map(track => ({...track, ...previousTracks.get(track.file)}));
    loadedFolder = data.folder;
    $('folder').value = data.folder;
    const first = tracks[0] || {};
    ['album','album_artist','year','genre'].forEach(field => {
      if (!editedAlbumFields.has(field) && !$(field).value.trim()) $(field).value = first[field] || (field === 'album_artist' ? first.artist : '') || '';
    });
    if (!editedAlbumFields.has('compilation')) $('compilation').checked = tracks.some(t => t.compilation);
    tracks.forEach(track => {
      if (track.artistOverride === undefined) {
        const originalAlbumArtist = track.album_artist || first.artist || '';
        track.artistOverride = !!track.artist.trim() && track.artist !== originalAlbumArtist;
      }
      if (!track.artistOverride) track.artist = $('album_artist').value.trim();
    });
    render();
    status(data.errors.length ? `Skipped unreadable files:\n${data.errors.join('\n')}` : `${tracks.length} tracks loaded. Review the details, then save.`, !!data.errors.length);
  } catch(e) { status(e.message,true); } finally { setBusy(false); }
};
$('album_artist').addEventListener('input', () => {
  const inputs = document.querySelectorAll('td.track-artist input');
  tracks.forEach((track, index) => {
    if (!track.artistOverride) {
      track.artist = $('album_artist').value.trim();
      if (inputs[index]) inputs[index].value = track.artist;
    }
  });
});
function clearArtwork() { if (previewURL) URL.revokeObjectURL(previewURL); previewURL = null; $('artwork').value = ''; $('preview').hidden = true; $('preview').removeAttribute('src'); $('artPrompt').hidden = false; $('clear-art').hidden = true; }
$('clear-art').onclick = clearArtwork;
$('artwork').onchange = () => { const file = $('artwork').files[0]; if (!file) return; if (previewURL) URL.revokeObjectURL(previewURL); previewURL = URL.createObjectURL(file); $('preview').src = previewURL; $('preview').hidden = false; $('artPrompt').hidden = true; $('clear-art').hidden = false; };
$('save').onclick = async () => {
  const album = {}; ['album','album_artist','year','genre'].forEach(field => album[field] = $(field).value.trim());
  album.compilation = $('compilation').checked;
  const body = new FormData(); body.append('metadata',JSON.stringify({album,tracks})); if ($('artwork').files[0]) body.append('artwork',$('artwork').files[0]);
  setBusy(true); status('Writing metadata and checking each MP3…');
  try { const data = await api('/api/save',body); const failures = data.results.filter(r => !r.ok); status(`${data.results.length - failures.length} of ${data.results.length} MP3s saved and verified.${failures.length ? '\n' + failures.map(r => `${r.file}: ${r.error}`).join('\n') : '\nYour files are ready to use.'}`, !!failures.length); }
  catch(e) { status(e.message,true); } finally { setBusy(false); }
};
