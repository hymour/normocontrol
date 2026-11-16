from collections.abc import Iterable
from collections.abc import Sequence
from io import BytesIO

from docx import Document
from docx.text.paragraph import Paragraph
from docx_plus.comments import add_comment

from services.rules import Issue

#Комментарий крепится именно к абзацу

COMMENT_AUTHOR = "Нормоконтролер"
DOCUMENT_LEVEL_PREFIX = "[Документ] "


def _find_first_non_empty_paragraph(paragraphs: Sequence[Paragraph]) -> Paragraph | None:
    for p in paragraphs:
        if p.text.strip():
            return p
    return None

def add_comments(file_bytes: bytes, issues: Iterable[Issue]) -> bytes:
    document = Document(BytesIO(file_bytes))
    paragraphs = document.paragraphs

    for issue in issues:
        idx = issue.paragraph_index
        message = issue.message

        if idx is None:
            # Ошибка уровня документа. Ищем первый абзац с текстом. (для красивого выделения
            anchor_target = _find_first_non_empty_paragraph(paragraphs)
            if anchor_target is None:
                continue  # Документ полностью пустой, клеить некуда
            message = DOCUMENT_LEVEL_PREFIX + message
        else:
            # Ошибка конкретного абзаца
            try:
                anchor_target = paragraphs[idx]
            except (IndexError, TypeError):
                continue

        try:
            add_comment(anchor_target, message, author=COMMENT_AUTHOR)
        except Exception:
            continue

    out = BytesIO()
    document.save(out)
    return out.getvalue()