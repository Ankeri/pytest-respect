"""Fixture for loading resources relative to test functions and fixtures."""

import builtins
import fnmatch
import inspect
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from types import EllipsisType
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, TypeAdapter
from pytest import FixtureRequest

__tracebackhide__ = True  # Dont' include in pytest tracebacks

from pytest_respect.utils import prepare_for_json_encode

DEFAULT_RESOURCES_DIR = "resources"

PMT = TypeVar("PMT", bound=BaseModel)
T = TypeVar("T")


class PathMaker(Protocol):
    """Protocol for functions which determine a directory and base file-name from the coordinates of a test function."""

    def __call__(
        self,
        test_dir: Path,
        test_file_name: str,
        test_class_name: str | None,
        test_name: str,
    ) -> tuple[Path, str | None]: ...


def list_dir(
    dir: Path,
    include: str | Sequence[str] = "*",
    *,
    exclude: str | Sequence[str] = tuple(),
    strip_ext: str | bool = False,
) -> list[str]:
    """List the names of the files in the directory, including and excluding globs."""
    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]

    names: set[str] = set()
    for inc in include:
        names.update(path.name for path in dir.glob(inc))
    for exc in exclude:
        names = {name for name in names if not fnmatch.fnmatch(name, exc)}
    name_list = sorted(names)
    name_list = strip_extensions(name_list, strip_ext=strip_ext)
    return name_list


def list_resources(
    include: str | Sequence[str] = "*",
    *,
    exclude: str | Sequence[str] = tuple(),
    path_maker: PathMaker | None = None,
    strip_ext: str | bool = False,
) -> builtins.list[str]:
    """Static version of TestResources.list method which can be used for parametric tests.

    This version does not have access to a FixtureRequest object so we use the directory of the calling module instead.
    We have no test class or test function to pass to the path_maker and we use only the directory from its return
    value.

    Parametric Test Example:

        >>> @pytest.mark.parametrize("curve_name", list_resources("power_curve_*.json")
        >>> def test_power_curve(resources, curve_name):
        >>>    curve = resources.load_pydantic(PowerCurve, curve_name)
        >>>    assert len(curve.points) >= 2

    Parametric Fixture Example:

        >>> @pytest.fixture(params=list_resources("power_curve_*.json", exclude=["*__actual*"], strip_ext=".json"))
        >>> def each_power_curve(request, resources) -> PowerCurve:
        >>>    return resources.load_pydantic(PowerCurve, request.param)

    Args:

        include: one or more glob patterns for filenames to include
        exclude: zero or more glob patterns for filenames to exclude
        path_maker: Function to turn test co-ordinates into a directory to look for
            resources in. The default uses the test file name for the directory.
        strip_ext: Whether to strip extension from listed resource file names. If
            True or False then strip all or no extensions from last dot.
            If string, then strip only that string from the ends of file names. A
            strip_ext string must include the dot (if wanted) to allow stripping
            suffixes such as `__bad.json`

    """
    if path_maker is None:
        path_maker = TestResources.pm_only_class

    calling_frame = inspect.stack()[1]
    test_file = Path(calling_frame.filename)

    dir_path, _ = path_maker(
        test_dir=test_file.parent,
        test_file_name=test_file.name.rsplit(".", 1)[0],
        test_class_name=None,
        test_name="",
    )

    resources = list_dir(dir_path, include, exclude=exclude)
    resources = strip_extensions(resources, strip_ext)
    return resources


def strip_extensions(
    resources: Iterable[str],
    strip_ext: str | bool = False,
) -> list[str]:
    """Strip file extensions from a list of resources, depending on strip_ext.

    Args:
        resources: list of resources to maybe strip extensions from.
        strip_ext: Whether to strip extension from listed resource file names. If
            True or False then strip all or no extensions from last dot.
            If string, then strip only that string from the ends of file names. A
            strip_ext string must include the dot (if wanted) to allow stripping
            suffixes such as `__bad.json`

    Returns:
        The original resources or a copy with extensions stripped.

    """
    if strip_ext is True:
        resources = [r.rsplit(".", 1)[0] for r in resources]
    elif isinstance(strip_ext, str):
        resources = [r.removesuffix(strip_ext) for r in resources]
    elif not isinstance(strip_ext, list):
        resources = list(resources)
    return resources


def python_json_encoder(obj: Any) -> str:
    """Standard JSON encoder in very verbose mode."""
    return json.dumps(obj, sort_keys=True, indent=2)


