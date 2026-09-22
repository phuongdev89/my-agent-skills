# Compatibility

This repository uses the standard Skills CLI layout: one skill per skills/<name>/SKILL.md directory.

Example target selection:
npx skills add https://github.com/phuongdev89/my-agent-skills --agent codex claude-code opencode

The instruction format is agent-agnostic, but runtime capabilities are not. Browser automation, FFmpeg, TTS, image APIs, and transcription engines may require separate tools, packages, or API keys. Read each selected skill's prerequisites. Repository validation checks frontmatter and directory names; provider availability and media quality must be tested in the target environment.
