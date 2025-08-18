from datetime import date, datetime
from pathlib import Path
from typing import Annotated
from unittest.mock import call

import pytest
from pytest import FixtureRequest

from pytest_respect.resources import PathMaker, TestResources, list_dir, list_resources, python_compact_json_encoder

# Optional imports falling back to stub implementations to make the type checker happy
try:
    from pydantic import BaseModel, ValidationError, WrapSerializer
except ImportError:  # pragma: no cover
    from pytest_respect._fakes import BaseModel, ValidationError, WrapSerializer


THIS_FILE = Path(__file__).absolute()
THIS_DIR = THIS_FILE.parent


@pytest.fixture(scope="module", autouse=True)
def dont_tracebackhide():
    """Tests in this module want to see tracebacks from inside the resources module."""
    import pytest_respect.resources as module

    previous = module.__tracebackhide__
    module.__tracebackhide__ = False
    yield
    module.__tracebackhide__ = previous


@pytest.fixture
def mock_list_dir(mocker):
    return mocker.patch(
        "pytest_respect.resources.list_dir",
        autospec=True,
        return_value=["scenario_1.json", "scenario_2.json"],
    )


@pytest.fixture
def resources(request: FixtureRequest) -> TestResources:
    """The fixture being tested."""
    return TestResources(request)


@pytest.fixture
def mock_delete(resources, mocker):
    """Mock resources.delete method"""
    return mocker.patch.object(resources, "delete", autospec=True)


@pytest.fixture
def resources_4digits(request: FixtureRequest) -> TestResources:
    """A TestResrouces fixture which defaults to rounding to 4 digits."""
    return TestResources(
        request,
        ndigits=4,
    )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Static Resource Listing


def test_list_dir(tmp_path: Path):
    # This test is not very stable and needs to be updated when the dir content changes
    # Having tested the file-access code we can use `mock_list_dir` for the rest.
    listed = list_dir(THIS_DIR / "test_resources", "*_load_*", exclude="*__actual.*")
    assert listed == [
        "test_expected_json__ndigits__test_load_json.json",
        "test_load_json.json",
        "test_load_pydantic.json",
        "test_load_pydantic_adapter.json",
        "test_load_pydantic_adapter__failing.json",
        "test_load_text.txt",
    ]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# JSON encoders & Decoders

# TODO test_python_json_encoder
# TODO test_python_compact_json_encoder
# TODO test_python_json_loader

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Path Makers & Paths


@pytest.mark.parametrize(
    "path_maker, ex_path",
    [
        [TestResources.pm_function, THIS_DIR / "test_resources__test_resources__dir"],
        [TestResources.pm_class, THIS_DIR / "test_resources"],
        [TestResources.pm_file, THIS_DIR / "test_resources"],
        [TestResources.pm_dir_named("stuff"), THIS_DIR / "stuff"],
    ],
    ids=str,
)
def test_resources__dir(resources, path_maker: PathMaker, ex_path: Path):
    """Build resource folders for different scopes."""
    path = resources.dir(path_maker)
    assert str(path) == str(ex_path)


@pytest.mark.parametrize(
    "parts, ext, ex_path",
    [
        [
            [],
            "",
            THIS_DIR / "test_resources" / "test_resources__path",
        ],
        [
            [],
            "json",
            THIS_DIR / "test_resources" / "test_resources__path.json",
        ],
        [
            ["input", "first"],
            "json",
            THIS_DIR / "test_resources" / "test_resources__path__input__first.json",
        ],
    ],
)
def test_resources__path(resources, parts: tuple[str], ext: str, ex_path):
    """Build resource paths with different parts and extension."""
    assert str(resources.path(*parts, ext=ext)) == str(ex_path)


@pytest.mark.parametrize(
    "path_maker, ex_path",
    [
        [
            TestResources.pm_function,
            THIS_DIR / "test_resources__test_resources__path__path_maker" / "data.txt",
        ],
        [
            TestResources.pm_class,
            THIS_DIR / "test_resources" / "test_resources__path__path_maker.txt",
        ],
        [
            TestResources.pm_file,
            THIS_DIR / "test_resources" / "test_resources__path__path_maker.txt",
        ],
        [
            TestResources.pm_dir,
            THIS_DIR / "resources" / "test_resources__test_resources__path__path_maker.txt",
        ],
        [
            TestResources.pm_dir_named("treasures"),
            THIS_DIR / "treasures" / "test_resources__test_resources__path__path_maker.txt",
        ],
    ],
    ids=str,
)
def test_resources__path__path_maker(resources, path_maker: PathMaker, ex_path: Path):
    """Build resource paths for different scopes."""
    path = resources.path(ext="txt", path_maker=path_maker)
    assert str(path) == str(ex_path)


