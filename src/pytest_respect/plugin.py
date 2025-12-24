import pytest

from pytest_respect.resources import TestResources


@pytest.fixture
def resources(request: pytest.FixtureRequest) -> TestResources:
    """Load file resources relative to test functions and fixtures."""
    accept = request.config.getoption("--respect-accept-max")
    resources = TestResources(request, accept_count=accept)
    resources.default.ndigits = 4
    return resources


def pytest_addoption(parser):
    group = parser.getgroup("respect")
    group.addoption(
        "--respect-accept",
        action="store_const",
        dest="respect_accept_max",
        const=1e9,
        help="When results don't match expectations, create or update the expected files instead of failing the tests.",
    )
    group.addoption(
        "--respect-accept-one",
        action="store_const",
        dest="respect_accept_max",
        const=1,
        help="Like --respect-accept but only for one expectation in each test.",
    )
    group.addoption(
        "--respect-accept-max",
        default=0,
        type=int,
        help="Like --respect-accept but only for this many expectations in each test.",
    )
