from dotenv import load_dotenv

load_dotenv()
from openai import OpenAI
import json
import os

client = OpenAI()

script = json.load(open("build/script.json"))

os.makedirs("audio", exist_ok=True)

for i, seg in enumerate(script):

    audio = client.audio.speech.create(
        model="gpt-4o-mini-tts", voice="alloy", input=seg["voiceover"]
    )

    path = f"audio/{i:02d}_{seg['id']}.mp3"

    with open(path, "wb") as f:
        f.write(audio.read())

    print("generated", path)
