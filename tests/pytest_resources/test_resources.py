from datetime import date, datetime
from pathlib import Path
from typing import Annotated
from unittest.mock import Mock, call

import pytest
from pytest import FixtureRequest
from pytest_mock import MockerFixture

from pytest_respect.resources import (
    Defaults,
    JsonLoader,
    PathMaker,
    TestResources,
    list_dir,
    list_resources,
    python_compact_json_encoder,
    python_json_encoder,
    python_json_loader,
)
from pytest_respect.utils import AbortJsonPrep

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
def mock_list_dir(mocker: MockerFixture):
    return mocker.patch(
        "pytest_respect.resources.list_dir",
        autospec=True,
        return_value=["scenario_1.json", "scenario_2.json"],
    )


@pytest.fixture
def resources(request: FixtureRequest) -> TestResources:
    """The fixture being tested."""
    return TestResources(
        request,
        accept_count=0,  # We set accept in individual tests instead of using the --respect-accept flag.
    )


@pytest.fixture
def mock_delete(resources, mocker: MockerFixture):
    """Mock resources.delete method"""
    return mocker.patch.object(resources, "delete", autospec=True)


@pytest.fixture
def resources_4digits(request: FixtureRequest) -> TestResources:
    """A TestResrouces fixture which defaults to rounding to 4 digits."""
    resources = TestResources(request)
    resources.default.ndigits = 4
    return resources


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Defaults


def test_Defaults_ndigits():
    defaults = Defaults()
    assert defaults._ndigits(...) is None
    assert defaults._ndigits(None) is None
    assert defaults._ndigits(4) == 4


def test_Defaults_json_encoder():
    defaults = Defaults()
    assert defaults._json_encoder(...) is python_json_encoder
    assert defaults._json_encoder(None) is python_json_encoder
    assert defaults._json_encoder(python_compact_json_encoder) is python_compact_json_encoder


def test_Defaults_json_loader():
    defaults = Defaults()
    assert defaults._json_loader(...) is python_json_loader
    assert defaults._json_loader(None) is python_json_loader

    mock_loader = Mock(spec=JsonLoader)
    assert defaults._json_loader(mock_loader) is mock_loader


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


@pytest.fixture(params=list_resources("*.json", exclude=["*__actual*"], strip_ext=True))
def each_resource_name(request) -> str:
    """Dependants run for name of each file in the resources folder."""
    return request.param


def test_list_resources(resources, each_resource_name):
    # The resources names already include the full file name
    print(each_resource_name)
    resources.default.path_maker = resources.pm_only_file
    path = resources.path(each_resource_name, ext="json")
    assert path.is_file()
    resources.load_json(each_resource_name)


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

    try:
        # Clean up file and dir from previous run. If other files have been added, remove manually.
        new_file.unlink(missing_ok=True)
        if missing_dir.is_dir():
            missing_dir.rmdir()

        def make_missing_path(*a, **kw):
            return (missing_dir, new_file_name)

        resources.save_text("Some text is here", path_maker=make_missing_path)

        text = new_file.read_text()
        assert text == "Some text is here"

    finally:
        new_file.unlink(missing_ok=True)
        if missing_dir.is_dir():
            missing_dir.rmdir()


def test_delete_text(resources, mock_delete):
    resources.delete_text("one", "two", path_maker=resources.pm_file)

    mock_delete.assert_called_once_with("one", "two", ext="txt", path_maker=resources.pm_file)


@pytest.mark.parametrize("accept", [1, 0])
def test_expect_text__match(resources, accept: bool):
    resources.accept_count = accept
    resources.expect_text("some text\nsome more text\n")


def test_expect_text__mismatch(resources):
    try:
        resources.delete_text("actual")
        with pytest.raises(AssertionError):
            resources.expect_text("actual text not found")

        # Actual file was written
        actual_path = resources.path("actual", ext="txt")
        assert actual_path.exists()
        written_actual = resources.load_text("actual")
        assert written_actual == "actual text not found"

        # Expected file was not changed
        resources.expect_text("original expected test\n")

    finally:
        resources.delete_text("actual")


