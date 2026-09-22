from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
errors = []
names = set()
for directory in sorted((root / "skills").iterdir()):
    if not directory.is_dir():
        continue
    path = directory / "SKILL.md"
    if not path.exists():
        errors.append(f"{directory.name}: missing SKILL.md")
        continue
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"^---\s*\n(.*?)\n---(?:\s*\n|$)", text, re.S)
    if not match:
        errors.append(f"{directory.name}: malformed frontmatter")
        continue
    fields = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    name = fields.get("name", "").strip()
    description = fields.get("description", "").strip()
    if not name or not description:
        errors.append(f"{directory.name}: name and description are required")
    if name in names:
        errors.append(f"duplicate skill name: {name}")
    names.add(name)
    if name and name != directory.name:
        errors.append(f"{directory.name}: frontmatter name is {name!r}")
if errors:
    print("\n".join(f"ERROR: {error}" for error in errors))
    sys.exit(1)
print(f"OK: {len(names)} skills validated")
