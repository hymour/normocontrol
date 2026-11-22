import re
from collections.abc import Iterator
from enum import StrEnum, auto
from typing import NamedTuple, SupportsIndex

from external.constraints import (
    AnyValue,
    Constraint,
    Maximum,
    Minimum,
    OneOf,
)
from services.parser import DocumentInfo, ParagraphInfo, RunInfo
from utils.constraints_extended import (
    CloseTo,
    CloseToOneOf,
    OptionalUnwrapConstraint,
    Regex,
    TextCase,
    constraint_to_str,
)


# for `StrEnum`'s, auto-generated values are lowercased names,
# e.g. `GOST_7_32 = auto()` <=> `GOST_7_32 = "gost_7_32"`
class Standard(StrEnum):
    GOST_7_32 = auto()
    MU_PO = auto()


class IssueCategory(StrEnum):
    DOCUMENT = auto()
    TEXT = auto()
    HEADINGS = auto()
    ILLUSTRATIONS = auto()
    LISTS = auto()
    TABLES = auto()
    REFERENCES = auto()


class IssueSeverity(StrEnum):
    ERROR = auto()


class Issue(NamedTuple):
    rule_id: str
    category: IssueCategory
    message: str
    standard: Standard
    severity: IssueSeverity = IssueSeverity.ERROR
    paragraph_index: SupportsIndex | None = None
    section_index: SupportsIndex | None = None


class MarginConstraints(NamedTuple):
    left: Constraint[float | None]
    right: Constraint[float | None]
    top: Constraint[float | None]
    bottom: Constraint[float | None]


class HeadingConstraints(NamedTuple):
    structural_titles: Constraint[str]
    heading_pattern: Constraint[str]
    structural_alignment: Constraint[str | None]
    structural_case: Constraint[str]
    numbered_case: Constraint[str]
    subsection_case: Constraint[str]
    no_trailing_period: Constraint[str]
    no_underline: Constraint[bool | None]
    no_line_break: Constraint[str]
    numbered_bold: Constraint[bool | None]
    numbered_indent: Constraint[float | None]


class IllustrationConstraints(NamedTuple):
    caption_pattern: Constraint[str]
    number_pattern: Constraint[str]
    sequential_limit: Constraint[int]
    single_figure_limit: Constraint[int]


class ListConstraints(NamedTuple):
    top_level_format: Constraint[str | None]
    second_level_format: Constraint[str | None]
    top_level_marker: Constraint[str]
    second_level_marker: Constraint[str]
    item_ending: Constraint[str]
    list_ending: Constraint[str]


class TableConstraints(NamedTuple):
    caption_pattern: Constraint[str]
    number_pattern: Constraint[str]
    name_pattern: Constraint[str]
    alignment: Constraint[str | None]
    name_alignment: Constraint[str | None]
    no_underline: Constraint[bool | None]
    no_period: Constraint[str]
    zero_indent: Constraint[float | None]
    sequential_limit: Constraint[int]


class ReferenceConstraints(NamedTuple):
    candidate_pattern: Constraint[str]
    valid_pattern: Constraint[str]


class StandardParams(NamedTuple):
    # document
    margin: MarginConstraints
    line_spacing: Constraint[float | None]

    # text
    font: Constraint[str | None]
    font_size: Constraint[float | None]
    first_line_indent: Constraint[float | None]
    font_color: Constraint[str | None]

    # headings
    headings: HeadingConstraints

    # illustrations
    illustrations: IllustrationConstraints

    # lists
    lists: ListConstraints

    # tables
    tables: TableConstraints

    # references
    references: ReferenceConstraints


