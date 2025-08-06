# pytest-respect

Pytest plugin to load resource files relative to test code and to expect values to match them. The name is a contraction of
`resources.expect`, which is frequently typed when using this plugin.

### Motivation

The primary use-case is running tests over moderately large datasets where adding them as constants in the test code would be cumbersome. This happens frequently with integration tests or when retrofitting tests onto an existing code-base.

### Examples

#### Json Data

The absolute simplest example is the following test:

```python
def test_computation(resources):
    """Running compute on input.json creates an output matching output.json"""
    input = resources.load_json("input")
    output = compute(input)
    resources.expect_json(output, "output")
```

If it is found in a file called `foo/test_stuff.py`, then it will load the content of
`foo/test_stuff/test_computation__input.json`, run the
`compute` function on it, and assert that the output exactly matches the content of the file
`foo/test_stuff/test_computation__output.json`.

#### Pydantic Models

With the optional
`pydantic` extra, the same can be done with pydantic data if you have models for your input and output data:

```python
def test_computation(resources):
    """Running compute on input.json creates an output matching output.json"""
    input = resources.load_pydantic(InputModel, "input")
    output = compute(input)
    resources.expect_pydantic(output, "output")
```

## Installation

Install with your favourite package manager such as:

- `pip install pydantic-respect`
- `poetry add --dev pydantic-respect`
- `uv add --dev pydantic-respect`

See your package management tool for details, especially on how to install optional extra dependencies.

### Extras

The following extra dependencies are required for additional functionality:

- `poetry` - load, save, and expect pydantic models of arbitrary data through type adapters.
- `numpy` - convert numpy arrays and scalars to python equivalents when converting to JSON
- `jsonyx` - alternative JSON encoder for semi-compact files, numeric keys, trailing commas, etc.


---
## The resources Fixture

The main entry point to the library is the `resources` fixture. Each method is fully documented in-line so here we will discuss clusters of functionality and list the members.

### Path Makers

**TBD**

### `resources.load_foo`

**TBD**

### `resources.save_foo`

**TBD**

### `resources.delete_foo`

**TBD**

### `resources.expect_foo`

**TBD**

### Utilities

**TBD:** `path`, `dir`, `json_to_text`

### JSON Enocders

**TBD**

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
