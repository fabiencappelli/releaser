import json
from dotenv import load_dotenv

load_dotenv()
from openai import OpenAI

client = OpenAI()

data = json.load(open("build/release_structured.json"))

tickets = data["tickets"]

ticket_text = "\n".join(f"{t['key']}: {t['summary']}" for t in tickets)

prompt = f"""
You are preparing a narrated release video.

Create a clean JSON array.
Each element must contain:
- id: short snake_case identifier
- title: short slide title
- on_screen_text: list of 2 to 4 concise bullet points for the slide
- voiceover: spoken narration paragraph for that segment

Rules:
- Keep on_screen_text short and readable.
- voiceover can be more detailed than the slide.
- Create 6 to 9 segments total.
- Output valid JSON only.
- No markdown fences.

Tickets:
{ticket_text}
"""
response = client.responses.create(model="gpt-4.1-mini", input=prompt)

script = response.output_text

with open("build/script.json", "w") as f:
    f.write(script)

print("Script generated")
