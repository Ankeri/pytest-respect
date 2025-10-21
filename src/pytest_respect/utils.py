import datetime as dt
from collections.abc import Callable, Collection, Iterable, Mapping
from functools import partial
from itertools import chain
from types import EllipsisType, UnionType
from typing import Any, Literal, TypeVar, overload

T = TypeVar("T")


@overload
def coalesce(default: T | None | None, *args: T | None | EllipsisType, nonable: Literal[True]) -> T | None: ...
@overload
def coalesce(default: T, *args: T | None | EllipsisType, nonable: Literal[False]) -> T: ...
@overload
def coalesce(default: T, *args: T | None | EllipsisType) -> T: ...


def coalesce(default: T | None, *args: T | None | EllipsisType, nonable: bool = False) -> T | None:
    """Return the first value among default, *args that is not ... and, if nonable is Fals, is not None either."""
    value: T | None = default
    for arg in args:
        if not isinstance(arg, EllipsisType) and (arg is not None or nonable is True):
            value = arg
    return value


class AbortJsonPrep(Exception):  # noqa: N818
    """Raised by a JSON prepper to indicate that even though the argument is of the expected type, it should not be
    handled by this prepper and any other ones should be given a chance."""


JSON_PREPPERS: list[tuple[type | UnionType, Callable[[Any], Any]]] = [
    (dt.date | dt.time | dt.datetime, lambda v: v.isoformat()),
]
"""List of types along with functions to prepare instances of (any sub-class of) those types for JSON encoding."""


def add_json_prepper(type_: type | UnionType, prepper: Callable[[Any], Any]) -> None:
    """Register a global JSON prepper for a given type, including sub-classes.

    The prepper can return a few kinds of values:
    - Simple value: encoded as-is and must be JSON serializable.
    - Dict: encoded recursively but must have keys that are supported by the json_encoder use, which is usually str.
    - Collection: list, tuple, set, etc will be recursively encoded as a list.

    It can also raise AbortJsonPrep to skip this prepper and continue trying others.
    """
    JSON_PREPPERS.append((type_, prepper))


# Try importing optional dependencies and register preppers for their types
try:
    from pydantic import BaseModel

    add_json_prepper(BaseModel, lambda v: v.model_dump(mode="json"))
except ImportError:
    pass

try:
    import numpy as np

    add_json_prepper(np.ndarray, lambda v: v.tolist())
    add_json_prepper(np.floating, lambda v: float(v))
except ImportError:
    pass


def prepare_for_json_encode(
    value: Any,
    *,
    ndigits: int | None = None,
    allow_negative_zero: bool = False,
    extra_preppers: Iterable[tuple[type | UnionType, Callable[[Any], Any]]] = tuple(),
) -> Any:
    """
    Copy a structure of lists, tuples, dicts, pydantic models and numpy values into a parallel structure of dicts and
    lists, trying to make them JSON encodable.

    The encoding is specifically intended for writing expectation files, so it doesn't need to be reversible, and if
    data or precision is lost in a way that is not acceptable, then the user has the opportunity to register a custom
    stringer.

    Args:
        value: The value to prepare for JSON encoding
        ndigits: The number of digits to round floats to, or None to omit rounding
        allow_negative_zero: If False, convert negative zero to plain zero in output
        extra_preppers: Additional preppers to apply before the default ones.
    """

    # Apply the configured preppers
    for type_, prepper in chain(extra_preppers, JSON_PREPPERS):
        if isinstance(value, type_):
            try:
                value = prepper(value)
                continue
            except AbortJsonPrep:
                pass

    # Apply rounding of floats values
    if isinstance(value, float):
        if ndigits is not None:
            value = round(value, ndigits)
        if not allow_negative_zero:
            value += 0.0
        return value

    # Return other JSON encodable values directly
    elif isinstance(value, str | int | bool | None):
        return value

    recurse = partial(
        prepare_for_json_encode,
        ndigits=ndigits,
        allow_negative_zero=allow_negative_zero,
        extra_preppers=extra_preppers,
    )

    # Recurse into dicts and collections
    if isinstance(value, Mapping):
        return {recurse(key): recurse(value) for key, value in value.items()}
    elif isinstance(value, Collection):
        # Collections other than strings are encoded to lists
        return [recurse(x) for x in value]

    # Convert anything else to a string
    else:
        return str(value)
