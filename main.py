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
            suffix = " (employer)" if plan.employer_only else ""
            print(f"{plan.issue.key}{suffix} - {plan.issue.title}")
            print(f"URL: {plan.issue.url}")
            for entry in plan.time_logs:
                print(f"{entry.hours} - {entry.comment}")
            print()

        print("-" * 40)


def main():
    customer = PatJiraClient(
        base_url=ORIGINAL_JIRA_URL,
        token=ORIGINAL_JIRA_TOKEN,
        verify_ssl=ORIGINAL_JIRA_VERIFY_SSL,
    )

    employer = ApiJiraClient(
        base_url=DUPLICATE_JIRA_URL,
        email=DUPLICATE_JIRA_EMAIL,
        token=DUPLICATE_JIRA_TOKEN,
        project_key=DUPLICATE_JIRA_PROJECT_KEY,
        verify_ssl=DUPLICATE_JIRA_VERIFY_SSL,
    )

    print("Checking Jira connections...")

    try:
        customer.ping()
        print(f"[OK] Customer Jira reachable: {customer.base_url}")

        employer.ping()
        print(f"[OK] Employer Jira reachable: {employer.base_url}")

    except JiraClientError as e:
        print(f"\n[CONNECTION ERROR] {e}")
        return

    while True:
        text = read_multiline_input()

        try:
            parsed = parse_input(text)
            break
        except ValueError as e:
            print(f"\n[PARSE ERROR] {e}\nTry again.\n")

    customer_days: list[PlannedDayWorklogs] = []
    employer_days: list[PlannedDayWorklogs] = []

    try:
        for date_str, issues in parsed.items():
            started = to_jira_started(date_str)

            customer_issue_plans = []
            employer_issue_plans = []

            for issue_key, (time_logs, employer_only) in issues.items():

                # EMPLOYER lookup
                if employer_only:
                    employer_issue = employer.find_issue_by_number(issue_key)
                else:
                    employer_issue = employer.find_issue_by_name_containing(issue_key)

                employer_issue_plans.append(
                    PlannedIssueWorklogs(
                        issue=employer_issue,
                        time_logs=time_logs,
                        employer_only=employer_only,
                    )
                )

                # CUSTOMER lookup
                if not employer_only:
                    customer_issue = customer.find_issue_by_number(issue_key)

                    customer_issue_plans.append(
                        PlannedIssueWorklogs(
                            issue=customer_issue,
                            time_logs=time_logs,
                            employer_only=False,
                        )
                    )

            customer_days.append(
                PlannedDayWorklogs(
                    date_str=date_str,
                    started=started,
                    issues=customer_issue_plans,
                )
            )

            employer_days.append(
                PlannedDayWorklogs(
                    date_str=date_str,
                    started=started,
                    issues=employer_issue_plans,
                )
            )

    except JiraClientError as e:
        print(f"\n[LOOKUP ERROR] {e}")
        return

    print_plans("CUSTOMER JIRA", customer_days, customer.base_url)
    print_plans("EMPLOYER JIRA", employer_days, employer.base_url)

    answer = input('Type "yes" to commit: ').strip()
    if answer != "yes":
        print("Cancelled.")
        return

    try:
        print("\nCommitting to CUSTOMER JIRA...\n")
        for day in customer_days:
            day.commit(customer, is_customer=True)

        print("\nCommitting to EMPLOYER JIRA...\n")
        for day in employer_days:
            day.commit(employer, is_customer=False)

    except JiraClientError as e:
        print(f"\n[COMMIT ERROR] {e}")
        return

    print("\nAll worklogs committed successfully.")


if __name__ == "__main__":
    main()