_STANDARD_PARAMS = {
    Standard.GOST_7_32: StandardParams(
        margin=MarginConstraints(
            left=OptionalUnwrapConstraint(
                CloseTo(30.0, abs_tol=1.0)
            ),
            right=OptionalUnwrapConstraint(
                CloseTo(15.0, abs_tol=1.0)
            ),
            top=OptionalUnwrapConstraint(
                CloseTo(20.0, abs_tol=1.0)
            ),
            bottom=OptionalUnwrapConstraint(
                CloseTo(20.0, abs_tol=1.0)
            ),
        ),
        line_spacing=OptionalUnwrapConstraint(CloseTo(1.5)),

        font=OneOf({"Times New Roman"}),
        font_size=OptionalUnwrapConstraint(Minimum(12.0)),
        first_line_indent=AnyValue(),
        font_color=OneOf({"000000"}),

        headings=HeadingConstraints(
            structural_titles=OneOf({
                "СОДЕРЖАНИЕ",
                "СПИСОК СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
                "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
                "ВВЕДЕНИЕ",
                "ЗАКЛЮЧЕНИЕ",
                "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
                "СПИСОК ЛИТЕРАТУРЫ",
                "ПРИЛОЖЕНИЕ",
            }),
            heading_pattern=Regex(
                r"^\s*\d+(?:\.\d+)*\.?\s+\S+",
            ),
            structural_alignment=OneOf({"center"}),
            structural_case=TextCase(TextCase.Variant.UPPER),
            numbered_case=TextCase(TextCase.Variant.TITLE),
            subsection_case=AnyValue(),
            no_trailing_period=Regex(r"[^.]$"),
            no_underline=OneOf({False}),
            no_line_break=Regex(r"^[^\r\n]*$", full_match=True),
            numbered_bold=OneOf({True}),
            numbered_indent=OptionalUnwrapConstraint(
                Minimum(0.02, inclusive=False)
            ),
        ),

        illustrations=IllustrationConstraints(
            caption_pattern=Regex(
                r"^\s*(?:Рисунок|Рис\.)\s+\d+(?:\.\d+)*",
            ),
            number_pattern=Regex(
                r"^\d+(?:\.\d+)?$",
                full_match=True,
            ),
            sequential_limit=Maximum(2**31 - 1),
            single_figure_limit=Maximum(0),
        ),

        lists=ListConstraints(
            top_level_format=OneOf({"bullet"}),
            second_level_format=OneOf({"bullet"}),
            top_level_marker=Regex(
                r"[-–—\uf0be\uf02d]|%1\)",
                full_match=True,
            ),
            second_level_marker=Regex(
                r"[-–—\uf0be\uf02d]|%1\)",
                full_match=True,
            ),
            item_ending=OneOf({",", ";", "."}),
            list_ending=OneOf({"."}),
        ),

        tables=TableConstraints(
            caption_pattern=Regex(
                r"^\s*Таблица\s+\d+(?:\.\d+)?\s*[—–-]\s*\S.*$",
                full_match=True,
            ),
            number_pattern=Regex(
                r"^\d+(?:\.\d+)?$",
                full_match=True,
            ),
            name_pattern=Regex(
                r"^\S.*$",
                full_match=True,
            ),
            alignment=OneOf({"left"}),
            name_alignment=AnyValue(),
            no_underline=AnyValue(),
            no_period=Regex(r"[^.]$"),
            zero_indent=OptionalUnwrapConstraint(
                CloseTo(0.0, abs_tol=0.1)
            ),
            sequential_limit=Maximum(2**31 - 1),
        ),

        references=ReferenceConstraints(
            candidate_pattern=Regex(r"\[[^\]]*\]"),
            valid_pattern=Regex(
                r"\[\d+\]",
                full_match=True,
            ),
        ),
    ),

    Standard.MU_PO: StandardParams(
        margin=MarginConstraints(
            left=OptionalUnwrapConstraint(
                CloseTo(30.0, abs_tol=1.0)
            ),
            right=OptionalUnwrapConstraint(Minimum(10.0)),
            top=OptionalUnwrapConstraint(Minimum(20.0)),
            bottom=OptionalUnwrapConstraint(Minimum(20.0)),
        ),
        line_spacing=OptionalUnwrapConstraint(CloseTo(1.5)),

        font=OneOf({"Times New Roman"}),
        font_size=OptionalUnwrapConstraint(
            CloseToOneOf({12.0, 14.0})
        ),
        first_line_indent=OptionalUnwrapConstraint(
            CloseTo(1.25, abs_tol=0.05)
        ),
        font_color=OneOf({"000000"}),

        headings=HeadingConstraints(
            structural_titles=OneOf({
                "СОДЕРЖАНИЕ",
                "ВВЕДЕНИЕ",
                "ЗАКЛЮЧЕНИЕ",
                "СПИСОК ЛИТЕРАТУРЫ",
                "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
                "ПРИЛОЖЕНИЕ",
            }),
            heading_pattern=Regex(
                r"^\s*\d+(?:\.\d+)*\.?\s+\S+",
            ),
            structural_alignment=AnyValue(),
            structural_case=TextCase(TextCase.Variant.UPPER),
            numbered_case=TextCase(TextCase.Variant.UPPER),
            subsection_case=TextCase(TextCase.Variant.TITLE),
            no_trailing_period=Regex(r"[^.]$"),
            no_underline=OneOf({False}),
            no_line_break=Regex(r"^[^\r\n]*$", full_match=True),
            numbered_bold=AnyValue(),
            numbered_indent=AnyValue(),
        ),

        illustrations=IllustrationConstraints(
            caption_pattern=Regex(
                r"^\s*(?:Рисунок|Рис\.)\s+\d+(?:\.\d+)*",
            ),
            number_pattern=Regex(
                r"^\d+(?:\.\d+)?$",
                full_match=True,
            ),
            sequential_limit=Maximum(9),
            single_figure_limit=CloseTo(1),
        ),

        lists=ListConstraints(
            top_level_format=OneOf({"decimal", "bullet"}),
            second_level_format=OneOf({
                "lowerLetter",
                "lowerletter",
                "bullet",
            }),
            top_level_marker=Regex(
                r"[-–—\uf0be\uf02d]|%1\)",
                full_match=True,
            ),
            second_level_marker=Regex(
                r"[-–—\uf0be\uf02d]|%1\)",
                full_match=True,
            ),
            item_ending=OneOf({",", ";", "."}),
            list_ending=OneOf({"."}),
        ),

        tables=TableConstraints(
            caption_pattern=Regex(
                r"^\s*Таблица\s+\d+(?:\.\d+)?\s*$",
                full_match=True,
            ),
            number_pattern=Regex(
                r"^\d+(?:\.\d+)?$",
                full_match=True,
            ),
            name_pattern=Regex(
                r"^\S.*$",
                full_match=True,
            ),
            alignment=OneOf({"right"}),
            name_alignment=OneOf({"center"}),
            no_underline=OneOf({False}),
            no_period=Regex(r"[^.]$"),
            zero_indent=OptionalUnwrapConstraint(
                CloseTo(0.0, abs_tol=0.1)
            ),
            sequential_limit=Maximum(9),
        ),

        references=ReferenceConstraints(
            candidate_pattern=Regex(r"/[^/\s]*/"),
            valid_pattern=Regex(
                r"/\d+/",
                full_match=True,
            ),
        ),
    ),
}


