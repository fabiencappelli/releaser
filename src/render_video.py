import json
import subprocess
from pathlib import Path
from textwrap import wrap

# ----------------------------
# Config
# ----------------------------
SCRIPT_PATH = Path("build/script.json")
TIMELINE_PATH = Path("build/timeline.json")
FINAL_AUDIO_PATH = Path("build/final_audio.wav")

BUILD_DIR = Path("build")
OUTPUT_DIR = Path("output")
BACKGROUND = Path("assets/background.png")
TEXT_DIR = BUILD_DIR / "drawtext"

VIDEO_WIDTH = 1536
VIDEO_HEIGHT = 1024
FPS = 25

FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_FILE_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

TITLE_SIZE = 56
BULLET_SIZE = 34
FOOTER_SIZE = 24

MAX_BULLETS = 4
BULLET_WRAP = 38
PAUSE_SECONDS = 1.0

TITLE_X = 130
TITLE_Y = 150

BULLET_X = 140
BULLET_START_Y = 290
BULLET_BLOCK_GAP = 145
BULLET_LINE_GAP = 44


# ----------------------------
# Helpers
# ----------------------------
def ensure_dirs() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)


def clean_render_outputs() -> None:
    for pattern in (
        "seg_*.mp4",
        "pause_*.mp4",
        "video_concat_list.txt",
        "release_video_only.mp4",
    ):
        for path in BUILD_DIR.glob(pattern):
            path.unlink()

    for path in TEXT_DIR.glob("*.txt"):
        path.unlink()

    output_file = OUTPUT_DIR / "release.mp4"
    if output_file.exists():
        output_file.unlink()


def ffmpeg_escape_path(path: Path) -> str:
    return (
        str(path.resolve()).replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'")
    )


def wrap_bullet_lines(text: str, width: int = BULLET_WRAP) -> list[str]:
    text = " ".join(text.split())
    return wrap(text, width=width) or [text]


def probe_audio_duration(audio_file: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_file),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def write_text_asset(name: str, text: str) -> Path:
    path = TEXT_DIR / name
    path.write_text(text, encoding="utf-8")
    return path


def add_drawtext_file(
    filters: list[str],
    *,
    text_file: Path,
    fontfile: str,
    x: str,
    y: str,
    fontsize: int,
    fontcolor: str = "white",
    shadowcolor: str = "black@0.9",
    shadowx: int = 2,
    shadowy: int = 2,
) -> None:
    safe_path = ffmpeg_escape_path(text_file)

    filters.append(
        "drawtext="
        f"fontfile='{fontfile}':"
        f"textfile='{safe_path}':"
        f"x={x}:"
        f"y={y}:"
        f"fontsize={fontsize}:"
        f"fontcolor={fontcolor}:"
        f"shadowcolor={shadowcolor}:"
        f"shadowx={shadowx}:"
        f"shadowy={shadowy}"
    )


