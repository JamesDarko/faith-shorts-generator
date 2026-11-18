
import json
import os
import math
import wave
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ----------------------------------
# VIDEO CONFIGURATION
# ----------------------------------

WIDTH = 1080
HEIGHT = 1920
FPS = 30
OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp")

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "faith_short.mp4"


# ----------------------------------
# READ DATA FROM GITHUB EVENT
# ----------------------------------

event_path = os.environ.get("GITHUB_EVENT_PATH")

payload = {}

if event_path and Path(event_path).exists():
    with open(event_path, "r", encoding="utf-8") as file:
        event = json.load(file)
        payload = event.get("client_payload", {})

# Sample content for a manual test
# Real n8n content will replace this later.

if not payload:
    payload = {
        "video_title": "YOU ARE A NEW CREATION IN CHRIST",
        "scenes": [
            {
                "scene_number": 1,
                "scene_type": "Opening Hook",
                "display_text": "Your past does not define your identity in Christ.",
                "duration_seconds": 6
            },
            {
                "scene_number": 2,
                "scene_type": "Scripture",
                "display_text": "2 Corinthians 5:17",
                "duration_seconds": 7
            },
            {
                "scene_number": 3,
                "scene_type": "Teaching Part 1",
                "display_text": "If anyone is in Christ, he is a new creation. The old has passed away.",
                "duration_seconds": 14
            },
            {
                "scene_number": 4,
                "scene_type": "Teaching Part 2",
                "display_text": "Your identity is now rooted in what Jesus Christ has accomplished.",
                "duration_seconds": 14
            },
            {
                "scene_number": 5,
                "scene_type": "Practical Application",
                "display_text": "Renew your mind with God's Word. Learn to see yourself through Christ.",
                "duration_seconds": 8
            },
            {
                "scene_number": 6,
                "scene_type": "Faith Declaration",
                "display_text": "I am a new creation in Christ Jesus. My identity is established in Him.",
                "duration_seconds": 8
            }
        ]
    }

scenes = payload.get("scenes", [])

if not scenes:
    raise ValueError("No video scenes were received.")

title = payload.get("video_title", "New Creation Realities")


# ----------------------------------
# FONT CONFIGURATION
# ----------------------------------

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def get_font(size, bold=False):
    path = BOLD_FONT_PATH if bold else FONT_PATH
    return ImageFont.truetype(path, size)


# ----------------------------------
# TEXT WRAPPING
# ----------------------------------

def wrap_text(text, font, max_width, draw):
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


# ----------------------------------
# CREATE BACKGROUND
# ----------------------------------

def create_background():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()

    for y in range(HEIGHT):
        ratio = y / HEIGHT

        red = int(12 + ratio * 15)
        green = int(18 + ratio * 10)
        blue = int(42 + ratio * 28)

        for x in range(WIDTH):
            pixels[x, y] = (red, green, blue)

    return image


# ----------------------------------
# CREATE VIDEO SCENES
# ----------------------------------

scene_files = []
durations = []

for index, scene in enumerate(scenes):

    image = create_background()
    draw = ImageDraw.Draw(image)

    scene_type = scene.get("scene_type", "Teaching")
    text = str(scene.get("display_text", ""))

    # Top branding
    brand_font = get_font(34, bold=True)

    draw.text(
        (WIDTH // 2, 160),
        "NEW CREATION REALITIES",
        font=brand_font,
        fill=(225, 183, 105),
        anchor="mm"
    )

    # Scene label
    label_font = get_font(28)

    draw.text(
        (WIDTH // 2, 330),
        scene_type.upper(),
        font=label_font,
        fill=(205, 205, 220),
        anchor="mm"
    )

    # Main message
    font_size = 58

    while font_size >= 34:
        main_font = get_font(font_size, bold=True)
        lines = wrap_text(text, main_font, 850, draw)

        if len(lines) <= 10:
            break

        font_size -= 4

    line_height = font_size + 35
    total_height = len(lines) * line_height

    y = (HEIGHT - total_height) // 2

    for line in lines:
        draw.text(
            (WIDTH // 2, y),
            line,
            font=main_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        y += line_height

    # Bottom branding
    footer_font = get_font(27)

    draw.text(
        (WIDTH // 2, 1750),
        "GROW IN THE KNOWLEDGE OF CHRIST",
        font=footer_font,
        fill=(225, 183, 105),
        anchor="mm"
    )

    filename = TEMP_DIR / f"scene_{index + 1}.png"
    image.save(filename)

    scene_files.append(filename)
    durations.append(int(scene.get("duration_seconds", 8)))


# ----------------------------------
# CREATE ORIGINAL AMBIENT AUDIO
# ----------------------------------

sample_rate = 22050
total_duration = sum(durations)

audio_file = TEMP_DIR / "background.wav"

# Gentle original synthesised background pad.
# This is not a commercial music recording.

chords = [
    (130.81, 164.81, 196.00),
    (146.83, 174.61, 220.00),
    (110.00, 130.81, 164.81),
    (130.81, 164.81, 196.00)
]

with wave.open(str(audio_file), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(sample_rate)

    for i in range(total_duration * sample_rate):

        t = i / sample_rate
        chord = chords[int(t // 8) % len(chords)]

        signal = sum(
            math.sin(2 * math.pi * frequency * t)
            for frequency in chord
        ) / 3

        envelope = min(1, t / 3, (total_duration - t) / 4)
        value = int(4500 * signal * max(0, envelope))

        wav.writeframesraw(
            value.to_bytes(2, byteorder="little", signed=True)
        )


# ----------------------------------
# CREATE FFMPEG INPUT LIST
# ----------------------------------

concat_file = TEMP_DIR / "scenes.txt"

with open(concat_file, "w", encoding="utf-8") as file:
    for filename, duration in zip(scene_files, durations):
        file.write(f"file '{filename.resolve()}'\n")
        file.write(f"duration {duration}\n")

    file.write(f"file '{scene_files[-1].resolve()}'\n")


# ----------------------------------
# RENDER FINAL VIDEO
# ----------------------------------

command = [
    "ffmpeg",
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", str(concat_file),
    "-i", str(audio_file),
    "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS},format=yuv420p",
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-crf", "23",
    "-c:a", "aac",
    "-b:a", "128k",
    "-shortest",
    "-movflags", "+faststart",
    str(OUTPUT_FILE)
]

subprocess.run(command, check=True)

print("VIDEO RENDERED SUCCESSFULLY")
print(f"Title: {title}")
print(f"Scenes: {len(scenes)}")
print(f"Duration: {total_duration} seconds")
print(f"Output: {OUTPUT_FILE}")

