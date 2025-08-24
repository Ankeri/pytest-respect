import pytest

from pytest_respect.resources import TestResources


@pytest.fixture
def resources(request: pytest.FixtureRequest) -> TestResources:
    """Load file resources relative to test functions and fixtures."""
    accept = request.config.getoption("--respect-accept")
    return TestResources(request, ndigits=4, accept=accept)


def pytest_addoption(parser):
    group = parser.getgroup("respect")
    group.addoption(
        "--respect-accept",
        action="store_true",
        default=False,
        help="When results don't match expectations, create or update the expected files insetad of failing the tests.",
    )
