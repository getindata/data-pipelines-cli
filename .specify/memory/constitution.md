<!--
SYNC IMPACT REPORT

Version Change: (initial) → 1.0.0
Constitution Type: MINOR (initial ratification - new governance document)

Modified Principles: N/A (initial creation)

Added Sections:
  - Core Principles (5 principles)
  - Code Quality Standards
  - Development Workflow
  - Governance

Removed Sections: N/A (initial creation)

Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check section aligns with principles
  ✅ spec-template.md - Requirements align with testing and quality standards
  ✅ tasks-template.md - Task organization reflects quality and testing principles

Follow-up TODOs: None
-->

# data-pipelines-cli Constitution

## Core Principles

### I. Configuration Over Code

All environment-specific settings MUST be externalized to YAML configuration files in the layered config system (`config/base/` + `config/{env}/`). Code MUST NOT contain hardcoded credentials, endpoints, or environment-specific values. The layered configuration merge pattern (base → env → global) is mandatory for all new configuration files.

**Rationale**: Enables multi-environment deployments (local, dev, prod) without code changes, supports template-based project creation, and maintains security by separating secrets from code.

### II. Command Pattern Consistency

Every CLI command MUST follow the established pattern: Click decorator for interface, wrapper function for framework integration, separate business logic function for testability. All commands MUST use the global error handler in `cli.py` and raise `DataPipelinesError` subclasses for semantic errors.

**Rationale**: Ensures consistent user experience, enables centralized error formatting, simplifies testing by separating concerns, and makes command addition predictable.

### III. Storage Abstraction

All cloud storage operations MUST use fsspec for provider abstraction. Direct use of provider-specific SDKs (boto3, google-cloud-storage) is prohibited in business logic. The `LocalRemoteSync` class pattern is mandatory for deployment operations.

**Rationale**: Enables seamless provider switching (GCS ↔ S3 ↔ Azure), reduces vendor lock-in, simplifies testing with local filesystem mocks, and maintains consistent sync semantics across providers.

### IV. dbt Integration Standards

All dbt operations MUST use `dbt_utils.run_dbt_command()` with proper variable aggregation from all three sources (base config, env config, global config). Direct subprocess calls to dbt are prohibited. Profile generation MUST be dynamic via `config_generation.generate_profiles_yml()`.

**Rationale**: Ensures variables are consistently available across all environments, prevents configuration drift, enables centralized dbt command logging, and maintains compatibility with multiple dbt adapters.

### V. Optional Dependency Graceful Degradation

Features requiring optional dependencies (docker, datahub, looker, specific dbt adapters) MUST check for import availability at function entry and raise clear `DependencyNotInstalledError` with installation instructions. Core functionality MUST NOT depend on optional packages.

**Rationale**: Allows minimal installation for users who don't need all features, provides clear error messages with remediation steps, prevents cryptic import errors, and maintains clean separation between core and optional features.

## Code Quality Standards

### Testing Requirements

- Unit tests MUST mirror source structure (`test_X.py` for `X.py`)
- Tests MUST use pytest with coverage reporting (minimum 80% for new code)
- External services MUST be mocked (moto for S3, gcp-storage-emulator for GCS)
- Tests MUST be named with `test_` prefix for PyCharm/pytest discovery
- Integration tests for multi-service workflows are REQUIRED for deploy command changes

### Code Style Enforcement

- Max line length: 100 characters (flake8 enforced)
- Type hints REQUIRED for all function signatures (mypy checked)
- All code MUST pass pre-commit hooks: isort, black, flake8, mypy, trailing-whitespace checks
- No unused imports or variables (flake8-blind-except, flake8-comprehensions enabled)

### Documentation Standards

- All public functions MUST have docstrings with parameter types and return types
- CLI commands MUST have clear help text via Click decorators
- Configuration file changes MUST be documented in relevant template repositories
- Breaking changes MUST be documented in CHANGELOG.md following keep-a-changelog format

## Development Workflow

### Branch Strategy

- All development MUST happen on `develop` branch
- Feature branches MUST be created from `develop`
- PRs MUST target `develop` branch (not `main`)
- `main` branch is release-only (managed by GitHub Actions)

### Pull Request Requirements

1. Unit tests MUST be provided for new functionality
2. CHANGELOG.md MUST be updated with changes
3. Pre-commit hooks MUST pass (all linters green)
4. Commits SHOULD be squashed with verbose PR title
5. Breaking changes MUST be clearly marked in PR description

### Release Process

1. Maintainer runs "Prepare Release" GitHub Action with version bump type (major/minor/patch)
2. Action creates PR with version update and changelog consolidation
3. PR is reviewed and merged to `main`
4. "Publish" workflow automatically publishes to PyPI and merges back to `develop`

**Version Semantics:**
- MAJOR: Breaking changes to CLI interface or configuration schema
- MINOR: New commands, new optional features, new dbt adapter support
- PATCH: Bug fixes, documentation updates, internal refactoring

## Governance

### Amendment Procedure

Constitution amendments require:
1. Proposal via GitHub issue with rationale and impact analysis
2. Discussion period (minimum 7 days for MAJOR changes, 3 days for MINOR)
3. Approval from project maintainers
4. Migration plan for existing code violating new principles
5. Version bump following semantic versioning (see Version History below)
6. Update to all dependent templates (plan, spec, tasks)

### Compliance Verification

- All PRs MUST be reviewed for constitution compliance before merge
- Violations MUST be justified in PR description with "Why Needed" and "Alternative Rejected" rationale
- Automated checks (pre-commit, CI) enforce code quality standards
- Template updates (`.specify/templates/`) MUST stay synchronized with constitution principles

### Version History

**Version**: 1.0.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27

**Versioning Policy:**
- MAJOR: Principle removal or redefinition breaking backward compatibility
- MINOR: New principle added or existing principle materially expanded
- PATCH: Clarifications, typo fixes, non-semantic refinements

**Runtime Guidance**: Refer to `CLAUDE.md` for AI-assisted development guidance, `CONTRIBUTING.md` for human contributor guidelines, and `README.md` for user-facing documentation.