class TestClass:
    @pytest.mark.parametrize(
        "path_maker, ex_path",
        [
            [
                TestResources.pm_function,
                THIS_DIR / "test_resources__TestClass__test_resources__dir",
            ],
            [TestResources.pm_class, THIS_DIR / "test_resources__TestClass"],
            [TestResources.pm_file, THIS_DIR / "test_resources"],
            [TestResources.pm_dir_named("stuff"), THIS_DIR / "stuff"],
        ],
        ids=str,
    )
    def test_resources__dir(self, resources, path_maker: PathMaker, ex_path: Path):
        """Build resource folders for different scopes."""
        path = resources.dir(path_maker)
        assert str(path) == str(ex_path)

    @pytest.mark.parametrize(
        "path_maker, ex_path",
        [
            [
                TestResources.pm_function,
                THIS_DIR / "test_resources__TestClass__test_resources__path__path_maker" / "data.txt",
            ],
            [
                TestResources.pm_class,
                THIS_DIR / "test_resources__TestClass" / "test_resources__path__path_maker.txt",
            ],
            [
                TestResources.pm_file,
                THIS_DIR / "test_resources" / "TestClass__test_resources__path__path_maker.txt",
            ],
            [
                TestResources.pm_dir,
                THIS_DIR / "resources" / "test_resources__TestClass__test_resources__path__path_maker.txt",
            ],
            [
                TestResources.pm_dir_named("treasures"),
                THIS_DIR / "treasures" / "test_resources__TestClass__test_resources__path__path_maker.txt",
            ],
        ],
        ids=str,
    )
    def test_resources__path__path_maker(self, resources, path_maker: PathMaker, ex_path: Path):
        """Build resource paths for different scopes."""
        path = resources.path(ext="txt", path_maker=path_maker)
        assert str(path) == str(ex_path)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# List Resources


def test_list_resources__patterns(mock_list_dir):
    listed = list_resources(
        "scenario_*.json",
        exclude=("*__actual*", "*__output*", "*__aggregate"),
    )
    assert listed == mock_list_dir.return_value
    assert mock_list_dir.call_args_list == [
        call(
            THIS_DIR / "test_resources",
            "scenario_*.json",
            exclude=("*__actual*", "*__output*", "*__aggregate"),
        )
    ]


def test_list_resources__path_maker(mock_list_dir):
    listed = list_resources(path_maker=TestResources.pm_only_dir)
    assert listed == mock_list_dir.return_value
    assert mock_list_dir.call_args_list == [
        call(
            THIS_DIR / "resources",
            "*",
            exclude=tuple(),
        )
    ]


def test_list_resources__strip_ext_True(mock_list_dir):
    mock_list_dir.return_value = [
        "resource_1.json",
        "resource_2.json",
        "resource_3.txt",
    ]
    listed = list_resources(strip_ext=True)
    assert listed == [
        "resource_1",
        "resource_2",
        "resource_3",
    ]


def test_list_resources__strip_ext_json(mock_list_dir):
    mock_list_dir.return_value = [
        "resource_1.json",
        "resource_2.json",
        "resource_3.txt",
    ]
    listed = list_resources(strip_ext=".json")
    assert listed == [
        "resource_1",
        "resource_2",
        "resource_3.txt",
    ]


def test_list__defaults(resources, mock_list_dir):
    assert resources.list() == mock_list_dir.return_value
    assert mock_list_dir.call_args_list == [
        call(
            THIS_DIR / "test_resources",
            "*",
            exclude=tuple(),
            strip_ext=False,
        )
    ]


def test_list__path_maker(resources, mock_list_dir):
    listed = resources.list(path_maker=TestResources.pm_only_dir_named("stuff"))
    assert listed == mock_list_dir.return_value
    assert mock_list_dir.call_args_list == [
        call(
            THIS_DIR / "stuff",
            "*",
            exclude=tuple(),
            strip_ext=False,
        )
    ]


