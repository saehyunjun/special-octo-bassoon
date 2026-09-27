# Jackrabbit class monitor

A GitHub Actions workflow checks Jackrabbit org 531495 every hour, at 17 minutes past.
It alerts when a class matches all of these:

- Location `SF` (San Francisco)
- Days includes `Fri`
- Start time `6:45pm`
- Class name contains `Level 1`. This also matches the combined `Level 1/Level 2 (ages 6-10)` classes.

## Where the data comes from

The [parent portal class page](https://app.jackrabbitclass.com/jr4.0/ParentPortal/Classes?OrgID=531495#classes)
shows only a sign-in form to logged-out visitors. The workflow reads Jackrabbit's public openings feed instead:
`https://app.jackrabbitclass.com/jr3.0/Openings/OpeningsJS?OrgID=531495&showcols=Location`.
This feed lists the org's classes with their location code.

## Alerts

On a match the workflow:

1. Sends an email, if the SMTP secrets below are set.
2. Opens a GitHub issue labelled `class-found` and assigns it to the repo owner. GitHub emails the owner about it.

It alerts once. Close the issue to re-arm the alert.

If the feed cannot be read or its format changes, the run fails. GitHub emails the owner about failed scheduled runs.

## Email setup

Add these repository secrets under Settings > Secrets and variables > Actions:

| Secret | Example |
| --- | --- |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | the sending Gmail address |
| `SMTP_PASSWORD` | a Gmail app password |
| `MAIL_TO` | the address that gets the alert |

Test it: Actions > Jackrabbit class monitor > Run workflow, tick "Send a test alert".

## Schedule

GitHub runs scheduled workflows only from the default branch.
GitHub disables the schedule after 60 days with no commits to the repo. Re-enable it from the Actions tab.
