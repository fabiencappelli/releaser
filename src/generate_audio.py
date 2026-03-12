import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

SCRIPT_PATH = Path("build/script.json")
AUDIO_DIR = Path("audio")


def clean_audio_outputs() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    for mp3_file in AUDIO_DIR.glob("*.mp3"):
        mp3_file.unlink()


def main() -> None:
    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))

    clean_audio_outputs()

    for i, seg in enumerate(script):
        voiceover = seg.get("voiceover", "").strip()
        if not voiceover:
            raise ValueError(f"Missing voiceover in segment {i}: {seg.get('id')}")

        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=voiceover,
        )

        path = AUDIO_DIR / f"{i:02d}_{seg['id']}.mp3"

        with path.open("wb") as f:
            f.write(audio.read())

        print("generated", path)


if __name__ == "__main__":
    main()
