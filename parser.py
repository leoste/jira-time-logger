from datetime import datetime
from typing import List

from models import TimeLogEntry, ParsedDay, ParsedIssue


def parse_issue_line(line: str) -> tuple[str, bool]:
    if line.endswith("(employer)"):
        issue = line[: -len("(employer)")].strip()
        return issue, True
    return line, False


def parse_input(text: str) -> List[ParsedDay]:
    lines = text.splitlines()

    days: List[ParsedDay] = []

    current_day: ParsedDay | None = None
    current_issue: ParsedIssue | None = None

    for raw_line in lines:
        line = raw_line.strip()

        if line == "":
            continue

        try:
            datetime.strptime(line, "%d.%m.%Y")

            current_day = ParsedDay(date_str=line, issues=[])
            days.append(current_day)
            current_issue = None
            continue

        except ValueError:
            pass

        if current_day is None:
            raise ValueError("Issue or timelog found before any date.")

        parts = line.split(maxsplit=1)

        if len(parts) >= 1:
            try:
                hours = float(parts[0])

                if current_issue is None:
                    raise ValueError("Timelog found before any issue.")

                comment = parts[1] if len(parts) > 1 else ""

                current_issue.time_logs.append(
                    TimeLogEntry(hours=hours, comment=comment)
                )

                continue

            except ValueError:
                pass

        issue_key, is_employer_only = parse_issue_line(line)

        for issue in current_day.issues:
            if issue.key == issue_key:
                issue.is_employer_only = (
                    issue.is_employer_only or is_employer_only
                )
                current_issue = issue
                break
        else:
            new_issue = ParsedIssue(
                key=issue_key,
                time_logs=[],
                is_employer_only=is_employer_only,
            )
            current_day.issues.append(new_issue)
            current_issue = new_issue

    return days