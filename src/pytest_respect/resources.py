"""Fixture for loading resources relative to test functions and fixtures."""

import builtins
import fnmatch
import inspect
import json
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from types import EllipsisType, UnionType
from typing import Any, Protocol, TypeVar

from pytest import FixtureRequest

# Optional imports falling back to stub implementations to make the type checker happy
try:
    from pydantic import BaseModel, TypeAdapter
except ImportError:  # pragma: no cover
    from ._fakes import BaseModel, TypeAdapter


# Dont' include in pytest tracebacks. We patch this out in unit tests to see where in our code errors occur.
__tracebackhide__ = True

from pytest_respect.utils import coalesce, prepare_for_json_encode

DEFAULT_RESOURCES_DIR = "resources"

PMT = TypeVar("PMT", bound=BaseModel)
T = TypeVar("T")


PathParts = tuple[Path, str | None]
"""Directory and base file-name for a resource path"""


class PathMaker(Protocol):
    """Protocol for functions which determine a directory and base file-name from the coordinates of a test function."""

    def __call__(
        self,
        test_dir: Path,
        test_file_name: str,
        test_class_name: str | None,
        test_name: str,
    ) -> PathParts: ...


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Static Resource Listing


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
        path_maker = TestResources.pm_only_file

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


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# JSON encoders & Decoders

JsonEncoder = Callable[[Any], str]
"""Function to convert data to JSON encoded text."""

JsonLoader = Callable[[str], Any]
"""Function to convert JSON encoded text to python data."""


def python_json_encoder(obj: Any) -> str:
    """Standard JSON encoder in very verbose mode."""
    return json.dumps(obj, sort_keys=True, indent=2)


def python_compact_json_encoder(obj: Any) -> str:
    """Standard JSON encoder in very compact mode."""
    return json.dumps(obj, sort_keys=True, indent=None)


def python_json_loader(text: str) -> Any:
    """Standard JSON loader."""
    return json.loads(text)


class Defaults:
    def __init__(self):
        self.ndigits: int | None = None
        """How many digits to round floats to by default when comparing JSON data."""

        self.json_encoder: JsonEncoder = python_json_encoder
        """Function used to convert data to JSON encoded text. Defaults to standard python JSON encoding."""

        self.json_loader: JsonLoader = python_json_loader
        """Function used to convert JSON encoded text to python data. Defaults to standard python JSON decoding."""

        self.path_maker: PathMaker = TestResources.pm_class
        """
        Function used to make paths to resources. Defaults to as pm_class making resource paths like
        ``<dir>/test_file__TestClass/test_method.<ext>``, omitting the ``__TestClass`` part if we are not in a class.
        """

    def _ndigits(self, value: int | None | EllipsisType) -> int | None:
        """Resolve ndigits given the default value here and optional override."""
        return coalesce(self.ndigits, value, nonable=True)

    def _json_encoder(self, value: JsonEncoder | None | EllipsisType) -> JsonEncoder:
        """Resolve json_encoder given the default value here and optional override."""
        return coalesce(self.json_encoder, value)

    def _json_loader(self, value: JsonLoader | None | EllipsisType) -> JsonLoader:
        """Resolve json_loader given the default value here and optional override."""
        return coalesce(self.json_loader, value)

    def _path_maker(self, value: PathMaker | None | EllipsisType) -> PathMaker:
        """Resolve path_maker given the default value here and optional override."""
        return coalesce(self.path_maker, value)


