from enum import StrEnum, auto
from typing import NamedTuple, SupportsIndex

from external.constraints import (
    AnyValue,
    Constraint,
    Minimum,
    OneOf,
)
from services.parser import DocumentInfo
from utils.constraints_extended import (
    CloseTo,
    CloseToOneOf,
    OptionalUnwrapConstraint,
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
    left:   Constraint[float | None]
    right:  Constraint[float | None]
    top:    Constraint[float | None]
    bottom: Constraint[float | None]


class StandardParams(NamedTuple):
    # document
    margin: MarginConstraints
    line_spacing: Constraint[float | None]

    # text
    font: Constraint[str | None]
    font_size: Constraint[float | None]  # pt
    first_line_indent: Constraint[float | None]  # cm


_STANDARDS_PARAMS = {
    Standard.GOST_7_32: StandardParams(
        margin=MarginConstraints(
            left   = OptionalUnwrapConstraint(CloseTo(30.0, abs_tol=1.0)),
            right  = OptionalUnwrapConstraint(CloseTo(15.0, abs_tol=1.0)),
            top    = OptionalUnwrapConstraint(CloseTo(20.0, abs_tol=1.0)),
            bottom = OptionalUnwrapConstraint(CloseTo(20.0, abs_tol=1.0)),
        ),
        line_spacing=OptionalUnwrapConstraint(CloseTo(1.5)),

        font=OneOf({"Times New Roman"}),
        font_size=OptionalUnwrapConstraint(Minimum(12.0)),
        first_line_indent=AnyValue(),
    ),
    Standard.MU_PO: StandardParams(
        margin=MarginConstraints(
            left   = OptionalUnwrapConstraint(CloseTo(30.0, abs_tol=1.0)),
            right  = OptionalUnwrapConstraint(Minimum(10.0)),
            top    = OptionalUnwrapConstraint(Minimum(20.0)),
            bottom = OptionalUnwrapConstraint(Minimum(20.0)),
        ),
        line_spacing=OptionalUnwrapConstraint(CloseTo(1.5)),

        font=OneOf({"Times New Roman"}),
        font_size=OptionalUnwrapConstraint(CloseToOneOf({12.0, 14.0})),
        first_line_indent=OptionalUnwrapConstraint(CloseTo(1.25)),
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


# --- функции проверки
# --- оформления документа
def check_sections(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []

    margin = _STANDARDS_PARAMS[standard].margin
    category = IssueCategory.DOCUMENT

    for i, s in enumerate(parsed.sections):
        if not margin.left.allows(s.margin.left):
            issues.append(Issue(
                rule_id=f"{category}.margins.left",
                category=category,
                message=format_issue_message(
                    "Левое поле",
                    f"{s.margin.left:.0f}",
                    f"{constraint_to_str(margin.left)}",
                    "мм",
                ),
                standard=standard,
                section_index=i,
            ))
        if not margin.right.allows(s.margin.right):
            issues.append(Issue(
                rule_id=f"{category}.margins.right",
                category=category,
                message=format_issue_message(
                    "Правое поле",
                    f"{s.margin.right:.0f}",
                    f"{constraint_to_str(margin.right)}",
                    "мм",
                ),
                standard=standard,
                section_index=i,
            ))
        if not margin.top.allows(s.margin.top):
            issues.append(Issue(
                rule_id=f"{category}.margins.top",
                category=category,
                message=format_issue_message(
                    "Верхнее поле",
                    f"{s.margin.top:.0f}",
                    f"{constraint_to_str(margin.top)}",
                    "мм",
                ),
                standard=standard,
                section_index=i,
            ))
        if not margin.bottom.allows(s.margin.bottom):
            issues.append(Issue(
                rule_id=f"{category}.margins.bottom",
                category=category,
                message=format_issue_message(
                    "Нижнее поле",
                    f"{s.margin.bottom:.0f}",
                    f"{constraint_to_str(margin.bottom)}",
                    "мм",
                ),
                standard=standard,
                section_index=i,
            ))

    return issues


def check_paragraphs(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []

    params = _STANDARDS_PARAMS[standard]

    for i, p in enumerate(parsed.paragraphs):
        if not params.line_spacing.allows(p.line_spacing):
            category = IssueCategory.DOCUMENT
            issues.append(Issue(
                rule_id=f"{category}.line_spacing",
                category=category,
                message=format_issue_message(
                    "Межстрочный интервал",
                    f"{p.line_spacing}",
                    f"{constraint_to_str(params.line_spacing)}",
                ),
                standard=standard,
                paragraph_index=i,
            ))

        if not params.first_line_indent.allows(p.first_line_indent):
            category = IssueCategory.TEXT
            issues.append(Issue(
                rule_id=f"{category}.first_line_indent",
                category=category,
                message=format_issue_message(
                    "Отступ первой строки",
                    f"{p.first_line_indent}",
                    f"{constraint_to_str(params.first_line_indent)}",
                    "см",
                ),
                standard=standard,
                paragraph_index=i,
            ))

    return issues


# --- финал
def _iter_runs(parsed: DocumentInfo):
    for para in parsed.paragraphs:
        for run in para.runs:
            if run.text.strip():
                yield para, run


RULES = [
    check_sections,
    check_paragraphs,
]
