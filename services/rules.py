from enum import StrEnum, auto
import math
from typing import NamedTuple, SupportsFloat, SupportsIndex

from services.parser import DocumentInfo, Margin


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


# --- константы ГОСТ
GOST_FONT = "Times New Roman"
GOST_FONT_SIZE_PT_MIN = 12
GOST_INTERVAL = 1.5
GOST_MARGIN_MM = Margin(
    left=30,
    right=15,
    top=20,
    bottom=20,
)

# --- константы МУ ПО
MUPO_FONT = "Times New Roman"
MUPO_FONT_SIZE_PT = {12, 14}
MUPO_INTERVAL = 1.5
MUPO_PARA_INDENT_CM = 1.25
MUPO_MARGIN_MM=Margin(
    left=30,
    right=10,
    top=20,
    bottom=20,
)


# --- функции проверки
# --- оформления документа
def check_margins(parsed: DocumentInfo, standard: Standard) -> list[Issue]:
    issues: list[Issue] = []

    match standard:
        case Standard.GOST_7_32:
            margin = GOST_MARGIN_MM
        case Standard.MU_PO:
            margin = MUPO_MARGIN_MM

    for s in parsed.sections:
        for name in Margin._fields:
            actual: SupportsFloat | None = getattr(s.margin, name)
            expected: SupportsFloat = getattr(margin, name)

            if actual is None:
                continue

            if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1.0):
                category = IssueCategory.DOCUMENT
                issues.append(Issue(
                    rule_id=f"{category}.margins.{name}",
                    category=category,
                    message=(
                        f"Поле {name} = {actual:.0f} мм, "
                        f"ожидается {expected} мм"
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
