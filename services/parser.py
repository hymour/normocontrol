from io import BytesIO
from typing import NamedTuple

from docx import Document
from docx.section import Section
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx_plus.styles import resolve_effective_formatting


class Margin(NamedTuple):
    left:   float | None  # mm
    right:  float | None  # mm
    top:    float | None  # mm
    bottom: float | None  # mm


class RunInfo(NamedTuple):
    text: str
    font_name: str | None
    font_size: float | None  # pt
    is_bold: bool | None
    is_italic: bool | None
    is_underline: bool | None


class ParagraphInfo(NamedTuple):
    index_: int
    text: str
    style: str | None
    alignment: str | None
    first_line_indent: float | None  # cm
    line_spacing: float | None
    runs: list[RunInfo]


class SectionInfo(NamedTuple):
    page_width: float | None  # mm
    page_height: float | None  # mm
    margin: Margin


class DocumentInfo(NamedTuple):
    filename: str
    paragraphs: list[ParagraphInfo]
    sections: list[SectionInfo]
    tables_count: int
    images_count: int


def _get_paragraph_info(i: int, p: Paragraph) -> ParagraphInfo:
    pf = resolve_effective_formatting(p)

    return ParagraphInfo(
        index_=i,
        text=p.text,
        style=pf.style_name,
        alignment=pf.alignment,

        # `pf.indent_first_line` is in twips
        # cm = twips * (2.54 / 1440)
        first_line_indent=(
            pf.indent_first_line / 1440 * 2.54
            if pf.indent_first_line is not None
            else None
        ),
        line_spacing=pf.line_spacing,
        runs=[_get_run_info(r) for r in p.runs],
    )


def _get_run_info(r: Run) -> RunInfo:
    rf = resolve_effective_formatting(r)

    return RunInfo(
        text=r.text,
        font_name=rf.font_name,
        font_size=rf.font_size,
        is_bold=rf.bold,
        is_italic=rf.italic,
        is_underline=(
            bool(rf.underline)
            if rf.underline is not None
            else None
        ),
    )


def _get_section_margin(s: Section) -> Margin:
    return Margin(
        left=s.left_margin.mm if s.left_margin is not None else None,
        right=s.right_margin.mm if s.right_margin is not None else None,
        top=s.top_margin.mm if s.top_margin is not None else None,
        bottom=s.bottom_margin.mm if s.bottom_margin is not None else None,
    )


def parse_docx_file(file_bytes: bytes, filename: str) -> DocumentInfo:
    try:
        document = Document(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError("Не удалось открыть файл") from e

    paragraphs = [
        _get_paragraph_info(i, p) for i, p in enumerate(document.paragraphs)
    ]

    sections = [
        SectionInfo(
            page_width=(
                s.page_width.mm if s.page_width is not None else None
            ),
            page_height=(
                s.page_height.mm if s.page_height is not None else None
            ),
            margin=_get_section_margin(s),
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
