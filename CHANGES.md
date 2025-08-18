# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-08-18

### Added

- `context` argument to `resources.expect_pydantic` method (#11).
- `resources.save_pydantic` method which serializes a pydantic model and accepts the new `context` (#11).
- `resources.save_pydantic_adapter` method which serializes arbitrary data using a pydantic `TypeAdapter`. It accepts the new `context` object in case there are pydantic models somewhere within the data being saved (#11).
- `resources.expect_pydantic_adapter` method which serializes like `save_pydantic_adapter` and expects the result to match a resource on-disk (#11).

### Changed

- Generated JSON now converts negative zero (`-0.0`) to non-negative zero (`0.0`) by default. The underlying `allow_negative_zero` takes a new argument `prepare_for_json_encode` to change this, but the save and expect methods don't make use of it (#10).

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

### Added

- Initial semi-functional release
