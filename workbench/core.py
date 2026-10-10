from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4


CHECKLIST_ITEMS = (
    "eligibility_checked",
    "policy_rechecked",
    "manual_submission",
    "truthful_submission",
    "reward_received",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return (slug[:48].rstrip("-") or "draft")


def format_draft(
    project_root: Path, topic: str, draft_format: str, audience: str
) -> Path:
    templates_path = project_root / "data" / "draft_templates.json"
    templates = load_json(templates_path, {})
    if draft_format not in templates:
        valid = ", ".join(sorted(templates))
        raise ValueError(f"Unknown draft format {draft_format!r}. Choose: {valid}")

    values = {
        "topic": topic.strip(),
        "audience": audience.strip() or "people who may need this service",
        "service": topic.strip(),
    }
    template = templates[draft_format]
    lines = [f"# {template['title'].format(**values)}", ""]
    lines.extend(section.format(**values) for section in template["sections"])
    lines += [
        "",
        "---",
        "Template-generated starting point. Review, fact-check, and edit before use.",
        "",
    ]

    output_dir = project_root / "output" / "drafts"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{utc_now():%Y%m%dT%H%M%SZ}-{safe_slug(topic)}.md"
    output_path = output_dir / filename
    output_path.write_text("\n\n".join(lines), encoding="utf-8")
    return output_path


def generate_ideas(skill: str, audience: str) -> list[str]:
    skill = skill.strip() or "writing and proofreading"
    audience = audience.strip() or "independent professionals"
    concepts = [
        ("A fixed-length checklist", f"Create a one-page checklist about {skill} for {audience}."),
        ("A polished short document", f"Edit one short, customer-provided document for {audience}."),
        ("A reusable template", f"Build a simple, editable template that helps {audience} complete a recurring {skill} task."),
        ("A short explainer", f"Draft a plain-language explainer about one well-defined {skill} problem faced by {audience}."),
        ("A small research summary", f"Summarize sources supplied by a customer into a concise brief for {audience}, with citations."),
    ]
    return [
        f"{index}. **{name}** — {description} Start with a sample and confirm scope before offering it."
        for index, (name, description) in enumerate(concepts, start=1)
    ]


def load_tasks(project_root: Path) -> list[dict[str, Any]]:
    tasks = load_json(project_root / "data" / "reward_tasks.json", [])
    if not isinstance(tasks, list):
        raise ValueError("data/reward_tasks.json must contain a JSON list.")
    return tasks


def save_tasks(project_root: Path, tasks: list[dict[str, Any]]) -> None:
    save_json(project_root / "data" / "reward_tasks.json", tasks)


def add_task(
    project_root: Path,
    title: str,
    platform: str,
    terms_url: str,
    policy_evidence: str,
    automation_permitted: bool,
) -> dict[str, Any]:
    parsed_url = urlparse(terms_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("The terms URL must be a full HTTPS URL.")
    if not automation_permitted:
        raise ValueError(
            "Not added: you must confirm the current terms explicitly permit the "
            "automation you intend to use. If unclear, do not track it here."
        )
    if not policy_evidence.strip():
        raise ValueError("Provide a concise note identifying the policy evidence.")
    if not title.strip() or not platform.strip():
        raise ValueError("Title and platform are required.")

    tasks = load_tasks(project_root)
    task = {
        "id": uuid4().hex[:8],
        "title": title.strip(),
        "platform": platform.strip(),
        "terms_url": terms_url.strip(),
        "policy_evidence": policy_evidence.strip(),
        "automation_permitted_confirmed_by_user": True,
        "policy_checked_at_utc": timestamp(),
        "checklist": {item: False for item in CHECKLIST_ITEMS},
        "reward_receipt": None,
        "created_at_utc": timestamp(),
    }
    tasks.append(task)
    save_tasks(project_root, tasks)
    return task


def find_task(tasks: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    for task in tasks:
        if task.get("id") == task_id:
            return task
    raise ValueError(f"No task found with ID {task_id!r}.")


def set_checklist_item(
    project_root: Path, task_id: str, item: str, done: bool
) -> dict[str, Any]:
    if item not in CHECKLIST_ITEMS:
        raise ValueError(f"Unknown checklist item {item!r}.")
    tasks = load_tasks(project_root)
    task = find_task(tasks, task_id)
    task["checklist"][item] = bool(done)
    if item == "reward_received" and not done:
        task["reward_receipt"] = None
    save_tasks(project_root, tasks)
    return task


def record_reward(
    project_root: Path, task_id: str, amount: str, currency: str, evidence: str
) -> dict[str, Any]:
    from decimal import Decimal, InvalidOperation

    try:
        value = Decimal(amount)
    except InvalidOperation as exc:
        raise ValueError("Reward amount must be a valid decimal.") from exc
    if not value.is_finite() or value <= 0:
        raise ValueError("Reward amount must be a positive, confirmed amount.")
    if not currency.strip() or not evidence.strip():
        raise ValueError("Currency and a note identifying receipt evidence are required.")
    tasks = load_tasks(project_root)
    task = find_task(tasks, task_id)
    if not task["checklist"].get("reward_received"):
        raise ValueError(
            "First mark reward_received after you personally confirm the payout."
        )
    task["reward_receipt"] = {
        "amount": format(value, "f"),
        "currency": currency.strip().upper(),
        "evidence_note": evidence.strip(),
        "recorded_at_utc": timestamp(),
        "reported_by_user": True,
    }
    save_tasks(project_root, tasks)
    return task


def write_snapshot(project_root: Path) -> tuple[Path, Path]:
    tasks = load_tasks(project_root)
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    tracker_path = output_dir / "reward_tracker.json"
    report_path = output_dir / "reward_report.md"
    shutil.copyfile(project_root / "data" / "reward_tasks.json", tracker_path)

    lines = [
        "# Reward opportunity checklist",
        "",
        f"Generated at {timestamp()}",
        "",
        "This is a planning record. The app does not interact with reward platforms.",
        "Any receipt shown below was entered by the user and is not independently verified.",
        "",
    ]
    if not tasks:
        lines.append("No opportunities are recorded.")
    for task in tasks:
        lines.extend(
            [
                f"## {task['title']} ({task['id']})",
                "",
                f"- Platform: {task['platform']}",
                f"- Terms: {task['terms_url']}",
                f"- Policy evidence note: {task['policy_evidence']}",
                f"- User-confirmed automation permission checked: {task['policy_checked_at_utc']}",
                "",
                "Checklist:",
            ]
        )
        for item in CHECKLIST_ITEMS:
            state = "x" if task["checklist"].get(item) else " "
            lines.append(f"- [{state}] {item.replace('_', ' ')}")
        receipt = task.get("reward_receipt")
        if receipt:
            lines += [
                "",
                f"User-reported confirmed receipt: {receipt['amount']} {receipt['currency']}",
                f"Evidence note: {receipt['evidence_note']}",
            ]
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return tracker_path, report_path
