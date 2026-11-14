from docx import Document
import io

def parse_docx_file(file_bytes: bytes, filename: str) -> dict:
    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Не удалось открыть файл") from e

    paras = []
    for i, p in enumerate(doc.paragraphs):
        pf = p.paragraph_format
        paras.append({
            "index": i,
            "text": p.text,
            "style": p.style.name if p.style else None,
            "alignment": str(p.alignment) if p.alignment is not None else None,
            "first_line_indent_cm": pf.first_line_indent.cm if pf.first_line_indent else None,
            "line_spacing": pf.line_spacing,
            "runs": [
                {
                    "text": r.text,
                    "font_name": r.font.name,
                    "font_size_pt": r.font.size.pt if r.font.size else None,
                    "bold": r.font.bold,
                    "italic": r.font.italic,
                    "underline": r.font.underline,
                }
                for r in p.runs
            ]
        })

    sections = [
        {
            "page_width_cm": s.page_width.cm,
            "page_height_cm": s.page_height.cm,
            "left_margin_cm": s.left_margin.cm,
            "right_margin_cm": s.right_margin.cm,
            "top_margin_cm": s.top_margin.cm,
            "bottom_margin_cm": s.bottom_margin.cm,
        }
        for s in doc.sections
    ]

    return {
        "filename": filename,
        "paragraphs": paras,
        "sections": sections,
        "tables_count": len(doc.tables),
        "images_count": len(doc.inline_shapes),
    }