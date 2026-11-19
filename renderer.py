
import json
import os
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ==========================================
# FAITH SHORTS V2 - CONFIGURATION
# ==========================================

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

GOLD = (231, 190, 112)
WHITE = (255, 255, 255)
MUTED = (210, 215, 230)
NAVY = (8, 15, 34)

PAUSE_AFTER_PHRASE = 0.25


# ==========================================
# READ AUTOMATION INPUT
# ==========================================

event_path = os.environ.get("GITHUB_EVENT_PATH")
payload = {}

if event_path and Path(event_path).exists():

    with open(event_path, encoding="utf-8") as f:

        event = json.load(f)
        payload = event.get("client_payload", {})

# Sample content for manual testing

if not payload:

    payload = {

        "video_title": "I AM A NEW CREATION IN CHRIST",

        "scripture_reference": "2 CORINTHIANS 5:17",

        "scenes": [

            {
                "scene_type": "Opening",
                "display_text": (
                    "Listen carefully! Your past does not "
                    "define who you are in Christ. Today, "
                    "I want you to understand something "
                    "powerful about your new identity."
                )
            },

            {
                "scene_type": "Scripture Foundation",
                "display_text": (
                    "Second Corinthians five seventeen "
                    "declares that if anyone is in Christ, "
                    "he is a new creation. The old has passed "
                    "away. Behold, the new has come. "
                    "This is God's Word concerning you."
                )
            },

            {
                "scene_type": "Your New Identity",
                "display_text": (
                    "Now, repeat after me! "
                    "I AM A NEW CREATION IN CHRIST! "
                    "I am not defined by my past. "
                    "I am defined by what Jesus has accomplished. "
                    "Say it again with confidence!"
                )
            },

            {
                "scene_type": "Your Position in Christ",
                "display_text": (
                    "Say this loudly! I AM ACCEPTED! "
                    "I AM LOVED! I AM RECONCILED TO GOD! "
                    "These are not empty words. "
                    "These are realities established through Jesus Christ."
                )
            },

            {
                "scene_type": "Personal Confession",
                "display_text": (
                    "Now, let this truth settle in your heart. "
                    "Stop allowing yesterday's failures to define "
                    "today's identity. Renew your mind with God's Word. "
                    "See yourself through what Christ has accomplished."
                )
            },

            {
                "scene_type": "Final Declaration",
                "display_text": (
                    "One more time! Declare this over your life! "
                    "I AM A NEW CREATION IN CHRIST JESUS! "
                    "I AM ACCEPTED, LOVED AND ESTABLISHED IN HIM! "
                    "I belong to God, and my identity is secure in Christ. "
                    "Walk in this truth today!"
                )
            }

        ]

    }


scenes = payload.get("scenes", [])

title = payload.get(
    "video_title",
    "New Creation Realities"
)

# Fix: make scripture reference available
# throughout the rendering functions.

scripture = payload.get(
    "scripture_reference",
    "NEW CREATION REALITIES"
)

if not scenes:
    raise ValueError("No scenes supplied.")

if len(scenes) > 10:
    raise ValueError("Maximum of 10 scenes allowed.")


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def run(command):

    subprocess.run(
        command,
        check=True
    )


def get_font(size, bold=False):

    font_path = BOLD if bold else FONT

    if not Path(font_path).exists():

        raise FileNotFoundError(
            f"Font file not found: {font_path}"
        )

    return ImageFont.truetype(
        font_path,
        size
    )


def probe_duration(path):

    result = subprocess.run(

        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path)
        ],

        capture_output=True,
        text=True,
        check=True

    )

    return float(result.stdout.strip())


def split_phrases(text, max_words=10):

    sentences = re.split(
        r'(?<=[.!?;:])\s+',
        text.strip()
    )

    phrases = []

    for sentence in sentences:

        words = sentence.split()

        for i in range(0, len(words), max_words):

            phrase = " ".join(
                words[i:i + max_words]
            )

            if phrase:
                phrases.append(phrase)

    return phrases


def wrap_text(text, font, draw, max_width):

    words = text.split()

    lines = []
    current = ""

    for word in words:

        test = f"{current} {word}".strip()

        width = draw.textbbox(
            (0, 0),
            test,
            font=font
        )[2]

        if width <= max_width:

            current = test

        else:

            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


# ==========================================
# CINEMATIC BACKGROUND
# ==========================================