def test_expect_text__mismatch__accept(resources, capsys):
    resources.accept_count = 1
    try:
        resources.save_text("previous actual\n", "actual")
        resources.save_text("original expected test\n")

        resources.expect_text("updated expected test\n")

        # The actual file was removed
        actual_path = resources.path("actual", ext="txt")
        assert not actual_path.exists()

        # The expected file was overwritten
        written_expected = resources.load_text()
        assert written_expected == "updated expected test\n"

        expected_path = resources.path(ext="txt")
        assert capsys.readouterr().out.splitlines()[-1] == f"The expectation file was updated at {expected_path}."

    finally:
        resources.delete_text()
        resources.delete_text("actual")


def test_expect_text__not_found(resources):
    test_dir = Path(__file__).with_suffix("")
    expected_file = test_dir / "test_expect_text__not_found.txt"
    actual_file = test_dir / "test_expect_text__not_found__actual.txt"
    text_content = "actual text not found"

    expected_file.unlink(missing_ok=True)
    actual_file.unlink(missing_ok=True)

    try:
        with pytest.raises(AssertionError) as exi:
            resources.expect_text(text_content)

        assert str(exi.value).startswith("The expectation file was not found at ")
        assert "test_expect_text__not_found.txt" in str(exi.value)

        assert not expected_file.exists()
        assert actual_file.exists()
        assert actual_file.read_text() == text_content

    finally:
        expected_file.unlink(missing_ok=True)
        actual_file.unlink(missing_ok=True)


def test_expect_text__not_found__accept(resources, capsys):
    resources.accept_count = 1

    test_dir = Path(__file__).with_suffix("")
    expected_file = test_dir / "test_expect_text__not_found__accept.txt"
    actual_file = test_dir / "test_expect_text__not_found__accept__actual.txt"
    text_content = "actual text not found"

    expected_file.unlink(missing_ok=True)
    actual_file.write_text("previous actual\n")

    try:
        resources.expect_text(text_content)

        assert expected_file.exists()
        assert expected_file.read_text() == text_content

        assert not actual_file.exists()

        assert capsys.readouterr().out.splitlines()[-1] == f"A new expectation file was written to {expected_file}."
    finally:
        expected_file.unlink(missing_ok=True)
        actual_file.unlink(missing_ok=True)


def test_accept_count(resources):
    assert resources.accept_count == 0
    resources.accept_count = 2
    resources.delete_text()  # Start with no expectation and accept 2 mismatches

    # Allow one failure
    resources.expect_text("first value")
    assert resources.accept_count == 1

    # Allow another failure
    resources.expect_text("second value")
    assert resources.accept_count == 0

    # Don't allow a third failure
    with pytest.raises(AssertionError):
        resources.expect_text("third value")

    # Second value is still in file
    resources.expect_text("second value")

    resources.delete_text()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# JSON Resources


def test_data_to_json__add_json_prepper(resources):
    class CustomType:
        def __init__(self, name: str):
            self.name = name

    data = {
        1: "something",
        2: CustomType("thingy"),
    }

    resources.add_json_prepper(CustomType, lambda ct: "my custom " + ct.name)

    resources.default.json_encoder = python_compact_json_encoder
    assert resources.data_to_json(data) == '{"1": "something", "2": "my custom thingy"}\n'


def test_data_to_json__abort_json_prepper(resources):
    class CustomType:
        def __init__(self, name: str):
            self.name = name

        def __str__(self):
            return f"CustomType({self.name})"

    aborting_prepper_called = False

    def aborting_prepper(ct: CustomType):
        nonlocal aborting_prepper_called
        aborting_prepper_called = True
        raise AbortJsonPrep()

    data = {
        1: "something",
        2: CustomType("thingy"),
    }

    resources.add_json_prepper(CustomType, aborting_prepper)

    resources.default.json_encoder = python_compact_json_encoder
    assert resources.data_to_json(data) == '{"1": "something", "2": "CustomType(thingy)"}\n'

    assert aborting_prepper_called


def test_load_json(resources):
    data = resources.load_json()
    assert data == {"look": ["what", "I", "found"]}


def test_load_json__missing(resources):
    with pytest.raises(ValueError) as exi:
        resources.load_json()

    assert str(exi.value).startswith("Failed to load JSON resource")
    assert "pytest_resources/test_resources/test_load_json__missing.json" in str(exi.value)


def test_load_json__overrides(resources):
    json_loader = Mock(wraps=resources.default.json_loader)

    data = resources.load_json(
        "test_load_json",
        path_maker=resources.pm_only_file,  # Override allows us to find the file
        json_loader=json_loader,
    )

    assert data == {"look": ["what", "I", "found"]}
    assert json_loader.call_count == 1


