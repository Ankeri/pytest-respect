import datetime as dt
import json

import numpy as np
from pydantic import BaseModel

from pytest_respect.utils import prepare_for_json_encode


class PydanticModel(BaseModel):
    name: str
    weight: float
    when: dt.datetime


def test_prepare_for_json_encode__simple():
    original = [
        {
            "f-zero": 0.123456789,
            "i-zero": 0,
            "s-zero": "0",
        },
        [1, 2, 3.333333333],
        ("a", "b", 5.1234321),
    ]

    assert prepare_for_json_encode(original) == [
        {
            "f-zero": 0.123456789,
            "i-zero": 0,
            "s-zero": "0",
        },
        [1, 2, 3.333333333],
        ("a", "b", 5.1234321),
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
        ("a", "b", 5.1234),  # last digit down
    ]


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


def test_prepare_for_json_encode__numpy():
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
