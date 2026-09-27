# Jackrabbit class monitor

A GitHub Actions workflow checks the
[class listing](https://app.jackrabbitclass.com/jr4.0/ParentPortal/Classes?OrgID=531495#classes)
every hour. It looks for a class that mentions all of: Level 1, Friday, 6:45 (not AM), and San Francisco.

When it finds one, it:

1. Sends an email, if the SMTP secrets below are set.
2. Opens a GitHub issue labelled `class-found` and assigns it to the repo owner. GitHub emails you about it.

It reports once. Close the issue to get alerted again.

## Setup

Add these repository secrets (Settings > Secrets and variables > Actions):

| Secret | Example |
| --- | --- |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | your Gmail address |
| `SMTP_PASSWORD` | a Gmail app password |
| `MAIL_TO` | where the alert goes |

The workflow must be on the default branch for the hourly schedule to run.

## Debugging

Each run uploads `page_text.txt` (what the page showed) and `matches.json` as the `page-text` artifact.
