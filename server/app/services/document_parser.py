"""
app.services.document_parser
============================
Turns raw uploaded files into plain text + structured tables + embedded images.

Strategy (one function per format, dispatched by extension):
    .pdf  → PyMuPDF (fitz)
    .docx → python-docx
    .pptx → python-pptx
    .xlsx → openpyxl
    .doc / .ppt / .xls → convert via LibreOffice headless OR Unstructured.io

Returned shape (keep it boring + serialisable):
    ParsedDocument(text=str, tables=list[list[list[str]]], images=list[bytes])
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedDocument:
    text: str = ""
    tables: list[list[list[str]]] = field(default_factory=list)
    images: list[bytes] = field(default_factory=list)


def parse(file_path: Path | str) -> ParsedDocument:
    """Dispatch parsing based on extension. Raise ValueError for unsupported types.

    TODO:
        * implement each branch below
        * extract tables via PyMuPDF (`page.find_tables()`) or python-docx tables
        * OCR images (pytesseract) if embedded visuals contain text worth parsing
    """
    p = Path(file_path)
    ext = p.suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(p)
    if ext == ".docx":
        return _parse_docx(p)
    if ext == ".pptx":
        return _parse_pptx(p)
    if ext == ".xlsx":
        return _parse_xlsx(p)

    raise ValueError(f"Unsupported file type: {ext}")


# --- stubs — implement one at a time ---------------------------------------


def _parse_pdf(path: Path) -> ParsedDocument:  # pragma: no cover
    # import fitz; doc = fitz.open(path); ...
    return ParsedDocument(text=f"[TODO parse PDF {path.name}]")


def _parse_docx(path: Path) -> ParsedDocument:  # pragma: no cover
    # from docx import Document; ...
    return ParsedDocument(text=f"[TODO parse DOCX {path.name}]")


def _parse_pptx(path: Path) -> ParsedDocument:  # pragma: no cover
    # from pptx import Presentation; ...
    return ParsedDocument(text=f"[TODO parse PPTX {path.name}]")


def _parse_xlsx(path: Path) -> ParsedDocument:  # pragma: no cover
    # from openpyxl import load_workbook; ...
    return ParsedDocument(text=f"[TODO parse XLSX {path.name}]")
