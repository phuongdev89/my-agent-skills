# Changelog

All notable changes are documented here.

## [Unreleased]

### Added
- Muse2API image skill with a dedicated CLI for generation and specialized image edits.
- Public installation and usage documentation in README.md.
- Skill-layout validator at scripts/validate_skills.py.
- Contribution guide and compatibility notes.
- Ignore rules for generated Python bytecode and local secrets.

### Changed
- Standardized the repository contract around skills/<name>/SKILL.md.
- Documented installation with the Vercel Skills CLI.

### Removed
- Tracked Python __pycache__ and .pyc artifacts.

## Release process
Run the validator, review the skill list, update this file, and create a version tag before release.
