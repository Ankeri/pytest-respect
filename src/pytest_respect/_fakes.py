"""Fake classes and other constructs with just enough stub code to make pyright accept our optional imports."""

from typing import Any, Generic, NoReturn, TypeVar, final

T = TypeVar("T")


def needs(name: str) -> NoReturn:
    raise NotImplementedError(f"This part of pytest-respect requires the optional {name} dependency.")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Fake pydantic types


class BaseModel:
    def __init__(self, type: Any, **kw) -> NoReturn:
        needs("pydantic")

    @classmethod
    def model_validate(cls, obj: Any, *a, **kw) -> NoReturn:
        needs("pydantic")

    def model_dump(self, **kw) -> NoReturn:
        needs("pydantic")


@final
class TypeAdapter(Generic[T]):
    def __init__(self, type: Any, **kw) -> NoReturn:
        needs("pydantic")

    def validate_python(self, obj: Any, *a, **kw) -> NoReturn:
        needs("pydantic")

    def dump_python(self, instance: T, /, **kw) -> Any:
        needs("pydantic")


class ValidationError(Exception):
    def errors(self, *a, **kw) -> NoReturn:
        needs("pydantic")


class WrapSerializer:
    def __init__(self, *a, **kw):
        super().__init__()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Fake numpy types


class ndarray:  # noqa N801
    def tolist(self) -> NoReturn:
        needs("numpy")


class ndfloat:  # noqa N801
    def __float__(self) -> NoReturn:
        needs("numpy")
