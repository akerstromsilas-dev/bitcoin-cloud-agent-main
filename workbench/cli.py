from __future__ import annotations

import argparse
from pathlib import Path

from .core import (
    CHECKLIST_ITEMS,
    add_task,
    format_draft,
    generate_ideas,
    load_tasks,
    record_reward,
    set_checklist_item,
    write_snapshot,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workbench",
        description="Local template drafting and a reward-task checklist.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    ideas = commands.add_parser("ideas", help="Draft digital service ideas locally.")
    ideas.add_argument("--skill", default="", help="A skill or service theme.")
    ideas.add_argument("--audience", default="", help="Who the service may help.")

    draft = commands.add_parser("draft", help="Create a local-template content draft.")
    draft.add_argument("--topic", required=True, help="Draft topic or service.")
    draft.add_argument(
        "--format",
        choices=("service_listing", "social_post", "article_outline"),
        default="service_listing",
    )
    draft.add_argument("--audience", default="")

    task = commands.add_parser("task", help="Manage the local reward checklist.")
    task_commands = task.add_subparsers(dest="task_command", required=True)

    add = task_commands.add_parser("add", help="Add an explicitly allowed opportunity.")
    add.add_argument("--title", required=True)
    add.add_argument("--platform", required=True)
    add.add_argument("--terms-url", required=True)
    add.add_argument("--policy-evidence", required=True)
    add.add_argument(
        "--automation-permitted",
        action="store_true",
        help="Confirm you verified current terms permit the intended automation.",
    )

    task_commands.add_parser("list", help="List recorded opportunities.")
    show = task_commands.add_parser("show", help="Show an opportunity checklist.")
    show.add_argument("task_id")

    check = task_commands.add_parser("check", help="Update one checklist item.")
    check.add_argument("task_id")
    check.add_argument("item", choices=CHECKLIST_ITEMS)
    check.add_argument("--done", action="store_true", help="Mark completed.")
    check.add_argument("--todo", action="store_true", help="Mark not completed.")

    reward = task_commands.add_parser(
        "reward", help="Record a reward only after confirming its receipt."
    )
    reward.add_argument("task_id")
    reward.add_argument("--amount", required=True)
    reward.add_argument("--currency", required=True)
    reward.add_argument("--evidence", required=True)

    commands.add_parser("snapshot", help="Write a tracker JSON and Markdown report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "ideas":
            for idea in generate_ideas(args.skill, args.audience):
                print(idea)
            print("\nThese are unresearched prompts, not validated offers or income claims.")
            return 0

        if args.command == "draft":
            path = format_draft(PROJECT_ROOT, args.topic, args.format, args.audience)
            print(f"Draft written to {path.relative_to(PROJECT_ROOT)}")
            return 0

        if args.command == "snapshot":
            tracker, report = write_snapshot(PROJECT_ROOT)
            print(f"Tracker snapshot written to {tracker.relative_to(PROJECT_ROOT)}")
            print(f"Readable report written to {report.relative_to(PROJECT_ROOT)}")
            return 0

        if args.command == "task":
            if args.task_command == "add":
                task = add_task(
                    PROJECT_ROOT,
                    args.title,
                    args.platform,
                    args.terms_url,
                    args.policy_evidence,
                    args.automation_permitted,
                )
                print(f"Added task {task['id']}: {task['title']}")
                print("Recheck the policy before each session; this app does not verify it.")
                return 0

            if args.task_command == "list":
                tasks = load_tasks(PROJECT_ROOT)
                if not tasks:
                    print("No opportunities recorded.")
                for task in tasks:
                    done = sum(task["checklist"].values())
                    total = len(CHECKLIST_ITEMS)
                    print(f"{task['id']}  {task['title']} — {done}/{total} checklist items")
                return 0

            tasks = load_tasks(PROJECT_ROOT)
            if args.task_command == "show":
                task = next((item for item in tasks if item["id"] == args.task_id), None)
                if task is None:
                    raise ValueError(f"No task found with ID {args.task_id!r}.")
                print(f"{task['title']} ({task['id']}) — {task['platform']}")
                print(f"Terms URL: {task['terms_url']}")
                print(f"Policy evidence: {task['policy_evidence']}")
                for key, done in task["checklist"].items():
                    print(f"[{'x' if done else ' '}] {key}")
                if task.get("reward_receipt"):
                    receipt = task["reward_receipt"]
                    print(
                        "User-reported confirmed receipt: "
                        f"{receipt['amount']} {receipt['currency']} "
                        f"(evidence: {receipt['evidence_note']})"
                    )
                return 0

            if args.task_command == "check":
                if args.done and args.todo:
                    raise ValueError("Choose either --done or --todo, not both.")
                if not args.done and not args.todo:
                    raise ValueError("Choose --done or --todo.")
                task = set_checklist_item(
                    PROJECT_ROOT, args.task_id, args.item, args.done
                )
                print(f"Updated {args.item} for {task['id']}.")
                return 0

            if args.task_command == "reward":
                task = record_reward(
                    PROJECT_ROOT,
                    args.task_id,
                    args.amount,
                    args.currency,
                    args.evidence,
                )
                print(
                    f"Recorded user-reported receipt for {task['id']}. "
                    "It is not independently verified."
                )
                return 0

        parser.error("Unknown command.")
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    return 2
