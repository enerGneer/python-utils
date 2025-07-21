## Youtube downloader with yt-dlp

개인 용도로 만들어본 Youtube downloader.
yt-dlp 라이브러리 사용.

## 기능 요약

- 🎬 **동영상 다운로드**

  - 고화질 MP4 (bestvideo + bestaudio) 병합
  - 플레이리스트 전체 또는 첫 영상 선택 가능

- 🎵 **오디오 다운로드**

  - MP3 변환 (원본 최대 품질 또는 128kbps)
  - YouTube 썸네일 자동 추출 → JPG 변환 → 커버 아트 삽입

- ⏳ **진행률 표시**

  - 콘솔에 실시간 프로그레스 바
  - 다운로드 상태(`downloading`, `finished`, `error`) 별 안내

- 🗂️ **폴더 자동 열기**

  - 다운로드 완료 후 탐색기/파인더 자동 실행

- 🧹 **임시 파일 정리**
  - MP3 변환 후 10분 이내 생성된 썸네일 파일 자동 삭제

## 파일 메모

- ytb-proto : 처음으로 제작해 본 가장 간단한 버전.
- ytb-BAK : yt-dlp의 썸네일 다운로드 기능을 사용하려 했는데 간헐적으로 실패하는 바람에 일단 백업.
- ytb : 최종 버전. mutagen 라이브러리를 이용하는 방식으로 우회함.
