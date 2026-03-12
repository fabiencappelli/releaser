import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

INPUT_PATH = Path("build/release_structured.json")
THEMES_PATH = Path("build/themes.json")
SCRIPT_PATH = Path("build/script.json")


def extract_json_text(text: str) -> str:
    """
    Nettoie une éventuelle réponse entourée de ```json ... ```
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def load_tickets() -> list[dict]:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    return data["tickets"]


def build_ticket_payload(tickets: list[dict]) -> str:
    """
    On envoie summary + description + metadata utile.
    """
    payload = []
    for t in tickets:
        payload.append(
            {
                "key": t["key"],
                "issue_type": t.get("issue_type", ""),
                "summary": t.get("summary", ""),
                "description": t.get("description", ""),
                "assignee": t.get("assignee", ""),
                "reporter": t.get("reporter", ""),
                "created": t.get("created", ""),
            }
        )
    return json.dumps(payload, indent=2, ensure_ascii=False)


def call_model(prompt: str, model: str = "gpt-4.1-mini") -> str:
    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text.strip()


def group_themes(tickets: list[dict]) -> list[dict]:
    ticket_payload = build_ticket_payload(tickets)

    prompt = f"""
You are preparing a technical software release video.

TASK: PASS 1 — group Jira tickets into coherent themes.

You must analyze the tickets and return a JSON array of THEMES.

STRICT RULES:
- Group tickets only when they clearly belong to the same functional topic.
- Do not merge unrelated tickets just because they sound vaguely similar.
- If a ticket does not clearly belong with others, it may remain alone in its own theme.
- Prefer precision over aggressive grouping.

STRICT UI/API CLASSIFICATION RULES:
- A theme may be labeled "UI" only if the underlying tickets explicitly mention user interface elements or clearly UI-specific concepts such as page, screen, modal, button, table, panel, filter bar, visible behavior, user-facing workflow, layout, click behavior, display, etc.
- A theme may be labeled "API" only if the underlying tickets explicitly mention API-specific concepts such as API, endpoint, request, response, payload, header, idempotency, webhook, schema, serialization, validation at API boundary, etc.
- If this is not explicit, use "unspecified".
- Never infer UI or API from plausibility alone.
- If tickets inside a candidate theme mix UI and API without a clearly shared explicit label, either split them or label the theme "unspecified".

OUTPUT FORMAT:
Return valid JSON only.
No markdown.
No commentary.

Each theme object must have:
- id: short snake_case identifier
- theme_title: concise technical theme title
- classification: one of "UI", "API", "unspecified"
- rationale: one short sentence explaining why these tickets belong together
- ticket_keys: list of Jira keys in that theme

TICKETS:
{ticket_payload}
"""
    raw = call_model(prompt)
    cleaned = extract_json_text(raw)
    themes = json.loads(cleaned)

    THEMES_PATH.write_text(
        json.dumps(themes, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return themes


def generate_video_script(tickets: list[dict], themes: list[dict]) -> list[dict]:
    ticket_map = {t["key"]: t for t in tickets}

    enriched_themes = []
    for theme in themes:
        enriched_tickets = []
        for key in theme["ticket_keys"]:
            if key in ticket_map:
                enriched_tickets.append(ticket_map[key])

        enriched_themes.append(
            {
                "id": theme["id"],
                "theme_title": theme["theme_title"],
                "classification": theme["classification"],
                "rationale": theme["rationale"],
                "tickets": enriched_tickets,
            }
        )

    enriched_payload = json.dumps(enriched_themes, indent=2, ensure_ascii=False)

    prompt = f"""
You are preparing the script for a technical software release update video.

TASK: PASS 2 — generate the final video script from already-grouped themes.

You must return a JSON array of slide objects.

GOAL:
Create a release video that is technical, clear, and pleasant to listen to.
The tone must not be promotional, but it must also avoid sounding cold, funerary, or like an obituary.

TONE RULES:
- technical and factual
- natural spoken rhythm
- clear and pleasant to listen to
- not salesy
- not stiff
- not overly cheerful
- no hype or exaggerated claims
- no marketing language
- no "exciting", "amazing", "powerful", "game-changing", etc.

STRUCTURE RULES:
- Start with a short introduction slide that says hello and introduces the release update.
- Then create the thematic content slides.
- End with a short conclusion slide that thanks the audience and says goodbye.

IMPORTANT CONTENT RULES:
- Use the provided themes as the organizing structure.
- Stay faithful to the tickets.
- Do not invent implementation details.
- If a theme classification is "UI", you may explicitly mention that it is a UI change.
- If a theme classification is "API", you may explicitly mention that it is an API change.
- If a theme classification is "unspecified", do not call it UI or API.
- Never invent UI/API labels beyond the provided classification.

SLIDE FORMAT:
Each slide object must contain:
- id: short snake_case identifier
- title: short technical slide title
- on_screen_text: list of 3 to 5 concise bullet points
- voiceover: spoken narration in 3 to 5 sentences

GUIDELINES FOR ON-SCREEN TEXT:
- concise
- concrete
- technical
- no vague filler
- 3 to 5 bullets max

GUIDELINES FOR VOICEOVER:
- slightly more detailed than the bullets
- spoken and natural, but still technical
- do not repeat the bullets word for word
- explain what changed and why it matters in practical terms
- no invented details

INTRO SLIDE REQUIREMENTS:
- friendly but professional hello
- mention that this is a release update
- mention that UI/API labels are only stated when explicit

OUTRO SLIDE REQUIREMENTS:
- brief thank you
- brief goodbye
- no fluff

OUTPUT:
- valid JSON only
- no markdown
- no comments
- no explanations outside the JSON

THEMES AND TICKETS:
{enriched_payload}
"""
    raw = call_model(prompt)
    cleaned = extract_json_text(raw)
    script = json.loads(cleaned)

    SCRIPT_PATH.write_text(
        json.dumps(script, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return script


def main() -> None:
    tickets = load_tickets()
    if not tickets:
        raise ValueError("No tickets found in build/release_structured.json")

    themes = group_themes(tickets)
    script = generate_video_script(tickets, themes)

    print(f"Grouped {len(tickets)} tickets into {len(themes)} themes")
    print(f"Generated {len(script)} slides")
    print(f"Wrote {THEMES_PATH}")
    print(f"Wrote {SCRIPT_PATH}")


if __name__ == "__main__":
    main()