def test_list__filtered(resources, mock_list_dir):
    listed = resources.list("*_load_*", exclude="*__actual.*")
    assert listed == mock_list_dir.return_value

    assert mock_list_dir.call_args_list == [
        call(
            THIS_DIR / "test_resources",
            "*_load_*",
            exclude="*__actual.*",
            strip_ext=False,
        )
    ]


def test_delete(resources):
    path = resources.path()
    path.write_text("temporary")
    assert path.is_file()

    resources.delete()
    assert not path.is_file()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Text Resources


def test_load_text(resources):
    text = resources.load_text()
    assert text == "text resource\n"


def test_save_text__dir_does_not_exist(resources):
    """We can write a file to a directory that doesn't exist yet."""
    my_dir = Path(__file__).parent
    missing_dir_name = "missing_dir"
    missing_dir = my_dir / missing_dir_name
    new_file_name = "new_file.txt"
    new_file = missing_dir / new_file_name

    # Clean up file and dir from previous run. If other files have been added, remove manually.
    new_file.unlink(missing_ok=True)
    if missing_dir.is_dir():
        missing_dir.rmdir()

    def make_missing_path(*a, **kw):
        return (missing_dir, new_file_name)

    resources.save_text("Some text is here", path_maker=make_missing_path)

    text = new_file.read_text()
    assert text == "Some text is here"

    new_file.unlink()
    missing_dir.rmdir()


def test_delete_text(resources, mock_delete):
    resources.delete_text("one", "two", path_maker=resources.pm_file)

    mock_delete.assert_called_once_with("one", "two", ext="txt", path_maker=resources.pm_file)


def test_expect_text(resources):
    resources.expect_text("some text\nsome more text\n")


def test_expect_text__mismatch(resources):
    try:
        resources.delete("actual", ext="txt")
        with pytest.raises(AssertionError):
            resources.expect_text("actual text not found")

        written_actual = resources.load_text("actual", ext="txt")
        assert written_actual == "actual text not found"

    finally:
        resources.delete("actual", ext="txt")


def test_expect_text__not_found(resources):
    test_dir = Path(__file__).with_suffix("")
    missing_file = test_dir / "test_expect_text__not_found.txt"
    created_file = test_dir / "test_expect_text__not_found__actual.txt"
    text_content = "actual text not found"

    missing_file.unlink(missing_ok=True)
    created_file.unlink(missing_ok=True)

    with pytest.raises(AssertionError) as exi:
        resources.expect_text(text_content)

    assert str(exi.value).startswith("The expectation file was not found at ")
    assert "test_expect_text__not_found.txt" in str(exi.value)

    assert not missing_file.exists()
    assert created_file.exists()
    assert created_file.read_text() == text_content

    created_file.unlink()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# JSON Resources


def test_load_json(resources):
    data = resources.load_json()
    assert data == {"look": ["what", "I", "found"]}


def test_load_json__missing(resources):
    with pytest.raises(ValueError) as exi:
        resources.load_json()

    assert str(exi.value).startswith("Failed to load JSON resource")
    assert "pytest_resources/test_resources/test_load_json__missing.json" in str(exi.value)


def test_save_json(resources):
    resources.delete_json()
    data = {
        "here": ["is", "a", "new", "one"],
        "foo": 1.23456,
    }

    resources.save_json(data, ndigits=2)

    assert resources.load_json() == {
        "here": ["is", "a", "new", "one"],
        "foo": 1.23,
    }
    resources.delete_json()


def test_delete_json(resources, mock_delete):
    resources.delete_json("one", "two", path_maker=resources.pm_file)

    mock_delete.assert_called_once_with("one", "two", ext="json", path_maker=resources.pm_file)


def test_expected_json(resources):
    resources.expect_json(
        {
            "look": ["what", "I", "found"],
            "float": 0.1234,
        }
    )


def test_expected_json__compact(resources):
    resources.json_encoder = python_compact_json_encoder
    resources.expect_json(
        {
            "look": ["what", "I", "found"],
            "float": 0.1234,
        }
    )


def test_expected_json__ndigits(resources):
    actual = {
        "float": 0.1234321,  # more digits than the resource
    }

    with pytest.raises(AssertionError):
        resources.expect_json(actual, "test_load_json")

    with pytest.raises(AssertionError):
        resources.expect_json(actual, "test_load_json", ndigits=6)

    resources.expect_json(actual, "test_load_json", ndigits=4)


