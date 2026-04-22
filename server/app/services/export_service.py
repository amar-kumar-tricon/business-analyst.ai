"""
app.services.export_service
===========================
Render stage outputs as PDF (WeasyPrint) or DOCX (python-docx).

The public API returns raw bytes — HTTP concerns (Content-Disposition etc.) stay
in `api/v1/export.py`.
"""
from __future__ import annotations

from typing import Any


def to_pdf(stage_output: dict[str, Any]) -> bytes:
    """Render a stage output dict to a PDF byte stream.

    TODO:
        * build an HTML template (Jinja2) under `app/templates/exports/<stage>.html`
        * render → HTML string → WeasyPrint → bytes
    """
    # from weasyprint import HTML
    # return HTML(string=rendered_html).write_pdf()
    return b"PDF-PLACEHOLDER"


def to_docx(stage_output: dict[str, Any]) -> bytes:
    """Render a stage output dict to a DOCX byte stream (python-docx)."""
    # from docx import Document; doc = Document(); ...
    # buf = io.BytesIO(); doc.save(buf); return buf.getvalue()
    return b"DOCX-PLACEHOLDER"
