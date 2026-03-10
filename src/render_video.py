import json
import subprocess
from pathlib import Path
from textwrap import wrap

# ----------------------------
# Config
# ----------------------------
SCRIPT_PATH = Path("build/script.json")
AUDIO_DIR = Path("audio")
BUILD_DIR = Path("build")
OUTPUT_DIR = Path("output")
BACKGROUND = Path("assets/background.png")

VIDEO_WIDTH = 1536
VIDEO_HEIGHT = 1024
FPS = 25

# Essaie d'adapter si besoin sur ta machine
FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_FILE_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

TITLE_SIZE = 56
BULLET_SIZE = 34
FOOTER_SIZE = 24

MAX_BULLETS = 4
BULLET_WRAP = 38


# ----------------------------
# Helpers
# ----------------------------
def ensure_dirs() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ffmpeg_escape(text: str) -> str:
    """
    Escape minimal pour drawtext.
    """
    return (
        text.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )


def wrap_bullet(text: str, width: int = BULLET_WRAP) -> str:
    lines = wrap(text, width=width)
    return "\n".join(lines)


def build_drawtext_filters(
    title: str, bullets: list[str], segment_idx: int, total_segments: int
) -> str:
    """
    Construit les filtres drawtext.
    """
    filters = []

    # 1) léger crop/scale pour standardiser le fond
    filters.append(
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}"
    )

    # 2) voile sombre global
    filters.append("drawbox=x=0:y=0:w=iw:h=ih:color=black@0.28:t=fill")

    # 3) panneau sombre principal pour le texte
    panel_x = 90
    panel_y = 120
    panel_w = VIDEO_WIDTH - 180
    panel_h = VIDEO_HEIGHT - 250
    filters.append(
        f"drawbox=x={panel_x}:y={panel_y}:w={panel_w}:h={panel_h}:color=black@0.45:t=fill"
    )

    # 4) bandeau titre
    filters.append(
        f"drawbox=x={panel_x}:y={panel_y}:w={panel_w}:h=110:color=black@0.58:t=fill"
    )

    safe_title = ffmpeg_escape(title)
    filters.append(
        "drawtext="
        f"fontfile='{FONT_FILE}':"
        f"text='{safe_title}':"
        "x=130:"
        "y=150:"
        f"fontsize={TITLE_SIZE}:"
        "fontcolor=white:"
        "shadowcolor=black@0.9:"
        "shadowx=2:"
        "shadowy=2"
    )

    # 5) bullets
    start_y = 290
    line_gap = 145

    for idx, bullet in enumerate(bullets[:MAX_BULLETS]):
        wrapped = wrap_bullet(bullet)
        safe_bullet = ffmpeg_escape(f"• {wrapped}")
        y = start_y + idx * line_gap

        filters.append(
            "drawtext="
            f"fontfile='{FONT_FILE_REGULAR}':"
            f"text='{safe_bullet}':"
            "x=140:"
            f"y={y}:"
            f"fontsize={BULLET_SIZE}:"
            "fontcolor=white:"
            "line_spacing=10:"
            "shadowcolor=black@0.9:"
            "shadowx=2:"
            "shadowy=2"
        )

    # 6) footer discret
    footer = ffmpeg_escape(f"Segment {segment_idx + 1}/{total_segments}")
    filters.append(
        "drawtext="
        f"fontfile='{FONT_FILE_REGULAR}':"
        f"text='{footer}':"
        "x=w-tw-110:"
        "y=h-70:"
        f"fontsize={FOOTER_SIZE}:"
        "fontcolor=white@0.85:"
        "shadowcolor=black@0.9:"
        "shadowx=1:"
        "shadowy=1"
    )

    return ",".join(filters)


def render_segment(
    audio_file: Path, title: str, bullets: list[str], idx: int, total: int
) -> Path:
    out_file = BUILD_DIR / f"seg_{idx}.mp4"
    vf = build_drawtext_filters(title, bullets, idx, total)

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(BACKGROUND),
        "-i",
        str(audio_file),
        "-shortest",
        "-r",
        str(FPS),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(out_file),
    ]

    subprocess.run(cmd, check=True)
    return out_file


def concat_segments(segment_files: list[Path]) -> None:
    list_file = BUILD_DIR / "list.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{seg.name}'\n")

    out_file = OUTPUT_DIR / "release.mp4"

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(out_file),
        ],
        check=True,
    )


def main() -> None:
    ensure_dirs()

    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))

    segment_files: list[Path] = []

    for idx, seg in enumerate(script):
        audio_file = AUDIO_DIR / f"{idx:02d}_{seg['id']}.mp3"

        if not audio_file.exists():
            raise FileNotFoundError(f"Missing audio file: {audio_file}")

        title = seg.get("title", f"Segment {idx + 1}")
        bullets = seg.get("on_screen_text", [])

        if not bullets:
            bullets = ["No on-screen bullets provided for this segment."]

        out = render_segment(
            audio_file=audio_file,
            title=title,
            bullets=bullets,
            idx=idx,
            total=len(script),
        )
        segment_files.append(out)

    concat_segments(segment_files)
    print(f"Video generated: {OUTPUT_DIR / 'release.mp4'}")


if __name__ == "__main__":
    main()
