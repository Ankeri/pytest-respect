import pytest

from pytest_respect.resources import TestResources


@pytest.fixture
def resources(request: pytest.FixtureRequest) -> TestResources:
    """Load file resources relative to test functions and fixtures."""
    accept = request.config.getoption("--respect-accept")
    resources = TestResources(request, accept=accept)
    resources.default.ndigits = 4
    return resources


def pytest_addoption(parser):
    group = parser.getgroup("respect")
    group.addoption(
        "--respect-accept",
        action="store_true",
        default=False,
        help="When results don't match expectations, create or update the expected files instead of failing the tests.",
    )
