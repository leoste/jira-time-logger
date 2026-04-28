from datetime import datetime
from typing import List

from models import (
    PlannedDayWorklogs,
    PlannedIssueWorklogs,
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
            started = self._to_jira_started(day.date_str)

            customer_issue_plans: List[PlannedIssueWorklogs] = []
            employer_issue_plans: List[PlannedIssueWorklogs] = []

            for issue in day.issues:
                employer_issue = self._resolve_employer_issue(
                    issue.key, issue.is_employer_only
                )

                employer_issue_plans.append(
                    PlannedIssueWorklogs(
                        issue=employer_issue,
                        time_logs=issue.time_logs,
                        is_employer_only=issue.is_employer_only,
                    )
                )

                if self._should_log_to_customer(issue.is_employer_only):
                    customer_issue = self._resolve_customer_issue(issue.key)

                    customer_issue_plans.append(
                        PlannedIssueWorklogs(
                            issue=customer_issue,
                            time_logs=issue.time_logs,
                            is_employer_only=False,
                        )
                    )

            customer_days.append(
                PlannedDayWorklogs(
                    date_str=day.date_str,
                    started=started,
                    issues=customer_issue_plans,
                )
            )

            employer_days.append(
                PlannedDayWorklogs(
                    date_str=day.date_str,
                    started=started,
                    issues=employer_issue_plans,
                )
            )

        return customer_days, employer_days

    def _should_log_to_customer(self, is_employer_only: bool) -> bool:
        return not is_employer_only

    def _resolve_employer_issue(self, issue_key: str, is_employer_only: bool):
        if is_employer_only:
            return self.employer.find_issue_by_number(issue_key)
        return self.employer.find_issue_by_name_containing(issue_key)

    def _resolve_customer_issue(self, issue_key: str):
        return self.customer.find_issue_by_number(issue_key)

    def _to_jira_started(self, date_str: str) -> str:
        dt = datetime.strptime(date_str, "%d.%m.%Y")
        return dt.strftime("%Y-%m-%dT12:00:00.000+0000")