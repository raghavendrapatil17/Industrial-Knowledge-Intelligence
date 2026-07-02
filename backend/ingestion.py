"""
Ingestion layer: read documents (txt / pdf), detect document type, and chunk them
by logical sections (not arbitrary token windows) so citations map to meaningful spans.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

from . import config


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_type: str
    text: str
    order: int

    def dict(self) -> dict:
        return asdict(self)


def _read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:  # pragma: no cover
            return f"[Could not parse PDF: {e}]"
    return path.read_text(encoding="utf-8", errors="ignore")


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
                   if p.suffix.lower() in {".txt", ".pdf", ".md"})
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
