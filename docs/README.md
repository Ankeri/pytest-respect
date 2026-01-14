# pytest-respect

Pytest plugin to load resource files relative to test code and to expect values to match such files. The name is a contraction of `resources.expect`, which is frequently typed when using this plugin.

## Motivation

The primary use-case is running tests over moderately large datasets where adding them as constants in the test code would be cumbersome. This happens frequently with integration tests or when retrofitting tests onto an existing code-base. If you find your test _code_ being obscured by the test _data_, filling with complex data generation code, or ad-hoc reading of input data or expected results, then pytest-respect is for you.

## Installation

Install with your favourite package manager such as:

- `pip install pydantic-respect`
- `poetry add --dev pydantic-respect`
- `uv add --dev pydantic-respect`

See your package management tool for details, especially on how to install optional extra dependencies.

### Extras

The following extra dependencies are required for additional functionality:

- `poetry` - Load, save, and expect pydantic models or arbitrary data through type adapters.
- `numpy` - Convert numpy arrays and scalars to python equivalents when generating JSON, both in save and expect.
- `jsonyx` - Alternative JSON encoder for semi-compact files, numeric keys, trailing commas, etc.

## Usage

### Text Data

The simplest use-case is loading textual input data and comparing textual output to an expectation file:

```python
def test_translate(resources: TestResources):
    input = resources.load_text("input")
    output = translate(input)
    resources.expect_text(output, "output")
```

If the test is found in a file called `foo/test_stuff.py`, then it will load the content of `foo/test_stuff/test_translate__input.txt`, run the `translate` function on it, and assert that the output exactly matches the content of the file `foo/test_stuff/test_translate__output.json`.

The expectation must also match on trailing spaces and trailing empty lines for the test to pass.

### Json Data

A much more interesting example is doing the same with JSON data:

```python
def test_compute(resources: TestResources):
    input = resources.load_json("input")
    output = compute(input)
    resources.expect_json(output, "output")
```

This will load the content of `foo/test_stuff/test_compute__input.json`, run the `compute` function on it, and assert that the output exactly matches the content of the file `foo/test_stuff/test_compute__output.json`.

