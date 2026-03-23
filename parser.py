# parser.py

from typing import Dict, List
from models import TimeLogEntry


def parse_input(text: str) -> Dict[str, List[TimeLogEntry]]:
    """
    Expected format:

    ISSUE-123
    0.5 did something
    3 did another thing

    ISSUE-456
    2 more work
    """

    lines = text.splitlines()
    result: Dict[str, List[TimeLogEntry]] = {}

    current_issue = None
    current_logs: List[TimeLogEntry] = []

    def flush_current():
        nonlocal current_issue, current_logs
        if current_issue is not None:
            if not current_logs:
                raise ValueError(f"Issue '{current_issue}' has no time log entries.")
            result[current_issue] = current_logs
            current_issue = None
            current_logs = []

    for raw_line in lines:
        line = raw_line.strip()

        # Empty line separates blocks
        if line == "":
            flush_current()
            continue

        # If no current issue, this line must be the issue key
        if current_issue is None:
            current_issue = line
            if current_issue in result:
                raise ValueError(f"Duplicate issue block found for '{current_issue}'.")
            continue

        # Otherwise this line must be a timelog line: "<hours> <comment>"
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            raise ValueError(
                f"Invalid timelog line under issue '{current_issue}': '{line}'. "
                f"Expected format: '<hours> <comment>'"
            )

        hours_str, comment = parts

        try:
            hours = float(hours_str)
        except ValueError:
            raise ValueError(
                f"Invalid hour value under issue '{current_issue}': '{hours_str}'"
            )

        if hours <= 0:
            raise ValueError(
                f"Hours must be greater than 0 under issue '{current_issue}': '{hours_str}'"
            )

        comment = comment.strip()
        if not comment:
            raise ValueError(
                f"Comment cannot be empty under issue '{current_issue}'."
            )

        current_logs.append(TimeLogEntry(hours=hours, comment=comment))

    # Flush final block if present
    flush_current()

    if not result:
        raise ValueError("No valid issue blocks found in input.")

    return result