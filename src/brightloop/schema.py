"""Validation for model-generated BrightLoop plans.

Only explicitly supported action types are accepted. Model output is treated
as untrusted input and is never executed as code or as a shell command.
"""

from __future__ import annotations

import json
import re
from typing import Any

ALLOWED_ACTIONS = {"write_note", "append_log"}
MAX_ACTIONS = 10
MAX_TEXT_LENGTH = 12_000


class PlanError(ValueError):
    """Raised when a generated or saved plan is invalid."""


def _strip_code_fence(value: str) -> str:
    value = value.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    return value


def parse_plan(raw: str) -> dict[str, Any]:
    """Parse and validate a JSON plan returned by the AI model."""
    try:
        data = json.loads(_strip_code_fence(raw))
    except json.JSONDecodeError as exc:
        raise PlanError(f"The AI response was not valid JSON: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise PlanError("A plan must be a JSON object.")
    summary = data.get("summary")
    actions = data.get("actions")
    if not isinstance(summary, str) or not summary.strip():
        raise PlanError("The plan needs a non-empty summary.")
    if len(summary) > 1_000:
        raise PlanError("The plan summary is too long.")
    if not isinstance(actions, list) or not 1 <= len(actions) <= MAX_ACTIONS:
        raise PlanError(f"A plan must contain between 1 and {MAX_ACTIONS} actions.")

    clean_actions: list[dict[str, str]] = []
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            raise PlanError(f"Action {index} must be an object.")
        action_type = action.get("type")
        if action_type not in ALLOWED_ACTIONS:
            raise PlanError(
                f"Action {index} uses unsupported type {action_type!r}. "
                f"Allowed types: {', '.join(sorted(ALLOWED_ACTIONS))}."
            )

        if action_type == "write_note":
            title = action.get("title")
            content = action.get("content")
            if not isinstance(title, str) or not title.strip():
                raise PlanError(f"Action {index} needs a note title.")
            if not isinstance(content, str) or not content.strip():
                raise PlanError(f"Action {index} needs note content.")
            if len(title) > 160 or len(content) > MAX_TEXT_LENGTH:
                raise PlanError(f"Action {index} is too large.")
            clean_actions.append({"type": action_type, "title": title.strip(), "content": content.strip()})
        else:
            content = action.get("content")
            if not isinstance(content, str) or not content.strip():
                raise PlanError(f"Action {index} needs log content.")
            if len(content) > MAX_TEXT_LENGTH:
                raise PlanError(f"Action {index} is too large.")
            clean_actions.append({"type": action_type, "content": content.strip()})

    return {"summary": summary.strip(), "actions": clean_actions}


def slugify(title: str) -> str:
    """Convert a title into a safe, simple filename stem."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug[:80].strip("-") or "note") + ".md"
