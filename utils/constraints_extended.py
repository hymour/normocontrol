import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, SupportsFloat, SupportsIndex

from external.constraints import (
    AnyValue,
    Constraint,
    Maximum,
    Minimum,
    OneOf,
    Range,
)


@dataclass(frozen=True, slots=True)
class OptionalUnwrapConstraint[T]:
    """Constraint wrapper to discard None values in Optional types."""

    constraint: Constraint[T]

    def allows(self, value: T | None, /) -> bool:
        """Unwrap optional value and check underlying constraint."""
        return value is not None and self.constraint.allows(value)


@dataclass(frozen=True, slots=True)
class CloseTo[T: SupportsFloat | SupportsIndex]:
    value: T
    rel_tol: SupportsFloat | SupportsIndex = 1e-9
    abs_tol: SupportsFloat | SupportsIndex = 0.0

    def allows(self, value: SupportsFloat | SupportsIndex, /) -> bool:
        return math.isclose(
            self.value,
            value,
            rel_tol=self.rel_tol,
            abs_tol=self.abs_tol,
        )


@dataclass(frozen=True, slots=True)
class CloseToOneOf[T: SupportsFloat | SupportsIndex]:
    values: frozenset[T]
    rel_tol: SupportsFloat | SupportsIndex = 1e-9
    abs_tol: SupportsFloat | SupportsIndex = 0.0

    def __init__(
        self,
        values: Iterable[T],
        /,
        *,
        rel_tol: SupportsFloat | SupportsIndex = 1e-9,
        abs_tol: SupportsFloat | SupportsIndex = 0.0,
    ) -> None:
        object.__setattr__(self, "values", frozenset(values))
        object.__setattr__(self, "rel_tol", rel_tol)
        object.__setattr__(self, "abs_tol", abs_tol)

    def allows(self, value: SupportsFloat | SupportsIndex, /) -> bool:
        return any(
            math.isclose(
                x,
                value,
                rel_tol=self.rel_tol,
                abs_tol=self.abs_tol,
            )
            for x in self.values
        )


@dataclass(frozen=True, slots=True)
class Regex[T: str]:
    """Constraint matching a string against a regular expression."""

    pattern: str
    full_match: bool = False
    flags: int = 0

    def allows(self, value: T, /) -> bool:
        if self.full_match:
            return re.fullmatch(self.pattern, value, self.flags) is not None

        return re.search(self.pattern, value, self.flags) is not None


@dataclass(frozen=True, slots=True)
class TextCase[T: str]:
    """Constraint checking the case of alphabetic characters."""

    class Variant(StrEnum):
        UPPER = "прописные буквы"
        LOWER = "строчные буквы"
        TITLE = "первая буква прописная"

    mode: Variant

    def allows(self, value: T, /) -> bool:
        letters = [char for char in value if char.isalpha()]

        if not letters:
            return False

        match self.mode:
            case self.Variant.UPPER:
                return all(char.isupper() for char in letters)
            case self.Variant.LOWER:
                return all(char.islower() for char in letters)
            case self.Variant.TITLE:
                words = [
                    word for word in value.split()
                    if any(char.isalpha() for char in word)
                ]
                return bool(words) and words[0][0].isupper()

_VALUE_LABELS = {
    "left": "по левому краю",
    "right": "по правому краю",
    "center": "по центру",
    "justify": "по ширине",
    "bullet": "маркированный список",
    "decimal": "нумерованный список",
    "lowerLetter": "буквенный список (а, б, в...)",
    "lowerletter": "буквенный список (а, б, в...)",
    "000000": "чёрный",
    True: "присутствует",
    False: "отсутствует",
}   

_REGEX_LABELS = {
    # Заголовки
    r"^\s*\d+(?:\.\d+)*\.?\s+\S+": "номер и название заголовка (например, 1 Введение)",
    r"[^.]$": "без точки в конце",
    r"^[^\r\n]*$": "в одну строку без разрывов",

    # Рисунки и таблицы
    r"^\s*(?:Рисунок|Рис\.)\s+\d+(?:\.\d+)*": "Рисунок 1 — Название рисунка",
    r"^\s*Таблица\s+\d+(?:\.\d+)?\s*[—–-]\s*\S.*$": "Таблица 1 — Название таблицы",
    r"^\s*Таблица\s+\d+(?:\.\d+)?\s*$": "Таблица 1",
    r"^\d+(?:\.\d+)?$": "число или номер через точку (например, 1 или 1.2)",
    r"^\S.*$": "непустой текст без пробела в начале",

    # Списки
    r"[-–—\uf0be\uf02d]|%1\)": "дефис или тире (–)",

    # Ссылки
    r"\[[^\]]*\]": "ссылка в квадратных скобках",
    r"\[\d+\]": "номер источника в квадратных скобках (например, [1])",
    r"/[^/\s]*/": "ссылка в косых чертах",
    r"/\d+/": "номер источника в косых чертах (например, /1/)",
}

def constraint_to_str(constraint: Constraint[Any]) -> str:
    match constraint:
        case AnyValue():
            return "любое значение"

        case OneOf(values) | CloseToOneOf(values):
            formatted = list(dict.fromkeys(
                _VALUE_LABELS.get(v, repr(v)) for v in values
            ))
            if len(formatted) == 1:
                return formatted[0]
            return (
                f"одно из значений: "
                f"{', '.join(sorted(formatted))}"
            )

        case Range(minimum, maximum, include_minimum, include_maximum):
            lower = "включительно" if include_minimum else "исключительно"
            upper = "включительно" if include_maximum else "исключительно"

            return (
                f"значение в промежутке от {minimum} {lower} "
                f"до {maximum} {upper}"
            )

        case Minimum(value, inclusive):
            return (
                f"значение не меньше {value}"
                if inclusive
                else f"значение больше {value}"
            )

        case Maximum(value, inclusive):
            return (
                f"значение не больше {value}"
                if inclusive
                else f"значение меньше {value}"
            )

        case CloseTo(value):
            return f"значение, равное {value}"

        case OptionalUnwrapConstraint(inner):
            return constraint_to_str(inner)

        case Regex(pattern, _, _):
            return _REGEX_LABELS.get(pattern, "соответствие формату стандарта")

        case TextCase(mode):
            return mode

        case _:
            raise TypeError(
                f"Неизвестный тип ограничения: {type(constraint).__name__}"
            )
