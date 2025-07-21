#!/usr/bin/env python3
"""
YouTube 다운로더 - yt-dlp 기반 (썸네일 임베딩 수정 버전)
최대 품질 동영상/오디오 다운로드 + 썸네일 커버 아트 지원
"""

import sys
import os
import subprocess
import time
import platform
from pathlib import Path
from typing import Optional
import yt_dlp


class YouTubeDownloader:
    """YouTube 다운로더 클래스 (썸네일 임베딩 수정 버전)"""
    
    def __init__(self, download_dir: Optional[str] = None):
        """
        초기화
        
        Args:
            download_dir: 다운로드 디렉토리 경로 (None이면 기본 폴더 사용)
        """
        if download_dir is None:
            self.video_dir = self._get_default_video_dir()
            self.music_dir = self._get_default_music_dir()
        else:
            download_dir = Path(download_dir)
            self.video_dir = download_dir / 'videos'
            self.music_dir = download_dir / 'music'
        
        # 디렉토리 생성
        self.video_dir.mkdir(exist_ok=True)
        self.music_dir.mkdir(exist_ok=True)
        
        # 다운로드된 파일 추적 (썸네일 정리용)
        self._downloaded_files = []
        
        # 의존성 확인
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """필수 의존성 확인"""
        try:
            import PIL
            print("✅ Pillow 라이브러리 확인됨 (썸네일 처리용)")
        except ImportError:
            print("⚠️  Pillow 라이브러리가 없습니다. 썸네일 임베딩에 문제가 발생할 수 있습니다.")
            print("설치: pip install Pillow")
    
    def _get_default_video_dir(self) -> Path:
        """OS별 기본 비디오 폴더 경로 반환"""
        if os.name == 'nt':  # Windows
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                videos_dir = Path(user_profile) / 'Videos'
                if videos_dir.exists():
                    return videos_dir
        return Path.home() / 'Videos'
    
    def _get_default_music_dir(self) -> Path:
        """OS별 기본 음악 폴더 경로 반환"""
        if os.name == 'nt':  # Windows
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                music_dir = Path(user_profile) / 'Music'
                if music_dir.exists():
                    return music_dir
        return Path.home() / 'Music'
    
    def _open_folder(self, folder_path: Path) -> bool:
        """OS별 탐색기/파인더 열기"""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(folder_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(folder_path)], check=True)
            elif system == "Linux":
                subprocess.run(["xdg-open", str(folder_path)], check=True)
            else:
                return False
            return True
        except Exception:
            return False
    
    def _cleanup_thumbnail_files(self) -> None:
        """다운로드된 MP3 파일과 매칭되는 썸네일 파일만 안전하게 정리"""
        try:
            if not self._downloaded_files:
                return
            
            current_time = time.time()
            thumbnail_extensions = ['.webp', '.jpg', '.jpeg', '.png']
            removed_count = 0
            
            for downloaded_file in self._downloaded_files:
                if downloaded_file.suffix.lower() == '.mp3':
                    base_name = downloaded_file.stem
                    
                    for ext in thumbnail_extensions:
                        potential_thumbnail = self.music_dir / f"{base_name}{ext}"
                        
                        if potential_thumbnail.exists():
                            try:
                                file_mtime = potential_thumbnail.stat().st_mtime
                                if (current_time - file_mtime) <= 600:  # 10분 이내
                                    potential_thumbnail.unlink()
                                    removed_count += 1
                                    print(f"🧹 썸네일 정리: {potential_thumbnail.name}")
                            except Exception:
                                pass
            
            if removed_count > 0:
                print(f"✨ 총 {removed_count}개 썸네일 파일 정리 완료")
            
            self._downloaded_files.clear()
                
        except Exception:
            pass
    
    def download_video(self, url: str, is_playlist: bool = False) -> bool:
        """
        동영상 다운로드 (최대 품질)
        
        Args:
            url: YouTube URL
            is_playlist: 플레이리스트 다운로드 여부
            
        Returns:
            bool: 성공 여부
        """
        print(f"🎬 최대 품질 동영상 다운로드")
        print(f"📁 저장 위치: {self.video_dir}")
        
        options = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': str(self.video_dir / '%(title)s.%(ext)s'),
            'noplaylist': not is_playlist,
        }
        
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            
            print(f"\n✅ 다운로드 완료! 📁 폴더 열기...")
            self._open_folder(self.video_dir)
            return True
            
        except Exception as e:
            print(f"\n❌ 다운로드 실패: {e}")
            return False
    
    def download_audio(self, url: str, quality: str = '0', is_playlist: bool = False) -> bool:
        """
        MP3 오디오 다운로드 (원본 최고 음질) + 썸네일 커버 아트
        
        Args:
            url: YouTube URL
            quality: 음질 설정 ('0': 최대품질, '128': 128kbps)
            is_playlist: 플레이리스트 다운로드 여부
            
        Returns:
            bool: 성공 여부
        """
        if quality == '0':
            print(f"🎵 MP3 최대 품질 + 썸네일 커버 아트")
        else:
            print(f"🎵 MP3 {quality}kbps + 썸네일 커버 아트")
        print(f"📁 저장 위치: {self.music_dir}")
        
        # 방법 1: 명시적 EmbedThumbnail 사용
        options_method1 = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.music_dir / '%(title)s.%(ext)s'),
            'noplaylist': not is_playlist,
            'writethumbnail': True,
            'writeinfojson': False,  # 불필요한 JSON 파일 생성 방지
            'ignoreerrors': False,  # 에러 발생시 중단
            'overwrites': True,  # 기존 파일 덮어쓰기
            'verbose': False,  # 상세 로그 (디버깅용)
            'postprocessors': [
                # 1단계: 오디오 추출
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                },
                # 2단계: 썸네일 임베딩 (명시적)
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                },
                # 3단계: 메타데이터 추가
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }
            ]
        }
        
        # 방법 2: 썸네일 없이 다운로드 후 수동 처리 (백업)
        options_method2 = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.music_dir / '%(title)s.%(ext)s'),
            'noplaylist': not is_playlist,
            'writethumbnail': True,  # 썸네일 파일만 저장
            'writeinfojson': False,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }
            ]
        }
        
        try:
            # 다운로드 전 파일 목록 저장
            existing_files = set(self.music_dir.glob('*.mp3'))
            
            print("🔄 다운로드 시작 (방법 1: 자동 썸네일 임베딩)...")
            
            try:
                # 방법 1 시도
                with yt_dlp.YoutubeDL(options_method1) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        if is_playlist:
                            print(f"📋 플레이리스트: {len(info['entries'])}개 항목")
                        else:
                            print(f"📹 첫 번째 항목만 다운로드")
                    else:
                        print(f"🎵 제목: {info.get('title', 'Unknown')}")
                        if info.get('thumbnail'):
                            print(f"🖼️  썸네일: 자동 임베딩 예정")
                    
                    # 실제 다운로드
                    print("🔄 다운로드 실행 중...")
                    ydl.download([url])
                    print("✅ 방법 1 성공: 썸네일 자동 임베딩 완료")
                    
            except Exception as e1:
                print(f"⚠️  방법 1 실패: {e1}")
                print("🔄 방법 2 시도: 썸네일 별도 처리...")
                
                # 방법 2 시도
                with yt_dlp.YoutubeDL(options_method2) as ydl:
                    ydl.download([url])
                    print("✅ 방법 2 성공: 오디오 다운로드 완료 (썸네일 별도 저장)")
            
            # 잠시 대기 (파일 시스템 동기화)
            time.sleep(1)
            
            # 새로 생성된 파일 찾기
            new_files = set(self.music_dir.glob('*.mp3')) - existing_files
            self._downloaded_files.extend(new_files)
            
            # 다운로드된 파일 확인
            if new_files:
                for file in new_files:
                    print(f"✅ 생성된 파일: {file.name}")
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"📦 파일 크기: {size_mb:.1f}MB")
                    
                    # 썸네일 임베딩 확인
                    has_thumbnail = self._check_embedded_thumbnail(file)
                    
                    # 썸네일이 없다면 수동으로 임베딩 시도
                    if not has_thumbnail:
                        print(f"🔧 수동 썸네일 임베딩 시도: {file.name}")
                        success = self._manual_embed_thumbnail(file)
                        if success:
                            print(f"✅ 수동 썸네일 임베딩 성공!")
                        else:
                            print(f"❌ 수동 썸네일 임베딩 실패")
                    else:
                        print(f"✅ 썸네일 이미 임베딩됨")
            else:
                print("❌ 새로 생성된 MP3 파일을 찾을 수 없습니다.")
                # 최근 파일 확인
                recent_files = []
                for ext in ['*.mp3', '*.webm', '*.m4a']:
                    for file in self.music_dir.glob(ext):
                        if (time.time() - file.stat().st_mtime) < 300:  # 5분 이내
                            recent_files.append(file)
                
                if recent_files:
                    print("🔍 최근 생성된 파일들:")
                    for file in recent_files:
                        print(f"  📄 {file.name}")
                
            # 썸네일 정리
            self._cleanup_thumbnail_files()
            
            print(f"\n✅ 다운로드 완료! 📁 폴더 열기...")
            self._open_folder(self.music_dir)
            return True
            
        except Exception as e:
            print(f"\n❌ 다운로드 실패: {e}")
            print(f"🔍 에러 타입: {type(e).__name__}")
            
            # 일반적인 문제들 진단
            print("\n🔧 문제 진단:")
            
            # 1. 네트워크 연결 확인
            try:
                import urllib.request
                urllib.request.urlopen('https://www.youtube.com', timeout=5)
                print("✅ 인터넷 연결 정상")
            except:
                print("❌ 인터넷 연결 문제")
            
            # 2. 동일한 파일명 존재 확인
            if 'already exists' in str(e).lower() or 'file exists' in str(e).lower():
                print("⚠️  동일한 파일명이 이미 존재할 수 있습니다")
                print("💡 해결방법: 기존 파일을 삭제하거나 이름을 변경하세요")
            
            # 3. FFmpeg 프로세스 확인
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ffmpeg.exe'], 
                                      capture_output=True, text=True, timeout=5)
                if 'ffmpeg.exe' in result.stdout:
                    print("⚠️  FFmpeg 프로세스가 실행 중일 수 있습니다")
                    print("💡 해결방법: 작업관리자에서 ffmpeg 프로세스를 종료하세요")
            except:
                pass
            
            # 4. 디스크 공간 확인
            try:
                import shutil
                free_space = shutil.disk_usage(self.music_dir).free / (1024**3)  # GB
                if free_space < 1:
                    print(f"⚠️  디스크 공간 부족: {free_space:.1f}GB 남음")
                else:
                    print(f"✅ 디스크 공간 충분: {free_space:.1f}GB 남음")
            except:
                pass
            
            print("\n🔧 트러블슈팅 팁:")
            print("  1. 다른 YouTube URL로 테스트해보세요")
            print("  2. 디버그 모드(옵션 4)로 재시도해보세요")
            print("  3. yt-dlp 업데이트: pip install -U yt-dlp")
            print("  4. 컴퓨터 재시작 후 다시 시도해보세요")
            return False
    
    def download_audio_debug(self, url: str, quality: str = '0', is_playlist: bool = False) -> bool:
        """
        디버그 모드 MP3 다운로드 (상세 로그 포함)
        
        Args:
            url: YouTube URL
            quality: 음질 설정 ('0': 최대품질, '128': 128kbps)
            is_playlist: 플레이리스트 다운로드 여부
            
        Returns:
            bool: 성공 여부
        """
        print(f"🔍 디버그 모드: MP3 다운로드 (상세 로그)")
        print(f"📁 저장 위치: {self.music_dir}")
        
        # 디버그 옵션 - 상세 로그 활성화
        options = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.music_dir / '%(title)s.%(ext)s'),
            'noplaylist': not is_playlist,
            'writethumbnail': True,
            'writeinfojson': False,
            'verbose': True,  # 상세 로그 활성화
            'postprocessors': [
                # 1단계: 오디오 추출
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                },
                # 2단계: 썸네일 임베딩 (명시적으로 추가)
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                },
                # 3단계: 메타데이터 추가
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }
            ]
        }
        
        try:
            existing_files = set(self.music_dir.glob('*.mp3'))
            
            print("🔄 디버그 다운로드 시작 (상세 로그 출력)...")
            print("=" * 60)
            
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 상세 정보 출력
                if 'entries' in info:
                    if is_playlist:
                        print(f"📋 플레이리스트: {len(info['entries'])}개 항목")
                    else:
                        print(f"📹 첫 번째 항목만 다운로드")
                        info = info['entries'][0]
                else:
                    print(f"🎵 제목: {info.get('title', 'Unknown')}")
                    print(f"🔗 원본 URL: {info.get('webpage_url', 'Unknown')}")
                    print(f"⏱️  길이: {info.get('duration', 0)}초")
                    print(f"👁️  조회수: {info.get('view_count', 'Unknown')}")
                    
                    if info.get('thumbnail'):
                        print(f"🖼️  썸네일 URL: {info['thumbnail']}")
                    
                    # 사용 가능한 포맷 정보
                    if info.get('formats'):
                        best_audio = None
                        for fmt in info['formats']:
                            if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                                best_audio = fmt
                                break
                        
                        if best_audio:
                            print(f"🎵 선택된 오디오 포맷:")
                            print(f"   - 포맷 ID: {best_audio.get('format_id')}")
                            print(f"   - 확장자: {best_audio.get('ext')}")
                            print(f"   - 비트레이트: {best_audio.get('abr', 'Unknown')}kbps")
                            print(f"   - 코덱: {best_audio.get('acodec')}")
                
                print("=" * 60)
                print("🔄 실제 다운로드 시작...")
                
                # 실제 다운로드
                ydl.download([url])
                
                print("=" * 60)
                print("✅ yt-dlp 다운로드 완료!")
            
            print("🔍 다운로드된 파일 확인 중...")
            
            # 새로 생성된 파일 확인
            new_files = set(self.music_dir.glob('*.mp3')) - existing_files
            self._downloaded_files.extend(new_files)
            
            print(f"📊 새로 생성된 MP3 파일: {len(new_files)}개")
            
            if new_files:
                for file in new_files:
                    print(f"✅ 생성된 파일: {file.name}")
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"📦 파일 크기: {size_mb:.1f}MB")
                    
                    # 상세 썸네일 확인
                    print(f"🔍 썸네일 임베딩 확인 중...")
                    has_thumbnail = self._detailed_thumbnail_check(file)
                    
                    if not has_thumbnail:
                        print(f"🔧 수동 썸네일 임베딩 시도...")
                        success = self._manual_embed_thumbnail(file)
                        
                        if success:
                            # 재확인
                            print(f"🔍 수동 임베딩 후 재확인...")
                            self._detailed_thumbnail_check(file)
                        else:
                            print(f"❌ 수동 썸네일 임베딩 실패")
                    else:
                        print(f"✅ 썸네일 임베딩 확인됨!")
            else:
                print("❌ 새로 생성된 MP3 파일이 없습니다!")
                print("🔍 현재 음악 폴더의 모든 MP3 파일:")
                all_mp3s = list(self.music_dir.glob('*.mp3'))
                for mp3 in all_mp3s[-5:]:  # 최근 5개만 표시
                    print(f"  📄 {mp3.name}")
            
            print("🔍 썸네일 파일 확인:")
            thumbnails = list(self.music_dir.glob('*.webp')) + list(self.music_dir.glob('*.jpg')) + list(self.music_dir.glob('*.png'))
            for thumb in thumbnails:
                print(f"  🖼️  {thumb.name}")
            
            # 썸네일 정리
            print("🧹 썸네일 파일 정리...")
            self._cleanup_thumbnail_files()
            
            print(f"\n✅ 디버그 다운로드 완료! 📁 폴더 열기...")
            self._open_folder(self.music_dir)
            return True
            
        except Exception as e:
            print(f"\n❌ 디버그 다운로드 실패: {e}")
            print(f"🔍 에러 타입: {type(e).__name__}")
            import traceback
            print("🔍 상세 에러 정보:")
            traceback.print_exc()
            
            # 부분적으로라도 다운로드된 파일이 있는지 확인
            print("\n🔍 부분 다운로드 파일 확인:")
            all_files = list(self.music_dir.glob('*'))
            recent_files = [f for f in all_files if (time.time() - f.stat().st_mtime) < 300]  # 5분 이내
            
            for file in recent_files:
                print(f"  📄 {file.name} ({file.stat().st_size / 1024:.1f}KB)")
                
            return False
    
    def _detailed_thumbnail_check(self, mp3_file: Path) -> bool:
        """상세한 썸네일 임베딩 확인"""
        try:
            # 비디오 스트림 확인
            result1 = subprocess.run([
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0', 
                '-show_entries', 'stream=codec_name,width,height', 
                '-of', 'csv=p=0', str(mp3_file)
            ], capture_output=True, text=True, timeout=10)
            
            # 첨부된 이미지 확인
            result2 = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'stream=codec_name,disposition', 
                '-of', 'json', str(mp3_file)
            ], capture_output=True, text=True, timeout=10)
            
            print(f"📊 FFprobe 결과:")
            print(f"   비디오 스트림: {result1.stdout.strip() if result1.stdout.strip() else '없음'}")
            
            if result2.returncode == 0 and result2.stdout:
                import json
                data = json.loads(result2.stdout)
                streams = data.get('streams', [])
                
                for i, stream in enumerate(streams):
                    print(f"   스트림 {i}: {stream.get('codec_name', 'unknown')}")
                    if stream.get('disposition', {}).get('attached_pic'):
                        print(f"     → 첨부된 이미지 발견!")
                        return True
            
            return result1.returncode == 0 and bool(result1.stdout.strip())
            
        except Exception as e:
            print(f"❓ 상세 썸네일 확인 오류: {e}")
            return False
    
    def _check_embedded_thumbnail(self, mp3_file: Path) -> bool:
        """MP3 파일에 썸네일이 임베딩되었는지 확인"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0', 
                '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', 
                str(mp3_file)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"🖼️  썸네일 임베딩 확인됨: {mp3_file.name}")
                return True
            else:
                print(f"⚠️  썸네일 임베딩 없음: {mp3_file.name}")
                return False
                
        except Exception:
            print(f"❓ 썸네일 상태 확인 불가: {mp3_file.name}")
            return False
    
    def _manual_embed_thumbnail(self, mp3_file: Path) -> bool:
        """수동으로 썸네일을 MP3 파일에 임베딩"""
        temp_mp3 = None
        try:
            # 같은 이름의 썸네일 파일 찾기
            base_name = mp3_file.stem
            thumbnail_extensions = ['.webp', '.jpg', '.jpeg', '.png']
            thumbnail_file = None
            
            for ext in thumbnail_extensions:
                potential_thumb = mp3_file.parent / f"{base_name}{ext}"
                if potential_thumb.exists():
                    thumbnail_file = potential_thumb
                    print(f"🔍 썸네일 파일 발견: {thumbnail_file.name}")
                    break
            
            if not thumbnail_file:
                print(f"❌ 썸네일 파일을 찾을 수 없습니다: {base_name}")
                return False
            
            # 임시 파일명 생성
            temp_mp3 = mp3_file.with_suffix('.temp.mp3')
            
            # FFmpeg로 썸네일 임베딩
            cmd = [
                'ffmpeg', '-y',  # 덮어쓰기 허용
                '-i', str(mp3_file),  # 입력 MP3
                '-i', str(thumbnail_file),  # 입력 썸네일
                '-map', '0:0',  # 첫 번째 파일의 오디오 스트림
                '-map', '1:0',  # 두 번째 파일의 이미지 스트림
                '-c:a', 'copy',  # 오디오 재인코딩 하지 않음
                '-c:v', 'mjpeg',  # 이미지를 JPEG로 변환
                '-id3v2_version', '3',  # ID3v2.3 사용
                '-metadata:s:v', 'title=Album cover',
                '-metadata:s:v', 'comment=Cover (front)',
                '-disposition:v', 'attached_pic',  # 첨부된 그림으로 표시
                str(temp_mp3)
            ]
            
            print(f"🔧 FFmpeg 명령어 실행 중...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # 성공시 원본 파일 교체
                mp3_file.unlink()
                temp_mp3.rename(mp3_file)
                print(f"✅ 수동 썸네일 임베딩 성공: {mp3_file.name}")
                
                # 썸네일 파일 삭제
                thumbnail_file.unlink()
                print(f"🧹 썸네일 파일 정리: {thumbnail_file.name}")
                
                return True
            else:
                print(f"❌ FFmpeg 실행 실패:")
                print(f"   stdout: {result.stdout}")
                print(f"   stderr: {result.stderr}")
                
                # 임시 파일 정리
                if temp_mp3 and temp_mp3.exists():
                    temp_mp3.unlink()
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ FFmpeg 실행 시간 초과")
            if temp_mp3 and temp_mp3.exists():
                temp_mp3.unlink()
            return False
        except Exception as e:
            print(f"❌ 수동 썸네일 임베딩 오류: {e}")
            if temp_mp3 and temp_mp3.exists():
                temp_mp3.unlink()
            return False


def validate_url(url: str) -> bool:
    """URL 유효성 검증"""
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
    return any(domain in url for domain in youtube_domains)


def is_playlist_url(url: str) -> bool:
    """플레이리스트 URL인지 확인"""
    return 'list=' in url


def check_ffmpeg() -> bool:
    """FFmpeg 설치 확인"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        print("✅ FFmpeg 확인됨")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg를 찾을 수 없습니다.")
        print("🔧 FFmpeg 설치 필요:")
        print("  Windows: https://ffmpeg.org/download.html")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt install ffmpeg")
        return False


