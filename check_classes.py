"""Check Jackrabbit for a Friday 6:45 PM Level 1 class at the San Francisco (SF) location.

The parent portal class page needs a login, so this reads Jackrabbit's public
openings feed for the same org. That feed lists the same classes as a table.

Writes matches to matches.json. Exits 1 if the feed can't be read or parsed.
"""
import html
import json
import re
import sys
import urllib.request

ORG_ID = "531495"
FEED_URL = f"https://app.jackrabbitclass.com/jr3.0/Openings/OpeningsJS?OrgID={ORG_ID}&showcols=Location"

LOCATION = "SF"
DAY = re.compile(r"\bFri", re.I)
TIME = re.compile(r"^0?6:45\s*pm", re.I)
LEVEL = re.compile(r"\bLevel\s*1(?!\d)", re.I)

CELL = re.compile(r'<t[hd][^>]*data-title="([^"]+)"[^>]*>(.*?)</t[hd]>', re.S)


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


def fetch_rows():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    body = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    # The feed is JavaScript that writes HTML, so quotes arrive escaped.
    body = body.replace('\\"', '"').replace("\\'", "'").replace("\\/", "/")
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
        cells = {k: clean(v) for k, v in CELL.findall(tr)}
        if "Class" in cells and "Days" in cells:
            rows.append(cells)
    return rows


def is_match(row):
    return (
        row.get("Location", "").upper() == LOCATION
        and DAY.search(row.get("Days", ""))
        and TIME.search(row.get("Times", ""))
        and LEVEL.search(row.get("Class", ""))
    )


def describe(row):
    return (f"{row.get('Class')} | {row.get('Days')} {row.get('Times')} | "
            f"Location {row.get('Location')} | Openings {row.get('Openings')} | "
            f"Starts {row.get('Class Starts')} | Tuition {row.get('Tuition')}")


def main():
    rows = fetch_rows()
    if not rows or not any("Location" in r for r in rows):
        print(f"Feed parse failed: {len(rows)} rows, location column missing. The feed format may have changed.")
        return 1

    sf_friday = [r for r in rows if r.get("Location", "").upper() == LOCATION and DAY.search(r.get("Days", ""))]
    print(f"{len(rows)} classes in feed. {len(sf_friday)} are Friday classes at {LOCATION}.")
    for r in sf_friday:
        if re.match(r"0?[5-7]:\d\d\s*pm", r.get("Times", ""), re.I):
            print("  evening:", describe(r))

    matches = [describe(r) for r in rows if is_match(r)]
    with open("matches.json", "w") as f:
        json.dump(matches, f, indent=2)
    print(f"Matches: {len(matches)}")
    for m in matches:
        print("  MATCH:", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
