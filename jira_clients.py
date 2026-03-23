# jira_clients.py

import base64
import requests
import urllib3

from models import IssueInfo


class JiraClientError(Exception):
    pass


class IssueNotFoundError(JiraClientError):
    pass


class MultipleIssuesFoundError(JiraClientError):
    pass


class PatJiraClient:
    def __init__(self, base_url: str, token: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def ping(self) -> None:
        url = f"{self.base_url}/rest/api/2/myself"

        try:
            response = self.session.get(url, timeout=15, verify=self.verify_ssl)
        except requests.RequestException as e:
            raise JiraClientError(
                f"Network error while connecting to {self.base_url}: {e}"
            )

        if response.status_code != 200:
            raise JiraClientError(
                f"Connection/auth check failed for {self.base_url}. "
                f"HTTP {response.status_code}: {response.text}"
            )

    def find_issue_by_number(self, issue_key: str) -> IssueInfo:
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"

        try:
            response = self.session.get(url, timeout=15, verify=self.verify_ssl)
        except requests.RequestException as e:
            raise JiraClientError(
                f"Network error while finding issue '{issue_key}' in {self.base_url}: {e}"
            )

        if response.status_code == 404:
            raise IssueNotFoundError(
                f"Issue '{issue_key}' not found in {self.base_url}"
            )

        if response.status_code != 200:
            raise JiraClientError(
                f"Failed to find issue '{issue_key}' in {self.base_url}. "
                f"HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        key = data["key"]
        title = data["fields"]["summary"]
        issue_url = f"{self.base_url}/browse/{key}"

        return IssueInfo(key=key, title=title, url=issue_url)

    def create_time_log(self, issue: IssueInfo, hours: float, comment: str) -> None:
        url = f"{self.base_url}/rest/api/2/issue/{issue.key}/worklog"

        payload = {
            "comment": comment,
            "timeSpent": f"{hours}h",
        }

        try:
            response = self.session.post(
                url, json=payload, timeout=15, verify=self.verify_ssl
            )
        except requests.RequestException as e:
            raise JiraClientError(
                f"Network error while creating worklog on '{issue.key}' in {self.base_url}: {e}"
            )

        if response.status_code not in (200, 201):
            raise JiraClientError(
                f"Failed to create worklog on '{issue.key}' in {self.base_url}. "
                f"HTTP {response.status_code}: {response.text}"
            )


class ApiJiraClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        token: str,
        project_key: str,
        verify_ssl: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.token = token
        self.project_key = project_key
        self.verify_ssl = verify_ssl

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        auth_bytes = f"{self.email}:{self.token}".encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Basic {auth_b64}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def ping(self) -> None:
        url = f"{self.base_url}/rest/api/3/myself"

        try:
            response = self.session.get(url, timeout=15, verify=self.verify_ssl)
        except requests.RequestException as e:
            raise JiraClientError(
                f"Network error while connecting to {self.base_url}: {e}"
            )

        if response.status_code != 200:
            raise JiraClientError(
                f"Connection/auth check failed for {self.base_url}. "
                f"HTTP {response.status_code}: {response.text}"
            )

    def find_issue_by_name_containing(self, text: str) -> IssueInfo:
        jql = f'project = "{self.project_key}" AND summary ~ "\\"{text}\\""'

        url = f"{self.base_url}/rest/api/3/search/jql"

        params = {
            "jql": jql,
            "maxResults": 2,
            "fields": "summary",
        }

        try:
            response = self.session.get(
                url, params=params, timeout=15, verify=self.verify_ssl
            )
        except requests.RequestException as e:
            raise JiraClientError(
                f"Network error while searching for '{text}' in {self.base_url}: {e}"
            )

        if response.status_code != 200:
            raise JiraClientError(
                f"Failed to search for '{text}' in {self.base_url}. "
                f"HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        issues = data.get("issues", [])

        if len(issues) == 0:
            raise IssueNotFoundError(
                f"No issue found in {self.base_url} with summary containing '{text}' "
                f"under project '{self.project_key}'."
            )

        if len(issues) > 1:
            found_keys = [issue["key"] for issue in issues]
            raise MultipleIssuesFoundError(
                f"Multiple issues found in {self.base_url} for '{text}' "
                f"under project '{self.project_key}': {found_keys}"
            )

        issue = issues[0]
        key = issue["key"]
        title = issue["fields"]["summary"]
        issue_url = f"{self.base_url}/browse/{key}"

        return IssueInfo(key=key, title=title, url=issue_url)

    def create_time_log(self, issue: IssueInfo, hours: float, comment: str) -> None:
        url = f"{self.base_url}/rest/api/3/issue/{issue.key}/worklog"

        payload = {
            "comment": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment,
                            }
                        ],
                    }
                ],
            },
            "timeSpent": f"{hours}h",
        }

        try:
            response = self.session.post(
                url, json=payload, timeout=15, verify=self.verify_ssl
            )
        except requests.RequestException as e:
            raise JiraClientError(
                f"Network error while creating worklog on '{issue.key}' in {self.base_url}: {e}"
            )

        if response.status_code not in (200, 201):
            raise JiraClientError(
                f"Failed to create worklog on '{issue.key}' in {self.base_url}. "
                f"HTTP {response.status_code}: {response.text}"
            )