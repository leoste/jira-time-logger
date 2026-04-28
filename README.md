# Dual Jira Time Logger

This script helps to easily create time logs across two Jira boards, where one is the original, customer Jira and other is the duplicate, employer Jira.
In the original Jira, ticket keys are used, for example "jira/TICKET-43" and title "magnificient change"
In the duplicate jira, the name of the original ticket is in the name of the duplicate ticket. For example: "jira/DUPL-3" and title "TICKET-43 magnificient change".

## Usage

You type out your logs as simple text, then just paste it into the script. The script finds all the necessary tickets and after approval from you, the script automatically commits the timelogs.

Sample timelog text:
```
27.04.2026
TICKET-43
2 I worked a lot
0.5 worked less
TICKET-73
1 worked on other task as well
2.5 explanation for long time
28.04.2026
TICKET-73
3 long morning
1.5 quick work
TICKET-7
0.5 looked into it
END
```

If any issue can't be found, Jira can't be connected to, or text can't be parsed, program will abort, giving you some safeguard.
NB! the program doesn't check for duplicate commits. If you commit the same thing twice, that's on you.

## Setup

copy-paste config.py.sample into config.py and fill out the details with your Jira tokens.

There are two types of Jira connections: API or PAT, which depends on the Jira version. if you go to get your token in Jira, you will see if it's PAT or API token.

In my current config sample, employer Jira is API and customer PAT type. If necessary, in main.py you can change if APIJiraClient or PatJiraClient is initialized for customer and employer, and provide the necessary values in config.py as well.