def test_save_json(resources):
    resources.delete_json()
    data = {
        "here": ["is", "a", "new", "one"],
        "foo": 1.23456,
    }

    resources.save_json(data)

    assert resources.load_json() == {
        "here": ["is", "a", "new", "one"],
        "foo": 1.23456,
    }
    resources.delete_json()


def test_save_json__overrides(resources):
    resources.delete_json()

    json_encoder = Mock(wraps=resources.default.json_encoder)
    data = {
        "here": ["is", "a", "new", "one"],
        "foo": 1.23456,
    }

    resources.save_json(
        data,
        json_encoder=json_encoder,
        ndigits=2,
    )

    assert resources.load_json() == {
        "here": ["is", "a", "new", "one"],
        "foo": 1.23,
    }
    assert json_encoder.call_count == 1
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
    resources.default.json_encoder = python_compact_json_encoder
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

    assert resources_4digits.default.ndigits == 4
    resources_4digits.expect_json(actual)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Pydantic Resources


class MyModel(BaseModel):  # type: ignore
    look: list[str | float]


class MyModelWithDates(BaseModel):  # type: ignore
    date: date
    datetime: datetime


@pytest.mark.pydantic
def test_load_pydantic(resources):
    data = resources.load_pydantic(MyModel)
    assert data == MyModel(look=["I", "found", "this"])


@pytest.mark.pydantic
def test_load_pydantic__overrides(resources):
    json_loader = Mock(wraps=resources.default.json_loader)

    data = resources.load_pydantic(
        MyModel,
        "test_load_pydantic",
        path_maker=resources.pm_only_file,  # Override allows us to find the file
        json_loader=json_loader,
    )

    assert data == MyModel(look=["I", "found", "this"])
    assert json_loader.call_count == 1


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
    data = MyModel(look=["saved", "pydantic", "data", 1.2345])

    resources.save_pydantic(data)

    assert resources.load_json() == {
        "look": ["saved", "pydantic", "data", 1.2345],
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


@pytest.mark.pydantic
def test_save_pydantic__overrides(resources):
    resources.delete_pydantic()

    json_encoder = Mock(wraps=resources.default.json_encoder)
    data = MyModel(look=["saved", "pydantic", "data", 1.2345])

    resources.save_pydantic(data, json_encoder=json_encoder, ndigits=2)

    assert resources.load_json() == {
        "look": ["saved", "pydantic", "data", 1.23],
    }
    resources.delete_pydantic()

    assert json_encoder.call_count == 1


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
def test_load_pydantic_adapter__overrides(resources):
    json_loader = Mock(wraps=resources.default.json_loader)

    data = resources.load_pydantic_adapter(
        dict[str, int],
        "test_load_pydantic_adapter",
        path_maker=resources.pm_only_file,  # Override allows us to find the file
        json_loader=json_loader,
    )

    assert data == {"a": 1, "b": 2, "c": 3}
    assert json_loader.call_count == 1


@pytest.mark.pydantic
def test_save_pydantic_adapter(resources):
    resources.delete_pydantic()
    data: dict[int, MyModelWithContext] = {
        1: MyModelWithContext(look=["I", "was", "expecting", "this"]),
        2: MyModel(look=["and", "also", "this", 1.2345]),  # Won't have the context
    }

    resources.save_pydantic_adapter(data, context=["with", "context"])

    assert resources.load_json() == {
        "1": {"look": ["I", "was", "expecting", "this", "with", "context"]},
        "2": {"look": ["and", "also", "this", 1.2345]},  # without context
    }
    resources.delete_pydantic()


@pytest.mark.pydantic
def test_save_pydantic_adapter__overrides(resources):
    resources.delete_pydantic()

    json_encoder = Mock(wraps=resources.default.json_encoder)
    data: dict[int, MyModelWithContext] = {
        1: MyModelWithContext(look=["I", "was", "expecting", "this"]),
        2: MyModel(look=["and", "also", "this", 1.2345]),  # Won't have the context
    }

    resources.save_pydantic_adapter(
        data,
        json_encoder=json_encoder,
        ndigits=2,
        context=["with", "context"],
    )

    assert resources.load_json() == {
        "1": {"look": ["I", "was", "expecting", "this", "with", "context"]},
        "2": {"look": ["and", "also", "this", 1.23]},  # without context
    }
    assert json_encoder.call_count == 1

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
