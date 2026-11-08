from docx import Document
import io

def parse_docx_file(file_bytes: bytes, filename: str):
    doc = Document(io.BytesIO(file_bytes))
    par_data = []
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            par_data.append({
                "index": i,
                "text": p.text[:50]
            })
    return {
        "filename": filename,
        "total_paragraphs": len(doc.paragraphs),
        "status": "Успех!"
    }