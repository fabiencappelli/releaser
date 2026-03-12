import subprocess
import sys
from pathlib import Path


STEPS = [
    ("Parse JIRA export", "src/parse_jira.py"),
    ("Generate grouped themes and script", "src/generate_script.py"),
    ("Generate audio", "src/generate_audio.py"),
    ("Build final audio track", "src/build_audio_track.py"),
    ("Render final video", "src/render_video.py"),
]


def run_step(label: str, script_name: str) -> None:
    script_path = Path(script_name)

    if not script_path.exists():
        raise FileNotFoundError(f"Missing script: {script_path}")

    print(f"\n{'=' * 72}")
    print(f"STEP: {label}")
    print(f"SCRIPT: {script_path}")
    print(f"{'=' * 72}\n")

    result = subprocess.run([sys.executable, str(script_path)])

    if result.returncode != 0:
        raise RuntimeError(
            f"Step failed: {label} ({script_name}) with exit code {result.returncode}"
        )

    print(f"\nOK - {label}\n")


def main() -> None:
    try:
        for label, script_name in STEPS:
            run_step(label, script_name)

        print("\n" + "=" * 72)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("Output video: output/release.mp4")
        print("=" * 72 + "\n")

    except Exception as e:
        print("\n" + "=" * 72)
        print("PIPELINE FAILED")
        print(str(e))
        print("=" * 72 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
