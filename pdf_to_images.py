from pathlib import Path
from pdf2image import convert_from_path

ROOT = Path(__file__).resolve().parent
PDFS = ROOT / "pdfs"
OUT = ROOT / "preview-images"
POPPLER = Path(r"C:\Users\76232\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin")
OUT.mkdir(exist_ok=True)

for pdf in sorted(PDFS.glob("*.pdf")):
    folder = OUT / pdf.stem
    folder.mkdir(exist_ok=True)
    for old in folder.glob("*.png"):
        old.unlink()
    pages = convert_from_path(str(pdf), dpi=130, fmt="png", poppler_path=str(POPPLER))
    for idx, page in enumerate(pages, 1):
        path = folder / f"page-{idx:03}.png"
        page.save(path, "PNG")
    print(f"OK {pdf.name}: {len(pages)} pages")
