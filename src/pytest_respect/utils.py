import datetime as dt
from functools import partial
from typing import Any

# Optional imports falling back to stub implementations to make the type checker happy
try:
    from pydantic import BaseModel
except ImportError:
    from ._fakes import BaseModel

try:
    from numpy import floating as ndfloat
    from numpy import ndarray
except ImportError:
    from ._fakes import ndarray, ndfloat


def prepare_for_json_encode(struct: Any, *, ndigits: int | None = None) -> Any:
    """
    Copy a structure of lists, tuples, dicts, pydantic models and numpy values into a parallel structure of dicts and
    lists, trying to make them JSON encodeable. The encoding doesn't have to be reversible since the target is always
    a block of text that we compare with one that we prepared earlier.

    Args:
        struct: The value to round the floats in
        ndigits: The number of digits to round floats to, or None to omit rounding
    """
    # Unwrap struct if needed
    if isinstance(struct, BaseModel):
        struct = struct.model_dump(mode="json")
    elif isinstance(struct, ndarray):
        struct = struct.tolist()
    elif isinstance(struct, ndfloat):
        struct = float(struct)

    recurse = partial(prepare_for_json_encode, ndigits=ndigits)

    # Special-case some leaf values
    if isinstance(struct, float):
        return round(struct, ndigits) if ndigits is not None else struct
    elif isinstance(struct, dt.date | dt.time | dt.datetime):
        return struct.isoformat()

    # Convert struct recursively
    elif isinstance(struct, dict):
        return {recurse(key): recurse(value) for key, value in struct.items()}
    elif isinstance(struct, list):
        return [recurse(x) for x in struct]
    elif isinstance(struct, tuple):
        return tuple(recurse(x) for x in struct)

    else:
        return struct
