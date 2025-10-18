# pytest-respect

Pytest plugin to load resource files relative to test code and to expect values to match them. The name is a contraction of `resources.expect`, which is frequently typed when using this plugin.

## Motivation

The primary use-case is running tests over moderately large datasets where adding them as constants in the test code would be cumbersome. This happens frequently with integration tests or when retrofitting tests onto an existing code-base. If you find your test _code_ being obscured by the test _data_, filling with complex data generation code, or ad-hoc reading of input data or expected results, then pytest-respect is probably for you.

## Installation

Install with your favourite package manager such as:

- `pip install pydantic-respect`
- `poetry add --dev pydantic-respect`
- `uv add --dev pydantic-respect`

See your package management tool for details, especially on how to install optional extra dependencies.

#### Extras

The following extra dependencies are required for additional functionality:

- `poetry` - Load, save, and expect pydantic models or arbitrary data through type adapters.
- `numpy` - Convert numpy arrays and scalars to python equivalents when generating JSON, both in save and expect.
- `jsonyx` - Alternative JSON encoder for semi-compact files, numeric keys, trailing commas, etc.

## Usage

#### Text Data

The simplest use-case is loading textual input data and comparing textual output to an expectation file:

```python
def test_translate(resources):
    input = resources.load_text("input")
    output = translate(input)
    resources.expect_text(output, "output")
```

If the test is found in a file called `foo/test_stuff.py`, then it will load the content of `foo/test_stuff/test_translate__input.txt`, run the `translate` function on it, and assert that the output exactly matches the content of the file `foo/test_stuff/test_translate__output.json`.

The expectation must also match on trailing spaces and trailing empty lines for the test to pass.

#### Json Data

A much more interesting example is doing the same with JSON data:

```python
def test_compute(resources):
    input = resources.load_json("input")
    output = compute(input)
    resources.expect_json(output, "output")
```

This will load the content of `foo/test_stuff/test_compute__input.json`, run the `compute` function on it, and assert that the output exactly matches the content of the file `foo/test_stuff/test_compute__output.json`.

The expectation matching is done on a text representation of the JSON data. This avoids having to parse the expectation files, and allows us to use text-based diff tools, but instead we must avoid other tools reformating the expectations. By default the JSON formatting is by `json.dumps(obj, sort_keys=True, indent=2)` but see the section on [JSON Formatting and Parsing](#json-formatting-and-parsing).

#### Pydantic Models

With the optional
`pydantic` extra, the same can be done with pydantic data if you have models for your input and output data:

```python
def test_compute(resources):
    input: InputModel = resources.load_pydantic(InputModel, "input")
    output: OutputModel = compute(input)
    resources.expect_pydantic(output, "output")
```

The input and output paths will be identical to the JSON test, since we re-used the name of the test function.

#### Failing Tests

If one of the above expectations fails, then a new file is created at `foo/test_stuff/test_compute__output__actual.json` containing the actual value passed to the expect function. In addition to this, the normal pytest assert re-writing happens to show the difference between the expected value and the actual value.

When the values being compared are more complex, then the diference shown on the console may be overwhelming. Then you can instead use your existing diff tools to compare the expected and actual values and perhaps pick individual changes from the actual file before fixing the code to deal with any remaining differences.

Once the test passes, the `__actual` file will be removed. Note that if you change the name of a test after an actual file has been created, then it will have to be deleted manually.

Alternatively, if you know that all the actual files from a test run are correct, you can run the test with the `--respect-accept` flag to update all the expectations.

#### Parametric Tests

The load and expect (and other) methods can take multiple strings for the resource file name `parts`. Above we only used `"input"` and `"output"` parts and failures implicitly added an `"actual"` part. We can pass in as many parts as we like, which nicely brings us to parametric tests:

```python
@pytest.mark.paramtrize("case", ["red", "blue", "green"])
def test_compute(resources, case):
    input = resources.load_json("input", case)
    output = compute(input)
    resources.expect_json(output, "output", case)
```

Omitting the directory name, this test will load each of `test_compute__input__red.json`, `test_compute__input__blue.json`, `test_compute__input__green.json` and compare the results to `test_compute__output__red.json`, `test_compute__output__blue.json`, `test_compute__output__green.json`

#### Data-driven Parametric Tests

We can use the `list_resources` function to generate a list of resource names to run parametric tests over:

```python
@pytest.fixture(params=list_resources("widget_*.json", exclude=["*__actual.json"], strip_ext=True))
def each_widget_name(request) -> str:
    """Request this fixture to run for each widget file in the resource directory."""
    return request.param
```

The `list_resources` function is run in a static context and so doesn't have a test function or class to build paths from. Instead, it constructs a path to the file that it is called from and uses the `pm_only_file` path maker by default.

Tests can then request `each_widget_name` to run on each of the resources but will have to use a suitable path-maker to find the resource files:

```python
def test_load_json_resource(resources, each_widget_name):
    resources.default_path_maker = resources.pm_only_file
    widget = resources.load_json(each_widget_name)
    assert transform(widget) == 42
```

- **To Document:**

- Using `list` function

#### JSON Formatting and Parsing

**To Document:**

- Default JSON formatter and parser
- Alternative JSON formatter
- Jsonyx extension

#### Resource Path Construction

**To Document:**

- Multiple path parts
- Default path maker
- Alternative path makers
- Custom path makers

## Development

### Installation

- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv sync --all-extras`
- Run `pre-commit install` to enable pre-commit linting.
- Run `pytest` to verify installation.

### Testing

This is a pytest plugin so you're expected to know how to run pytest when hacking on it. Additionally, `scripts/pytest-extras` runs the test suite with different sets of optional extras. The CI Pipelines will go through an equivalent process for each Pull Request.
