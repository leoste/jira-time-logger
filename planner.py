from datetime import datetime, timedelta
from typing import List

from models import (
    PlannedDayWorklogs,
    PlannedIssueWorklogs,
    PlannedTimeLogEntry,
    ParsedDay,
)


class WorklogPlanner:
    def __init__(self, customer_client, employer_client):
        self.customer = customer_client
        self.employer = employer_client

    def build(
        self,
        parsed: List[ParsedDay],
    ) -> tuple[List[PlannedDayWorklogs], List[PlannedDayWorklogs]]:
        customer_days: List[PlannedDayWorklogs] = []
        employer_days: List[PlannedDayWorklogs] = []

        for day in parsed:
            customer_issue_plans: List[PlannedIssueWorklogs] = []
            employer_issue_plans: List[PlannedIssueWorklogs] = []

            cumulative_hours = 0.0

            for issue in day.issues:
                employer_issue = (
                    self._resolve_employer_issue(issue.key, issue.is_employer_only)
                    if self._should_log_to_employer(issue.is_client_only)
                    else None
                )
                customer_issue = (
                    self._resolve_customer_issue(issue.key)
                    if self._should_log_to_customer(issue.is_employer_only)
                    else None
                )

                planned_logs: List[PlannedTimeLogEntry] = []
                for tl in issue.time_logs:
                    started = self._compute_started(day.date_str, day.start_time, cumulative_hours)
                    planned_logs.append(PlannedTimeLogEntry(hours=tl.hours, comment=tl.comment, started=started))
                    cumulative_hours += tl.hours

                if employer_issue is not None:
                    employer_issue_plans.append(
                        PlannedIssueWorklogs(
                            issue=employer_issue,
                            time_logs=planned_logs,
                            is_employer_only=issue.is_employer_only,
                            is_client_only=False,
                        )
                    )

                if customer_issue is not None:
                    customer_issue_plans.append(
                        PlannedIssueWorklogs(
                            issue=customer_issue,
                            time_logs=planned_logs,
                            is_employer_only=False,
                            is_client_only=issue.is_client_only,
                        )
                    )

            customer_days.append(
                PlannedDayWorklogs(
                    date_str=day.date_str,
                    issues=customer_issue_plans,
                )
            )

            employer_days.append(
                PlannedDayWorklogs(
                    date_str=day.date_str,
                    issues=employer_issue_plans,
                )
            )

        return customer_days, employer_days

    def _should_log_to_customer(self, is_employer_only: bool) -> bool:
        return not is_employer_only

    def _should_log_to_employer(self, is_client_only: bool) -> bool:
        return not is_client_only

    def _resolve_employer_issue(self, issue_key: str, is_employer_only: bool):
        if is_employer_only:
            return self.employer.find_issue_by_number(issue_key)
        return self.employer.find_issue_by_name_containing(issue_key)

    def _resolve_customer_issue(self, issue_key: str):
        return self.customer.find_issue_by_number(issue_key)

    def _compute_started(self, date_str: str, start_time: str, offset_hours: float) -> str:
        local_tz = datetime.now().astimezone().tzinfo
        dt = datetime.strptime(f"{date_str} {start_time}", "%d.%m.%Y %H:%M").replace(tzinfo=local_tz)
        dt = dt + timedelta(hours=offset_hours)
        return dt.strftime("%Y-%m-%dT%H:%M:00.000%z")