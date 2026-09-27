"""Check the Jackrabbit parent portal for a Friday 6:45 PM Level 1 class in San Francisco.

Writes matches to matches.json and page text to page_text.txt.
Exit code 0 always, unless both data sources fail to load.
"""
import json
import re
import sys
import urllib.request

from playwright.sync_api import sync_playwright

ORG_ID = "531495"
PORTAL_URL = f"https://app.jackrabbitclass.com/jr4.0/ParentPortal/Classes?OrgID={ORG_ID}#classes"
OPENINGS_URL = f"https://app.jackrabbitclass.com/jr3.0/Openings/OpeningsJS?OrgID={ORG_ID}"

LEVEL = re.compile(r"level\s*(1(?!\d)|one\b|I\b)", re.I)
DAY = re.compile(r"\bfri(day)?\b", re.I)
TIME = re.compile(r"\b0?6:45(?!\s*a\.?m)", re.I)
LOCATION = re.compile(r"san\s*francisco|\bSF\b", re.I)


def is_match(text: str) -> bool:
    return all(p.search(text) for p in (LEVEL, DAY, TIME, LOCATION))


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# Runs in the browser. For every element that mentions "Level 1", climb to the
# smallest ancestor that also mentions a day and a time. That ancestor is the
# class card or table row.
CARDS_JS = r"""
() => {
  const level = /level\s*(1(?!\d)|one\b|I\b)/i;
  const day = /\b(mon|tue|wed|thu|fri|sat|sun)/i;
  const time = /\d{1,2}:\d{2}/;
  const out = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    if (!level.test(walker.currentNode.textContent)) continue;
    let node = walker.currentNode.parentElement;
    for (let i = 0; i < 12 && node; i++) {
      const t = node.innerText || '';
      if (t.length > 3000) break;
      if (day.test(t) && time.test(t)) { out.add(t); break; }
      node = node.parentElement;
    }
  }
  return Array.from(out);
}
"""


def from_portal():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(PORTAL_URL, wait_until="networkidle", timeout=90_000)
        # Scroll until the page stops growing, in case classes load lazily.
        last = -1
        for _ in range(20):
            height = page.evaluate("document.body.scrollHeight")
            if height == last:
                break
            last = height
            page.mouse.wheel(0, 20_000)
            page.wait_for_timeout(1500)
        text = page.inner_text("body")
        cards = [clean(c) for c in page.evaluate(CARDS_JS)]
        browser.close()
    return text, cards


def from_openings():
    req = urllib.request.Request(OPENINGS_URL, headers={"User-Agent": "Mozilla/5.0"})
    body = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    body = body.replace("\\'", "'").replace('\\"', '"').replace("\\/", "/")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.I | re.S)
    cells = [clean(re.sub(r"<[^>]+>", " ", r)) for r in rows]
    return body, cells


def main():
    candidates, texts, errors = [], [], []
    for name, fn in (("portal", from_portal), ("openings", from_openings)):
        try:
            text, items = fn()
            texts.append(f"===== {name} =====\n{text}")
            candidates += [(name, i) for i in items]
            print(f"{name}: {len(text)} chars of page text, {len(items)} candidate rows")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e!r}")
            print(f"WARN {name} failed: {e!r}", file=sys.stderr)

    with open("page_text.txt", "w") as f:
        f.write("\n\n".join(texts))

    if len(errors) == 2:
        print("Both sources failed:\n" + "\n".join(errors), file=sys.stderr)
        sys.exit(1)

    matches = sorted({i for _, i in candidates if is_match(i)})
    with open("matches.json", "w") as f:
        json.dump(matches, f, indent=2)
    # Rows that match some but not all rules. Shows what the page calls things.
    near = [(n, i) for n, i in candidates
            if sum(bool(p.search(i)) for p in (LEVEL, DAY, TIME, LOCATION)) >= 2]
    print(f"Near matches (2+ of 4 rules): {len(near)}")
    for n, i in near[:40]:
        print(f"  [{n}] {i[:300]}")
    print(f"Checked {len(candidates)} candidate rows. Matches: {len(matches)}")
    for m in matches:
        print(" -", m)


if __name__ == "__main__":
    main()
