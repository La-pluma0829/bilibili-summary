#!/usr/bin/env python3
"""Acquire grounded Bilibili evidence; the calling assistant writes the summary."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

CACHE = Path(os.environ.get('BILIBILI_SUMMARY_CACHE', Path.home() / '.cache' / 'bilibili-summary')).expanduser()

def stamp(seconds):
    seconds = int(seconds)
    return f'{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}'

def make_frames(url, dest, duration):
    import yt_dlp
    import av
    from PIL import Image, ImageDraw
    with yt_dlp.YoutubeDL({'noplaylist': True, 'format': 'worstvideo',
                           'socket_timeout': 20, 'retries': 1,
                           'outtmpl': str(dest / 'video.%(ext)s')}) as ydl:
        info = ydl.extract_info(url, download=True)
        video = ydl.prepare_filename(info)
    frame_dir = dest / 'frames'
    frame_dir.mkdir(exist_ok=True)
    images = []
    with av.open(video) as container:
        length = duration or (container.duration or 0) / 1000000
        if length <= 0:
            raise RuntimeError('Cannot determine video duration for visual sampling')
        for index in range(24):
            target = length * index / 24
            container.seek(int(target * 1000000))
            for frame in container.decode(video=0):
                if frame.time is not None and frame.time >= target:
                    im = frame.to_image()
                    im.thumbnail((640, 360))
                    im.save(frame_dir / f'{index:02}.jpg')
                    images.append((target, im))
                    break
    for start in range(0, len(images), 8):
        sheet = Image.new('RGB', (1280, 1560), 'white')
        draw = ImageDraw.Draw(sheet)
        for j, (target, im) in enumerate(images[start:start+8]):
            x, y = j % 2 * 640, j // 2 * 390
            sheet.paste(im, (x, y))
            draw.text((x+4, y+363), stamp(target), fill='black')
        sheet.save(frame_dir / f'contact-{start // 8}.jpg')
    print(f'Visual samples: {frame_dir}', file=sys.stderr)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('video')
    p.add_argument('--output-dir', required=True)
    p.add_argument('--language', default='zh', help='ASR language code or auto')
    p.add_argument('--model', default='base', help='Whisper model name or local .pt path')
    p.add_argument('--model-dir', default=str(CACHE / 'models'))
    p.add_argument('--frames', action='store_true', help='Download video and sample visual contact sheets')
    p.add_argument('--refresh', action='store_true', help='Rebuild transcript; reuse downloaded media')
    args = p.parse_args()
    match = re.search(r'BV[0-9A-Za-z]{10}(?![0-9A-Za-z])', args.video)
    if not match:
        p.error('请提供有效 BV 号或含 BV 号的 B 站链接')
    bvid = match.group()
    part = re.search(r'[?&]p=(\d+)', args.video)
    url = f'https://www.bilibili.com/video/{bvid}/' + (f'?p={part.group(1)}' if part else '')
    dest = Path(args.output_dir).resolve() / bvid / ('p' + (part.group(1) if part else '1'))
    dest.mkdir(parents=True, exist_ok=True)
    evidence_file = dest / 'evidence.json'
    if not args.refresh and evidence_file.exists() and (dest / 'transcript.txt').exists():
        old = json.loads(evidence_file.read_text(encoding='utf-8'))
        if old.get('url') == url and old.get('asr_request') == [args.language, args.model]:
            if args.frames:
                make_frames(url, dest, old.get('duration'))
            print(json.dumps({'cached': True, 'evidence': str(evidence_file)}, ensure_ascii=False))
            return
    import yt_dlp
    options = {'noplaylist': True, 'skip_download': True, 'format': 'worstaudio',
               'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': ['all', '-danmaku'],
               'socket_timeout': 20, 'retries': 1, 'extractor_retries': 1,
               'outtmpl': str(dest / 'audio.%(ext)s')}
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get('entries'):
        info = next(e for e in info['entries'] if e)
    evidence = {k: info.get(k) for k in ('id', 'title', 'uploader', 'duration', 'description', 'chapters', 'upload_date')}
    evidence.update(url=url, scope='链接指定分P；未指定则第一P', asr_request=[args.language, args.model])
    rows = None
    tracks = {**info.get('automatic_captions', {}), **info.get('subtitles', {})}
    languages = sorted((k for k in tracks if k != 'danmaku'), key=lambda k: (not ('zh' in k or 'cn' in k), k))
    for language in languages:
        for track in tracks[language]:
            try:
                request = urllib.request.Request(track['url'], headers={'Referer': url, 'User-Agent': 'Mozilla/5.0'})
                raw = urllib.request.urlopen(request, timeout=20).read().decode('utf-8-sig')
                if track.get('ext') == 'json':
                    body = json.loads(raw).get('body', [])
                    candidate = [{'start': r['from'], 'end': r['to'], 'text': r['content']} for r in body]
                elif track.get('ext') in ('srt', 'vtt'):
                    pattern = r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})[^\n]*\n(.*?)(?=\n\s*\n|\Z)'
                    def seconds(value):
                        h, m, s = value.replace(',', '.').split(':')
                        return int(h)*3600 + int(m)*60 + float(s)
                    candidate = [{'start': seconds(a), 'end': seconds(b), 'text': re.sub('<[^>]*>', '', t).replace('\n', ' ')} for a,b,t in re.findall(pattern, raw, re.S)]
                else:
                    continue
                if candidate:
                    rows = candidate
                    evidence.update(source='subtitle', subtitle_language=language)
                    break
            except Exception as exc:
                print(f'Subtitle unavailable: {type(exc).__name__}', file=sys.stderr)
        if rows:
            break
    if not rows:
        audio = next((f for f in dest.glob('audio.*') if f.suffix in ('.m4a', '.mp3', '.webm', '.mp4', '.ogg')), None)
        if audio is None:
            with yt_dlp.YoutubeDL({**options, 'skip_download': False, 'writesubtitles': False, 'writeautomaticsub': False}) as ydl:
                audio_info = ydl.extract_info(url, download=True)
                audio = Path(ydl.prepare_filename(audio_info))
        os.environ['NUMBA_CACHE_DIR'] = str(CACHE / 'numba-cache')
        import av
        import numpy as np
        import torch
        import whisper
        resampler = av.AudioResampler(format='fltp', layout='mono', rate=16000)
        samples = []
        with av.open(str(audio)) as container:
            for frame in container.decode(audio=0):
                samples.extend(f.to_ndarray().flatten() for f in resampler.resample(frame))
        samples.extend(f.to_ndarray().flatten() for f in resampler.resample(None))
        torch.set_num_threads(min(6, os.cpu_count() or 1))
        model = whisper.load_model(args.model, device='cpu', download_root=str(Path(args.model_dir).expanduser()))
        result = model.transcribe(np.concatenate(samples), language=None if args.language == 'auto' else args.language, fp16=False, verbose=False, condition_on_previous_text=False)
        rows = [{k: s[k] for k in ('start', 'end', 'text')} for s in result['segments']]
        evidence.update(source='local_whisper', model=args.model, language=result.get('language'), audio=str(audio))
    if not rows or not any(r['text'].strip() for r in rows):
        raise RuntimeError('未能获取可用字幕或语音内容，不能据此概括视频')
    evidence['segments'] = rows
    evidence_file.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    (dest / 'transcript.txt').write_text('\n'.join(f"[{stamp(r['start'])}] {r['text'].strip()}" for r in rows), encoding='utf-8')
    if args.frames:
        make_frames(url, dest, evidence.get('duration'))
    print(json.dumps({'evidence': str(evidence_file), 'source': evidence['source'], 'segments': len(rows)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
