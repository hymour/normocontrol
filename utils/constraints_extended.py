from collections.abc import Iterable
from dataclasses import dataclass
import math
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
class OptionalUnwrapConstraint[T]():
    """Constraint wrapper to discard None values in Optional types"""
    constraint: Constraint[T]

    def allows(self, value: T | None, /) -> bool:
        """Unwrap optional value and check underlying constraint.

        Returns:
            False if value is None; otherwise result of underlying
            constraint
        """
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
        return any(map(lambda x: math.isclose(
                x,
                value,
                rel_tol=self.rel_tol,
                abs_tol=self.abs_tol,
            ),
            self.values,
        ))


def constraint_to_str(constraint: Constraint[Any]) -> str:
    match constraint:
        case AnyValue():
            return "любое значение"
        case OneOf(values) | CloseToOneOf(values):
            return f"одно из значений: {", ".join(sorted(map(repr, values)))}"
        case Range(minimum, maximum, include_minimum, include_maximum):
            match (include_minimum, include_maximum):
                case (True, True):
                    return (
                        f"значение в промежутке от {minimum} включительно "
                        f"до {maximum} включительно"
                    )
                case (True, False):
                    return (
                        f"значение в промежутке от {minimum} включительно "
                        f"до {maximum} исключительно"
                    )
                case (False, True):
                    return (
                        f"значение в промежутке от {minimum} включительно "
                        f"до {maximum} включительно"
                    )
                case (False, False):
                    return (
                        f"значение в промежутке от {minimum} исключительно "
                        f"до {maximum} исключительно"
                    )
        case Minimum(value, inclusive):
            match inclusive:
                case True:
                    return f"значение не меньше {value}"
                case False:
                    return f"значение больше {value}"
        case Maximum(value, inclusive):
            match inclusive:
                case True:
                    return f"значение не больше {value}"
                case False:
                    return f"значение меньше {value}"
        case CloseTo(value):
            return f"значение, равное {value}"
        case _:
            raise NotImplementedError
