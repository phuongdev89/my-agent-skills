# Contributing

## Adding a skill
1. Create skills/<skill-name>/SKILL.md.
2. Start it with YAML frontmatter containing name and description.
3. Keep instructions portable; never commit credentials or developer-local paths.
4. Document CLIs, packages, environment variables, and provider limits.
5. Run: python scripts/validate_skills.py
6. Update README.md and CHANGELOG.md when the public skill set changes.

## Pull requests
Keep PRs focused. Include validator output. Never commit .env, API keys, generated media, __pycache__, or .pyc files.
