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


def constraint_to_str(constraint: Constraint[Any]) -> str:
    match constraint:
        case AnyValue():
            return "любое значение"

        case OneOf(values) | CloseToOneOf(values):
            return (
                f"одно из значений: "
                f"{', '.join(sorted(map(repr, values)))}"
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

        case Regex(pattern, full_match, _):
            if full_match:
                return (
                    "текст полностью соответствует "
                    f"регулярному выражению {pattern!r}"
                )

            return (
                "текст содержит соответствие "
                f"регулярному выражению {pattern!r}"
            )

        case TextCase(mode):
            return mode

        case _:
            raise TypeError(
                f"Неизвестный тип ограничения: {type(constraint).__name__}"
            )