def python_compact_json_encoder(obj: Any) -> str:
    """Standard JSON encoder in very compact mode."""
    return json.dumps(obj, sort_keys=True, indent=None)


def python_json_loader(text: str) -> Any:
    """Standard JSON loader."""
    return json.loads(text)


class TestResources:
    __test__ = False  # Don't try to collect this as a test

    def __init__(
        self,
        request: FixtureRequest,
        ndigits: int | None = None,
    ):
        """Create test resources instance, usually in a function-scoped fixture.

        Args:
            request: The pytest fixture request object.
            ndigits: How many digits to round floats to by default when comparing JSON
                data and objects which are converted to JSON before comparison. Defaults
                to no rounding.

        """
        self.request: FixtureRequest = request

        self.json_encoder = python_json_encoder
        self.json_loader = python_json_loader

        self.default_ndigits = ndigits
        """How many digits to round floats to by default when comparing JSON data."""

        self.default_path_maker = TestResources.pm_class
        """
        Default method to make paths to resources. Starts as pm_class making resource
        paths like ``<dir>/test_file__TestClass/test_method.<ext>``, omitting the
        ``__TestClass`` part if we are not in a class.
        """

    # # # BUILD RELATIVE PATHS # # #

    @staticmethod
    def pm_function(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> tuple[Path, str | None]:
        """PathMaker to build directory from test_file, class if present, and function. No contribution is made to the
        file name.

        - ``<dir>/test_file__TestClass__test_method/data.<ext>``
        - ``<dir>/test_file__test_method/data.<ext>``
        """
        if test_class_name:
            dir = test_dir / f"{test_file_name}__{test_class_name}__{test_name}"
        else:
            dir = test_dir / f"{test_file_name}__{test_name}"

        return dir, None

    @staticmethod
    def pm_class(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> tuple[Path, str | None]:
        """PathMaker to build directory from test_file and class if present, and file-name from test method.

        This is the default method for constructing resource paths.

        - ``<dir>/test_file__TestClass/test_method.<ext>``
        - ``<dir>/test_file/test_method.<ext>``
        """
        if test_class_name:
            dir = test_dir / f"{test_file_name}__{test_class_name}"
        else:
            dir = test_dir / test_file_name
        return dir, test_name

    @staticmethod
    def pm_only_class(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> tuple[Path, str | None]:
        """PathMaker to build directory from test_file and class if present and contribute nothing to the file-name

        - ``<dir>/test_file__TestClass/data.<ext>``
        - ``<dir>/test_file/data.<ext>``
        """
        if test_class_name:
            dir = test_dir / f"{test_file_name}__{test_class_name}"
        else:
            dir = test_dir / test_file_name
        return dir, None

    @staticmethod
    def pm_file(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> tuple[Path, str | None]:
        """PathMaker to build directory from test_file and file-name from test class if present, and test method.

        - ``<dir>/test_file__TestClass/test_method.<ext>``
        - ``<dir>/test_file/test_method.<ext>``
        """
        if test_class_name:
            file = f"{test_class_name}__{test_name}"
        else:
            file = test_name
        return test_dir / test_file_name, file

    @staticmethod
    def pm_only_file(
        test_dir: Path,
        test_file_name: str,
        test_class_name: str | None = None,
        test_name: str | None = None,
    ) -> tuple[Path, str | None]:
        """PathMaker to build directory from test_file and contribute to the file-name.

        - ``<dir>/test_file/data.<ext>``
        """
        return test_dir / test_file_name, None

    @staticmethod
    def pm_dir(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> tuple[Path, str | None]:
        """PathMaker to use "resources" for directory and build file-name from test file, test class if present and
        test function.

        - ``<dir>/resources/test_file__TestClass__test_method.<ext>``
        - ``<dir>/resources/test_file__test_method.<ext>``
        """
        path_maker = TestResources.pm_dir_named(DEFAULT_RESOURCES_DIR)
        return path_maker(test_dir, test_file_name, test_class_name, test_name)

    @staticmethod
    def pm_dir_named(dir_name: str = DEFAULT_RESOURCES_DIR) -> PathMaker:
        """PathMaker to use the given name for directory and build file-name from test file, test class if present and
        test function.

        - ``<dir>/<dir_name>/test_file__TestClass__test_method.<ext>``
        - ``<dir>/<dir_name>/test_file__test_method.<ext>``
        """

        def path_from_dir(
            test_dir: Path,
            test_file_name: str,
            test_class_name: str | None,
            test_name: str,
        ) -> tuple[Path, str | None]:
            if test_class_name:
                file = f"{test_file_name}__{test_class_name}__{test_name}"
            else:
                file = f"{test_file_name}__{test_name}"
            return test_dir / dir_name, file

        return path_from_dir

    @staticmethod
    def pm_only_dir(
        test_dir: Path,
        test_file_name: str,
        test_class_name: str | None = None,
        test_name: str | None = None,
    ) -> tuple[Path, str | None]:
        """Use "resources" for directory and nothing for the file-name."""
        return test_dir / DEFAULT_RESOURCES_DIR, None

    @staticmethod
    def pm_only_dir_named(dir_name: str = DEFAULT_RESOURCES_DIR) -> PathMaker:
        """Use the given name for directory nothing for the file-name."""

        def path_from_dir(
            test_dir: Path,
            test_file_name: str,
            test_class_name: str | None,
            test_name: str,
        ) -> tuple[Path, str | None]:
            return test_dir / dir_name, None

        return path_from_dir

    def dir(self, path_maker: PathMaker | None = None) -> Path:
        """Directory for resources belonging to the test.

        Args:
            path_maker: Function to turn test co-ordinates into a directory and partial
                file-name for the resource. The file part will be ignored.

        """
        if path_maker is None:
            path_maker = self.default_path_maker

        test_file = Path(self.request.node.fspath)
        test_class: type | None = self.request.node.cls

        dir_path, base_name = path_maker(
            test_dir=test_file.parent,
            test_file_name=test_file.name.rsplit(".", 1)[0],
            test_class_name=test_class.__name__ if test_class else None,
            test_name=self.request.node.originalname,
        )

        return dir_path

    def path(
        self,
        *parts: Any,
        ext: str | None = None,
        path_maker: PathMaker | None = None,
    ) -> Path:
        """Path to a resource file within this test file/class's directory.

        Args:
            parts: Concatenate these parts to the function name, with __ separator to
                make file-name.
            ext: Add this extension to the file-name if not already present. Defaults
                to nothing which can be appropriate if we knot that the last ``part``
                already has an extension.
            path_maker: Function to turn test co-ordinates into a directory and partial
                file-name for the resource. Defaults to one which uses the test file
                (and class if present) for the dir and the test function for the file.

        """
        if path_maker is None:
            path_maker = self.default_path_maker

        test_file = Path(self.request.node.fspath)
        test_class: type | None = self.request.node.cls

        dir_path, base_name = path_maker(
            test_dir=test_file.parent,
            test_file_name=test_file.name.rsplit(".", 1)[0],
            test_class_name=test_class.__name__ if test_class else None,
            test_name=self.request.node.originalname,
        )

        name_parts: list[str] = []
        if base_name:
            name_parts.append(base_name)
        name_parts.extend(map(str, parts))
        if not name_parts:
            # If we have not file-name parts from anywhere, then fall back to "data"
            name_parts = ["data"]

        name = "__".join(name_parts)
        if ext and not name.endswith(f".{ext}"):
            name = f"{name}.{ext}"
        return dir_path / name

    # # # LIST RESOURCES # # #

    def list(
        self,
        include: str | Sequence[str] = "*",
        *,
        exclude: str | Sequence[str] = tuple(),
        path_maker: PathMaker | None = None,
        strip_ext: str | bool = False,
    ) -> list[str]:
        """List the names of the resources in the folder.

        Args:
            include: one or more glob patterns for filenames to include
            exclude: zero or more glob patterns for filenames to exclude
            path_maker: Function to turn test co-ordinates into a directory and partial
                file-name for the resource. The file part will be ignored.
        strip_ext: Whether to strip extension from listed resource file names. If
            True or False then strip all or no extensions from last dot.
            If string, then strip only that string from the ends of file names. A
            strip_ext string must include the dot (if wanted) to allow stripping
            suffixes such as `__bad.json`

        """
        dir: Path = self.dir(path_maker)
        return list_dir(dir, include, exclude=exclude, strip_ext=strip_ext)

    # # # DELETE RESOURCE # # #

    def delete(
        self,
        *parts,
        ext: str | None = None,
        path_maker: PathMaker | None = None,
    ):
        """Delete a string resource relative to the current test."""
        path = self.path(*parts, ext=ext, path_maker=path_maker)
        path.unlink(missing_ok=True)

    def delete_json(
        self,
        *parts,
        path_maker: PathMaker | None = None,
    ):
        """Delete a json resource relative to the current test."""
        path = self.path(*parts, ext="json", path_maker=path_maker)
        path.unlink(missing_ok=True)

    # # # LOAD DATA FROM RESOURCE # # #

    def load_text(
        self,
        *parts,
        ext: str = "txt",
        path_maker: PathMaker | None = None,
    ) -> str:
        """Load a string resource relative to the current test."""
        path = self.path(*parts, ext=ext, path_maker=path_maker)
        return path.read_text()

    def load_json(
        self,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
    ) -> Any:
        """Load a json resource relative to the current test."""
        path = self.path(*parts, ext=ext, path_maker=path_maker)
        try:
            text = path.read_text()
            return self.json_loader(text)
        except Exception as e:
            raise ValueError(f"Failed to load JSON resource {path}: {repr(e)}") from e

    def load_pydantic(
        self,
        model_class: type[PMT],
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
    ) -> PMT:
        """Load a pydantic resource relative to the current test."""
        data = self.load_json(*parts, ext=ext, path_maker=path_maker)
        return model_class.model_validate(data)

    def load_pydantic_adapter(
        self,
        type_: type[T] | TypeAdapter[T],
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
    ) -> T:
        """Load a resource with a pydantic TypeAdapter relative to the current test."""
        data = self.load_json(*parts, ext=ext, path_maker=path_maker)
        adapter = type_ if isinstance(type_, TypeAdapter) else TypeAdapter(type_)
        return adapter.validate_python(data)

    # # # SAVA DATA TO RESOURCE # # #

    def save_text(
        self,
        text: str,
        *parts,
        ext: str = "txt",
        path_maker: PathMaker | None = None,
    ) -> None:
        """Write a string to a resource relative to the current test."""
        path = self.path(*parts, ext=ext, path_maker=path_maker)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        print(f"write {len(text)} chars to {path}")
        path.parent.mkdir(parents=False, exist_ok=True)
        path.write_text(text)

    def save_json(
        self,
        data: Any,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        ndigits: int | None | EllipsisType = ...,
    ) -> None:
        """Write JSON data to a resource relative to the current test."""
        text = self.data_to_json(data, ndigits=ndigits)
        self.save_text(text, *parts, ext=ext, path_maker=path_maker)

    def data_to_json(self, data: Any, ndigits: int | None | EllipsisType = ...) -> str:
        """Convert data to json string for use by both expectations and save_json."""
        if ndigits is ...:
            ndigits = self.default_ndigits
        if ndigits is not None:
            data = prepare_for_json_encode(data, ndigits=ndigits)
        text = self.json_encoder(data)
        if not text.endswith("\n"):
            text += "\n"
        return text

    # # # EXPECTED FILE CONTENT # # #

    def expect_text(
        self,
        actual: str,
        *parts,
        ext: str = "txt",
        path_maker: PathMaker | None = None,
    ) -> None:
        """Assert that the actual value matches the content from resource."""
        expected_path = self.path(*parts, ext=ext, path_maker=path_maker)
        actual_path = self.path(*parts, "actual", ext=ext, path_maker=path_maker)

        if not expected_path.is_file():
            expected_path.parent.mkdir(parents=False, exist_ok=True)
            actual_path.write_text(actual)
            raise AssertionError(
                f"The expectation file was not found at {expected_path}. The actual value has been written to {actual_path}."
            )

        expected = expected_path.read_text()

        try:
            assert actual == expected, (
                f"The actual value did not match the content of {expected_path}. It has been written to {actual_path} for comparison."
            )
            if actual_path.exists():
                actual_path.unlink(missing_ok=True)
                print("removing matching actual file", actual_path)
        except AssertionError:
            actual_path.write_text(actual)
            raise

    def expect_json(
        self,
        actual: Any,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        ndigits: int | None | EllipsisType = ...,
    ) -> None:
        """Assert that the actual value encodes to the JSON content from resource."""
        actual_text = self.data_to_json(actual, ndigits=ndigits)
        self.expect_text(actual_text, *parts, ext=ext, path_maker=path_maker)

    def expect_pydantic(
        self,
        actual: BaseModel,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        ndigits: int | None | EllipsisType = ...,
    ) -> None:
        """Assert that the actual value encodes to the JSON content from resource."""
        actual_data = actual.model_dump(
            mode="json",  # convert fields such as datetime to JSON serializable types
        )
        self.expect_json(
            actual_data,
            *parts,
            ext=ext,
            path_maker=path_maker,
            ndigits=ndigits,
        )
