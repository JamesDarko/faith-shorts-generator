"""
Faith Shorts portrait thumbnail generator.

Expected repository structure:
    renderer.py
    thumbnail.py
    assets/
        thumbnail_background.jpg
    output/

The background is a clean 9:16 sunrise image with a glowing cross,
leaves and a worshipper silhouette. This module adds the title,
brush-stroke banners, subtitle and scripture references.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent

THUMB_WIDTH = 1080
THUMB_HEIGHT = 1920

THUMBNAIL_BACKGROUND = BASE_DIR / "assets" / "thumbnail_background.jpg"
THUMBNAIL_OUTPUT = BASE_DIR / "output" / "faith_short_thumbnail.jpg"
FONT_DIR = BASE_DIR / "assets" / "fonts"

FONT_HEADLINE = FONT_DIR / "Anton-Regular.ttf"
FONT_BOLD = FONT_DIR / "Montserrat-ExtraBold.ttf"
FONT_SUBTITLE = FONT_DIR / "Montserrat-Bold.ttf"


def _load_font(font_path, size):
    """Load the preferred font, with Linux font fallbacks."""
    candidates = (
        font_path,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
    )
    for candidate in candidates:
        try:
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_font(draw, text, font_path, max_width, start_size, min_size=30):
    """Reduce font size until a single line fits the available width."""
    size = start_size
    while size >= min_size:
        font = _load_font(font_path, size)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        if box[2] - box[0] <= max_width:
            return font
        size -= 3
    return _load_font(font_path, min_size)


def _center_text(
    draw,
    text,
    y,
    font,
    fill,
    stroke_fill="#111111",
    stroke_width=2,
    x_center=THUMB_WIDTH // 2,
):
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_width = box[2] - box[0]
    x = x_center - text_width // 2
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


def _brush_banner(draw, points, fill, extra_strokes=()):
    """Draw an irregular brush-stroke banner."""
    draw.polygon(points, fill=fill)
    for line_points, line_fill, line_width in extra_strokes:
        draw.line(line_points, fill=line_fill, width=line_width)


def _split_thumbnail_title(video_title):
    """
    Arrange common Faith Shorts titles into the channel's three-line style.
    Accepts either the full video title or the shorter thumbnail_text field.
    """
    title = " ".join((video_title or "").upper().replace("| FAITH SHORTS", "").split())

    known_layouts = {
        "YOU ARE THE RIGHTEOUSNESS OF GOD":
            ("YOU ARE THE", "RIGHTEOUSNESS", "OF GOD"),
        "RIGHTEOUSNESS OF GOD":
            ("YOU ARE THE", "RIGHTEOUSNESS", "OF GOD"),
        "YOU ARE A NEW CREATION IN CHRIST":
            ("YOU ARE A", "NEW CREATION", "IN CHRIST"),
        "NEW CREATION IN CHRIST":
            ("YOU ARE A", "NEW CREATION", "IN CHRIST"),
        "YOU ARE ACCEPTED IN THE BELOVED":
            ("YOU ARE", "ACCEPTED", "IN THE BELOVED"),
        "ACCEPTED IN THE BELOVED":
            ("YOU ARE", "ACCEPTED", "IN THE BELOVED"),
    }
    if title in known_layouts:
        return known_layouts[title]

    words = title.split()
    if len(words) >= 5 and words[:3] == ["YOU", "ARE", "THE"]:
        top, rest = "YOU ARE THE", words[3:]
    elif len(words) >= 5 and words[:3] == ["YOU", "ARE", "A"]:
        top, rest = "YOU ARE A", words[3:]
    elif len(words) >= 4 and words[:2] == ["YOU", "ARE"]:
        top, rest = "YOU ARE", words[2:]
    else:
        top, rest = (" ".join(words[:2]), words[2:]) if len(words) > 2 else (title, [])

    if len(rest) >= 3:
        middle, lower = " ".join(rest[:-2]), " ".join(rest[-2:])
    elif len(rest) == 2:
        middle, lower = rest[0], rest[1]
    elif len(rest) == 1:
        middle, lower = rest[0], ""
    else:
        middle, lower = "", ""

    return top, middle, lower


def _draw_scripture_panel(draw, scripture_reference):
    """Draw one or two scripture references on a yellow panel."""
    refs = [
        part.strip()
        for part in (scripture_reference or "").replace(";", "|").split("|")
        if part.strip()
    ]
    if not refs:
        return

    panel = [
        (555, 1050), (1015, 1035), (1040, 1250),
        (585, 1275), (535, 1195),
    ]
    _brush_banner(draw, panel, "#FFD21C")

    if len(refs) == 1:
        font = _fit_font(draw, refs[0], FONT_BOLD, 420, 58, 30)
        _center_text(
            draw, refs[0], 1120, font, "#101010",
            stroke_fill="#FFD21C", stroke_width=1, x_center=790,
        )
    else:
        font1 = _fit_font(draw, refs[0], FONT_BOLD, 420, 52, 28)
        font2 = _fit_font(draw, refs[1], FONT_BOLD, 420, 52, 28)
        _center_text(
            draw, refs[0], 1080, font1, "#101010",
            stroke_fill="#FFD21C", stroke_width=1, x_center=790,
        )
        draw.line((650, 1160, 930, 1152), fill="#B51E18", width=5)
        _center_text(
            draw, refs[1], 1180, font2, "#101010",
            stroke_fill="#FFD21C", stroke_width=1, x_center=790,
        )


def create_faith_shorts_thumbnail(
    video_title,
    scripture_reference,
    subtitle="Faith Declaration",
    background_path=THUMBNAIL_BACKGROUND,
    output_path=THUMBNAIL_OUTPUT,
):
    """
    Create a 1080 x 1920 Faith Shorts thumbnail.

    video_title may be the full title or the shorter n8n thumbnail_text.
    scripture_reference accepts one reference or two separated by ';'.
    """
    background_path = Path(background_path)
    output_path = Path(output_path)

    if not background_path.exists():
        raise FileNotFoundError(
            f"Thumbnail background not found: {background_path}. "
            "Ensure assets/thumbnail_background.jpg is committed to GitHub."
        )

    image = Image.open(background_path).convert("RGB")
    image = image.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.Resampling.LANCZOS)
    image = image.convert("RGBA")

    draw = ImageDraw.Draw(image)
    top_line, middle_line, lower_line = _split_thumbnail_title(video_title)

    # Top line is shifted left so it does not cover the glowing cross.
    top_font = _fit_font(draw, top_line, FONT_HEADLINE, 690, 112, 40)
    _center_text(
        draw, top_line, 115, top_font, "#FFFFFF",
        stroke_fill="#101010", stroke_width=5, x_center=420,
    )

    # Red brush-stroke banner and highlighted yellow phrase.
    red_banner = [
        (38, 285), (160, 255), (895, 247), (1040, 275),
        (1010, 475), (865, 500), (115, 510), (25, 465),
    ]
    _brush_banner(
        draw, red_banner, "#D71920",
        extra_strokes=[
            ([(55, 300), (1020, 270)], "#F33A32", 8),
            ([(40, 465), (1005, 485)], "#A90E18", 7),
        ],
    )
    if middle_line:
        middle_font = _fit_font(draw, middle_line, FONT_HEADLINE, 900, 170, 46)
        _center_text(
            draw, middle_line, 310, middle_font, "#FFE500",
            stroke_fill="#5B0808", stroke_width=6,
        )

    # Dark brush-stroke banner for the final title line.
    dark_banner = [
        (75, 500), (225, 480), (930, 490), (1010, 520),
        (990, 675), (850, 695), (150, 695), (55, 650),
    ]
    _brush_banner(
        draw, dark_banner, "#171313",
        extra_strokes=[
            ([(95, 525), (990, 515)], "#332323", 7),
            ([(70, 660), (975, 675)], "#090909", 8),
        ],
    )
    if lower_line:
        lower_font = _fit_font(draw, lower_line, FONT_HEADLINE, 900, 160, 44)
        _center_text(
            draw, lower_line, 515, lower_font, "#FFFFFF",
            stroke_fill="#8D1515", stroke_width=7,
        )

    # Gold subtitle brush stroke.
    subtitle_banner = [
        (190, 715), (330, 695), (745, 700), (890, 725),
        (860, 810), (300, 825), (180, 780),
    ]
    _brush_banner(
        draw, subtitle_banner, "#F4C542",
        extra_strokes=[
            ([(215, 725), (865, 740)], "#FFE18A", 5),
            ([(205, 800), (850, 800)], "#C58B20", 5),
        ],
    )
    subtitle_font = _fit_font(draw, subtitle, FONT_SUBTITLE, 650, 72, 32)
    _center_text(
        draw, subtitle, 725, subtitle_font, "#111111",
        stroke_fill="#F4C542", stroke_width=1,
    )

    _draw_scripture_panel(draw, scripture_reference)

    # Thin gold frame, matching the reference design.
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (22, 22, THUMB_WIDTH - 22, THUMB_HEIGHT - 22),
        radius=24,
        outline=(255, 215, 110, 180),
        width=3,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "JPEG", quality=94, optimize=True)
    return str(output_path)