def format_issue_message(
    subject: str,
    actual: str,
    expected: str,
    units: str | None = None,
) -> str:
    if units:
        return f"{subject} — {actual} {units}, ожидается {expected} {units}"

    # `units` is None or empty string
    return f"{subject} — {actual}, ожидается {expected}"


def _add_issue(
    issues: list[Issue],
    *,
    rule_id: str,
    category: IssueCategory,
    subject: str,
    actual: str,
    expected: str,
    standard: Standard,
    paragraph_index: int | None = None,
    section_index: int | None = None,
    units: str | None = None,
) -> None:
    issues.append(
        Issue(
            rule_id=rule_id,
            category=category,
            message=format_issue_message(
                subject,
                actual,
                expected,
                units,
            ),
            standard=standard,
            paragraph_index=paragraph_index,
            section_index=section_index,
        )
    )


def _iter_runs(
    parsed: DocumentInfo,
) -> Iterator[tuple[ParagraphInfo, RunInfo]]:
    for para in parsed.paragraphs:
        for run in para.runs:
            if run.text.strip():
                yield para, run


def _is_structural_heading(
    paragraph: ParagraphInfo,
    params: StandardParams,
) -> bool:
    return params.headings.structural_titles.allows(
        paragraph.text.strip().upper()
    )


def _is_numbered_heading(
    paragraph: ParagraphInfo,
    params: StandardParams,
) -> bool:
    return params.headings.heading_pattern.allows(
        paragraph.text.strip()
    )


def _is_heading(
    paragraph: ParagraphInfo,
    params: StandardParams,
) -> bool:
    if not paragraph.text.strip():
        return False

    style = (paragraph.style or "").lower()

    return (
        _is_structural_heading(paragraph, params)
        or _is_numbered_heading(paragraph, params)
        or "heading" in style
        or "заголовок" in style
    )


def _is_black(color: str | None) -> str | None:
    return color.upper().replace("#", "") if color else None


