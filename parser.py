# parser.py

from datetime import datetime
from typing import Dict, List, Tuple

from models import TimeLogEntry


def parse_issue_line(line: str) -> Tuple[str, bool]:
    if line.endswith("(employer)"):
        issue = line[: -len("(employer)")].strip()
        return issue, True
    return line, False


def parse_input(
    text: str,
) -> Dict[str, Dict[str, Tuple[List[TimeLogEntry], bool]]]:
    lines = text.splitlines()

    result: Dict[str, Dict[str, Tuple[List[TimeLogEntry], bool]]] = {}

    current_date: str | None = None
    current_issue: str | None = None

    for raw_line in lines:
        line = raw_line.strip()

        if line == "":
            continue

        # Date
        try:
            datetime.strptime(line, "%d.%m.%Y")
            current_date = line
            current_issue = None

            if current_date not in result:
                result[current_date] = {}

            continue
        except ValueError:
            pass

        if current_date is None:
            raise ValueError("Issue or timelog found before any date.")

        # Timelog
        parts = line.split(maxsplit=1)

        if len(parts) >= 1:
            try:
                hours = float(parts[0])

                if current_issue is None:
                    raise ValueError("Timelog found before any issue.")

                comment = parts[1] if len(parts) > 1 else ""

                issue_map = result[current_date]

                logs, employer_only = issue_map[current_issue]
                logs.append(TimeLogEntry(hours=hours, comment=comment))

                continue

            except ValueError:
                pass

        # Issue
        issue_key, employer_only = parse_issue_line(line)

        current_issue = issue_key
        issue_map = result[current_date]

        if current_issue not in issue_map:
            issue_map[current_issue] = ([], employer_only)
        else:
            logs, existing_flag = issue_map[current_issue]
            issue_map[current_issue] = (logs, existing_flag or employer_only)

    return result