def main():
    """메인 함수"""
    print("🎬 YouTube 다운로더 (썸네일 임베딩 수정 버전)")
    print("=" * 50)
    
    # FFmpeg 확인
    if not check_ffmpeg():
        return
    
    # URL 입력
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if not url:
        url = input("📎 YouTube URL을 입력하세요: ").strip()
    
    if not validate_url(url):
        print("❌ 유효하지 않은 YouTube URL입니다.")
        return
    
    # 다운로더 인스턴스 생성
    downloader = YouTubeDownloader()
    
    print(f"📁 비디오: {downloader.video_dir}")
    print(f"🎵 음악: {downloader.music_dir}")
    
    # 다운로드 옵션 선택
    print("\n📥 다운로드 옵션:")
    print("1. 동영상 (최대 품질)")
    print("2. 음악 (MP3 + 최대품질 + 썸네일)")
    print("3. 음악 (MP3 + 128kbps + 썸네일)")
    print("4. 디버그 모드 (상세 로그 + 썸네일)")
    
    choice = input("\n선택 (1-4): ").strip()
    
    # 플레이리스트 확인
    is_playlist_download = False
    if is_playlist_url(url):
        print("\n🔍 플레이리스트가 감지되었습니다!")
        playlist_choice = input("📋 전체 다운로드? (Y/N, 기본값: N): ").strip().lower()
        is_playlist_download = playlist_choice in ['y', 'yes', '예', 'ㅇ']
        
        if is_playlist_download:
            print("✅ 플레이리스트 전체 다운로드")
        else:
            print("📹 첫 번째 동영상만 다운로드")
    
    # 다운로드 실행
    print()  # 공백 줄
    
    if choice == '1':
        downloader.download_video(url, is_playlist=is_playlist_download)
        
    elif choice == '2':
        downloader.download_audio(url, quality='0', is_playlist=is_playlist_download)
        
    elif choice == '3':
        downloader.download_audio(url, quality='128', is_playlist=is_playlist_download)
        
    elif choice == '4':
        print("🔍 디버그 모드: 상세 로그와 함께 다운로드")
        downloader.download_audio_debug(url, quality='0', is_playlist=is_playlist_download)
        
    else:
        print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    # 필수 의존성 확인
    try:
        import yt_dlp
    except ImportError:
        print("❌ yt-dlp가 설치되지 않았습니다.")
        print("설치: pip install yt-dlp")
        sys.exit(1)
    
    # 도움말
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("🎬 YouTube 다운로더 (썸네일 임베딩 수정 버전)")
        print("=" * 40)
        print("사용법:")
        print("  python script.py [URL]")
        print("\n📁 저장 위치:")
        print("  - 비디오: ~/Videos")
        print("  - 음악: ~/Music")
        print("\n🎨 특징:")
        print("  - 개선된 썸네일 임베딩")
        print("  - 자동 썸네일 커버 아트")
        print("  - 완료 후 폴더 자동 열기")
        print("  - 다양한 음질 옵션")
        print("\n🎵 음질 옵션:")
        print("  - 최대품질: 원본 음질 유지")
        print("  - 128kbps: 작은 파일 크기")
        print("\n필수 요구사항:")
        print("  - yt-dlp: pip install yt-dlp")
        print("  - FFmpeg: 시스템 설치 필요")
        print("  - Pillow: pip install Pillow (권장)")
        sys.exit(0)
    
    main()