def _get_heading_level(text: str) -> int:
    match = re.match(r"^\s*(\d+(?:\.\d+)*)", text)

    if match is None:
        return 1

    return match.group(1).count(".") + 1


def _get_actual_numbering(paragraph: ParagraphInfo) -> str:
    if paragraph.list_text:
        return paragraph.list_text

    if paragraph.num_id is None:
        return "отсутствует"

    return (
        f"num_id={paragraph.num_id}, "
        f"level={paragraph.num_level}"
    )


def _all_runs_allow(
    paragraph: ParagraphInfo,
    constraint: Constraint[bool | None],
) -> bool:
    runs = [
        run for run in paragraph.runs
        if run.text.strip()
    ]

    return bool(runs) and all(
        constraint.allows(run.is_bold)
        for run in runs
    )


def _has_underlined_runs(paragraph: ParagraphInfo) -> bool:
    return any(
        run.is_underline is True
        for run in paragraph.runs
        if run.text.strip()
    )

def _starts_with_upper(text: str) -> bool:
    first_letter = next((ch for ch in text if ch.isalpha()), None)
    return first_letter is not None and first_letter.isupper()


def _prev_non_empty_index(paragraphs: list[ParagraphInfo], start_idx: int | None) -> int | None:
    idx = start_idx
    while idx is not None and idx >= 0:
        if paragraphs[idx].text.strip():
            return idx
        idx -= 1
    return None


