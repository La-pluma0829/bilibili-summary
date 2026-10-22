import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('extract', Path(__file__).parents[1] / 'scripts' / 'extract.py')
extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract)

class ExtractionTests(unittest.TestCase):
    def run_fake(self, root, video, subtitle=True):
        urls = []
        class YDL:
            def __init__(self, options):
                self.options = options
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def extract_info(self, url, download=False):
                urls.append(url)
                return {'id': 'test', 'title': '测试标题', 'duration': 10,
                        'subtitles': {'zh-CN': [{'ext': 'json', 'url': 'https://example.test/sub.json'}]} if subtitle else {}}
        body = {'body': [{'from': 1.5, 'to': 4, 'content': '真实字幕内容'}]}
        args = ['extract.py', video, '--output-dir', str(root)]
        with patch.object(sys, 'argv', args), patch.dict(sys.modules, {'yt_dlp': types.SimpleNamespace(YoutubeDL=YDL)}), patch.object(extract.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(body).encode())), patch('sys.stdout', new_callable=io.StringIO):
            extract.main()
        return urls

    def test_subtitles_and_part_scoped_cache(self):
        with tempfile.TemporaryDirectory() as root:
            first = self.run_fake(root, 'BV1fZUGYaEHx')
            p1 = Path(root) / 'BV1fZUGYaEHx' / 'p1'
            evidence = json.loads((p1 / 'evidence.json').read_text(encoding='utf-8'))
            self.assertEqual(evidence['source'], 'subtitle')
            self.assertIn('[00:00:01] 真实字幕内容', (p1 / 'transcript.txt').read_text(encoding='utf-8'))
            self.assertEqual(len(first), 1)
            # A cached run must not contact the extractor.
            self.assertEqual(self.run_fake(root, 'BV1fZUGYaEHx'), [])
            second = self.run_fake(root, 'https://www.bilibili.com/video/BV1fZUGYaEHx/?p=2')
            self.assertEqual(len(second), 1)
            self.assertTrue((Path(root) / 'BV1fZUGYaEHx' / 'p2' / 'evidence.json').exists())
            self.run_fake(root, 'BV1Utaye5E8c')
            self.assertTrue((Path(root) / 'BV1Utaye5E8c' / 'p1' / 'evidence.json').exists())

    def test_invalid_id_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(sys, 'argv', ['extract.py', 'BV1fZUGYaEHxx', '--output-dir', root]), patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
                extract.main()
            self.assertEqual(list(Path(root).iterdir()), [])

if __name__ == '__main__':
    unittest.main()
