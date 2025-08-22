#!/usr/bin/env python3
"""
YouTube 다운로더 - yt-dlp 기반 (최적화 버전)
- 최대 품질 동영상/오디오 다운로드
- 진행률 표시(프로그레스 바)
- mutagen으로 썸네일 커버 아트 확실히 삽입
"""

import sys
import os
import subprocess
import time
import platform
from pathlib import Path
from typing import Optional, Dict, Any

import yt_dlp

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError


class YouTubeDownloader:
    def __init__(self, download_dir: Optional[str] = None):
        # 다운로드 폴더 설정
        if download_dir:
            base = Path(download_dir)
            self.video_dir = base / 'videos'
            self.music_dir = base / 'music'
        else:
            self.video_dir = self._get_default_video_dir()
            self.music_dir = self._get_default_music_dir()

        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.music_dir.mkdir(parents=True, exist_ok=True)

        # 진행률 후크 변수
        self._last_time = 0
        self._cur_file = ""
        self._printed = False
        # 다운로드된 MP3 리스트 (썸네일 청소용)
        self._downloaded_files = []

    def _get_default_video_dir(self) -> Path:
        if os.name == 'nt':
            up = os.environ.get('USERPROFILE', '')
            d = Path(up) / 'Videos'
            if d.exists(): return d
        return Path.home() / 'Videos'

    def _get_default_music_dir(self) -> Path:
        if os.name == 'nt':
            up = os.environ.get('USERPROFILE', '')
            d = Path(up) / 'Music'
            if d.exists(): return d
        return Path.home() / 'Music'

    def _progress_hook(self, d: Dict[str, Any]):
        now = time.time()
        if now - self._last_time < 0.2:
            return
        self._last_time = now

        status = d.get('status')
        if status == 'downloading':
            fn = os.path.basename(d.get('filename') or '')
            if fn != self._cur_file:
                self._cur_file = fn
                if self._printed:
                    print()
                print(f"📥 다운로드 중: {fn}")
                self._printed = False

            # ✅ None-safe 취득
            downloaded = d.get('downloaded_bytes') or 0
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            speed = d.get('speed') or 0.0
            eta   = d.get('eta') or 0

            if total:
                try:
                    percent = downloaded / total * 100
                except ZeroDivisionError:
                    percent = 0.0

                bar_len = 30
                filled = int(bar_len * (downloaded / total)) if total else 0
                bar = '█' * filled + '░' * (bar_len - filled)

                dl_mb = downloaded / (1024 ** 2)
                tot_mb = total / (1024 ** 2)
                speed_str = f"{speed/1024/1024:.1f}MB/s" if speed else "--MB/s"

                # ✅ eta None/비수치 방어
                try:
                    eta_m = int(eta // 60)
                    eta_s = int(eta % 60)
                    eta_str = f"{eta_m}:{eta_s:02d}"
                except Exception:
                    eta_str = "--:--"

                line = f"\r[{bar}] {percent:5.1f}% | {dl_mb:6.1f}/{tot_mb:6.1f}MB | {speed_str} | {eta_str}"
                print(line, end='', flush=True)
                self._printed = True
            else:
                dl_mb = downloaded / (1024 ** 2)
                speed_str = f"{speed/1024/1024:.1f}MB/s" if speed else "--MB/s"
                print(f"\r📥 다운로드 중... {dl_mb:6.1f}MB | {speed_str}", end='', flush=True)
                self._printed = True

        elif status == 'finished':
            if self._printed:
                print()
            fn = os.path.basename(d.get('filename') or '')
            size = d.get('total_bytes') or 0
            size_str = f" ({size/1024/1024:.1f}MB)" if size else ""
            print(f"✅ 완료: {fn}{size_str}")
            self._printed = False
            self._cur_file = ""

        elif status == 'error':
            if self._printed:
                print()
            print("❌ 다운로드 오류")
            self._printed = False

    def _cleanup_thumbs(self):
        now = time.time()
        for mp3 in self._downloaded_files:
            if mp3.suffix.lower() == '.mp3':
                stem = mp3.stem
                for ext in ('.webp','.jpg','.jpeg','.png'):
                    t = self.music_dir / f"{stem}{ext}"
                    if t.exists() and now - t.stat().st_mtime < 600:
                        t.unlink()
        self._downloaded_files.clear()

    def download_video(self, url: str, is_playlist: bool = False) -> bool:
        print(f"🎬 최대 품질 동영상 다운로드 → {self.video_dir}")
        opts = {
            **self._base_opts(),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'merge_output_format': 'mp4',
            'outtmpl': str(self.video_dir / '%(title)s.%(ext)s'),
            'noplaylist': not is_playlist,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            print("📁 폴더 열기...")
            self._open(self.video_dir)
            return True
        except Exception as e:
            print(f"❌ 실패: {e}")
            return False

    def download_audio(self, url: str, quality: str = '0', is_playlist: bool = False) -> bool:
        print(f"🎵 MP3 { '최대' if quality=='0' else quality+'kbps' } + 썸네일 → {self.music_dir}")
        opts = {
            **self._base_opts(),
            'format': 'bestaudio/best',
            'outtmpl': str(self.music_dir / '%(title)s.%(ext)s'),
            'noplaylist': not is_playlist,
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality},
                {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
                {'key': 'FFmpegMetadata', 'add_metadata': True},
            ]
        }
        try:
            before = set(self.music_dir.glob('*.mp3'))
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            after = set(self.music_dir.glob('*.mp3'))
            new = after - before
            self._downloaded_files.extend(new)

            # mutagen으로 확실하게 Embed
            for mp3 in new:
                jpg = self.music_dir / f"{mp3.stem}.jpg"
                if jpg.exists():
                    try:
                        audio = MP3(mp3, ID3=ID3)
                    except ID3NoHeaderError:
                        audio = MP3(mp3)
                        audio.add_tags()
                    with open(jpg, 'rb') as img:
                        audio.tags.add(APIC(
                            encoding=3, mime='image/jpeg',
                            type=3, desc='Cover', data=img.read()
                        ))
                    audio.save(v2_version=3)
                    # --- 여기서 트랙 번호(Track Number) 프레임만 삭제 ---
                    if audio.tags.getall('TRCK'):
                        audio.tags.delall('TRCK')
                        audio.save(v2_version=3)

            self._cleanup_thumbs()
            print("📁 폴더 열기...")
            self._open(self.music_dir)
            return True
        except Exception as e:
            print(f"❌ 실패: {e}")
            return False

    def _base_opts(self):
        return {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'progress_hooks': [self._progress_hook],
        }

    def _open(self, path: Path):
        system = platform.system()
        try:
            if system == "Windows": os.startfile(path)
            elif system == "Darwin": subprocess.run(["open", str(path)], check=True)
            elif system == "Linux": subprocess.run(["xdg-open", str(path)], check=True)
        except:
            pass


def validate_url(u: str) -> bool:
    return any(d in u for d in ('youtube.com','youtu.be'))

def is_playlist_url(u: str) -> bool:
    return 'list=' in u


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else input("📎 YouTube URL을 입력하세요: ").strip()
    if not validate_url(url):
        print("❌ 유효하지 않은 URL"); return

    dl = YouTubeDownloader()
    print(f"📁 비디오: {dl.video_dir}")
    print(f"🎵 음악: {dl.music_dir}")
    print("\n📥 다운로드 옵션:")
    print("1. 동영상 (최대 품질)")
    print("2. 음악 (MP3 + 최대품질 + 썸네일)")
    print("3. 음악 (MP3 + 128kbps + 썸네일)")
    ch = input("선택 (1-3): ").strip()

    is_playlist_download = False
    if is_playlist_url(url):
        print("\n🔍 플레이리스트가 감지되었습니다!")
        playlist_choice = input("📋 전체 다운로드? (Y/N, 기본값: N): ").strip().lower()
        is_playlist_download = playlist_choice in ['y', 'yes', '예', 'ㅇ']
        if is_playlist_download:
            print("✅ 플레이리스트 전체 다운로드")
        else:
            print("📹 첫 번째 동영상만 다운로드")

    if ch == '1':
        dl.download_video(url, is_playlist_download)
    elif ch == '2':
        dl.download_audio(url, '0', is_playlist_download)
    elif ch == '3':
        dl.download_audio(url, '128', is_playlist_download)
    else:
        print("❌ 잘못된 선택")


if __name__ == '__main__':
    try:
        import yt_dlp, mutagen
    except ImportError:
        print("❌ yt-dlp 및 mutagen 설치 필요: pip install yt-dlp mutagen")
        sys.exit(1)
    main()
