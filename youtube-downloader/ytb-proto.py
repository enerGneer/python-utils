#!/usr/bin/env python3
import os
from pathlib import Path
from yt_dlp import YoutubeDL

def get_library_path(kind: str) -> str:
    """
    Windows 기본 라이브러리 경로 반환
    kind: 'video' 또는 'audio'
    """
    home = Path.home()
    if os.name == 'nt':  # Windows
        return str(home / ('Videos' if kind == 'video' else 'Music'))
    # macOS/Linux fallback
    return str(home / ('Videos' if kind == 'video' else 'Music'))

def download_video(url: str, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "merge_output_format": "mp4",
        "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])

def download_audio(url: str, out_dir: str):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0",
        }],
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])

def main():
    url = input("📎 YouTube URL을 입력하세요: ").strip()
    print("다운로드 모드 선택:")
    print("  1) Audio (Music 라이브러리)")
    print("  2) Video (Videos 라이브러리)")
    choice = input("선택 (1/2): ").strip()

    if choice == "1":
        out_dir = get_library_path('audio')
        print(f"\n🎵 Music 라이브러리로 다운로드: {out_dir}")
        download_audio(url, out_dir)
    elif choice == "2":
        out_dir = get_library_path('video')
        print(f"\n🎬 Videos 라이브러리로 다운로드: {out_dir}")
        download_video(url, out_dir)
    else:
        print("❌ 잘못된 선택입니다. 1 또는 2를 입력하세요.")

if __name__ == "__main__":
    main()
