from bs4 import BeautifulSoup
import json
from pathlib import Path

INPUT = Path("data/jira_export.html")
OUTPUT = Path("build/release_structured.json")

with INPUT.open(encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

tickets = []

# On cible directement les vraies lignes de tickets
for row in soup.select("tr.issuerow"):
    cols = row.find_all("td")
    if len(cols) < 7:
        continue

    issue_type = cols[0].get_text(" ", strip=True)
    key = cols[1].get_text(" ", strip=True)
    summary = cols[2].get_text(" ", strip=True)
    created = cols[3].get_text(" ", strip=True)
    assignee = cols[4].get_text(" ", strip=True)
    reporter = cols[5].get_text(" ", strip=True)
    description = cols[6].get_text("\n", strip=True)

    if key.startswith("OPD-"):
        tickets.append(
            {
                "key": key,
                "issue_type": issue_type,
                "summary": summary,
                "created": created,
                "assignee": assignee,
                "reporter": reporter,
                "description": description,
            }
        )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump({"tickets": tickets}, f, indent=2, ensure_ascii=False)

print(f"Parsed {len(tickets)} tickets")
