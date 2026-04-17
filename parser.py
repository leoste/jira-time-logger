# parser.py

from datetime import datetime
from typing import Dict, List

from models import TimeLogEntry


def parse_input(text: str) -> Dict[str, Dict[str, List[TimeLogEntry]]]:
    lines = text.splitlines()

    result: Dict[str, Dict[str, List[TimeLogEntry]]] = {}

    current_date: str | None = None
    current_issue: str | None = None

    for raw_line in lines:
        line = raw_line.strip()

        if line == "":
            continue

        # Try parse as date
        try:
            dt = datetime.strptime(line, "%d.%m.%Y")
            current_date = line
            current_issue = None

            if current_date not in result:
                result[current_date] = {}

            continue
        except ValueError:
            pass

        # If no date yet → error
        if current_date is None:
            raise ValueError("Issue or timelog found before any date.")

        # Try parse as timelog line
        parts = line.split(maxsplit=1)

        if len(parts) >= 1:
            try:
                hours = float(parts[0])

                if current_issue is None:
                    raise ValueError("Timelog found before any issue.")

                comment = parts[1] if len(parts) > 1 else ""

                issue_map = result[current_date]

                if current_issue not in issue_map:
                    issue_map[current_issue] = []

                issue_map[current_issue].append(
                    TimeLogEntry(hours=hours, comment=comment)
                )

                continue

            except ValueError:
                pass

        # Otherwise it's an issue line
        current_issue = line

        issue_map = result[current_date]

        if current_issue not in issue_map:
            issue_map[current_issue] = []

    return result