The expectation matching is done on a text representation of the JSON data. This avoids having to parse the expectation files, and allows us to use text-based diff tools, but instead we must avoid other tools reformating the expectations. By default the JSON formatting is by `json.dumps(obj, sort_keys=True, indent=2)` but see the section on [JSON Formatting and Parsing](#json-formatting-and-parsing).

### Pydantic Models and Type Adapters

With the optional
`pydantic` extra, the same can be done with pydantic data if you have models for your input and output data:

```python
def test_compute(resources: TestResources):
    input: InputModel = resources.load_pydantic(InputModel, "input")
    output: OutputModel = compute(input)
    resources.expect_pydantic(output, "output")
```

The input and output paths will be identical to the JSON test, since we re-used the name of the test function.

There are also `load_pydantic_adatper` and `expect_pydantic_adapter` variants which take a pydantic `TypeAdapter` instead of a model class, or they can take an arbitrary type to wrap in a `TypeAdapter` instance. Please refer to the pydantic documentation for how type adapters work.

### Failing Tests

#### Actual Files

If an expectation fails, then a new file is created containing the actual value passed to the expect function. Its path is constructed in the same way as that of the expectation file, but with an `actual` part appended. So in the JSON and Pydantic examples above, it would create the file `foo/test_stuff/test_compute__output__actual.json`. In addition to this, the normal pytest assert re-writing is done to show the difference between the expected value and the actual value.

When the values being compared are large or complex, the difference shown on the console may be overwhelming. Then you can instead use your existing diff tools to compare the expected and actual files and perhaps pick individual changes from the actual file before fixing the code to deal with any remaining differences.

Once the test passes, the `__actual` file will be removed. Note that if you change the name of a test after an actual file has been created, then it will have to be deleted manually.

#### Accepting Changes

Alternatively, if you know that all the actual files from a test run are correct, you can run the test with the `--respect-accept` flag to update all the expectations. You can also use the `--respect-accept-one` and `--respect-accept-max=n` flags to update only a single expectation or the first `n` expectations for each test, before failing on any remaining differences.

### Resource Path Construction

#### Multiple name parts

In all of the above examples, we passed a single string `"input"` or `"output"` to the load or expect methods. We can pass as many such name parts as we like, which affects the name of the resource file.

Using the JSON and Pydantic examples above, these paths would be constructed:

- `resources.load_json()` → `foo/test_stuff/test_compute.json`
- `resources.load_json("data")` → `foo/test_stuff/test_compute__data.json`
- `resources.load_json("scenario", "funky")` → `foo/test_stuff/test_compute__scenario__funky.json`

#### Path Makers

So far all our resource paths have been fairly rigidly constructed from the path to the test file and the test function within it. The way this is done is in fact fully configurable by passing a custom `PathMaker` to any method which accesses resource files, or by assigning a different one to `resources.default.path_maker`. A path maker is any function which implements the `PathMaker` protocol and a few standard ones are already present on the `resources` fixture.

If we revisit the JSON example from above, but using a different path maker, it will function in exactly the same way except that the resource files will be at `foo/test_stuff/input.json` and `foo/test_stuff/output.json` instead, ignoring the test function name.

```python
def test_compute(resources: TestResources):
    input = resources.load_json("input", path_maker=resources.pm_only_file)
    output = compute(input)
    resources.expect_json(output, "output")
```

The table below shows the paths made by the different path makers when calling `resource.path("data")` in a `test_function` in a `test_file.py` in a `<dir>`, including when it is a member of a `TestClass`.

| Path Maker                      | `test_compute`                                   | `TestMachine.test_compute`
|---------------------------------|--------------------------------------------------|-----------------------------------------------------------
| `pm_function`                   | `<dir>/test_file__test_function/data.<ext>`      | `<dir>/test_file__TestClass__test_method/data.<ext>`
| `pm_class`                      | `<dir>/test_file/test_function.<ext>`            | `<dir>/test_file__TestClass/test_method.<ext>`
| `pm_only_class`                 | `<dir>/test_file/data.<ext>`                     | `<dir>/test_file__TestClass/data.<ext>`
| `pm_file`                       | `<dir>/test_file/test_function.<ext>`            | `<dir>/test_file/TestClass__test_method.<ext>`
| `pm_only_file`                  | `<dir>/test_file/data.<ext>`                     | `<dir>/test_file/data.<ext>`
| `pm_dir`                        | `<dir>/resources/test_file__test_function.<ext>` | `<dir>/resources/test_file__TestClass__test_method.<ext>`
| `pm_dir_named("dir_name")`      | `<dir>/dir_name/test_file__test_function.<ext>`  | `<dir>/dir_name/test_file__TestClass__test_method.<ext>`
| `pm_only_dir`                   | `<dir>/resources`                                | `<dir>/resources`
| `pm_only_dir_named("dir_name")` | `<dir>/dir_name`                                 | `<dir>/dir_name`

#### Custom Path Makers

If none of these strategies suits your needs, then you can make your own path maker with the same signature as one of the included ones and use that instead.

The following example is similar to the default `pm_file` path maker, but creates a sub-directory for each date inside the resource directory:

```python
def pm_file_dated(test_dir: Path, test_file_name: str, test_class_name: str | None, test_name: str) -> PathParts:
    file = f"{test_class_name}__{test_name}" if test_class_name else test_name
    sub = date.today().isoformat()
    return test_dir / sub / test_file_name, file
```

### Other I/O on Resource Files

Each of the `load` and `expect` methods above also has a corresponding `save` method which simply writes the data to a file, as well as a `delete` method. The resource path resolution is also exposed as the `resources.path(*parts: str, ext: str | None = None, path_maker: PathMaker | None = None)` method if you need to access the files directly.

Using those, we can test a function which manilpulates external data files:

```python
def test_external_processing(resources: TestResources):
    resources.save_json(make_data(), "data")
    path: Path = resources.path("data", ext="json")
    result = external_processing(path)
    assert result == 42
    resources.delete_json("data")
```

As a utility, the `save_foo` and `delete_foo`methods also return the path to the affected file, so the test can be written as:

```python
def test_external_processing(resources: TestResources):
    path: Path = resources.save_json(make_data(), "data")
    result = external_processing(path)
    assert result == 42
    path.unlink()
```

Finally, the `resources.list()` method lists the names of resources within the test's resource folder as constructed by the path maker. It takes one or more include or exclude glob patterns to filter the results and defaults to `inclues="*"` with no `excludes`.

### Parametric Tests

We have seen how the `load` and `expect` (and other) methods can take multiple strings for the resource file name `parts`. In the earlier examples we only used `"input"` and `"output"` parts and failures implicitly added an `"actual"` part. But using multiple parts is useful when working with parametric tests:

```python
@pytest.mark.paramtrize("case", ["red", "green", "blue"])
def test_compute(resources, case):
    input = resources.load_json(case, "input")
    output = compute(input)
    resources.expect_json(output, case, "output")
```

Omitting the directory name, this test will load each of `test_compute__red__input.json`, `test_compute__green__input.json`, `test_compute__blue__input.json` and compare the results to `test_compute__red__output.json`, `test_compute__green__output.json`, `test_compute__blue__output.json`

### Data-driven Parametric Tests

We can use the `list_resources` function to generate a list of resource names to run parametric tests over. With the below fixture, the content of the resource directory is listed, and the fixture is run once for each match. We can then add test cases simply by adding new resource files:

```python
@pytest.fixture(params=list_resources("widget_*.json", exclude=["*__actual.json"], strip_ext=True))
def each_widget_name(request) -> str:
    """Request this fixture to run for each widget file in the resource directory."""
    return request.param
```

The `list_resources` function is run in a static context and so doesn't have a test function or class to build paths from. Instead, it constructs a path to the file that it is called from and uses the `pm_only_file` path maker by default. However, it takes an optional `path_maker` argument to override this.

Tests can then request `each_widget_name` to run on each of the resources but will have to use a suitable path-maker to find the resource files:

```python
def test_load_json_resource(resources, each_widget_name):
    widget = resources.load_json(each_widget_name, path_maker=resources.pm_only_file)
    assert transform(widget) == 42
```

### JSON Formatting and Parsing

### TODO:

- Default JSON formatter and parser
- Alternative JSON formatter
- Jsonyx extension

### Configuration

**TODO**

- Default path makers
- Default JSON encoder and loader
- Default ndigits

## Development

### Installation

- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv sync --all-extras`
- Run `pre-commit install` to enable pre-commit linting.
- Run `pytest` to verify installation.

### Testing

This is a pytest plugin so you're expected to know how to run pytest when hacking on it. Additionally, `scripts/pytest-extras` runs the test suite with different sets of optional extras. The CI Pipelines will go through an equivalent process for each Pull Request.
