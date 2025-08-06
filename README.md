# pytest-respect

Pytest plugin to load resource files relative to test code and to expect values to match them. The name is a contraction of `resources.expect`, which is frequently typed when using this plugin.

### Motivation

The primary use-case is running tests over moderately large datasets where adding them as constants in the test code would be cumbersome. This happens frequently with integration tests or when retrofitting tests onto an existing code-base.

### Examples

#### Json Data

The absolute simplest example is the following test:

```python
def test_compute(resources):
    input = resources.load_json("input")
    output = compute(input)
    resources.expect_json(output, "output")
```

If it is found in a file called `foo/test_stuff.py`, then it will load the content of
`foo/test_stuff/test_compute__input.json`, run the
`compute` function on it, and assert that the output exactly matches the content of the file
`foo/test_stuff/test_compute__output.json`.

#### Pydantic Models

With the optional
`pydantic` extra, the same can be done with pydantic data if you have models for your input and output data:

```python
def test_compute(resources):
    input = resources.load_pydantic(InputModel, "input")
    output = compute(input)
    resources.expect_pydantic(output, "output")
```

The input and output paths will be identical, since we re-used the name of the test function.

#### Failing Tests

If one of the above expectations fails, then a new file is created at `foo/test_stuff/test_compute__output__actual.json` with the actual value passed to the expect function, as well as the usual diff from pytest's assert. You can then use your existing diff tools to compare the expected and actual values and even to pick individual changes from the actual file before fixing the code to deal with any remaining differences.

Once the test passes, the actual file will be removed. Note that if you change the name of a test after an actual file has been created, the actual file will have to be deleted manually.

#### Parametric Tests

The load and expect (and other) methods can take multiple strings for the resource file name `parts`. Above we only used `"input"` and `"output"` parts and failures implicitly added an `"actual"` part. We can pass in as many parts as we like, which nicely brings us to parametric tests:

```python
@pytest.mark.paramtrize("case", ["red", "blue", "green"])
def test_compute(resources, case):
    input = resources.load_json("input", case)
    output = compute(input)
    resources.expect_json(output, "output", case)
```

Omitting directory name, this test will load each of `test_compute__input__red.json`, `test_compute__input__blue.json`, `test_compute__input__green.json` and compare the results to `test_compute__output__red.json`, `test_compute__output__blue.json`, `test_compute__output__green.json`

## Installation

Install with your favourite package manager such as:

- `pip install pydantic-respect`
- `poetry add --dev pydantic-respect`
- `uv add --dev pydantic-respect`

See your package management tool for details, especially on how to install optional extra dependencies.

### Extras

The following extra dependencies are required for additional functionality:

- `poetry` - Load, save, and expect pydantic models or arbitrary data through type adapters.
- `numpy` - Convert numpy arrays and scalars to python equivalents when generating JSON both in save and expect.
- `jsonyx` - Alternative JSON encoder for semi-compact files, numeric keys, trailing commas, etc.


---
## The resources Fixture

The main entry point to the library is the `resources` fixture. Each method is fully documented in-line so here we will discuss clusters of functionality and list the members.

### Load

- **To Document:** `load_text`, `load_json`, `load_pydantic`, `load_pydantic_adapter`

### Save

- **To Document:** `save_text`, `save_json`
- **To Implement:** `save_pydantic`, `save_pydantic_adapter`

### Delete

- **To Document:** `delete`, `delete_json`
- **To Implement:** `delete_text`, `delete_pydantic`

### Expect

- **To Document:** `expect_text`, `expect_json`, `expect_pydantic`
- **To Implement:** `expect_pydantic_adapter`

### Utilities

- **To Document:** `path`, `dir`, `json_to_text`

### Path Makers

- **To Implement**

### JSON Enocders

- **To Implement**

### Configuration

- **To Implement**

---
## Development

### Installation

- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv sync --all-extras`
- Run `pre-commit install` to enable pre-commit linting.
- Run `pytest` to verify installation.

### Testing

This is a pytest plugin so you're expected to know how to run pytest when hacking on it. Additionally,
`scripts/pytest-extras` runs the test suite with different sets of optional extras. The CI Pipelines will go through an equivalent process for each Pull Request.
