# models.py

from dataclasses import dataclass
from typing import List


@dataclass
class TimeLogEntry:
    hours: float
    comment: str


@dataclass
class IssueInfo:
    key: str
    title: str
    url: str


@dataclass
class PlannedIssueWorklogs:
    issue: IssueInfo
    time_logs: List[TimeLogEntry]

    def commit(self, client) -> None:
        import time

        for entry in self.time_logs:
            client.create_time_log(self.issue, entry.hours, entry.comment)
            print(
                f"[OK] {client.base_url} -> {self.issue.key} | {entry.hours}h | {entry.comment}"
            )
            time.sleep(1)