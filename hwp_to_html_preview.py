import html
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
PREVIEWS = ROOT / "previews"
PREVIEWS.mkdir(exist_ok=True)

# Reuse the extractor from the PDF preview script without running its batch block.
source = (ROOT / "hwp_to_pdf_preview.py").read_text(encoding="utf-8-sig")
source = source.split("failures = []")[0]
namespace = {"__file__": str(ROOT / "hwp_to_pdf_preview.py")}
exec(source, namespace)
extract_hwp_text = namespace["extract_hwp_text"]

STYLE = """
:root { color-scheme: light; }
body {
  margin: 0;
  padding: 28px;
  background: #ffffff;
  color: #172238;
  font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
  line-height: 1.72;
}
.header {
  position: sticky;
  top: 0;
  margin: -28px -28px 24px;
  padding: 20px 28px;
  background: #eef6ff;
  border-bottom: 1px solid #dbe3ef;
}
h1 { margin: 0; color: #0054a6; font-size: 22px; line-height: 1.35; }
.notice { margin: 8px 0 0; color: #657188; font-size: 13px; }
.content { white-space: pre-wrap; font-size: 14px; }
"""

for hwp in sorted(DOCS.glob("*.hwp")):
    try:
        text = extract_hwp_text(hwp)
    except Exception as exc:
        text = f"텍스트 미리보기를 생성하지 못했습니다. 원본 HWP 파일을 다운로드해 확인해 주세요.\n\n오류: {exc}"
    title = hwp.stem
    body = f"""<!doctype html>
<html lang=\"ko\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{html.escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <header class=\"header\">
    <h1>{html.escape(title)}</h1>
    <p class=\"notice\">웹앱 미리보기용 화면입니다. 원본 서식 확인은 HWP 다운로드 파일을 이용해 주세요.</p>
  </header>
  <main class=\"content\">{html.escape(text)}</main>
</body>
</html>
"""
    (PREVIEWS / f"{hwp.stem}.html").write_text(body, encoding="utf-8")
    print(f"OK {hwp.name}")

