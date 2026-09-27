"""Check Jackrabbit for an open spot in a Friday 6:45 PM Level 1 class at San Francisco (SF).

Reads Jackrabbit's public JSON class feed for the org. showClosed=1 makes the
feed include full classes too, so the log shows whether the target class
exists and is full, or does not exist at all.

Writes classes with open spots to matches.json. Exits 1 if the feed can't be read.
"""
import html
import json
import re
import sys
import urllib.request

ORG_ID = "531495"
LOCATION = "SF"
FEED_URL = (f"https://app.jackrabbitclass.com/jr3.0/Openings/OpeningsJson"
            f"?OrgID={ORG_ID}&Loc={LOCATION}&showClosed=1")

DAY = "fri"
START = "18:45"
LEVEL = re.compile(r"\bLevel\s*1(?!\d)", re.I)


def fetch_classes():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)["rows"]


def openings(c):
    return int((c.get("openings") or {}).get("calculated_openings") or 0)


def is_target(c):
    return (
        c.get("location_code") == LOCATION
        and (c.get("meeting_days") or {}).get(DAY)
        and c.get("start_time") == START
        and LEVEL.search(f"{c.get('category1', '')} {c.get('name', '')}")
    )


def describe(c):
    # Full classes come with an empty link, so build one from the class ID.
    link = html.unescape(c.get("online_reg_link") or "") or (
        f"https://app.jackrabbitclass.com/reg.asp?id={ORG_ID}&preLoadClassID={c.get('id')}&loc={LOCATION}")
    return (f"{c.get('name')} | {c.get('start_time')}-{c.get('end_time')} | "
            f"{c.get('location_name')} | openings {openings(c)} | "
            f"instructor {', '.join(c.get('instructors') or [])} | class ID {c.get('id')} | register: {link}")


def main():
    classes = fetch_classes()
    if not classes:
        print("Feed returned no classes. The feed may have changed.")
        return 1

    full = sum(1 for c in classes if openings(c) <= 0)
    print(f"{len(classes)} classes at {LOCATION} ({full} full).")

    targets = [c for c in classes if is_target(c)]
    print(f"Friday {START} Level 1 classes at {LOCATION}: {len(targets)}")
    for c in targets:
        print("  ", describe(c))

    matches = [describe(c) for c in targets if openings(c) > 0]
    with open("matches.json", "w") as f:
        json.dump(matches, f, indent=2)
    print(f"With open spots: {len(matches)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
