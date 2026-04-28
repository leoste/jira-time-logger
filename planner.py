# planner.py

from datetime import datetime
from typing import Dict, List, Tuple

from jira_clients import JiraClientError
from models import PlannedDayWorklogs, PlannedIssueWorklogs, TimeLogEntry


class WorklogPlanner:
    def __init__(self, customer_client, employer_client):
        self.customer = customer_client
        self.employer = employer_client

    def build(
        self,
        parsed: Dict[str, Dict[str, Tuple[List[TimeLogEntry], bool]]],
    ) -> tuple[List[PlannedDayWorklogs], List[PlannedDayWorklogs]]:
        customer_days: List[PlannedDayWorklogs] = []
        employer_days: List[PlannedDayWorklogs] = []

        for date_str, issues in parsed.items():
            started = self._to_jira_started(date_str)

            customer_issue_plans: List[PlannedIssueWorklogs] = []
            employer_issue_plans: List[PlannedIssueWorklogs] = []

            for issue_key, (time_logs, employer_only) in issues.items():
                employer_issue = self._resolve_employer_issue(
                    issue_key, employer_only
                )

                employer_issue_plans.append(
                    PlannedIssueWorklogs(
                        issue=employer_issue,
                        time_logs=time_logs,
                        employer_only=employer_only,
                    )
                )

                if not employer_only:
                    customer_issue = self._resolve_customer_issue(issue_key)

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

        return customer_days, employer_days

    def _resolve_employer_issue(self, issue_key: str, employer_only: bool):
        if employer_only:
            return self.employer.find_issue_by_number(issue_key)
        return self.employer.find_issue_by_name_containing(issue_key)

    def _resolve_customer_issue(self, issue_key: str):
        return self.customer.find_issue_by_number(issue_key)

    def _to_jira_started(self, date_str: str) -> str:
        dt = datetime.strptime(date_str, "%d.%m.%Y")
        return dt.strftime("%Y-%m-%dT12:00:00.000+0000")