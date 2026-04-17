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
from models import PlannedIssueWorklogs, PlannedDayWorklogs
from parser import parse_input


def to_jira_started(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%d.%m.%Y")
    return dt.strftime("%Y-%m-%dT12:00:00.000+0000")


def read_multiline_input() -> str:
    print("Paste your worklog input. Finish with a line containing only END.")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines)


def print_plans(title: str, days: list[PlannedDayWorklogs], client_url: str) -> None:
    print("\n" + "=" * 80)
    print(f"{title} ({client_url})")
    print("=" * 80)

    for day in days:
        print(f"\nDate: {day.date_str}\n")

        for plan in day.issues:
            print(f"{plan.issue.key} - {plan.issue.title}")
            print(f"URL: {plan.issue.url}")
            for entry in plan.time_logs:
                print(f"{entry.hours} - {entry.comment}")
            print()

        print("-" * 40)


def main():
    # Create clients
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

    # Ping
    print("Checking Jira connections...")

    try:
        original.ping()
        print(f"[OK] Original Jira reachable: {original.base_url}")

        duplicate.ping()
        print(f"[OK] Duplicate Jira reachable: {duplicate.base_url}")

    except JiraClientError as e:
        print(f"\n[CONNECTION ERROR] {e}")
        return

    # Parse input
    while True:
        text = read_multiline_input()

        try:
            parsed = parse_input(text)
            break
        except ValueError as e:
            print(f"\n[PARSE ERROR] {e}\nTry again.\n")

    original_days: list[PlannedDayWorklogs] = []
    duplicate_days: list[PlannedDayWorklogs] = []

    # Resolve issues
    try:
        for date_str, issues in parsed.items():
            started = to_jira_started(date_str)

            original_issue_plans: list[PlannedIssueWorklogs] = []
            duplicate_issue_plans: list[PlannedIssueWorklogs] = []

            for issue_key, time_logs in issues.items():
                original_issue = original.find_issue_by_number(issue_key)
                duplicate_issue = duplicate.find_issue_by_name_containing(issue_key)

                original_issue_plans.append(
                    PlannedIssueWorklogs(issue=original_issue, time_logs=time_logs)
                )
                duplicate_issue_plans.append(
                    PlannedIssueWorklogs(issue=duplicate_issue, time_logs=time_logs)
                )

            original_days.append(
                PlannedDayWorklogs(
                    date_str=date_str,
                    started=started,
                    issues=original_issue_plans,
                )
            )

            duplicate_days.append(
                PlannedDayWorklogs(
                    date_str=date_str,
                    started=started,
                    issues=duplicate_issue_plans,
                )
            )

    except JiraClientError as e:
        print(f"\n[LOOKUP ERROR] {e}")
        return

    # Preview
    print_plans("ORIGINAL JIRA", original_days, original.base_url)
    print_plans("DUPLICATE JIRA", duplicate_days, duplicate.base_url)

    # Confirm
    answer = input('Type "yes" to commit: ').strip()
    if answer != "yes":
        print("Cancelled.")
        return

    # Commit
    try:
        print("\nCommitting to ORIGINAL JIRA...\n")
        for day in original_days:
            day.commit(original)

        print("\nCommitting to DUPLICATE JIRA...\n")
        for day in duplicate_days:
            day.commit(duplicate)

    except JiraClientError as e:
        print(f"\n[COMMIT ERROR] {e}")
        return

    print("\nAll worklogs committed successfully.")


if __name__ == "__main__":
    main()