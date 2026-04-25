# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2025-04-25

### Added
- 🔒 Audit trail system with 5 cryptographic integrity principles
- SHA-256 hash chain: config → results → execution binding
- Tamper-evident persistence to disk
- Independent verification capability
- 16 tests covering all 5 integrity principles

### Documentation
- `docs/audit_integrity_principles.md` — Core principle reference
- `docs/verification_guide.md` — Third-party audit guide
- `docs/testing_strategy.md` — Test coverage and strategy
- `ADR/001-audit-hash-chain-design.md` — Design decision record
- Updated `README.md` with audit trail section