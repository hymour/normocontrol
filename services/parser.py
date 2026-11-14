from io import BytesIO
from typing import NamedTuple, SupportsFloat, SupportsIndex

from docx import Document


class DocumentInfo(NamedTuple):
    filename: str
    paragraphs: list[ParagraphInfo]
    sections: list[SectionInfo]
    tables_count: SupportsIndex
    images_count: SupportsIndex


class ParagraphInfo(NamedTuple):
    index_: SupportsIndex
    text: str
    style: str | None
    alignment: str | None
    first_line_indent: SupportsFloat | None  ## cm
    line_spacing: SupportsFloat | None
    runs: list[RunInfo]


class RunInfo(NamedTuple):
    text: str
    font_name: str | None
    font_size: SupportsFloat | None  # pt
    is_bold: bool | None
    is_italic: bool | None
    is_underline: bool | None


class SectionInfo(NamedTuple):
    page_width:  SupportsFloat | None  # mm
    page_height: SupportsFloat | None  # mm
    margin: Margin


class Margin(NamedTuple):
    left:   SupportsFloat | None  # mm
    right:  SupportsFloat | None  # mm
    top:    SupportsFloat | None  # mm
    bottom: SupportsFloat | None  # mm


def parse_docx_file(file_bytes: bytes, filename: str) -> DocumentInfo:
    try:
        document = Document(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Не удалось открыть файл") from e

    paragraphs = [
        ParagraphInfo(
            index_=i,
            text=p.text,
            style=p.style.name if p.style else None,
            alignment=str(p.alignment) if p.alignment is not None else None,
            first_line_indent=(
                p.paragraph_format.first_line_indent.cm
                if p.paragraph_format.first_line_indent
                else None
            ),
            line_spacing=p.paragraph_format.line_spacing,
            runs=[
                RunInfo(
                    text=r.text,
                    font_name=r.font.name,
                    font_size=r.font.size.pt if r.font.size else None,
                    is_bold=r.font.bold,
                    is_italic=r.font.italic,
                    is_underline=r.font.underline,
                )
                for r in p.runs
            ],
        )
        for i, p in enumerate(document.paragraphs)
    ]

    sections = [
        SectionInfo(
            page_width=(
                s.page_width.mm if s.page_width is not None else None
            ),
            page_height=(
                s.page_height.mm if s.page_height is not None else None
            ),
            margin=Margin(
                left=(
                    s.left_margin.mm if s.left_margin is not None else None
                ),
                right=(
                    s.right_margin.mm if s.right_margin is not None else None
                ),
                top=(
                    s.top_margin.mm if s.top_margin is not None else None
                ),
                bottom=(
                    s.bottom_margin.mm if s.bottom_margin is not None else None
                ),
            ),
        )
        for s in document.sections
    ]

    return DocumentInfo(
        filename=filename,
        paragraphs=paragraphs,
        sections=sections,
        tables_count=len(document.tables),
        images_count=len(document.inline_shapes),
    )