# --- функции проверки
# --- оформления документа
def check_sections(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []

    params = _STANDARD_PARAMS[standard]
    margin = params.margin
    category = IssueCategory.DOCUMENT

    for i, s in enumerate(parsed.sections):
        checks = (
            ("left", "Левое поле", s.margin.left, margin.left),
            ("right", "Правое поле", s.margin.right, margin.right),
            ("top", "Верхнее поле", s.margin.top, margin.top),
            ("bottom", "Нижнее поле", s.margin.bottom, margin.bottom),
        )

        for field, subject, actual, constraint in checks:
            if not constraint.allows(actual):
                _add_issue(
                    issues,
                    rule_id=f"{category}.margins.{field}",
                    category=category,
                    subject=subject,
                    actual=str(actual),
                    expected=constraint_to_str(constraint),
                    standard=standard,
                    section_index=i,
                    units="мм",
                )

    return issues


# --- оформление основного текста
def check_paragraphs(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []
    params = _STANDARD_PARAMS[standard]

    for p in parsed.paragraphs:
        if (
            not p.text.strip() 
            or _is_heading(p, params) 
            or (p.num_id is not None and p.num_id != 0)
        ):
            continue
        
        if not params.line_spacing.allows(p.line_spacing):
            _add_issue(
                issues,
                rule_id="document.line_spacing",
                category=IssueCategory.DOCUMENT,
                subject="Межстрочный интервал",
                actual=str(p.line_spacing),
                expected=constraint_to_str(params.line_spacing),
                standard=standard,
                paragraph_index=p.index_,
            )

        is_centered_or_right = p.alignment in ("center", "right")
        is_caption = (
            params.illustrations.caption_pattern.allows(p.text.strip())
            or params.tables.caption_pattern.allows(p.text.strip())
        )

        if (
            not is_centered_or_right
            and not is_caption
            and not params.first_line_indent.allows(p.first_line_indent)
        ):
            _add_issue(
                issues,
                rule_id="text.first_line_indent",
                category=IssueCategory.TEXT,
                subject="Отступ первой строки",
                actual=str(p.first_line_indent),
                expected=constraint_to_str(
                    params.first_line_indent
                ),
                standard=standard,
                paragraph_index=p.index_,
                units="см",
            )

    return issues


def check_runs(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []
    params = _STANDARD_PARAMS[standard]
    seen: set[tuple[int,str]] = set()

    for paragraph, run in _iter_runs(parsed):
        i = paragraph.index_

        if not params.font.allows(run.font_name) and (i, "text.font") not in seen:
            seen.add((i, "text.font"))
            _add_issue(
                issues,
                rule_id="text.font",
                category=IssueCategory.TEXT,
                subject="Тип шрифта",
                actual=str(run.font_name),
                expected=constraint_to_str(params.font),
                standard=standard,
                paragraph_index=i,
            )

        if not params.font_size.allows(run.font_size) and (i, "text.font_size") not in seen:
            seen.add((i, "text.font_size"))
            _add_issue(
                issues,
                rule_id="text.font_size",
                category=IssueCategory.TEXT,
                subject="Размер шрифта",
                actual=str(run.font_size),
                expected=constraint_to_str(params.font_size),
                standard=standard,
                paragraph_index=i,
                units="пт",
            )

        color = _is_black(run.color_rgb)

        if not params.font_color.allows(color) and (i, "text.font_color") not in seen:
            seen.add((i, "text.font_color"))
            _add_issue(
                issues,
                rule_id="text.font_color",
                category=IssueCategory.TEXT,
                subject="Цвет шрифта",
                actual=str(color),
                expected=constraint_to_str(params.font_color),
                standard=standard,
                paragraph_index=i,
            )

    return issues


# --- оформление заголовков
def check_headings(
    parsed: DocumentInfo,
    standard: Standard,
) -> list[Issue]:
    issues: list[Issue] = []
    params = _STANDARD_PARAMS[standard]
    headings = params.headings

    for p in parsed.paragraphs:
        if not _is_heading(p, params):
            continue

        text = p.text.strip()
        i = p.index_

        if not headings.no_trailing_period.allows(text):
            _add_issue(
                issues,
                rule_id="headings.trailing_period",
                category=IssueCategory.HEADINGS,
                subject="Точка в конце заголовка",
                actual=text[-1:] or "пусто",
                expected=constraint_to_str(
                    headings.no_trailing_period
                ),
                standard=standard,
                paragraph_index=i,
            )

        if not headings.no_line_break.allows(p.text):
            _add_issue(
                issues,
                rule_id="headings.line_break",
                category=IssueCategory.HEADINGS,
                subject="Перенос в заголовке",
                actual="присутствует",
                expected=constraint_to_str(
                    headings.no_line_break
                ),
                standard=standard,
                paragraph_index=i,
            )

        if not headings.no_underline.allows(
            _has_underlined_runs(p)
        ):
            _add_issue(
                issues,
                rule_id="headings.underline",
                category=IssueCategory.HEADINGS,
                subject="Подчёркивание заголовка",
                actual="присутствует",
                expected=constraint_to_str(
                    headings.no_underline
                ),
                standard=standard,
                paragraph_index=i,
            )

        if _is_structural_heading(p, params):
            if not headings.structural_case.allows(text):
                _add_issue(
                    issues,
                    rule_id="headings.structural.case",
                    category=IssueCategory.HEADINGS,
                    subject="Регистр структурного заголовка",
                    actual=text,
                    expected=constraint_to_str(
                        headings.structural_case
                    ),
                    standard=standard,
                    paragraph_index=i,
                )

            if not headings.structural_alignment.allows(
                p.alignment
            ):
                _add_issue(
                    issues,
                    rule_id="headings.structural.alignment",
                    category=IssueCategory.HEADINGS,
                    subject="Выравнивание структурного заголовка",
                    actual=str(p.alignment),
                    expected=constraint_to_str(
                        headings.structural_alignment
                    ),
                    standard=standard,
                    paragraph_index=i,
                )

        elif _is_numbered_heading(p, params):
            level = _get_heading_level(text)

            if standard == Standard.GOST_7_32:
                if not headings.numbered_bold.allows(
                    _all_runs_allow(p, headings.numbered_bold)
                ):
                    _add_issue(
                        issues,
                        rule_id="headings.numbered.bold",
                        category=IssueCategory.HEADINGS,
                        subject="Полужирное начертание заголовка",
                        actual="не все запуски полужирные",
                        expected=constraint_to_str(
                            headings.numbered_bold
                        ),
                        standard=standard,
                        paragraph_index=i,
                    )

                if not headings.numbered_case.allows(text):
                    _add_issue(
                        issues,
                        rule_id="headings.numbered.case",
                        category=IssueCategory.HEADINGS,
                        subject="Регистр заголовка",
                        actual=text,
                        expected=constraint_to_str(
                            headings.numbered_case
                        ),
                        standard=standard,
                        paragraph_index=i,
                    )

                if not headings.numbered_indent.allows(
                    p.first_line_indent
                ):
                    _add_issue(
                        issues,
                        rule_id="headings.numbered.indent",
                        category=IssueCategory.HEADINGS,
                        subject="Абзацный отступ заголовка",
                        actual=str(p.first_line_indent),
                        expected=constraint_to_str(
                            headings.numbered_indent
                        ),
                        standard=standard,
                        paragraph_index=i,
                        units="см",
                    )

            elif standard == Standard.MU_PO:
                title = re.sub(
                    r"^\s*\d+(?:\.\d+)*\.?\s*",
                    "",
                    text,
                )

                constraint = (
                    headings.numbered_case
                    if level == 1
                    else headings.subsection_case
                )

                actual = text if level == 1 else title

                if not constraint.allows(actual):
                    _add_issue(
                        issues,
                        rule_id=(
                            "headings.section.case"
                            if level == 1
                            else "headings.subsection.case"
                        ),
                        category=IssueCategory.HEADINGS,
                        subject=(
                            "Регистр заголовка раздела"
                            if level == 1
                            else "Регистр заголовка подраздела"
                        ),
                        actual=actual,
                        expected=constraint_to_str(constraint),
                        standard=standard,
                        paragraph_index=i,
                    )

    return issues


# --- оформление иллюстраций
def check_illustrations(
    parsed: DocumentInfo,
    standard: Standard,
) -> list[Issue]:
    issues: list[Issue] = []
    params = _STANDARD_PARAMS[standard].illustrations

    figures: list[tuple[int, str]] = []

    for p in parsed.paragraphs:
        text = p.text.strip()

        if params.caption_pattern.allows(text):
            match = re.search(
                r"(?:Рисунок|Рис\.)\s+(\d+(?:\.\d+)*)",
                text,
            )

            if match is not None:
                figures.append((p.index_, match.group(1)))

    if standard == Standard.MU_PO and parsed.images_count == 1:
        for p_index, _ in figures:
            _add_issue(
                issues,
                rule_id="illustrations.single_figure",
                category=IssueCategory.ILLUSTRATIONS,
                subject="Подпись единственного рисунка",
                actual="присутствует нумерация / «Рис.»",
                expected="не нумеруется, без слова «Рис.»",
                standard=standard,
                paragraph_index=p_index,
            )
        return issues

    sequential = params.sequential_limit.allows(len(figures))

    if sequential:
        for expected, (p_index, number) in enumerate(
            figures,
            start=1,
        ):
            if "." not in number and number != str(expected):
                _add_issue(
                    issues,
                    rule_id="illustrations.numbering",
                    category=IssueCategory.ILLUSTRATIONS,
                    subject="Нумерация рисунков",
                    actual=number,
                    expected=str(expected),
                    standard=standard,
                    paragraph_index=p_index,
                )

    for p_index, number in figures:
        if not params.number_pattern.allows(number):
            _add_issue(
                issues,
                rule_id="illustrations.number_format",
                category=IssueCategory.ILLUSTRATIONS,
                subject="Формат номера рисунка",
                actual=number,
                expected=constraint_to_str(
                    params.number_pattern
                ),
                standard=standard,
                paragraph_index=p_index,
            )

    return issues


# --- оформление списков
def check_lists(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []
    params = _STANDARD_PARAMS[standard].lists

    list_paragraphs = [
        p for p in parsed.paragraphs
        if p.num_id is not None
        and p.num_id != 0
        and p.text.strip()
    ]

    for p in list_paragraphs:
        level = p.num_level or 0

        fmt_constraint = (
            params.top_level_format
            if level == 0
            else params.second_level_format
        )

        marker_constraint = (
            params.top_level_marker
            if level == 0
            else params.second_level_marker
        )

        fmt = p.list_format
        marker = p.list_text or ""

        if not fmt_constraint.allows(fmt):
            _add_issue(
                issues,
                rule_id="lists.format",
                category=IssueCategory.LISTS,
                subject="Тип нумерации списка",
                actual=str(fmt),
                expected=constraint_to_str(fmt_constraint),
                standard=standard,
                paragraph_index=p.index_,
            )

        if not marker_constraint.allows(marker):
            _add_issue(
                issues,
                rule_id="lists.marker",
                category=IssueCategory.LISTS,
                subject="Маркер списка",
                actual=_get_actual_numbering(p),
                expected=constraint_to_str(marker_constraint),
                standard=standard,
                paragraph_index=p.index_,
            )

        text = p.text.rstrip()

        if text:
            ending = text[-1]

            if not params.item_ending.allows(ending):
                _add_issue(
                    issues,
                    rule_id="lists.item_ending",
                    category=IssueCategory.LISTS,
                    subject="Разделитель элемента списка",
                    actual=ending,
                    expected=constraint_to_str(
                        params.item_ending
                    ),
                    standard=standard,
                    paragraph_index=p.index_,
                )

    if list_paragraphs:
        last = list_paragraphs[-1]
        text = last.text.rstrip()

        if text and not params.list_ending.allows(text[-1]):
            _add_issue(
                issues,
                rule_id="lists.list_ending",
                category=IssueCategory.LISTS,
                subject="Окончание списка",
                actual=text[-1],
                expected=constraint_to_str(
                    params.list_ending
                ),
                standard=standard,
                paragraph_index=last.index_,
            )

    return issues


# --- оформление таблиц
def check_tables(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []
    params = _STANDARD_PARAMS[standard].tables

    table_numbers: list[tuple[int, str]] = []

    for table in parsed.tables:
        p_index = table.preceding_paragraph_index

        if p_index is None:
            _add_issue(
                issues,
                rule_id="tables.caption",
                category=IssueCategory.TABLES,
                subject="Подпись таблицы",
                actual="отсутствует",
                expected=constraint_to_str(
                    params.caption_pattern
                ),
                standard=standard,
            )
            continue

        if standard == Standard.GOST_7_32:
            if not params.caption_pattern.allows(text):
                _add_issue(
                    issues,
                    rule_id="tables.caption",
                    category=IssueCategory.TABLES,
                    subject="Подпись таблицы",
                    actual=text or "отсутствует",
                    expected=constraint_to_str(
                        params.caption_pattern
                    ),
                    standard=standard,
                    paragraph_index=p_index,
                )
                continue

            paragraph = parsed.paragraphs[p_index]
            text = paragraph.text.strip()
            
            match = re.search(
                r"Таблица\s+(\d+(?:\.\d+)*)",
                text,
            )
            
            if match is None:
                continue

            number = match.group(1)
            table_numbers.append((p_index, number))

            if not params.alignment.allows(paragraph.alignment):
                _add_issue(
                    issues,
                    rule_id="tables.alignment",
                    category=IssueCategory.TABLES,
                    subject="Выравнивание подписи таблицы",
                    actual=str(paragraph.alignment),
                    expected=constraint_to_str(params.alignment),
                    standard=standard,
                    paragraph_index=p_index,
                )

            if not params.zero_indent.allows(
                paragraph.first_line_indent
            ):
                _add_issue(
                    issues,
                    rule_id="tables.indent",
                    category=IssueCategory.TABLES,
                    subject="Абзацный отступ подписи таблицы",
                    actual=str(paragraph.first_line_indent),
                    expected=constraint_to_str(params.zero_indent),
                    standard=standard,
                    paragraph_index=p_index,
                    units="см",
                )

            name = text[match.end():].strip(" —–-")

            if not params.name_pattern.allows(name):
                _add_issue(
                    issues,
                    rule_id="tables.name",
                    category=IssueCategory.TABLES,
                    subject="Наименование таблицы",
                    actual=name or "отсутствует",
                    expected=constraint_to_str(params.name_pattern),
                    standard=standard,
                    paragraph_index=p_index,
                )

            if not params.no_period.allows(name):
                _add_issue(
                    issues,
                    rule_id="tables.name.period",
                    category=IssueCategory.TABLES,
                    subject="Точка в конце наименования таблицы",
                    actual=name[-1:] or "пусто",
                    expected="без точки",
                    standard=standard,
                    paragraph_index=p_index,
                )

            if name and not name[0].isupper():
                _add_issue(
                    issues,
                    rule_id="tables.name.case",
                    category=IssueCategory.TABLES,
                    subject="Регистр наименования таблицы",
                    actual=name,
                    expected="с прописной буквы",
                    standard=standard,
                    paragraph_index=p_index,
                )
            

        elif standard == Standard.MU_PO:
            if params.caption_pattern.allows(parsed.paragraphs[p_index].text.strip()):
                label_para = parsed.paragraphs[p_index]
                name_para = None
            else:
                if p_index < 1:
                    _add_issue(
                        issues,
                        rule_id="tables.caption",
                        category=IssueCategory.TABLES,
                        subject="Подпись таблицы",
                        actual="отсутствует",
                        expected=constraint_to_str(
                            params.caption_pattern
                        ),
                        standard=standard,
                        paragraph_index=p_index,
                    )
                    continue

                label_para = parsed.paragraphs[p_index - 1]
                name_para = parsed.paragraphs[p_index]

            label_text = label_para.text.strip()
            name_text = name_para.text.strip() if name_para else ""

            if not params.caption_pattern.allows(label_text):
                _add_issue(
                    issues,
                    rule_id="tables.caption",
                    category=IssueCategory.TABLES,
                    subject="Надпись «Таблица»",
                    actual=label_text or "отсутствует",
                    expected=constraint_to_str(
                        params.caption_pattern
                    ),
                    standard=standard,
                    paragraph_index=label_para.index_,
                )
                continue

            match = re.search(
                r"Таблица\s+(\d+(?:\.\d+)*)",
                label_text,
            )

            if match is not None:
                table_numbers.append((label_para.index_, match.group(1)))

            if not params.alignment.allows(label_para.alignment):
                _add_issue(
                    issues,
                    rule_id="tables.alignment",
                    category=IssueCategory.TABLES,
                    subject="Положение надписи «Таблица»",
                    actual=str(label_para.alignment),
                    expected=constraint_to_str(params.alignment),
                    standard=standard,
                    paragraph_index=label_para.index_,
                )

            if not params.zero_indent.allows(
                label_para.first_line_indent
            ):
                _add_issue(
                    issues,
                    rule_id="tables.indent",
                    category=IssueCategory.TABLES,
                    subject="Абзацный отступ надписи таблицы",
                    actual=str(label_para.first_line_indent),
                    expected=constraint_to_str(params.zero_indent),
                    standard=standard,
                    paragraph_index=label_para.index_,
                    units="см",
                )

            if name_para is not None:
                if not params.name_alignment.allows(name_para.alignment):
                    _add_issue(
                        issues,
                        rule_id="tables.name.alignment",
                        category=IssueCategory.TABLES,
                        subject="Выравнивание заголовка таблицы",
                        actual=str(name_para.alignment),
                        expected=constraint_to_str(params.name_alignment),
                        standard=standard,
                        paragraph_index=name_para.index_,
                    )

                if not params.no_underline.allows(
                    _has_underlined_runs(name_para)
                ):
                    _add_issue(
                        issues,
                        rule_id="tables.name.underline",
                        category=IssueCategory.TABLES,
                        subject="Подчёркивание заголовка таблицы",
                        actual="присутствует",
                        expected="без подчёркивания",
                        standard=standard,
                        paragraph_index=name_para.index_,
                    )

                if name_text and not name_text[0].isupper():
                    _add_issue(
                        issues,
                        rule_id="tables.name.case",
                        category=IssueCategory.TABLES,
                        subject="Регистр заголовка таблицы",
                        actual=name_text,
                        expected="с прописной буквы",
                        standard=standard,
                        paragraph_index=name_para.index_,
                    )

    sequential = params.sequential_limit.allows(len(parsed.tables))

    if sequential:
        for expected, (p_index, number) in enumerate(
            table_numbers,
            start=1,
        ):
            if "." not in number and number != str(expected):
                _add_issue(
                    issues,
                    rule_id="tables.numbering",
                    category=IssueCategory.TABLES,
                    subject="Нумерация таблиц",
                    actual=number,
                    expected=str(expected),
                    standard=standard,
                    paragraph_index=p_index,
                )

    return issues


# --- оформление ссылок
def check_references(
    parsed: DocumentInfo,
    standard: Standard,
) -> list[Issue]:
    issues: list[Issue] = []
    params = _STANDARD_PARAMS[standard].references

    for p in parsed.paragraphs:
        if not p.text.strip():
            continue

        candidate_pattern = params.candidate_pattern

        if not isinstance(candidate_pattern, Regex):
            continue

        candidates = re.finditer(
            candidate_pattern.pattern,
            p.text,
        )

        for match in candidates:
            actual = match.group(0)

            if not params.valid_pattern.allows(actual):
                _add_issue(
                    issues,
                    rule_id="references.format",
                    category=IssueCategory.REFERENCES,
                    subject="Формат ссылки",
                    actual=actual,
                    expected=constraint_to_str(
                        params.valid_pattern
                    ),
                    standard=standard,
                    paragraph_index=p.index_,
                )

    return issues


# --- финал
RULES = [
    check_sections,
    check_paragraphs,
    check_runs,
    check_headings,
    check_illustrations,
    check_lists,
    check_tables,
    check_references,
]
