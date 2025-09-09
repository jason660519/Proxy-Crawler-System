# Changelog

## [Unreleased]

### Added

- Centralized settings module (`config.settings`).
- Service layer: FetchService, ValidationService, PersistenceService.
- Prometheus metrics endpoint `/metrics`.
- GitHub Actions CI pipeline (lint, type check, tests, security scans).
- English architecture overview doc.

### Changed

- `ProxyManager` delegates fetch/validation/persistence logic to services.
- Auto-fetch loop executes immediately on start.

### Security

- Removed hard-coded API key from `test_mcp_servers.py`.
