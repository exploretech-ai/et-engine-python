# Change Log

## [0.0.1] - 2024-11-26

Minor bug fixes and additional features for high-level clients

### Added

- Ability to connect to Batch objects
- Delete method for Tool objects

### Changed

- Empty HTTP responses in Base client returns `None` instead of empty dict

### Fixed

- Buggy `from_json` methods for Batch and Tool
