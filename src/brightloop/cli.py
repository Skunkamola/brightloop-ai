"""Command-line interface for BrightLoop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .executor import apply_plan, preview_plan
from .planner import create_plan
from .schema import PlanError, parse_plan

DEFAULT_PLAN = Path(".brightloop/last-plan.json")
DEFAULT_WORKSPACE = Path(".brightloop/workspace")


def _read_plan(path: Path) -> dict:
    try:
        return parse_plan(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Could not read plan file {path}: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brightloop",
        description="Turn a task into a Claude-generated plan, review it, then approve safe local actions.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    plan_cmd = commands.add_parser("plan", help="Ask Claude to draft a workflow plan.")
    plan_cmd.add_argument("task", help="Describe what you want to organise or automate.")
    plan_cmd.add_argument("--output", type=Path, default=DEFAULT_PLAN, help=f"Plan file (default: {DEFAULT_PLAN}).")
    plan_cmd.add_argument("--model", help="Claude model ID (defaults to BRIGHTLOOP_MODEL or claude-sonnet-5-5).")

    show_cmd = commands.add_parser("show", help="Preview a saved plan without applying it.")
    show_cmd.add_argument("plan_file", nargs="?", type=Path, default=DEFAULT_PLAN)

    apply_cmd = commands.add_parser("apply", help="Apply a saved plan after explicit confirmation.")
    apply_cmd.add_argument("plan_file", nargs="?", type=Path, default=DEFAULT_PLAN)
    apply_cmd.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            plan = create_plan(args.task, model=args.model)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(preview_plan(plan))
            print(f"\nSaved plan to {args.output}. Review it with: brightloop show {args.output}")
            return 0

        plan = _read_plan(args.plan_file)
        print(preview_plan(plan))
        if args.command == "show":
            return 0

        print(f"\nWorkspace: {args.workspace}")
        print("BrightLoop will only create Markdown notes or append to daily-log.md.")
        try:
            confirmation = input("Type APPLY to approve these changes: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled. No changes made.")
            return 1
        if confirmation != "APPLY":
            print("Cancelled. No changes made.")
            return 1
        changed = apply_plan(plan, args.workspace)
        print("\nApproved plan applied:")
        for path in changed:
            print(f"- {path}")
        return 0
    except (PlanError, RuntimeError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
