# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-10-21

### Added

- Added `resources.default` structure with defaults for `path_maker`, `json_loader`, `json_encoder` and `ndigits`.
- Added optional `json_loader` argument to: `load_json`, `load_pydantic` and `load_pydantic_adapter` which overrides the default.
- Added optional `json_encoder` argument to : `data_to_json`, `save_json`, `expect_json`, `save_pydantic`, `expect_pydantic`, `save_pydantic_adapter`, `expect_pydantic_adapter` to override the default.
- Added global list of `JSON_PREPPERS` and `add_json_prepper` function to add functions for preparing values of specific types before they are either JSON encoded _or_ recursively descended into in `prepare_for_json_encode`.
- Converted the pydantic and numpy special preparations to JSON preppers.
- Prepare any collection (other than str) recursively as a list
- Any value, which is not directly JSON encodable and isn't prepared by a JSON prepper, will be prepared using `str()`.

### Breaking

- `resources.default_path_maker` was moved to `default.path_maker` and `default_ndigits` was moved to `default.ndigits`.

## [0.3.0] - 2025-08-25

### Added

- `resources.accept` property which decides whether to accept a result if it differs from the expectation instead of failing the test.
- `--respect-accept` command-line option which populates the `resources.accept` property.

### Changed

- The `jsonyx_encoder` variants now allow all JSON deviations. Most notably, they will encode `nan` values.

## [0.2.0] - 2025-08-18

### Added

- `context` argument to `resources.expect_pydantic` method (#11).
- `resources.save_pydantic` method which serializes a pydantic model and accepts the new `context` (#11).
- `resources.save_pydantic_adapter` method which serializes arbitrary data using a pydantic `TypeAdapter`. It accepts the new `context` object in case there are pydantic models somewhere within the data being saved (#11).
- `resources.expect_pydantic_adapter` method which serializes like `save_pydantic_adapter` and expects the result to match a resource on-disk (#11).

### Changed

- Generated JSON now converts negative zero (`-0.0`) to non-negative zero (`0.0`) (#10).

## [0.1.2] - 2025-08-18

### Fixed

- Documentation

## [0.1.1] - 2025-08-06

### Fixed

- Documentation.

## [0.1.0] - 2025-08-06

### Added

- Convert to pytest plugin.

### Fixed

- Make work without the optional dependencies (#4).

## [0.0.1] - 2025-08-05

Initial import from [Ankeri](https://ankeri.com/)'s proprietary [Platform](https://platform.ankeri.net/) code-base.