def test_expected_json__default_digits(resources_4digits):
    actual = {
        "float": 0.1234321,  # more digits than the resource
    }

    assert resources_4digits.default_ndigits == 4
    resources_4digits.expect_json(actual)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Pydantic Resources


class MyModel(BaseModel):  # type: ignore
    look: list[str]


class MyModelWithDates(BaseModel):  # type: ignore
    date: date
    datetime: datetime


@pytest.mark.pydantic
def test_load_pydantic(resources):
    data = resources.load_pydantic(MyModel)
    assert data == MyModel(look=["I", "found", "this"])


def add_context(x, handler, info) -> list[str]:
    x = handler(x)
    if info.context:
        return x + info.context
    return x


class MyModelWithContext(BaseModel):  # type: ignore
    look: Annotated[
        list[str],
        WrapSerializer(add_context),
    ]
    """A property whose custom serializer adds to it whatever is in the serialization context."""


@pytest.mark.pydantic
def test_save_pydantic(resources):
    resources.delete_pydantic()
    data = MyModel(look=["saved", "pydantic", "data"])

    resources.save_pydantic(data, ndigits=2)

    assert resources.load_json() == {
        "look": ["saved", "pydantic", "data"],
    }
    resources.delete_pydantic()


@pytest.mark.pydantic
def test_save_pydantic__with_context(resources):
    resources.delete_pydantic()
    data = MyModelWithContext(look=["saved", "pydantic", "data"])

    resources.save_pydantic(data, ndigits=2, context=["with", "context"])

    assert resources.load_json() == {
        "look": ["saved", "pydantic", "data", "with", "context"],
    }
    resources.delete_pydantic()


def test_delete_pydantic(resources, mock_delete):
    resources.delete_pydantic("one", "two", path_maker=resources.pm_file)

    mock_delete.assert_called_once_with("one", "two", ext="json", path_maker=resources.pm_file)


@pytest.mark.pydantic
def test_expected_pydantic(resources):
    resources.expect_pydantic(MyModel(look=["I", "was", "expecting", "this"]))


@pytest.mark.pydantic
def test_expected_pydantic__with_context(resources):
    resources.expect_pydantic(
        MyModelWithContext(look=["I", "was", "expecting", "this"]),
        context=["with", "context"],
    )

    # Show that the expectation contains the context
    assert resources.load_json()["look"] == ["I", "was", "expecting", "this", "with", "context"]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Pydantic TypeAdapter Resources


@pytest.mark.pydantic
def test_load_pydantic_adapter(resources):
    data = resources.load_pydantic_adapter(dict[str, int])
    assert data == {"a": 1, "b": 2, "c": 3}


@pytest.mark.pydantic
def test_load_pydantic_adapter__failing(resources):
    with pytest.raises(ValidationError) as exi:
        resources.load_pydantic_adapter(dict[str, int])

    assert exi.value.errors()[0]["msg"] == ("Input should be a valid integer, unable to parse string as an integer")


@pytest.mark.pydantic
def test_save_pydantic_adapter(resources):
    resources.delete_pydantic()
    data: dict[int, MyModelWithContext] = {
        1: MyModelWithContext(look=["I", "was", "expecting", "this"]),
        2: MyModel(look=["and", "also", "this"]),  # Won't have the context
    }

    resources.save_pydantic_adapter(data, context=["with", "context"])

    assert resources.load_json() == {
        "1": {"look": ["I", "was", "expecting", "this", "with", "context"]},
        "2": {"look": ["and", "also", "this"]},  # without context
    }
    resources.delete_pydantic()


def test_delete_pydantic_adapter(resources, mock_delete):
    resources.delete_pydantic("one", "two", path_maker=resources.pm_file)

    mock_delete.assert_called_once_with("one", "two", ext="json", path_maker=resources.pm_file)


@pytest.mark.pydantic
def test_expected_pydantic_adapter(resources):
    data: dict[int, MyModelWithContext] = {
        1: MyModelWithContext(look=["I", "was", "expecting", "this"]),
        2: MyModel(look=["and", "also", "this"]),  # Won't have the context
    }
    resources.expect_pydantic_adapter(data, context=["with", "context"])
