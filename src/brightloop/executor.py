"""Preview and apply approved plans to a local workspace."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schema import slugify


def preview_plan(plan: dict[str, Any]) -> str:
    lines = [f"PLAN: {plan['summary']}", "", "Proposed changes:"]
    for number, action in enumerate(plan["actions"], start=1):
        if action["type"] == "write_note":
            lines.append(f"{number}. Create note: {slugify(action['title'])}")
        elif action["type"] == "append_log":
            lines.append(f"{number}. Append entry to: daily-log.md")
    lines.extend(["", "Only these local Markdown-file actions are supported."])
    return "\n".join(lines)


def _preflight(plan: dict[str, Any], workspace: Path) -> None:
    """Check all targets before changing anything, avoiding partial writes."""
    notes_dir = workspace / "notes"
    pending: set[Path] = set()

    needs_notes = any(action["type"] == "write_note" for action in plan["actions"])
    needs_log = any(action["type"] == "append_log" for action in plan["actions"])

    if needs_notes:
        if notes_dir.is_symlink():
            raise ValueError(f"Refusing to write through a symlinked notes directory: {notes_dir}")
        if notes_dir.exists() and not notes_dir.is_dir():
            raise ValueError(f"The notes path exists but is not a directory: {notes_dir}")

    log_path = workspace / "daily-log.md"
    if needs_log:
        if log_path.is_symlink():
            raise ValueError(f"Refusing to write through a symlinked log file: {log_path}")
        if log_path.exists() and not log_path.is_file():
            raise ValueError(f"The daily log path exists but is not a regular file: {log_path}")

    for action in plan["actions"]:
        if action["type"] == "write_note":
            target = notes_dir / slugify(action["title"])
            if target in pending:
                raise FileExistsError(f"The plan contains duplicate note title: {action['title']}")
            pending.add(target)
            if target.is_symlink():
                raise ValueError(f"Refusing to overwrite a symlink: {target}")
            if target.exists():
                raise FileExistsError(f"Refusing to overwrite an existing note: {target}")


def _append_log(workspace: Path, content: str) -> Path:
    """Append to the log without following a final-component symlink."""
    target = workspace / "daily-log.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n- **{timestamp}:** {content.strip()}\n"
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(entry)
    return target


def apply_plan(plan: dict[str, Any], workspace: str | Path) -> list[Path]:
    """Apply a validated plan. The caller must obtain approval first."""
    root = Path(workspace).expanduser().resolve()
    _preflight(plan, root)
    created: list[Path] = []

    for action in plan["actions"]:
        if action["type"] == "write_note":
            notes_dir = root / "notes"
            notes_dir.mkdir(parents=True, exist_ok=True)
            target = notes_dir / slugify(action["title"])
            with target.open("x", encoding="utf-8") as handle:
                handle.write(f"# {action['title'].strip()}\n\n{action['content'].strip()}\n")
            created.append(target)
        elif action["type"] == "append_log":
            root.mkdir(parents=True, exist_ok=True)
            created.append(_append_log(root, action["content"]))

    return created
