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
    employer_only: bool


@dataclass
class PlannedDayWorklogs:
    date_str: str
    started: str
    issues: List[PlannedIssueWorklogs]

    def commit(self, client) -> None:
        import time

        for planned_issue in self.issues:
            for entry in planned_issue.time_logs:
                client.create_time_log(
                    planned_issue.issue,
                    entry.hours,
                    entry.comment,
                    started=self.started,
                )

                print(
                    f"[OK] {client.base_url} | {self.date_str} | "
                    f"{planned_issue.issue.key} | {entry.hours}h | {entry.comment}"
                )

                time.sleep(1)