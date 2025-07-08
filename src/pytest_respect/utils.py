from functools import partial
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel


def round_floats_in(
    struct: Any,
    ndigits: int = 4,
    model_dump_mode: Literal["json", "python"] | str = "python",
) -> Any:
    """Copy a structure of lists, dicts, pydantic models and numpy values and round.

    The pydantic models will be dumped to dict in the recursion and numpy arrays and
    values will be converted to python native values.

    This allows us to write easy-to-read unit tests comparing complex data structures
    to simple dicts, lists and floats.

    Args:
        struct: The value to round the floats in
        ndigits: The number of digits to round floats to
        model_dump_mode: The mode to pass to pydantic model_dump method
    """
    # Unwrap struct if needed
    if isinstance(struct, BaseModel):
        struct = struct.model_dump(mode=model_dump_mode)
    elif isinstance(struct, np.ndarray):
        struct = struct.tolist()

    # Convert struct recursively
    recurse = partial(round_floats_in, ndigits=ndigits, model_dump_mode=model_dump_mode)
    if isinstance(struct, np.floating):
        struct = float(struct)
    if isinstance(struct, float):
        return round(struct, ndigits)
    elif isinstance(struct, dict):
        return {recurse(key): recurse(value) for key, value in struct.items()}
    elif isinstance(struct, list):
        return [recurse(x) for x in struct]
    elif isinstance(struct, tuple):
        return tuple(recurse(x) for x in struct)
    else:
        return struct