def create_cinematic_background(index):

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        NAVY
    )

    glow = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0)
    )

    glow_draw = ImageDraw.Draw(glow)

    glow_draw.ellipse(
        (180, 150, 1100, 1100),
        fill=(191, 133, 61, 85)
    )

    glow_draw.ellipse(
        (-300, 850, 800, 1800),
        fill=(48, 83, 140, 55)
    )

    glow = glow.filter(
        ImageFilter.GaussianBlur(180)
    )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        glow
    )

    draw = ImageDraw.Draw(image)

    for offset in range(-600, 1400, 180):

        draw.line(
            (WIDTH // 2, 0, offset, HEIGHT),
            fill=(225, 187, 119, 17),
            width=5
        )

    draw.rounded_rectangle(
        (45, 45, WIDTH - 45, HEIGHT - 45),
        radius=35,
        outline=(221, 182, 112, 100),
        width=3
    )

    return image.convert("RGB")


# ==========================================
# CREATE PHRASE FRAME
# ==========================================

def create_phrase_frame(
    phrase,
    scene,
    scene_index,
    phrase_index
):

    image = create_cinematic_background(
        scene_index
    )

    draw = ImageDraw.Draw(image)

    # Channel branding

    draw.text(
        (WIDTH // 2, 170),
        "NEW CREATION REALITIES",
        font=get_font(33, True),
        fill=GOLD,
        anchor="mm"
    )

    # Scene heading

    heading = scene.get(
        "scene_type",
        "DECLARATION"
    ).upper()

    draw.text(
        (WIDTH // 2, 330),
        heading,
        font=get_font(29, True),
        fill=MUTED,
        anchor="mm"
    )

    # Main declaration

    font_size = 76

    while font_size >= 40:

        font = get_font(
            font_size,
            True
        )

        lines = wrap_text(
            phrase,
            font,
            draw,
            850
        )

        if len(lines) <= 5:
            break

        font_size -= 4

    line_height = font_size + 55

    total_height = (
        len(lines) * line_height
    )

    y = (
        HEIGHT - total_height
    ) // 2

    # Emphasise important declarations

    emphasis_words = [
        "CHRIST",
        "ACCEPTED",
        "LOVED",
        "NEW",
        "FORGIVEN",
        "RIGHTEOUS",
        "BLESSED",
        "COMPLETE"
    ]

    phrase_upper = phrase.upper()

    highlighted = any(
        word in phrase_upper
        for word in emphasis_words
    )

    for line_number, line in enumerate(lines):

        if highlighted:
            colour = GOLD
        elif line_number == 0:
            colour = GOLD
        else:
            colour = WHITE

        draw.text(
            (WIDTH // 2, y),
            line,
            font=font,
            fill=colour,
            anchor="mm",
            stroke_width=1,
            stroke_fill=(5, 10, 25)
        )

        y += line_height

    # Scripture reference

    draw.text(
        (WIDTH // 2, 1550),
        scripture,
        font=get_font(30, True),
        fill=GOLD,
        anchor="mm"
    )

    # Footer

    draw.text(
        (WIDTH // 2, 1740),
        "FAITH • IDENTITY • CHRIST",
        font=get_font(25),
        fill=MUTED,
        anchor="mm"
    )

    path = TEMP / (
        f"frame_{scene_index}_{phrase_index}.png"
    )

    image.save(path)

    return path


# ==========================================
# GENERATE VIDEO AND NARRATION
# ==========================================

segments = []

total_words = 0

for scene_index, scene in enumerate(scenes):

    narration = str(
        scene.get("display_text", "")
    ).strip()

    if not narration:

        raise ValueError(
            f"Scene {scene_index + 1} is empty."
        )

    total_words += len(
        narration.split()
    )

    print(
        f"Processing scene {scene_index + 1}: "
        f"{scene.get('scene_type', 'Declaration')}"
    )

    phrases = split_phrases(narration)

    for phrase_index, phrase in enumerate(phrases):

        print(
            f"Generating narration: {phrase}"
        )

        audio_path = TEMP / (
            f"voice_{scene_index}_{phrase_index}.wav"
        )

        # Generate Piper narration

        voice_command = [

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
            phrase

        ]

        run(voice_command)

        if not audio_path.exists():

            raise FileNotFoundError(
                f"Missing narration: {audio_path}"
            )

        audio_duration = probe_duration(
            audio_path
        )

        clip_duration = (
            audio_duration + PAUSE_AFTER_PHRASE
        )

        # Generate matching visual

        image_path = create_phrase_frame(
            phrase,
            scene,
            scene_index,
            phrase_index
        )

        clip_path = TEMP / (
            f"clip_{scene_index}_{phrase_index}.mp4"
        )

        # Subtle cinematic zoom

        video_filter = (

            "zoompan="
            "z='min(zoom+0.00035,1.04)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=1:"
            f"s={WIDTH}x{HEIGHT}:"
            f"fps={FPS},"
            "format=yuv420p"

        )

        render_command = [

            "ffmpeg",
            "-y",

            "-loop", "1",
            "-framerate", str(FPS),
            "-i", str(image_path),

            "-i", str(audio_path),

            "-vf", video_filter,
            "-af", "apad",

            "-t", str(clip_duration),

            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",

            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", "44100",

            "-pix_fmt", "yuv420p",

            "-movflags", "+faststart",
            "-shortest",

            str(clip_path)

        ]

        run(render_command)

        segments.append(clip_path)


# ==========================================
# JOIN VIDEO SEGMENTS
# ==========================================

if not segments:

    raise RuntimeError(
        "No video segments were generated."
    )

concat_file = TEMP / "segments.txt"

with open(
    concat_file,
    "w",
    encoding="utf-8"
) as f:

    for segment in segments:

        f.write(
            f"file '{segment.resolve()}'\n"
        )


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

run(concat_command)


# ==========================================
# FINAL QUALITY REPORT
# ==========================================

duration = probe_duration(
    FINAL_VIDEO
)

print("\n================================")
print("FAITH SHORTS V2 GENERATED")
print("================================")

print(f"Title: {title}")
print(f"Scripture: {scripture}")
print(f"Scenes: {len(scenes)}")
print(f"Words: {total_words}")
print(f"Duration: {duration:.1f} seconds")
print(f"Output: {FINAL_VIDEO}")

if duration < 45:

    print(
        "WARNING: Video is shorter than 45 seconds."
    )

elif duration > 60:

    print(
        "WARNING: Video exceeds 60 seconds."
    )

else:

    print(
        "SUCCESS: Video meets the 45-60 second target."
    )

print("Audio: Embedded male Piper narration")
print("Background music: None")
print("Visuals: Cinematic golden lighting")
print("Engagement: Interactive faith declarations")
print("================================")
