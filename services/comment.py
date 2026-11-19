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

def add_comments(file_bytes: bytes, issues: Iterable[Issue]) -> bytes:
    document = Document(BytesIO(file_bytes))
    paragraphs = document.paragraphs

    # собираем параграфы через iter_inner_content
    all_paragraphs = []
    for element in document.iter_inner_content():
        if isinstance(element, Paragraph):
            all_paragraphs.append(element)

    first_text_paragraph = next((p for p in all_paragraphs if p.text.strip()), None)

    # группировка ошибок по абзацам
    grouped_issues = {}
    doc_level_messages = []

    for issue in issues:
        if issue.paragraph_index is None:
            doc_level_messages.append(issue.message)
        else:
            idx = issue.paragraph_index
            if idx not in grouped_issues:
                grouped_issues[idx] = []
            grouped_issues[idx].append(issue.message)

    # добавляем общий комментарий для ошибок уровня документа
    if doc_level_messages and first_text_paragraph:
        text = "[Документ]\n- " + "\n- ".join(doc_level_messages)
        try:
            add_comment(first_text_paragraph, text, author=COMMENT_AUTHOR)
        except Exception:
            pass

    # добавляем комментарии к конкретным абзацам
    for idx, messages in grouped_issues.items():
        if idx >= len(all_paragraphs):
            continue
            
        anchor_target = all_paragraphs[idx]
        
        # если ошибок несколько - склеиваем их в список через дефис
        if len(messages) > 1:
            text = "\n- " + "\n- ".join(messages)
        else:
            text = messages[0]

        try:
            add_comment(anchor_target, text, author=COMMENT_AUTHOR)
        except Exception:
            continue

    out = BytesIO()
    document.save(out)
    return out.getvalue()