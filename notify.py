"""Send one notification per new match.

An open GitHub issue labelled "class-found" marks that the match was already
reported. Close the issue to get notified again.
"""
import json
import os
import smtplib
import subprocess
import sys
from email.message import EmailMessage

LABEL = "class-found"
TITLE = "Friday 6:45 PM Level 1 class in San Francisco is listed"
URL = "https://app.jackrabbitclass.com/jr4.0/ParentPortal/Classes?OrgID=531495#classes"


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def send_email(body, test=False):
    """Send the alert email. Returns False if sending failed."""
    host = os.environ.get("SMTP_HOST")
    if not host:
        print("SMTP_HOST not set. Skipping email.")
        return True
    try:
        _send(host, body, test)
    except Exception as e:  # noqa: BLE001
        print(f"::error::Email failed: {e!r}")
        return False
    return True


def _send(host, body, test):
    msg = EmailMessage()
    msg["Subject"] = ("[TEST] " if test else "") + TITLE
    msg["From"] = os.environ["SMTP_USERNAME"]
    msg["To"] = os.environ["MAIL_TO"]
    msg.set_content(body)
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT") or 587)) as s:
        s.starttls()
        s.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        s.send_message(msg)
    print(f"Email sent to {msg['To']}.")


def main():
    matches = json.load(open("matches.json"))
    repo = os.environ["GITHUB_REPOSITORY"]
    owner = repo.split("/")[0]

    if os.environ.get("TEST_ALERT") == "true":
        body = "TEST alert from the Jackrabbit class monitor. No action needed.\n\n" + \
               "Current matches:\n" + ("\n".join(f"- {m}" for m in matches) or "(none)") + f"\n\n{URL}\n"
        if os.environ.get("SMTP_HOST"):
            return 0 if send_email(body, test=True) else 1
        else:
            out = gh("issue", "create", "-R", repo, "--title", "[TEST] " + TITLE,
                     "--assignee", owner, "--body", body)
            gh("issue", "close", out.strip(), "-R", repo)
            print(f"SMTP not set. Created and closed test issue {out.strip()}.")
        return

    if not matches:
        print("No match.")
        return

    open_issues = json.loads(gh("issue", "list", "-R", repo, "--label", LABEL,
                                "--state", "open", "--json", "number"))
    if open_issues:
        print(f"Already reported in issue #{open_issues[0]['number']}. Not notifying again.")
        return

    body = "Matching class listing:\n\n" + "\n".join(f"- {m}" for m in matches) + f"\n\nSign up: {URL}\n"
    # Open the issue even if email fails, so the alert is not lost.
    email_ok = send_email(body)

    gh("label", "create", LABEL, "-R", repo, "--force", "--color", "2ea44f")
    gh("issue", "create", "-R", repo, "--title", TITLE, "--label", LABEL,
       "--assignee", owner, "--body", body + f"\n@{owner} close this issue to re-arm the alert.")
    print("Issue created.")
    return 0 if email_ok else 1


if __name__ == "__main__":
    sys.exit(main())
