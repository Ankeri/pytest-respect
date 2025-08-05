# pytest-respect

Pytest plugin to load resource files relative to test code and to expect values to match them. The name is a contraction of `resources.expect`, which is frequently typed when using this plugin.

The primary use-case is running tests over moderately large datasets where adding them as constants in the test code would be cumbersome. This happens frequently with integration tests or when retrofitting tests onto an existing code-base.

## Example

The absolute simplest example is the following test. If it is found in a file called `foo/test_stuff.py`, then it will load the content of `foo/test_stuff/test_computation__input.json`, run the `compute` function on it, and assert that the output exactly matches the content of the file `foo/test_stuff/test_computation__output.json`.

```python
def test_computation(resources):
    """Running compute on input.json creates an output matching output.json"""
    input = resources.load_json("input")
    output = compute(input)
    resources.expect_json(output, "output")
```