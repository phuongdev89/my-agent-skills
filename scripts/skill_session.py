"""Repository-local skill sessions; usable from any working directory."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import unicodedata

REPO_ROOT = Path(__file__).resolve().parents[2]
SAIGON = timezone(timedelta(hours=7), "Asia/Saigon")


def slugify(value):
    value = str(value).replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:80].rstrip("-") or "default"


def create_session(skill_name, task_name="default", *, session_dir=None, repo_root=None, now=None):
    """Create a new session, or explicitly resume a canonical session of this skill.

    Same-second collisions reserve the next available second atomically, preserving
    the required basename grammar. The manifest records the actual creation time.
    """
    root = Path(repo_root or REPO_ROOT).resolve()
    scratch = root / ".scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    skill = slugify(skill_name)
    task = slugify(task_name)
    current = now or datetime.now(SAIGON)
    if current.tzinfo is None:
        current = current.replace(tzinfo=SAIGON)
    current = current.astimezone(SAIGON)
    if session_dir:
        path = Path(session_dir)
        path = (root / path).resolve() if not path.is_absolute() else path.resolve()
        pattern = rf"\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}}_{re.escape(skill)}_[a-z0-9]+(?:-[a-z0-9]+)*"
        if path.parent != scratch.resolve() or not re.fullmatch(pattern, path.name):
            raise ValueError("session_dir must be repo/.scratch/YYYY-MM-DD_HH-mm-ss_<skill>_<task-slug>")
        datetime.strptime(path.name[:19], "%Y-%m-%d_%H-%M-%S")
        path.mkdir(exist_ok=True)
    else:
        allocated = current
        while True:
            path = scratch / f"{allocated:%Y-%m-%d_%H-%M-%S}_{skill}_{task}"
            try:
                path.mkdir()
                break
            except FileExistsError:
                allocated += timedelta(seconds=1)
    for name in ("input", "output", "scripts", "temp"):
        (path / name).mkdir(exist_ok=True)
    manifest = path / "session.json"
    try:
        with manifest.open("x", encoding="utf-8") as stream:
            json.dump({"skill": skill, "task": path.name.split("_", 3)[3],
                       "created_at": current.isoformat(), "timezone": "Asia/Saigon",
                       "session_dir": str(path)}, stream, ensure_ascii=False, indent=2)
    except FileExistsError:
        pass
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--task", required=True)
    args = parser.parse_args()
    print(create_session(args.skill, args.task))
