import pytest

from pytest_respect.resources import TestResources


@pytest.fixture
def resources(request: pytest.FixtureRequest) -> TestResources:
    """Load file resources relative to test functions and fixtures."""
    return TestResources(request, ndigits=4)
