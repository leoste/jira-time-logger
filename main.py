# main.py

from datetime import datetime

from config import (
    ORIGINAL_JIRA_URL,
    ORIGINAL_JIRA_TOKEN,
    ORIGINAL_JIRA_VERIFY_SSL,
    DUPLICATE_JIRA_URL,
    DUPLICATE_JIRA_EMAIL,
    DUPLICATE_JIRA_TOKEN,
    DUPLICATE_JIRA_PROJECT_KEY,
    DUPLICATE_JIRA_VERIFY_SSL,
)
from jira_clients import (
    PatJiraClient,
    ApiJiraClient,
    JiraClientError,
)
from models import PlannedIssueWorklogs
from parser import parse_input


def read_worklog_date() -> str | None:
    while True:
        raw = input(
            'Worklog date (dd.mm.yyyy), press Enter for default: '
        ).strip()

        if raw == "":
            return None

        try:
            dt = datetime.strptime(raw, "%d.%m.%Y")
        except ValueError:
            print("Invalid date format. Use dd.mm.yyyy (example: 28.03.2026).")
            continue

        # Jira expects a full timestamp, not date-only.
        # Using fixed noon UTC for stable backdating by date.
        return dt.strftime("%Y-%m-%dT12:00:00.000+0000")


def get_display_date(started: str | None) -> str:
    if started is None:
        return datetime.now().strftime("%d.%m.%Y")

    dt = datetime.strptime(started, "%Y-%m-%dT%H:%M:%S.000+0000")
    return dt.strftime("%d.%m.%Y")


def read_multiline_input() -> str:
    print("Paste your worklog input. Finish with a line containing only END.")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines)


def print_plans(
    title: str,
    plans: list[PlannedIssueWorklogs],
    client_url: str,
    display_date: str,
) -> None:
    print("\n" + "=" * 80)
    print(f"{title} ({client_url})")
    print("=" * 80)

    for plan in plans:
        print(f"{plan.issue.key} - {plan.issue.title}")
        print(f"URL: {plan.issue.url}")
        print(f"Date: {display_date}")
        for entry in plan.time_logs:
            print(f"{entry.hours} - {entry.comment}")
        print()


def main():
    # Create clients first
    original = PatJiraClient(
        base_url=ORIGINAL_JIRA_URL,
        token=ORIGINAL_JIRA_TOKEN,
        verify_ssl=ORIGINAL_JIRA_VERIFY_SSL,
    )

    duplicate = ApiJiraClient(
        base_url=DUPLICATE_JIRA_URL,
        email=DUPLICATE_JIRA_EMAIL,
        token=DUPLICATE_JIRA_TOKEN,
        project_key=DUPLICATE_JIRA_PROJECT_KEY,
        verify_ssl=DUPLICATE_JIRA_VERIFY_SSL,
    )

    # Ping both before asking for input
    print("Checking Jira connections...")

    try:
        original.ping()
        print(f"[OK] Original Jira reachable: {original.base_url}")

        duplicate.ping()
        print(f"[OK] Duplicate Jira reachable: {duplicate.base_url}")

    except JiraClientError as e:
        print(f"\n[CONNECTION ERROR] {e}")
        print("Program stopped.")
        return

    # Ask optional worklog date
    started = read_worklog_date()
    display_date = get_display_date(started)

    # Parse loop
    while True:
        text = read_multiline_input()

        try:
            parsed = parse_input(text)
            break
        except ValueError as e:
            print(f"\n[PARSE ERROR] {e}\nPlease try again.\n")

    original_plans: list[PlannedIssueWorklogs] = []
    duplicate_plans: list[PlannedIssueWorklogs] = []

    # Resolve issues (stop on first error)
    try:
        for source_issue_key, time_logs in parsed.items():
            original_issue = original.find_issue_by_number(source_issue_key)
            duplicate_issue = duplicate.find_issue_by_name_containing(source_issue_key)

            original_plans.append(
                PlannedIssueWorklogs(issue=original_issue, time_logs=time_logs)
            )
            duplicate_plans.append(
                PlannedIssueWorklogs(issue=duplicate_issue, time_logs=time_logs)
            )

    except JiraClientError as e:
        print(f"\n[LOOKUP ERROR] {e}")
        print("Program stopped.")
        return

    # Preview
    print_plans("ORIGINAL JIRA", original_plans, original.base_url, display_date)
    print_plans("DUPLICATE JIRA", duplicate_plans, duplicate.base_url, display_date)

    # Confirm
    answer = input('Type "yes" to commit: ').strip()
    if answer != "yes":
        print("Cancelled.")
        return

    # Commit original first, then duplicate
    try:
        print("\nCommitting to ORIGINAL JIRA...\n")
        for plan in original_plans:
            plan.commit(original, started=started)

        print("\nCommitting to DUPLICATE JIRA...\n")
        for plan in duplicate_plans:
            plan.commit(duplicate, started=started)

    except JiraClientError as e:
        print(f"\n[COMMIT ERROR] {e}")
        print("Program stopped.")
        return

    print("\nAll worklogs committed successfully.")


if __name__ == "__main__":
    main()