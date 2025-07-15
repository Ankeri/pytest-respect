"""
JSON encoders and loaders using the jsonyx library.
See https://github.com/nineteendo/jsonyx
"""

from typing import Any


def jsonyx_encoder(obj: Any) -> str:
    """JSONYX encoder in very verbose mode."""
    import jsonyx.allow

    return jsonyx.dumps(
        obj,
        sort_keys=True,
        indent=2,
        allow=jsonyx.allow.NON_STR_KEYS,
    )


def jsonyx_compactish_encoder(obj: Any) -> str:
    """JSONYX encoder which encodes lists and objects of primitives in compact mode."""
    import jsonyx.allow

    return jsonyx.dumps(
        obj,
        sort_keys=True,
        indent=2,
        indent_leaves=False,
        allow=jsonyx.allow.NON_STR_KEYS,
    )


def jsonyx_compact_encoder(obj: Any) -> str:
    """JSONYX encoder in very compact mode."""
    import jsonyx.allow

    return jsonyx.dumps(
        obj,
        sort_keys=True,
        allow=jsonyx.allow.NON_STR_KEYS,
    )


def jsonyx_permissive_loader(text: str) -> Any:
    """JSONYX loader in very permissive mode."""
    import jsonyx.allow

    return jsonyx.loads(text, allow=jsonyx.allow.EVERYTHING)
