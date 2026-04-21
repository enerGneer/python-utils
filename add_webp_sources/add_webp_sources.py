"""
HTML 파일의 jpg 이미지에 WebP <source> 태그를 추가합니다.

처리 대상 파일은 아래 TARGETS 목록에 직접 추가하세요.
커맨드라인 인수가 있는 경우에는 그쪽을 우선합니다.

사용법:
    python3 scripts/add_webp_sources.py          # TARGETS 목록 사용
    python3 scripts/add_webp_sources.py index.html contact/index.html
"""

import re
import sys
from pathlib import Path

# ── 처리할 파일 목록 ──────────────────────────────────────────
TARGETS = [
    "index.html",
    # "contact/index.html",
    # "about/index.html",
]
# ─────────────────────────────────────────────────────────────


def add_webp_sources(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"[SKIP] ファイルが見つかりません: {file_path}")
        return

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    result = []
    in_picture = False
    in_comment = False

    for line in lines:
        # マルチライン HTML コメント管理
        if not in_comment and "<!--" in line:
            if "-->" not in line:
                in_comment = True
            result.append(line)
            continue

        if in_comment:
            if "-->" in line:
                in_comment = False
            result.append(line)
            continue

        # <picture> コンテキスト追跡
        if "<picture>" in line:
            in_picture = True
            result.append(line)
            continue

        if "</picture>" in line:
            in_picture = False
            result.append(line)
            continue

        if in_picture:
            # <source srcset="*.jpg"> → webp source を上に追加
            if re.search(r"<source\s", line) and '.jpg"' in line:
                webp_line = line.replace('.jpg"', '.webp"', 1).rstrip()
                if webp_line.endswith(">"):
                    webp_line = webp_line[:-1] + ' type="image/webp">'
                result.append(webp_line)
                result.append(line)
                continue

            # <img src="*.jpg"> → webp source を上に追加
            m = re.match(r'^(\s*)<img\s+src="([^"]+\.jpg)"', line)
            if m:
                indent, jpg_src = m.group(1), m.group(2)
                webp_src = jpg_src.replace(".jpg", ".webp")
                result.append(f'{indent}<source srcset="{webp_src}" type="image/webp">')
                result.append(line)
                continue
        else:
            # standalone <img src="*.jpg"> → <picture> でラップ
            m = re.match(r'^(\s*)<img\s+src="([^"]+\.jpg)"', line)
            if m:
                indent, jpg_src = m.group(1), m.group(2)
                webp_src = jpg_src.replace(".jpg", ".webp")
                child_indent = indent + "    "
                result.append(f"{indent}<picture>")
                result.append(f'{child_indent}<source srcset="{webp_src}" type="image/webp">')
                result.append(f'{child_indent}{line.lstrip()}')
                result.append(f"{indent}</picture>")
                continue

        result.append(line)

    path.write_text("\n".join(result), encoding="utf-8")
    print(f"[OK] {file_path}")


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else TARGETS
    for t in targets:
        add_webp_sources(t)
