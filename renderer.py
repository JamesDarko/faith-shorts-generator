
import json
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# =====================================
# CONFIGURATION
# =====================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30

OUTPUT = Path("output")
TEMP = Path("temp")
VOICES = Path("voices")

OUTPUT.mkdir(exist_ok=True)
TEMP.mkdir(exist_ok=True)

FINAL_VIDEO = OUTPUT / "faith_short.mp4"
VOICE_MODEL = "en_US-joe-medium"

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PAUSE_AFTER_SCENE = 0.5


# =====================================
# READ INPUT
# =====================================

event_path = os.environ.get("GITHUB_EVENT_PATH")
payload = {}

if event_path and Path(event_path).exists():
    with open(event_path, encoding="utf-8") as f:
        event = json.load(f)
        payload = event.get("client_payload", {})

# Sample content for testing
if not payload:
    payload = {
        "video_title": "I AM A NEW CREATION IN CHRIST",
        "scenes": [
            {
                "scene_type": "Opening Declaration",
                "display_text": "My past does not define me. I am a new creation in Christ."
            },
            {
                "scene_type": "Scripture",
                "display_text": "2 Corinthians 5:17. If anyone is in Christ, he is a new creation."
            },
            {
                "scene_type": "New Identity",
                "display_text": "The old has passed away. My life has a new foundation in Jesus Christ."
            },
            {
                "scene_type": "My Position in Christ",
                "display_text": "I am accepted, loved and reconciled to God through Jesus."
            },
            {
                "scene_type": "My Confession",
                "display_text": "I refuse to define myself by my past. I choose to see myself through God's Word."
            },
            {
                "scene_type": "Faith Declaration",
                "display_text": "I am a new creation in Christ Jesus. My identity is established in Him."
            }
        ]
    }

scenes = payload.get("scenes", [])

if not scenes:
    raise ValueError("No scenes received.")

if len(scenes) > 10:
    raise ValueError("Maximum of 10 scenes allowed.")

title = payload.get("video_title", "New Creation Realities")


# =====================================
# FONT AND TEXT FUNCTIONS
# =====================================

def get_font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def wrap_text(text, font, draw, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()

        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


# =====================================
# CREATE VISUAL SCENE
# =====================================

def create_scene(scene, index):

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (12, 19, 43)
    )

    draw = ImageDraw.Draw(image)

    # Elegant gold branding
    brand_font = get_font(34, True)

    draw.text(
        (WIDTH // 2, 170),
        "NEW CREATION REALITIES",
        font=brand_font,
        fill=(226, 188, 112),
        anchor="mm"
    )

    # Scene heading
    heading = scene.get("scene_type", "DECLARATION")

    draw.text(
        (WIDTH // 2, 340),
        heading.upper(),
        font=get_font(29),
        fill=(210, 210, 225),
        anchor="mm"
    )

    # Main declaration
    text = str(scene.get("display_text", ""))

    font_size = 62

    while font_size >= 34:
        font = get_font(font_size, True)
        lines = wrap_text(text, font, draw, 850)

        if len(lines) <= 10:
            break

        font_size -= 4

    line_height = font_size + 38
    total_height = len(lines) * line_height

    y = (HEIGHT - total_height) // 2

    for line in lines:

        draw.text(
            (WIDTH // 2, y),
            line,
            font=font,
            fill=(255, 255, 255),
            anchor="mm"
        )

        y += line_height

    # Scene number
    draw.text(
        (WIDTH // 2, 1740),
        f"SCENE {index + 1:02d}",
        font=get_font(28),
        fill=(226, 188, 112),
        anchor="mm"
    )

    path = TEMP / f"scene_{index + 1}.png"
    image.save(path)

    return path


# =====================================
# GENERATE NARRATION FOR EACH SCENE
# =====================================

segments = []

for index, scene in enumerate(scenes):

    narration = str(scene.get("display_text", "")).strip()

    if not narration:
        raise ValueError(f"Scene {index + 1} has no text.")

    print(f"Generating narration for scene {index + 1}")

    audio_path = TEMP / f"voice_{index + 1}.wav"

    command = [
        "python",
        "-m",
        "piper",
        "-m",
        VOICE_MODEL,
        "--data-dir",
        str(VOICES),
        "-f",
        str(audio_path),
        "--",
        narration
    ]

    subprocess.run(command, check=True)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Narration missing for scene {index + 1}"
        )

    image_path = create_scene(scene, index)

    # Determine actual spoken duration
    probe = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    audio_duration = float(probe.stdout.strip())

    # Give the listener a short pause after speaking
    segment_duration = audio_duration + PAUSE_AFTER_SCENE

    segment_path = TEMP / f"segment_{index + 1}.mp4"

    # Keep the image on screen while the narration plays
    render_command = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(image_path),
        "-i", str(audio_path),
        "-t", str(segment_duration),
        "-vf", "format=yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        str(segment_path)
    ]

    subprocess.run(render_command, check=True)

    segments.append(segment_path)


# =====================================
# JOIN ALL VIDEO SEGMENTS
# =====================================

concat_file = TEMP / "segments.txt"

with open(concat_file, "w", encoding="utf-8") as f:

    for segment in segments:
        f.write(f"file '{segment.resolve()}'\n")

concat_command = [
    "ffmpeg",
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", str(concat_file),
    "-c", "copy",
    "-movflags", "+faststart",
    str(FINAL_VIDEO)
]

subprocess.run(concat_command, check=True)


# =====================================
# FINAL REPORT
# =====================================

probe = subprocess.run(
    [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(FINAL_VIDEO)
    ],
    capture_output=True,
    text=True,
    check=True
)

duration = float(probe.stdout.strip())

print("--------------------------------")
print("FAITH SHORT GENERATED SUCCESSFULLY")
print(f"Title: {title}")
print(f"Scenes: {len(scenes)}")
print(f"Duration: {duration:.1f} seconds")
print(f"Output: {FINAL_VIDEO}")
print("--------------------------------")
