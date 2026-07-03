"""
Ingestion layer: read documents (txt / pdf), detect document type, and chunk them
by logical sections (not arbitrary token windows) so citations map to meaningful spans.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, asdict
from pathlib import Path

from . import config

# structured + unstructured formats we can ingest (images use OCR)
_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
SUPPORTED_EXT = {".txt", ".md", ".pdf", ".csv", ".xlsx", ".eml"} | _IMAGE_EXT

_ocr_engine = None


# equipment/instrument tag shapes found on P&IDs / drawings
_TAG_RE = re.compile(r"\b(?:PUMP|MOTOR|VALVE|FO|PT|TT|FT|LT|PSV|HX|B|K|V|E|P)-?\d{1,4}[A-Z]?\b", re.I)


def _ocr_image(raw: bytes) -> str:
    """OCR a scanned form / photo. If it looks like an engineering drawing (P&ID),
    digitise it: extract tags AND infer connections from their layout (drawing digitisation)."""
    global _ocr_engine
    import numpy as np, cv2
    from rapidocr_onnxruntime import RapidOCR
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return "[Could not decode image]"
    res, _ = _ocr_engine(img)
    items = res or []
    # (text, center-x, center-y) for every detected string
    placed = []
    for box, text, _score in items:
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        placed.append((text.strip(), sum(xs) / 4.0, sum(ys) / 4.0))

    # tags with positions
    tags = []
    for text, cx, cy in placed:
        m = _TAG_RE.search(text.replace(" ", ""))
        if m:
            tags.append((m.group(0).upper(), cx, cy))
    uniq = {}
    for t, x, y in tags:
        uniq.setdefault(t, (x, y))

    if len(uniq) >= 3:   # treat as a P&ID / engineering drawing → digitise structure
        names = list(uniq.keys())
        lines = ["DOCUMENT TYPE: Engineering Drawing (P&ID) — digitised by OCR + layout analysis", ""]
        lines.append("EQUIPMENT / INSTRUMENT TAGS DETECTED: " + ", ".join(sorted(names)))
        lines.append("")
        lines.append("INFERRED CONNECTIONS (from tag proximity on the drawing):")
        seen = set()
        pts = uniq
        for a in names:
            ax, ay = pts[a]
            nearest = sorted(((((ax - pts[b][0]) ** 2 + (ay - pts[b][1]) ** 2) ** 0.5, b)
                              for b in names if b != a))
            for _d, b in nearest[:1]:      # link each tag to its closest neighbour
                pair = tuple(sorted((a, b)))
                if pair not in seen:
                    seen.add(pair)
                    lines.append(f"{pair[0]} is connected to {pair[1]}")
        lines.append("")
        lines.append("RAW EXTRACTED TEXT: " + " ".join(t for t, _, _ in placed))
        return "\n".join(lines)

    body = "\n".join(t for t, _, _ in placed)
    return "DOCUMENT TYPE: Scanned Document (OCR)\n\n" + (body or "[No text detected in image]")


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_type: str
    text: str
    order: int

    def dict(self) -> dict:
        return asdict(self)


def parse_bytes(filename: str, raw: bytes) -> str:
    """Extract plain text from any supported format (PDF, spreadsheet, email, text).
    Used by both the offline index builder and the live-upload endpoint."""
    ext = Path(filename).suffix.lower()
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        if ext == ".xlsx":
            return _parse_xlsx(raw)
        if ext == ".csv":
            return _parse_csv(raw.decode("utf-8", "ignore"))
        if ext == ".eml":
            return _parse_eml(raw)
        if ext in _IMAGE_EXT:
            return _ocr_image(raw)
    except Exception as e:  # pragma: no cover
        return f"[Could not parse {ext or 'file'}: {e}]"
    return raw.decode("utf-8", "ignore")


def _parse_csv(text: str) -> str:
    import csv
    from itertools import zip_longest
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return text
    header = rows[0]
    out = ["DOCUMENT TYPE: Spreadsheet / Data Export", "COLUMNS: " + ", ".join(header), ""]
    for r in rows[1:]:
        # render each row as "Col: value" pairs so entity extraction & citations work
        out.append(" | ".join(f"{h}: {v}" for h, v in zip_longest(header, r, fillvalue="") if v))
    return "\n".join(out)


def _parse_xlsx(raw: bytes) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    blocks = ["DOCUMENT TYPE: Spreadsheet / Data Export"]
    for ws in wb.worksheets:
        rows = [[("" if c is None else str(c)) for c in row] for row in ws.iter_rows(values_only=True)]
        rows = [r for r in rows if any(r)]
        if not rows:
            continue
        header = rows[0]
        blocks.append(f"\nSHEET: {ws.title}  |  COLUMNS: " + ", ".join(header) + "\n")
        from itertools import zip_longest
        for r in rows[1:]:
            blocks.append(" | ".join(f"{h}: {v}" for h, v in zip_longest(header, r, fillvalue="") if v))
    return "\n".join(blocks)


def _parse_eml(raw: bytes) -> str:
    from email import policy
    from email.parser import BytesParser
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content(); break
    else:
        body = msg.get_content() if msg.get_content_type() == "text/plain" else ""
    return (
        "DOCUMENT TYPE: Email\n"
        f"FROM: {msg.get('From','')}\nTO: {msg.get('To','')}\n"
        f"DATE: {msg.get('Date','')}\nSUBJECT: {msg.get('Subject','')}\n\n"
        f"{body}"
    )


def _read_file(path: Path) -> str:
    return parse_bytes(path.name, path.read_bytes())


def detect_doc_type(text: str, filename: str) -> str:
    m = re.search(r"DOCUMENT TYPE:\s*(.+)", text)
    if m:
        return m.group(1).strip().split("(")[0].strip()
    # fall back to filename heuristics
    fn = filename.lower()
    for key, label in [
        ("wo-", "Maintenance Work Order"), ("nm-", "Near-Miss Report"),
        ("ins-", "Inspection Report"), ("inc-", "Incident Report"),
        ("ptw", "Permit to Work"), ("sp-", "Safety Procedure"),
        ("pid", "Engineering Drawing (P&ID)"), ("oisd", "Regulatory Guideline"),
        ("factory", "Regulatory Reference"), ("msds", "Material Safety Data Sheet"),
        ("om-", "O&M Manual"), ("shiftlog", "Shift Log"), ("boiler", "Operating Procedure"),
    ]:
        if key in fn:
            return label
    return "Document"


def _split_sections(text: str) -> list[str]:
    """Split on blank lines / numbered sections, then pack into size-bounded chunks."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 2 <= config.CHUNK_MAX_CHARS:
            buf = f"{buf}\n\n{p}" if buf else p
        else:
            if buf:
                chunks.append(buf)
            # if a single paragraph is huge, hard-split it
            if len(p) > config.CHUNK_MAX_CHARS:
                for i in range(0, len(p), config.CHUNK_MAX_CHARS - config.CHUNK_OVERLAP_CHARS):
                    chunks.append(p[i:i + config.CHUNK_MAX_CHARS])
                buf = ""
            else:
                buf = p
    if buf:
        chunks.append(buf)
    return chunks


def ingest_dir(directory: Path | None = None) -> list[Chunk]:
    directory = directory or config.DATA_DIR
    chunks: list[Chunk] = []
    files = sorted(p for p in directory.iterdir()
                   if p.suffix.lower() in SUPPORTED_EXT)
    for path in files:
        text = _read_file(path)
        doc_type = detect_doc_type(text, path.name)
        for i, sect in enumerate(_split_sections(text)):
            chunks.append(Chunk(
                chunk_id=f"{path.name}::{i}",
                doc_id=path.name,
                doc_type=doc_type,
                text=sect,
                order=i,
            ))
    return chunks


if __name__ == "__main__":
    cs = ingest_dir()
    print(f"{len(cs)} chunks from {len(set(c.doc_id for c in cs))} documents")
    for c in cs[:3]:
        print(f"  {c.chunk_id}  [{c.doc_type}]  {len(c.text)} chars")
