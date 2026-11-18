from io import BytesIO
from typing import NamedTuple

from docx import Document
from docx.document import Document as DocumentObject
from docx.section import Section
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx_plus.numbering import read_list_definitions
from docx_plus.styles import resolve_effective_formatting


class Margin(NamedTuple):
    left: float | None  # mm
    right: float | None  # mm
    top: float | None  # mm
    bottom: float | None  # mm


class RunInfo(NamedTuple):
    text: str
    font_name: str | None
    font_size: float | None  # pt
    is_bold: bool | None
    is_italic: bool | None
    is_underline: bool | None
    color_rgb: str | None


class ParagraphInfo(NamedTuple):
    index_: int
    text: str
    style: str | None
    alignment: str | None
    first_line_indent: float | None  # cm
    line_spacing: float | None
    runs: list[RunInfo]
    is_bold: bool | None
    is_underline: bool | None
    caps: bool | None
    num_id: int | None
    num_level: int | None
    list_format: str | None
    list_text: str | None


class SectionInfo(NamedTuple):
    page_width: float | None  # mm
    page_height: float | None  # mm
    margin: Margin


class TableInfo(NamedTuple):
    index_: int
    rows_count: int
    columns_count: int
    preceding_paragraph_index: int | None


class DocumentInfo(NamedTuple):
    filename: str
    paragraphs: list[ParagraphInfo]
    sections: list[SectionInfo]
    tables_count: int
    images_count: int
    tables: list[TableInfo]


def _get_paragraph_info(
    i: int,
    p: Paragraph,
    list_formats: dict[tuple[int, int], tuple[str | None, str | None]],
) -> ParagraphInfo:
    pf = resolve_effective_formatting(p)

    num_id = pf.num_id
    num_level = pf.num_level

    list_format: str | None = None
    list_text: str | None = None

    if num_id is not None and num_level is not None:
        list_format, list_text = list_formats.get(
            (num_id, num_level),
            (None, None),
        )

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
        is_bold=pf.bold,
        is_underline=(
            bool(pf.underline)
            if pf.underline is not None
            else None
        ),
        caps=pf.caps,
        num_id=num_id,
        num_level=num_level,
        list_format=list_format,
        list_text=list_text,
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
        color_rgb=rf.color_rgb,
    )


def _get_section_margin(s: Section) -> Margin:
    return Margin(
        left=s.left_margin.mm if s.left_margin is not None else None,
        right=s.right_margin.mm if s.right_margin is not None else None,
        top=s.top_margin.mm if s.top_margin is not None else None,
        bottom=s.bottom_margin.mm if s.bottom_margin is not None else None,
    )


def _get_list_formats(
    document: DocumentObject,
) -> dict[tuple[int, int], tuple[str | None, str | None]]:
    result: dict[
        tuple[int, int],
        tuple[str | None, str | None],
    ] = {}

    for definition in read_list_definitions(document):
        for level in definition.levels:
            result[(definition.num_id, level.level)] = (
                level.fmt,
                level.text,
            )

    return result


def _get_table_info(
    table: Table,
    index_: int,
    preceding_paragraph_index: int | None,
) -> TableInfo:
    return TableInfo(
        index_=index_,
        rows_count=len(table.rows),
        columns_count=len(table.columns),
        preceding_paragraph_index=preceding_paragraph_index,
    )


def parse_docx_file(file_bytes: bytes, filename: str) -> DocumentInfo:
    try:
        document = Document(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError("Не удалось открыть файл") from e

    list_formats = _get_list_formats(document)

    paragraphs: list[ParagraphInfo] = []
    tables: list[TableInfo] = []

    for element in document.iter_inner_content():
        if isinstance(element, Paragraph):
            paragraphs.append(
                _get_paragraph_info(
                    len(paragraphs),
                    element,
                    list_formats,
                )
            )

        else:
            # isinstance(element, Table) = True
            preceding_paragraph_index = (
                len(paragraphs) - 1
                if paragraphs
                else None
            )

            tables.append(
                _get_table_info(
                    element,
                    len(tables),
                    preceding_paragraph_index,
                )
            )

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
        tables=tables,
    )