class TestResources:
    __test__ = False  # Don't try to collect this as a test

    def __init__(self, request: FixtureRequest, accept_count: int = 0):
        """Create test resources instance, usually in a function-scoped fixture.

        Args:
            request: The pytest fixture request object.
            ndigits: How many digits to round floats to by default when comparing JSON data and objects which are
                converted to JSON before comparison. Defaults to no rounding.
            accept_count: Accept the actual results for this many mismatches before failing the test.

        """
        self.request: FixtureRequest = request
        """The pytest fixture request that we get context information from."""

        self.accept_count: int = accept_count
        """Mimatches remaining before we fail the test."""

        self.default: Defaults = Defaults()
        """Default behaviours. They can be optionally overridden in methods that use them."""

        self._extra_preppers: list[tuple[type | UnionType, Callable[[Any], Any]]] = []
        """JSON Preppers to apply after the global JSON_PREPPERS."""

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Path Makers

    @staticmethod
    def pm_function(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> PathParts:
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
    def pm_class(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> PathParts:
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
    def pm_only_class(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> PathParts:
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
    def pm_file(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> PathParts:
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
    def pm_dir(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> PathParts:
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
        ) -> PathParts:
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
    ) -> PathParts:
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
        ) -> PathParts:
            return test_dir / dir_name, None

        return path_from_dir

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Paths

    def dir(self, path_maker: PathMaker | None = None) -> Path:
        """Directory for resources belonging to the test.

        Args:
            path_maker: Function to turn test co-ordinates into a directory and partial
                file-name for the resource. The file part will be ignored.

        """
        path_maker = self.default._path_maker(path_maker)
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
        path_maker = self.default._path_maker(path_maker)
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

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # List Resources

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

    def delete(
        self,
        *parts,
        ext: str | None = None,
        path_maker: PathMaker | None = None,
    ):
        """Delete a string resource relative to the current test."""
        path = self.path(*parts, ext=ext, path_maker=path_maker)
        path.unlink(missing_ok=True)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Text Resources

    def load_text(
        self,
        *parts,
        ext: str = "txt",
        path_maker: PathMaker | None = None,
    ) -> str:
        """Load a string resource relative to the current test."""
        path = self.path(*parts, ext=ext, path_maker=path_maker)
        return path.read_text()

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

    def delete_text(
        self,
        *parts,
        ext: str = "txt",
        path_maker: PathMaker | None = None,
    ):
        """Delete a json resource relative to the current test."""
        self.delete(*parts, ext=ext, path_maker=path_maker)

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
            if self._accept_one():
                expected_path.write_text(actual)
                print(f"A new expectation file was written to {expected_path}.")
                actual_path.unlink(missing_ok=True)
            else:
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
            if self._accept_one():
                print(f"The expectation file was updated at {expected_path}.")
                expected_path.write_text(actual)
                actual_path.unlink(missing_ok=True)
            else:
                actual_path.write_text(actual)
                raise

    def _accept_one(self) -> bool:
        """Whether to accept one more mismatch before failing the test."""
        self.accept_count -= 1
        return self.accept_count >= 0

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # JSON Resources

    def add_json_prepper(self, type_: type | UnionType, prepper: Callable[[Any], Any]) -> None:
        """Register a local JSON prepper for a given type, including sub-classes.

        The prepper can return a few kinds of values:
        - Simple value: encoded as-is and must be JSON serializable.
        - Dict: encoded recursively but must have keys that are supported by the json_encoder in use, usually str.
        - Collection: list, tuple, set, etc will be recursively encoded as a list.

        It can also raise AbortJsonPrep to skip this prepper and continue trying others.
        """
        self._extra_preppers.append((type_, prepper))

    def load_json(
        self,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_loader: JsonLoader | EllipsisType = ...,
    ) -> Any:
        """Load a json resource relative to the current test."""
        path = self.path(*parts, ext=ext, path_maker=path_maker)
        try:
            text = path.read_text()
            json_loader = self.default._json_loader(json_loader)
            return json_loader(text)
        except Exception as e:
            raise ValueError(f"Failed to load JSON resource {path}: {repr(e)}") from e

    def data_to_json(
        self,
        data: Any,
        json_encoder: JsonEncoder | EllipsisType = ...,
        ndigits: int | None | EllipsisType = ...,
    ) -> str:
        """Convert data to a json string used for both expectations and save_json."""
        ndigits = self.default._ndigits(ndigits)
        data = prepare_for_json_encode(data, ndigits=ndigits, extra_preppers=self._extra_preppers)
        json_encoder = self.default._json_encoder(json_encoder)
        text = json_encoder(data)
        if not text.endswith("\n"):
            text += "\n"
        return text

    def save_json(
        self,
        data: Any,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_encoder: JsonEncoder | EllipsisType = ...,
        ndigits: int | None | EllipsisType = ...,
    ) -> None:
        """Write JSON data to a resource relative to the current test."""
        text = self.data_to_json(data, json_encoder=json_encoder, ndigits=ndigits)
        self.save_text(text, *parts, ext=ext, path_maker=path_maker)

    def delete_json(
        self,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
    ):
        """Delete a json resource relative to the current test."""
        self.delete(*parts, ext=ext, path_maker=path_maker)

    def expect_json(
        self,
        actual: Any,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_encoder: JsonEncoder | EllipsisType = ...,
        ndigits: int | None | EllipsisType = ...,
    ) -> None:
        """Assert that the actual value encodes to the JSON content from resource."""
        actual_text = self.data_to_json(actual, json_encoder=json_encoder, ndigits=ndigits)
        self.expect_text(
            actual_text,
            *parts,
            ext=ext,
            path_maker=path_maker,
        )

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Pydantic Resources

    def load_pydantic(
        self,
        model_class: type[PMT],
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_loader: JsonLoader | EllipsisType = ...,
    ) -> PMT:
        """Load a pydantic resource relative to the current test."""
        data = self.load_json(*parts, ext=ext, path_maker=path_maker, json_loader=json_loader)
        return model_class.model_validate(data)

    def save_pydantic(
        self,
        data: Any,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_encoder: JsonEncoder | EllipsisType = ...,
        ndigits: int | None | EllipsisType = ...,
        context: Any = None,
    ) -> None:
        """Write pydantic data to a resource relative to the current test."""
        actual_data = data.model_dump(mode="json", context=context)
        self.save_json(actual_data, *parts, ext=ext, path_maker=path_maker, json_encoder=json_encoder, ndigits=ndigits)

    def delete_pydantic(self, *parts, ext: str = "json", path_maker: PathMaker | None = None):
        """Delete a json resource relative to the current test."""
        self.delete(*parts, ext=ext, path_maker=path_maker)

    def expect_pydantic(
        self,
        actual: BaseModel,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_encoder: JsonEncoder | EllipsisType = ...,
        ndigits: int | None | EllipsisType = ...,
        context: Any = None,
    ) -> None:
        """Assert that the actual value encodes to the JSON content from resource."""
        actual_data = actual.model_dump(mode="json", context=context)
        self.expect_json(
            actual_data,
            *parts,
            ext=ext,
            path_maker=path_maker,
            json_encoder=json_encoder,
            ndigits=ndigits,
        )

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Pydantic TypeAdapter Resources

    def load_pydantic_adapter(
        self,
        type_: type[T] | TypeAdapter[T],
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_loader: JsonLoader | EllipsisType = ...,
    ) -> T:
        """Load a resource with a pydantic TypeAdapter relative to the current test."""
        data = self.load_json(*parts, ext=ext, path_maker=path_maker, json_loader=json_loader)
        adapter: TypeAdapter[T] = type_ if isinstance(type_, TypeAdapter) else TypeAdapter(type_)
        return adapter.validate_python(data)

    def save_pydantic_adapter(
        self,
        data: Any,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_encoder: JsonEncoder | EllipsisType = ...,
        ndigits: int | None | EllipsisType = ...,
        type_: type[T] | TypeAdapter[T] | None = None,
        context: Any = None,
    ) -> None:
        """Write pydantic data to a resource relative to the current test."""
        type_ = type_ or type(data)
        adapter: TypeAdapter[T] = type_ if isinstance(type_, TypeAdapter) else TypeAdapter(type_)
        actual_data: T = adapter.dump_python(data, mode="json", context=context)
        self.save_json(actual_data, *parts, ext=ext, path_maker=path_maker, json_encoder=json_encoder, ndigits=ndigits)

    def delete_pydantic_adapter(self, *parts, ext: str = "json", path_maker: PathMaker | None = None):
        """Delete a json resource relative to the current test."""
        self.delete(*parts, ext=ext, path_maker=path_maker)

    def expect_pydantic_adapter(
        self,
        actual: Any,
        *parts,
        ext: str = "json",
        path_maker: PathMaker | None = None,
        json_encoder: JsonEncoder | EllipsisType = ...,
        ndigits: int | None | EllipsisType = ...,
        type_: type[T] | TypeAdapter[T] | None = None,
        context: Any = None,
    ) -> None:
        """Assert that the type adapter encodes the actual value to the JSON content from resource. This allows us to
        pass a context to the serializers of any objects embedded within actual."""
        type_ = type_ or type(actual)
        adapter: TypeAdapter[T] = type_ if isinstance(type_, TypeAdapter) else TypeAdapter(type_)
        actual_data: T = adapter.dump_python(actual, mode="json", context=context)
        self.expect_json(
            actual_data,
            *parts,
            ext=ext,
            path_maker=path_maker,
            json_encoder=json_encoder,
            ndigits=ndigits,
        )
