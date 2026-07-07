import os
import re
import struct
import zlib
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
PDFS = ROOT / "pdfs"
PDFS.mkdir(exist_ok=True)

FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
DIFSECT = 0xFFFFFFFC

class CFB:
    def __init__(self, path):
        self.data = Path(path).read_bytes()
        if self.data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            raise ValueError("not a compound file")
        self.sector_size = 1 << struct.unpack_from("<H", self.data, 30)[0]
        self.mini_sector_size = 1 << struct.unpack_from("<H", self.data, 32)[0]
        self.dir_start = struct.unpack_from("<I", self.data, 48)[0]
        self.mini_cutoff = struct.unpack_from("<I", self.data, 56)[0]
        self.mini_fat_start = struct.unpack_from("<I", self.data, 60)[0]
        self.mini_fat_count = struct.unpack_from("<I", self.data, 64)[0]
        self.difat_start = struct.unpack_from("<I", self.data, 68)[0]
        self.difat_count = struct.unpack_from("<I", self.data, 72)[0]
        self.difat = [x for x in struct.unpack_from("<109I", self.data, 76) if x not in (FREESECT, ENDOFCHAIN)]
        self._read_extra_difat()
        self.fat = self._read_fat()
        self.dirs = self._read_dirs()
        self.root = self.dirs[0]
        self.mini_stream = self._read_chain(self.root["start"], self.root["size"]) if self.root["start"] != ENDOFCHAIN else b""
        self.mini_fat = self._read_mini_fat()

    def sector_offset(self, sid):
        return 512 + sid * self.sector_size

    def sector(self, sid):
        off = self.sector_offset(sid)
        return self.data[off:off + self.sector_size]

    def _read_extra_difat(self):
        sid = self.difat_start
        for _ in range(self.difat_count):
            if sid in (FREESECT, ENDOFCHAIN):
                break
            sec = self.sector(sid)
            vals = struct.unpack("<" + "I" * (self.sector_size // 4), sec)
            self.difat.extend([x for x in vals[:-1] if x not in (FREESECT, ENDOFCHAIN)])
            sid = vals[-1]

    def _read_fat(self):
        raw = b"".join(self.sector(sid) for sid in self.difat if sid not in (FREESECT, ENDOFCHAIN))
        return list(struct.unpack("<" + "I" * (len(raw) // 4), raw))

    def _read_chain(self, start, size=None):
        if start in (FREESECT, ENDOFCHAIN):
            return b""
        out = bytearray()
        sid = start
        seen = set()
        while sid not in (FREESECT, ENDOFCHAIN) and sid not in seen and sid < len(self.fat):
            seen.add(sid)
            out.extend(self.sector(sid))
            sid = self.fat[sid]
        data = bytes(out)
        return data[:size] if size is not None else data

    def _read_dirs(self):
        raw = self._read_chain(self.dir_start)
        dirs = []
        for i in range(0, len(raw), 128):
            ent = raw[i:i + 128]
            if len(ent) < 128:
                continue
            name_len = struct.unpack_from("<H", ent, 64)[0]
            name = ent[:max(0, name_len - 2)].decode("utf-16le", errors="ignore")
            obj_type = ent[66]
            left, right, child = struct.unpack_from("<III", ent, 68)
            start = struct.unpack_from("<I", ent, 116)[0]
            size = struct.unpack_from("<Q", ent, 120)[0]
            dirs.append({"name": name, "type": obj_type, "left": left, "right": right, "child": child, "start": start, "size": size})
        return dirs

    def _read_mini_fat(self):
        if self.mini_fat_start in (FREESECT, ENDOFCHAIN):
            return []
        raw = self._read_chain(self.mini_fat_start, self.mini_fat_count * self.sector_size)
        return list(struct.unpack("<" + "I" * (len(raw) // 4), raw)) if raw else []

    def _read_mini_chain(self, start, size):
        out = bytearray()
        sid = start
        seen = set()
        while sid not in (FREESECT, ENDOFCHAIN) and sid not in seen and sid < len(self.mini_fat):
            seen.add(sid)
            off = sid * self.mini_sector_size
            out.extend(self.mini_stream[off:off + self.mini_sector_size])
            sid = self.mini_fat[sid]
        return bytes(out)[:size]

    def paths(self):
        result = {}
        def walk(idx, prefix):
            if idx in (FREESECT, ENDOFCHAIN) or idx >= len(self.dirs):
                return
            ent = self.dirs[idx]
            walk(ent["left"], prefix)
            path = prefix + [ent["name"]]
            if ent["type"] == 2:
                result["/".join(path)] = ent
            if ent["child"] not in (FREESECT, ENDOFCHAIN):
                walk(ent["child"], path)
            walk(ent["right"], prefix)
        walk(self.root["child"], [])
        return result

    def open_stream(self, path):
        ent = self.paths()[path]
        if ent["size"] < self.mini_cutoff and ent["start"] != ENDOFCHAIN:
            return self._read_mini_chain(ent["start"], ent["size"])
        return self._read_chain(ent["start"], ent["size"])

def hwp_is_compressed(cfb):
    header = cfb.open_stream("FileHeader")
    flags = struct.unpack_from("<I", header, 36)[0]
    return bool(flags & 1)

def clean_text(text):
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_hwp_text(path):
    cfb = CFB(path)
    compressed = hwp_is_compressed(cfb)
    pieces = []
    for stream_path in sorted([p for p in cfb.paths() if p.startswith("BodyText/Section")]):
        raw = cfb.open_stream(stream_path)
        if compressed:
            try:
                raw = zlib.decompress(raw, -15)
            except zlib.error:
                raw = zlib.decompress(raw)
        pos = 0
        while pos + 4 <= len(raw):
            header = struct.unpack_from("<I", raw, pos)[0]
            pos += 4
            tag_id = header & 0x3ff
            size = (header >> 20) & 0xfff
            if size == 0xfff:
                if pos + 4 > len(raw):
                    break
                size = struct.unpack_from("<I", raw, pos)[0]
                pos += 4
            payload = raw[pos:pos + size]
            pos += size
            if tag_id == 67:
                text = payload.decode("utf-16le", errors="ignore")
                text = text.replace("\r", "\n")
                pieces.append(text)
    return clean_text("\n".join(pieces))

def wrap_text(text, max_chars=58):
    lines = []
    for para in text.splitlines():
        para = para.strip()
        if not para:
            lines.append("")
            continue
        while len(para) > max_chars:
            cut = para.rfind(" ", 0, max_chars)
            if cut < 20:
                cut = max_chars
            lines.append(para[:cut].strip())
            para = para[cut:].strip()
        lines.append(para)
    return lines

def register_font():
    candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf"),
    ]
    for font in candidates:
        if font.exists():
            pdfmetrics.registerFont(TTFont("Korean", str(font)))
            return "Korean"
    return "Helvetica"

def write_pdf(text, source_name, pdf_path):
    font = register_font()
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    margin_x = 18 * mm
    y = height - 18 * mm
    line_height = 13
    c.setTitle(source_name)
    c.setFont(font, 14)
    c.drawString(margin_x, y, source_name.replace(".hwp", ""))
    y -= 18
    c.setFont(font, 9)
    c.drawString(margin_x, y, "브라우저 미리보기용 PDF입니다. 원본 서식 확인은 HWP 다운로드 파일을 이용해 주세요.")
    y -= 18
    c.setFont(font, 10)
    for line in wrap_text(text or "텍스트를 추출하지 못했습니다. 원본 HWP 파일을 다운로드해 확인해 주세요."):
        if y < 18 * mm:
            c.showPage()
            c.setFont(font, 10)
            y = height - 18 * mm
        c.drawString(margin_x, y, line)
        y -= line_height
    c.save()

failures = []
for hwp in sorted(DOCS.glob("*.hwp")):
    pdf = PDFS / (hwp.stem + ".pdf")
    try:
        text = extract_hwp_text(hwp)
        write_pdf(text, hwp.name, pdf)
        print(f"OK {hwp.name} -> {pdf.name} ({len(text)} chars)")
    except Exception as exc:
        failures.append((hwp.name, str(exc)))
        write_pdf("", hwp.name, pdf)
        print(f"FALLBACK {hwp.name}: {exc}")

if failures:
    print("Failures:")
    for name, err in failures:
        print(f"- {name}: {err}")
