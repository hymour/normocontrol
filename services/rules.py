from enum import StrEnum, auto
from typing import NamedTuple, SupportsFloat, SupportsIndex

from external.constraints import (
    AnyValue,
    Constraint,
    Minimum,
    OneOf,
)
from services.parser import DocumentInfo, Margin
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
    left:   Constraint[SupportsFloat | None]
    right:  Constraint[SupportsFloat | None]
    top:    Constraint[SupportsFloat | None]
    bottom: Constraint[SupportsFloat | None]


class StandardParams(NamedTuple):
    # document
    margin: MarginConstraints
    line_spacing: Constraint[float | int]

    # text
    font: Constraint[str]
    font_size: Constraint[float | int]  # pt
    first_line_indent: Constraint[float | int]  # cm


_STANDARDS_PARAMS = {
    Standard.GOST_7_32: StandardParams(
        margin=MarginConstraints(
            left   = OptionalUnwrapConstraint(CloseTo(30, abs_tol=1.0)),
            right  = OptionalUnwrapConstraint(CloseTo(15, abs_tol=1.0)),
            top    = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
            bottom = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
        ),
        line_spacing=CloseTo(1.5),

        font=OneOf({"Times New Roman"}),
        font_size=Minimum(12),
        first_line_indent=AnyValue(),
    ),
    Standard.MU_PO: StandardParams(
        margin=MarginConstraints(
            left   = OptionalUnwrapConstraint(CloseTo(30, abs_tol=1.0)),
            right  = OptionalUnwrapConstraint(CloseTo(10, abs_tol=1.0)),
            top    = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
            bottom = OptionalUnwrapConstraint(CloseTo(20, abs_tol=1.0)),
        ),
        line_spacing=CloseTo(1.5),

        font=OneOf({"Times New Roman"}),
        font_size=CloseToOneOf({12, 14}),
        first_line_indent=CloseTo(1.25),
    ),
}


# --- функции проверки
# --- оформления документа
def check_margins(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []

    margin = _STANDARDS_PARAMS[standard].margin

    for s in parsed.sections:
        for name in Margin._fields:
            actual: SupportsFloat | None = getattr(s.margin, name)
            constraint: Constraint[SupportsFloat | None] = getattr(margin, name)

            if actual is None:
                continue

            if not constraint.allows(actual):
                category = IssueCategory.DOCUMENT
                issues.append(Issue(
                    rule_id=f"{category}.margins.{name}",
                    category=category,
                    message=(
                        f"Поле {name} = {actual:.0f} мм, "
                        f"ожидается {constraint_to_str(constraint)} мм"
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
    check_margins,
]
