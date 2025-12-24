"""
JSON encoders and loaders using the jsonyx library.
See https://github.com/nineteendo/jsonyx
"""

from typing import Any


def jsonyx_encoder(obj: Any) -> str:
    """JSONYX encoder which allows non-string dict keys.
    Here it runs in very verbose mode."""
    import jsonyx.allow

    return jsonyx.dumps(
        obj,
        sort_keys=True,
        indent=2,
        allow=jsonyx.allow.EVERYTHING,
    )


def jsonyx_compactish_encoder(obj: Any) -> str:
    """JSONYX encoder which allows non-string dict keys.
    Here it runs in a semi-compact mode where arrays and dicts containing only primitives are not indented."""
    import jsonyx.allow

    return jsonyx.dumps(
        obj,
        sort_keys=True,
        indent=2,
        indent_leaves=False,
        allow=jsonyx.allow.EVERYTHING,
    )


def jsonyx_compact_encoder(obj: Any) -> str:
    """JSONYX encoder which allows non-string dict keys.
    Here it runs in very compact mode."""
    import jsonyx.allow

    return jsonyx.dumps(
        obj,
        sort_keys=True,
        allow=jsonyx.allow.EVERYTHING,
    )


def jsonyx_permissive_loader(text: str) -> Any:
    """JSONYX loader in very permissive mode."""
    import jsonyx.allow

    return jsonyx.loads(text, allow=jsonyx.allow.EVERYTHING)
