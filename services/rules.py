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
            left   = OptionalUnwrapConstraint(CloseTo(30, abs_tol=1.0)),
            right  = OptionalUnwrapConstraint(CloseTo(15, abs_tol=1.0)),
            top    = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
            bottom = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
        ),
        line_spacing=OptionalUnwrapConstraint(CloseTo(1.5)),

        font=OneOf({"Times New Roman"}),
        font_size=OptionalUnwrapConstraint(Minimum(12.0)),
        first_line_indent=AnyValue(),
    ),
    Standard.MU_PO: StandardParams(
        margin=MarginConstraints(
            left   = OptionalUnwrapConstraint(CloseTo(30, abs_tol=1.0)),
            right  = OptionalUnwrapConstraint(CloseTo(10, abs_tol=1.0)),
            top    = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
            bottom = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
        ),
        line_spacing=OptionalUnwrapConstraint(CloseTo(1.5)),

        font=OneOf({"Times New Roman"}),
        font_size=OptionalUnwrapConstraint(CloseToOneOf({12, 14})),
        first_line_indent=OptionalUnwrapConstraint(CloseTo(1.25)),
    ),
}


# --- функции проверки
# --- оформления документа
def check_sections(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []

    margin = _STANDARDS_PARAMS[standard].margin
    category = IssueCategory.DOCUMENT

    for s in parsed.sections:
        if not margin.left.allows(s.margin.left):
            issues.append(Issue(
                rule_id=f"{category}.margins.left",
                category=category,
                message=(
                    f"Левое поле — {s.margin.left:.0f} мм, "
                    f"ожидается {constraint_to_str(margin.left)} мм"
                ),
                standard=standard,
            ))
        if not margin.right.allows(s.margin.right):
            issues.append(Issue(
                rule_id=f"{category}.margins.right",
                category=category,
                message=(
                    f"Правое поле — {s.margin.right:.0f} мм, "
                    f"ожидается {constraint_to_str(margin.right)} мм"
                ),
                standard=standard,
            ))
        if not margin.top.allows(s.margin.top):
            issues.append(Issue(
                rule_id=f"{category}.margins.top",
                category=category,
                message=(
                    f"Верхнее поле — {s.margin.top:.0f} мм, "
                    f"ожидается {constraint_to_str(margin.top)} мм"
                ),
                standard=standard,
            ))
        if not margin.bottom.allows(s.margin.bottom):
            issues.append(Issue(
                rule_id=f"{category}.margins.bottom",
                category=category,
                message=(
                    f"Нижнее поле — {s.margin.bottom:.0f} мм, "
                    f"ожидается {constraint_to_str(margin.bottom)} мм"
                ),
                standard=standard,
            ))

    return issues


def check_paragraphs(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []

    params = _STANDARDS_PARAMS[standard]

    for p in parsed.paragraphs:
        if not params.line_spacing.allows(p.line_spacing):
            category = IssueCategory.DOCUMENT
            issues.append(Issue(
                rule_id=f"{category}.line_spacing",
                category=category,
                message=(
                    f"Межстрочный интервал — {p.line_spacing:.0f} мм, "
                    f"ожидается {constraint_to_str(params.line_spacing)} мм"
                ),
                standard=standard,
            ))

        if not params.first_line_indent.allows(p.first_line_indent):
            category = IssueCategory.TEXT
            issues.append(Issue(
                rule_id=f"{category}.first_line_indent",
                category=category,
                message=(
                    f"Отступ первой строки — {p.first_line_indent:.0f} мм, "
                    f"ожидается {constraint_to_str(params.first_line_indent)} мм"
                ),
                standard=standard,
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
