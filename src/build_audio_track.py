import json
import subprocess
from pathlib import Path

SCRIPT_PATH = Path("build/script.json")
AUDIO_DIR = Path("audio")
BUILD_DIR = Path("build")

PAUSE_SECONDS = 1.0
FINAL_AUDIO = BUILD_DIR / "final_audio.wav"
NORMALIZED_DIR = BUILD_DIR / "normalized_audio"


def ensure_dirs() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)


def clean_audio_build_files() -> None:
    for pattern in ("audio_concat_list.txt", "pause_*.wav", "final_audio.wav"):
        for path in BUILD_DIR.glob(pattern):
            path.unlink()

    for path in NORMALIZED_DIR.glob("*.wav"):
        path.unlink()


def normalize_audio_to_wav(src: Path, index: int, seg_id: str) -> Path:
    out_file = NORMALIZED_DIR / f"{index:03d}_{seg_id}.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ar",
        "48000",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)
    return out_file


def create_pause_wav(index: int) -> Path:
    out_file = BUILD_DIR / f"pause_{index:03d}.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=48000:cl=stereo",
        "-t",
        str(PAUSE_SECONDS),
        "-c:a",
        "pcm_s16le",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)
    return out_file


def main() -> None:
    ensure_dirs()
    clean_audio_build_files()

    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    if not script:
        raise ValueError("No slides found in build/script.json")

    concat_items: list[Path] = []

    for idx, seg in enumerate(script):
        audio_file = AUDIO_DIR / f"{idx:02d}_{seg['id']}.mp3"
        if not audio_file.exists():
            raise FileNotFoundError(f"Missing audio file: {audio_file}")

        normalized = normalize_audio_to_wav(audio_file, idx, seg["id"])
        concat_items.append(normalized)

        if idx < len(script) - 1:
            pause_file = create_pause_wav(idx)
            concat_items.append(pause_file)

    list_file = BUILD_DIR / "audio_concat_list.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for item in concat_items:
            f.write(f"file '{item.resolve()}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c:a",
        "pcm_s16le",
        str(FINAL_AUDIO),
    ]
    subprocess.run(cmd, check=True)

    print(f"Final audio track generated: {FINAL_AUDIO}")


if __name__ == "__main__":
    main()