def build_drawtext_filters(
    title: str, bullets: list[str], segment_idx: int, total_segments: int
) -> str:
    filters: list[str] = []

    filters.append(
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}"
    )
    filters.append("drawbox=x=0:y=0:w=iw:h=ih:color=black@0.28:t=fill")

    panel_x = 90
    panel_y = 120
    panel_w = VIDEO_WIDTH - 180
    panel_h = VIDEO_HEIGHT - 250
    filters.append(
        f"drawbox=x={panel_x}:y={panel_y}:w={panel_w}:h={panel_h}:color=black@0.45:t=fill"
    )
    filters.append(
        f"drawbox=x={panel_x}:y={panel_y}:w={panel_w}:h=110:color=black@0.58:t=fill"
    )

    title_file = write_text_asset(f"seg_{segment_idx:03d}_title.txt", title)
    add_drawtext_file(
        filters,
        text_file=title_file,
        fontfile=FONT_FILE,
        x=str(TITLE_X),
        y=str(TITLE_Y),
        fontsize=TITLE_SIZE,
    )

    for bullet_idx, bullet in enumerate(bullets[:MAX_BULLETS]):
        lines = wrap_bullet_lines(bullet)
        block_y = BULLET_START_Y + bullet_idx * BULLET_BLOCK_GAP

        for line_idx, line in enumerate(lines):
            prefix = "• " if line_idx == 0 else "  "
            y = block_y + line_idx * BULLET_LINE_GAP

            line_file = write_text_asset(
                f"seg_{segment_idx:03d}_bullet_{bullet_idx:02d}_{line_idx:02d}.txt",
                f"{prefix}{line}",
            )
            add_drawtext_file(
                filters,
                text_file=line_file,
                fontfile=FONT_FILE_REGULAR,
                x=str(BULLET_X),
                y=str(y),
                fontsize=BULLET_SIZE,
            )

    footer_file = write_text_asset(
        f"seg_{segment_idx:03d}_footer.txt",
        f"Segment {segment_idx + 1}/{total_segments}",
    )
    add_drawtext_file(
        filters,
        text_file=footer_file,
        fontfile=FONT_FILE_REGULAR,
        x="w-tw-110",
        y="h-70",
        fontsize=FOOTER_SIZE,
        fontcolor="white@0.85",
        shadowx=1,
        shadowy=1,
    )

    return ",".join(filters)


def render_silent_segment(
    duration_seconds: float, title: str, bullets: list[str], idx: int, total: int
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
        "-t",
        f"{duration_seconds:.3f}",
        "-r",
        str(FPS),
        "-vf",
        vf,
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)
    return out_file


def create_silent_pause_segment(index: int) -> Path:
    out_file = BUILD_DIR / f"pause_{index}.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(BACKGROUND),
        "-t",
        str(PAUSE_SECONDS),
        "-r",
        str(FPS),
        "-vf",
        (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
            "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.28:t=fill"
        ),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)
    return out_file


def concat_video_segments(segment_files: list[Path]) -> Path:
    list_file = BUILD_DIR / "video_concat_list.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for seg in segment_files:
            f.write(f"file '{seg.resolve()}'\n")

    out_file = BUILD_DIR / "release_video_only.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)
    return out_file


def mux_final(video_file: Path, audio_file: Path) -> None:
    out_file = OUTPUT_DIR / "release.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_file),
        "-i",
        str(audio_file),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-shortest",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    ensure_dirs()
    clean_render_outputs()

    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    if not script:
        raise ValueError("No slides found in build/script.json")

    if not FINAL_AUDIO_PATH.exists():
        raise FileNotFoundError(
            f"Missing final audio track: {FINAL_AUDIO_PATH}. "
            "Run build_audio_track.py first."
        )

    total = len(script)
    timeline = []
    assembled_files: list[Path] = []

    for idx, seg in enumerate(script):
        audio_file = BUILD_DIR / "normalized_audio" / f"{idx:03d}_{seg['id']}.wav"
        if not audio_file.exists():
            raise FileNotFoundError(f"Missing audio file: {audio_file}")

        duration = probe_audio_duration(audio_file)

        title = seg.get("title", f"Segment {idx + 1}")
        bullets = seg.get("on_screen_text", []) or ["No on-screen bullets provided."]

        out = render_silent_segment(
            duration_seconds=duration,
            title=title,
            bullets=bullets,
            idx=idx,
            total=total,
        )
        assembled_files.append(out)

        timeline.append(
            {
                "type": "segment",
                "index": idx,
                "id": seg["id"],
                "title": title,
                "duration_seconds": duration,
            }
        )

        if idx < total - 1:
            pause_file = create_silent_pause_segment(idx)
            assembled_files.append(pause_file)
            timeline.append(
                {
                    "type": "pause",
                    "after_segment_index": idx,
                    "duration_seconds": PAUSE_SECONDS,
                }
            )

    video_only = concat_video_segments(assembled_files)
    mux_final(video_only, FINAL_AUDIO_PATH)

    TIMELINE_PATH.write_text(
        json.dumps(timeline, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Video generated: {OUTPUT_DIR / 'release.mp4'}")
    print(f"Timeline written: {TIMELINE_PATH}")


if __name__ == "__main__":
    main()
