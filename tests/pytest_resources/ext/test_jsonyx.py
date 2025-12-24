from math import isnan, nan
from unittest.mock import ANY

import pytest
from pytest import FixtureRequest

from pytest_respect.ext.jsonyx import jsonyx_compactish_encoder, jsonyx_permissive_loader
from pytest_respect.resources import TestResources

# All these tests need jsonyx
pytestmark = pytest.mark.jsonyx


@pytest.fixture
def resources(request: FixtureRequest) -> TestResources:
    """The fixture being tested."""
    return TestResources(request)


def test_load_json__jsonyx_permissive(resources):
    data = resources.load_json(json_loader=jsonyx_permissive_loader)
    assert data == {"look": ["I", "found", "a", ANY]}
    assert isnan(data["look"][-1])


def test_expected_json__jsonyx(resources):
    resources.expect_json(
        {
            "look": ["what", "I", "found"],
            "numbers": [1, 2, 3, nan],
            "sub": {"simple": 1, "dict": 2, "is": 3, "flat": 4},
        },
        json_encoder=jsonyx_compactish_encoder,
    )
