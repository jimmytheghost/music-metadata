import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import lameenc
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from PIL import Image

from app import app, SESSION, TOKEN
from metadata import inferred_track, prepare_artwork, write_track


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(128)
        encoder.set_in_sample_rate(44100)
        encoder.set_channels(1)
        self.audio = bytes(encoder.encode(b'\0\0' * 22050) + encoder.flush())
        self.path = self.folder / '03-4thWave.mp3'
        self.path.write_bytes(self.audio)
        self.album = dict(album='Test Album', artist='Test Artist', album_artist='Test Artist', year='2026', genre='Electronic', compilation=False)
        self.track = dict(file=self.path.name, title='4th Wave', number=3, artist='Test Artist')
        image = Image.new('RGBA', (64, 64), (20, 100, 70, 128))
        stream = io.BytesIO()
        image.save(stream, 'PNG')
        self.art = prepare_artwork(stream.getvalue())
        self.client = app.test_client()
        self.headers = {'X-App-Token': TOKEN}

    def test_filename(self):
        self.assertEqual(inferred_track('01-Crazy.mp3'), (1, 'Crazy'))
        self.assertEqual(inferred_track(self.path.name), (3, '4th Wave'))

    def test_tags_cover_and_audio_preserved(self):
        write_track(self.path, self.track, self.album, self.art, 1)
        tags = ID3(self.path)
        self.assertEqual(tags.version[:2], (2, 3))
        for key, value in {'TIT2':'4th Wave', 'TALB':'Test Album', 'TPE1':'Test Artist', 'TRCK':'3/1', 'TDRC':'2026'}.items():
            self.assertEqual(str(tags[key]), value)
        self.assertEqual(tags.getall('APIC')[0].data, self.art)
        self.assertTrue(self.path.read_bytes().endswith(self.audio))
        write_track(self.path, self.track, self.album, None, 1)
        self.assertEqual(ID3(self.path).getall('APIC')[0].data, self.art)
        self.assertGreater(MP3(self.path).info.length, 0)

    def test_failure_preserves_original(self):
        with patch('metadata.os.replace', side_effect=OSError('simulated failure')):
            with self.assertRaises(OSError):
                write_track(self.path, self.track, self.album, self.art, 1)
        self.assertEqual(self.path.read_bytes(), self.audio)
        self.assertEqual(list(self.folder.iterdir()), [self.path])

    def test_api_validation_and_compilation(self):
        self.assertEqual(self.client.post('/api/load', json={'folder':str(self.folder)}).status_code, 403)
        response = self.client.post('/api/load', json={'folder':str(self.folder)}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['tracks'][0]['title'], '4th Wave')
        self.album.update(compilation=True, album_artist='Various Artists')
        self.track['artist'] = 'Guest Artist'
        data = dict(metadata=json.dumps(dict(album=self.album, tracks=[self.track])), artwork=(io.BytesIO(self.art), 'cover.jpg'))
        response = self.client.post('/api/save', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json['results'][0]['ok'])
        tags = ID3(self.path)
        self.assertEqual(str(tags['TPE1']), 'Guest Artist')
        self.assertEqual(str(tags['TPE2']), 'Various Artists')
        self.assertEqual(str(tags['TCMP']), '1')
        original = self.path.read_bytes()
        self.track['number'] = 0
        response = self.client.post('/api/save', data={'metadata':json.dumps(dict(album=self.album, tracks=[self.track]))}, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.path.read_bytes(), original)

    def test_reject_invalid_image_before_write(self):
        SESSION.update(folder=self.folder.resolve(), files={self.path.name})
        response = self.client.post('/api/save', data={'metadata':json.dumps(dict(album=self.album, tracks=[self.track])), 'artwork':(io.BytesIO(b'not an image'), 'bad.jpg')}, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.path.read_bytes(), self.audio)

    def test_track_artist_override_without_compilation(self):
        SESSION.update(folder=self.folder.resolve(), files={self.path.name})
        self.album.pop('artist')
        self.track['artist'] = 'Test Artist feat. Guest'
        def save():
            return self.client.post('/api/save', data={'metadata':json.dumps(dict(album=self.album, tracks=[self.track]))}, headers=self.headers)
        response = save()
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json['results'][0]['ok'], response.json)
        self.assertEqual(str(ID3(self.path)['TPE1']), 'Test Artist feat. Guest')
        self.assertEqual(str(ID3(self.path)['TPE2']), 'Test Artist')
        self.assertEqual(str(ID3(self.path)['TCMP']), '0')
        self.track['artist'] = ' '
        response = save()
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json['results'][0]['ok'], response.json)
        self.assertEqual(str(ID3(self.path)['TPE1']), 'Test Artist')


if __name__ == '__main__':
    unittest.main()
