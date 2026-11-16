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
    #Ищет первый абзац, в котором есть хоть какой-то текст.
    for p in paragraphs:
        if p.text.strip():  # Проверяем, что там не просто пробелы
            return p
    return None  # Если документ вообще пустой


def add_comments(file_bytes: bytes, issues: Sequence[Issue]) -> bytes:
    document = Document(BytesIO(file_bytes))
    paragraphs = document.paragraphs

    for issue in issues:
        idx = issue.paragraph_index
        message = issue.message

        if idx is None:
            # Ошибка уровня документа. Ищем первый абзац с текстом.
            anchor_target = _find_first_non_empty_paragraph(paragraphs)
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