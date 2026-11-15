# Copyright (c) 2026 Si-Oleg
# SPDX-License-Identifier: MIT
#
# This module was originally developed independently
# by Si-Oleg and is contributed to hymour/normocontrol.

from collections.abc import Hashable
from dataclasses import dataclass
from typing import Protocol, Self


class Comparable(Protocol):
    """Protocol for values supporting ordering comparisons."""

    def __lt__(self, other: Self, /) -> bool: ...

    def __le__(self, other: Self, /) -> bool: ...


class Constraint[T](Protocol):
    """Structural interface for a constraint on values of type T.

    A constraint defines a predicate that determines whether a value
    satisfies a particular set of conditions.

    Implementations may represent finite sets of values, numeric
    intervals, bounds, or domain-specific validation rules.

    Examples:
        >>> constraint: Constraint[int] = AnyValue()
        >>> constraint.allows(42)
        True

        >>> constraint = OneOf({1, 2, 3})
        >>> constraint.allows(2)
        True
        >>> constraint.allows(4)
        False
    """

    def allows(self, value: T, /) -> bool:
        """Return whether value satisfies this constraint.

        Args:
            value: The value to validate.

        Returns:
            True if the value satisfies the constraint; otherwise False.
        """
        ...


@dataclass(frozen=True, slots=True)
class AnyValue[T]:
    """A constraint that accepts every value of type T.

    This represents the absence of restrictions.

    Examples:
        >>> constraint = AnyValue[int]()
        >>> constraint.allows(10)
        True
        >>> constraint.allows(-100)
        True
    """

    def allows(self, _: T, /) -> bool:
        """Accept any value.

        Args:
            value: The value to validate.

        Returns:
            Always True.
        """
        return True


@dataclass(frozen=True, slots=True)
class OneOf[T: Hashable]:
    """A constraint accepting only values from a finite set.

    Values are stored in a frozenset, ensuring immutability and
    efficient membership checks.

    T must be hashable.

    Examples:
        >>> constraint = OneOf({1, 2, 3})
        >>> constraint.allows(2)
        True
        >>> constraint.allows(5)
        False

        >>> constraint = OneOf({"red", "green", "blue"})
        >>> constraint.allows("red")
        True
        >>> constraint.allows("yellow")
        False
    """

    values: frozenset[T]

    def __init__(self, values: frozenset[T] | set[T], /) -> None:
        """Initialize the constraint from a collection of allowed values.

        Args:
            values: The values accepted by this constraint.
                An empty collection represents a constraint that
                accepts no values.
        """
        object.__setattr__(self, "values", frozenset(values))

    def allows(self, value: T, /) -> bool:
        """Check whether value belongs to the allowed set.

        Args:
            value: The value to validate.

        Returns:
            True if value belongs to the allowed set; otherwise False.
        """
        return value in self.values


@dataclass(frozen=True, slots=True)
class Range[T: Comparable]:
    """A constraint restricting values to an ordered interval.

    The lower and upper bounds can independently be inclusive or
    exclusive.

    T must implement the less-than comparison operation.

    The interval is defined as:

        minimum <= value <= maximum  (both inclusive)

    or, depending on the boundary flags:

        minimum < value <= maximum
        minimum <= value < maximum
        minimum < value < maximum

    Examples:
        >>> constraint = Range(10, 100)
        >>> constraint.allows(10)
        True
        >>> constraint.allows(100)
        True
        >>> constraint.allows(101)
        False

        >>> constraint = Range(10, 100, False, True)
        >>> constraint.allows(10)
        False
        >>> constraint.allows(11)
        True

        >>> constraint = Range(0.0, 1.0, False, False)
        >>> constraint.allows(0.5)
        True
        >>> constraint.allows(0.0)
        False
    """

    minimum: T
    maximum: T
    include_minimum: bool = True
    include_maximum: bool = True

    def __post_init__(self) -> None:
        """Validate the interval bounds.

        Raises:
            ValueError: If the lower bound exceeds the upper bound.
        """
        if self.maximum < self.minimum:
            raise ValueError(
                "The maximum bound must not be less than the minimum bound."
            )

        if (
            self.minimum == self.maximum
            and not (self.include_minimum and self.include_maximum)
        ):
            raise ValueError(
                "An interval with equal bounds must include both boundaries."
            )

    def allows(self, value: T, /) -> bool:
        """Check whether value belongs to the interval.

        Args:
            value: The value to validate.

        Returns:
            True if value lies within the interval; otherwise False.
        """
        lower_ok = (
            self.minimum <= value
            if self.include_minimum
            else self.minimum < value
        )

        upper_ok = (
            value <= self.maximum
            if self.include_maximum
            else value < self.maximum
        )

        return lower_ok and upper_ok


@dataclass(frozen=True, slots=True)
class Minimum[T: Comparable]:
    """A constraint requiring a value to meet a lower bound.

    The boundary can be inclusive or exclusive.

    T must implement the less-than comparison operation.

    Examples:
        >>> constraint = Minimum(10)
        >>> constraint.allows(10)
        True
        >>> constraint.allows(9)
        False

        >>> constraint = Minimum(10, inclusive=False)
        >>> constraint.allows(10)
        False
        >>> constraint.allows(11)
        True
    """

    value: T
    inclusive: bool = True

    def allows(self, value: T, /) -> bool:
        """Check whether value meets the lower bound.

        Args:
            value: The value to validate.

        Returns:
            True if value satisfies the lower-bound condition;
            otherwise False.
        """
        return self.value <= value if self.inclusive else self.value < value


@dataclass(frozen=True, slots=True)
class Maximum[T: Comparable]:
    """A constraint requiring a value not to exceed an upper bound.

    The boundary can be inclusive or exclusive.

    T must implement the less-than comparison operation.

    Examples:
        >>> constraint = Maximum(100)
        >>> constraint.allows(100)
        True
        >>> constraint.allows(101)
        False

        >>> constraint = Maximum(100, inclusive=False)
        >>> constraint.allows(100)
        False
        >>> constraint.allows(99)
        True
    """

    value: T
    inclusive: bool = True

    def allows(self, value: T, /) -> bool:
        """Check whether value meets the upper bound.

        Args:
            value: The value to validate.

        Returns:
            True if value satisfies the upper-bound condition;
            otherwise False.
        """
        return value <= self.value if self.inclusive else value < self.value
