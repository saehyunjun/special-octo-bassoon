# Jackrabbit class monitor

A GitHub Actions workflow checks Jackrabbit org 531495 every 15 minutes, at 2, 17, 32 and 47 minutes past the hour.
It alerts when a class matching all of these has at least one open spot:

- Location code `SF` (San Francisco)
- Meets on Friday
- Starts at 18:45 (6:45 PM)
- Class level or name contains `Level 1`. This also matches the combined `Level 1/Level 2 (ages 6-10)` classes.

## Where the data comes from

The [parent portal class page](https://app.jackrabbitclass.com/jr4.0/ParentPortal/Classes?OrgID=531495#classes)
needs a login. The workflow reads Jackrabbit's public JSON class feed instead:
`https://app.jackrabbitclass.com/jr3.0/Openings/OpeningsJson?OrgID=531495&Loc=SF&showClosed=1`.

- `Loc=SF` limits the feed to San Francisco.
- `showClosed=1` includes full classes. Without it the feed lists only classes with open spots.
- Each class has an `openings.calculated_openings` count and a direct registration link.

Each run logs every Friday 6:45 PM Level 1 class at SF, with its opening count, so you can see whether the class exists and is full.

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
