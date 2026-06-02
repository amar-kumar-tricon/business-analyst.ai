"""
Convert sprint_agent.md → sprint_agent.pdf
Pipeline: Markdown → styled HTML → PDF via xhtml2pdf (pure Python, no system libs)
"""
from __future__ import annotations

from pathlib import Path
import markdown
from xhtml2pdf import pisa

# ── CSS stylesheet (xhtml2pdf / ReportLab compatible) ──────────────────────
CSS = """
@page {
    size: A4;
    margin: 2cm 2.2cm 2cm 2.2cm;
    @frame footer {
        -pdf-frame-content: footerContent;
        bottom: 1cm;
        height: 0.8cm;
    }
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #111827;
    background: #ffffff;
}

/* ── Headings ── */
h1 {
    font-size: 22pt;
    font-weight: 700;
    color: #1F2937;
    border-bottom: 3px solid #3B82F6;
    padding-bottom: 6pt;
    margin-top: 0;
    page-break-after: avoid;
}
h2 {
    font-size: 15pt;
    font-weight: 700;
    color: #1D4ED8;
    border-bottom: 1.5px solid #BFDBFE;
    padding-bottom: 4pt;
    margin-top: 20pt;
    page-break-after: avoid;
}
h3 {
    font-size: 12pt;
    font-weight: 600;
    color: #1E40AF;
    margin-top: 14pt;
    page-break-after: avoid;
}
h4, h5, h6 {
    font-size: 10.5pt;
    font-weight: 600;
    color: #374151;
    margin-top: 10pt;
    page-break-after: avoid;
}

/* ── Paragraphs ── */
p {
    margin: 5pt 0 8pt 0;
    orphans: 3;
    widows: 3;
}

/* ── Tables ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}
thead tr {
    background-color: #1F2937;
    color: #F9FAFB;
}
thead th {
    padding: 7pt 10pt;
    text-align: left;
    font-weight: 600;
}
tbody tr:nth-child(even) {
    background-color: #F3F4F6;
}
tbody tr:nth-child(odd) {
    background-color: #FFFFFF;
}
tbody td {
    padding: 6pt 10pt;
    border-bottom: 1px solid #E5E7EB;
    vertical-align: top;
}

/* ── Code blocks ── */
pre {
    background-color: #F3F4F6;
    border-left: 4px solid #3B82F6;
    padding: 10pt 12pt;
    border-radius: 4pt;
    font-family: 'Fira Code', 'Courier New', monospace;
    font-size: 8.5pt;
    color: #1F2937;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 10pt 0;
    page-break-inside: avoid;
}
code {
    font-family: 'Fira Code', 'Courier New', monospace;
    font-size: 8.8pt;
    background-color: #FEF3C7;
    color: #92400E;
    padding: 1pt 4pt;
    border-radius: 3pt;
}
pre code {
    background: none;
    color: inherit;
    padding: 0;
    font-size: 8.5pt;
}

/* ── Lists ── */
ul, ol {
    margin: 6pt 0;
    padding-left: 18pt;
}
li {
    margin-bottom: 3pt;
}

/* ── Blockquotes ── */
blockquote {
    border-left: 4px solid #93C5FD;
    background: #EFF6FF;
    margin: 10pt 0;
    padding: 6pt 12pt;
    color: #1E40AF;
    font-style: italic;
    border-radius: 0 4pt 4pt 0;
}

/* ── Horizontal rule ── */
hr {
    border: none;
    border-top: 1.5px solid #E5E7EB;
    margin: 14pt 0;
}

/* ── Links ── */
a {
    color: #2563EB;
    text-decoration: none;
}

/* ── Strong / em ── */
strong { font-weight: 700; color: #111827; }
em     { font-style: italic; color: #374151; }
"""

# ── conversion ──────────────────────────────────────────────────────────────

def convert(md_path: Path, pdf_path: Path):
    md_text = md_path.read_text(encoding="utf-8")

    # Convert markdown → HTML (with tables and fenced code blocks)
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "nl2br", "sane_lists"],
    )

    html_full = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Sprint Agent — Technical Reference</title>
</head>
<body>
{html_body}
</body>
</html>"""

    # Inline the CSS into the HTML for xhtml2pdf
    html_with_css = html_full.replace(
        "</head>",
        f"<style>{CSS}</style>\n</head>"
    )

    with open(pdf_path, "wb") as f:
        result = pisa.CreatePDF(html_with_css, dest=f, encoding="utf-8")

    if result.err:
        print(f"⚠️  PDF created with {result.err} warning(s): {pdf_path}")
    else:
        print(f"✅  Saved: {pdf_path}")


if __name__ == "__main__":
    base = Path(__file__).parent
    convert(base / "sprint_agent.md", base / "sprint_agent.pdf")

