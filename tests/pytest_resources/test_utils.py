import datetime as dt
import json

import pytest

from pytest_respect.utils import coalesce, prepare_for_json_encode

# Optional imports, falling back to stub classes
try:
    from pydantic import BaseModel
except ImportError:
    from pytest_respect._fakes import BaseModel


def test_coalesce__given():
    assert coalesce(42, None, ..., 888, None, ...) == 888


def test_coalesce__not_given():
    assert coalesce(42, None, ...) == 42


def test_coalesce__nonable__given__not_none():
    assert coalesce(42, 888, ..., nonable=True) == 888


def test_coalesce__nonable__given__none():
    assert coalesce(42, None, ..., nonable=True) is None


@pytest.mark.parametrize("default", [42, None])
def test_coalesce__nonable__not_given(default):
    assert coalesce(default, ..., ..., nonable=True) == default


def test_prepare_for_json_encode__simple():
    import uuid

    original = [
        {
            "f-zero": 0.123456789,
            "i-zero": 0,
            "s-zero": "0",
            "stringable": uuid.NAMESPACE_X500,
        },
        [1, 2, 3.333333333],
        ("a", "b", 5.1234321),
    ]

    assert prepare_for_json_encode(original) == [
        {
            "f-zero": 0.123456789,
            "i-zero": 0,
            "s-zero": "0",
            "stringable": "6ba7b814-9dad-11d1-80b4-00c04fd430c8",
        },
        [1, 2, 3.333333333],
        ["a", "b", 5.1234321],
    ]


def test_prepare_for_json_encode__round():
    original = [
        {
            "f-zero": 0.123456789,
            "i-zero": 0,
            "s-zero": "0",
        },
        [1, 2, 3.333333333],
        ("a", "b", 5.1234321),
    ]

    assert prepare_for_json_encode(original, ndigits=4) == [
        {
            "f-zero": 0.1235,  # last digit up
            "i-zero": 0,
            "s-zero": "0",
        },
        [1, 2, 3.3333],
        ["a", "b", 5.1234],  # last digit down
    ]


def test_prepare_for_json_encode__collections():
    map = {1: "a", 2: "b", 3: "c"}
    original = {
        "frozenset": frozenset((4, 5, 6)),
        "items": map.items(),
        "keys": map.keys(),
        "set": {1, 2, 3},
        "values": map.values(),
    }

    assert prepare_for_json_encode(original) == {
        "frozenset": [4, 5, 6],
        "items": [[1, "a"], [2, "b"], [3, "c"]],
        "keys": [1, 2, 3],
        "set": [1, 2, 3],
        "values": ["a", "b", "c"],
    }


def test_prepare_for_json_encode__date_and_time():
    original = {
        "date": dt.date(2025, 7, 22),
        "time": dt.time(11, 9, 23),
        "time_utc": dt.time(11, 9, 23, tzinfo=dt.timezone.utc),
        "datetime": dt.datetime(2025, 7, 22, 11, 9, 23),
        "datetime_utc": dt.datetime(2025, 7, 22, 11, 9, 23, tzinfo=dt.timezone.utc),
    }

    prepared = prepare_for_json_encode(original)

    assert prepared == {
        "date": "2025-07-22",
        "datetime": "2025-07-22T11:09:23",
        "datetime_utc": "2025-07-22T11:09:23+00:00",
        "time": "11:09:23",
        "time_utc": "11:09:23+00:00",
    }
    json.dumps(prepared)


class PydanticModel(BaseModel):  # type: ignore (fake is insufficient)
    name: str
    weight: float
    when: dt.datetime


@pytest.mark.pydantic
def test_prepare_for_json_encode__pydantic_model():
    when = dt.datetime(1986, 3, 1, 12, 34, 56)
    original = [
        0.111111,
        PydanticModel(name="foo", weight=75.4321, when=when),
        0.555555,
    ]

    prepared = prepare_for_json_encode(original, ndigits=2)

    assert prepared == [
        0.11,
        {"name": "foo", "weight": 75.43, "when": "1986-03-01T12:34:56"},
        0.56,
    ]
    json.dumps(prepared)


@pytest.mark.pydantic
def test_prepare_for_json_encode__pydantic_model__json_mode():
    when = dt.datetime(1986, 3, 1, 12, 34, 56)
    original = [
        0.111111,
        PydanticModel(name="foo", weight=75.4321, when=when),
        0.555555,
    ]

    prepared = prepare_for_json_encode(original, ndigits=2)

    assert prepared == [
        0.11,
        {"name": "foo", "weight": 75.43, "when": "1986-03-01T12:34:56"},
        0.56,
    ]
    json.dumps(prepared)


@pytest.mark.numpy
def test_prepare_for_json_encode__numpy():
    import numpy as np

    original = [
        0.111111,
        np.arange(2, 5) * 1 / 9,  # 1-D array
        np.full((2, 3), 10 / 3),  # 2-D array
        np.full(1, 1 / 7)[0],  # scalar
        0.555555,
    ]
    assert isinstance(original[-2], np.floating)

    prepared = prepare_for_json_encode(original, ndigits=2)

    assert prepared == [
        0.11,
        [0.22, 0.33, 0.44],
        [[3.33, 3.33, 3.33], [3.33, 3.33, 3.33]],
        0.14,
        0.56,
    ]
    json.dumps(prepared)


def test_prepare_for_json_encode__allow_negative_zero__default_to_False():
    precise = [
        -0.001,
        [-0.001, -0.003, -0.005],
    ]

    # Compare json dumps since 0.0 == -0.0 as numbers
    rounded = prepare_for_json_encode(precise, ndigits=2)
    assert json.dumps(rounded) == "[0.0, [0.0, 0.0, -0.01]]"


def test_prepare_for_json_encode__allow_negative_zero__True():
    precise = [
        -0.001,
        [-0.001, -0.003, -0.005],
    ]

    # Compare json dumps since 0.0 == -0.0 as numbers
    rounded = prepare_for_json_encode(precise, ndigits=2, allow_negative_zero=True)
    assert json.dumps(rounded) == "[-0.0, [-0.0, -0.0, -0.01]]"


@pytest.mark.numpy
def test_prepare_for_json_encode__allow_negative_zero__default_to_False__numpy():
    import numpy as np

    precise = [
        -0.001,
        np.array([-0.001, -0.003, -0.005]),
    ]

    # Compare json dumps since 0.0 == -0.0 as numbers
    rounded = prepare_for_json_encode(precise, ndigits=2)
    assert json.dumps(rounded) == "[0.0, [0.0, 0.0, -0.01]]"


@pytest.mark.numpy
def test_prepare_for_json_encode__allow_negative_zero__True__numpy():
    import numpy as np

    precise = [
        -0.001,
        np.array([-0.001, -0.003, -0.005]),
    ]

    # Compare json dumps since 0.0 == -0.0 as numbers
    rounded = prepare_for_json_encode(precise, ndigits=2, allow_negative_zero=True)
    assert json.dumps(rounded) == "[-0.0, [-0.0, -0.0, -0.01]]"
