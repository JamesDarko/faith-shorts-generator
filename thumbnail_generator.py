# ============================================================
# FAITH SHORTS — PORTRAIT THUMBNAIL GENERATOR
# Design: vivid sunrise, glowing cross, raised-hands silhouette,
# red headline brush stroke, dark lower brush stroke, gold subtitle,
# and yellow scripture panel.
#
# REQUIRED ASSET:
# Save a CLEAN 9:16 background image (without any words or banners)
# as: assets/thumbnail_background.jpg
#
# The clean background should contain the scenic sky/sunrise,
# glowing cross at the upper-right, leaves at upper-left, and
# worshipper silhouette on a rock in the lower half.
# ============================================================

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

THUMB_WIDTH = 1080
THUMB_HEIGHT = 1920

THUMBNAIL_BACKGROUND = Path("assets/thumbnail_background.jpg")
THUMBNAIL_OUTPUT = Path("output/faith_shorts_thumbnail.jpg")
FONT_DIR = Path("assets/fonts")

# Put these font files in assets/fonts if available.
# The generator falls back to a standard bold font if they are absent.
FONT_HEADLINE = FONT_DIR / "Anton-Regular.ttf"
FONT_BOLD = FONT_DIR / "Montserrat-ExtraBold.ttf"
FONT_SUBTITLE = FONT_DIR / "Montserrat-Bold.ttf"


def _load_font(font_path, size):
    """Load the requested font, with safe fallbacks."""
    candidates = [
        font_path,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ]
    for candidate in candidates:
        try:
            if candidate and candidate.exists():
                return ImageFont.truetype(str(candidate), size)
        except OSError:
            pass
    return ImageFont.load_default()


def _fit_font(draw, text, font_path, max_width, start_size, min_size=34):
    """Reduce font size until the text fits the available width."""
    size = start_size
    while size >= min_size:
        font = _load_font(font_path, size)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        if box[2] - box[0] <= max_width:
            return font
        size -= 3
    return _load_font(font_path, min_size)


def _center_text(draw, text, y, font, fill, stroke_fill="#111111",
                 stroke_width=2, x_center=THUMB_WIDTH // 2):
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_width = box[2] - box[0]
    x = x_center - text_width // 2
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill
    )


def _brush_banner(draw, points, fill, extra_strokes=()):
    """Draw a slightly irregular brush-stroke banner."""
    draw.polygon(points, fill=fill)
    for line_points, line_fill, line_width in extra_strokes:
        draw.line(line_points, fill=line_fill, width=line_width)


def _split_thumbnail_title(video_title):
    """
    Arrange common Faith Shorts titles into the three-line visual style.
    Returns: top line, highlighted middle line, lower line.
    """
    title = " ".join((video_title or "").upper().split())

    known_layouts = {
        "YOU ARE THE RIGHTEOUSNESS OF GOD":
            ("YOU ARE THE", "RIGHTEOUSNESS", "OF GOD"),
        "YOU ARE A NEW CREATION IN CHRIST":
            ("YOU ARE A", "NEW CREATION", "IN CHRIST"),
        "YOU ARE ACCEPTED IN THE BELOVED":
            ("YOU ARE", "ACCEPTED", "IN THE BELOVED"),
    }
    if title in known_layouts:
        return known_layouts[title]

    # General fallback: remove a familiar opening phrase, then split
    # the remaining words into a strong middle phrase and a short ending.
    words = title.split()
    if len(words) >= 5 and words[:3] == ["YOU", "ARE", "THE"]:
        top = "YOU ARE THE"
        rest = words[3:]
    elif len(words) >= 5 and words[:3] == ["YOU", "ARE", "A"]:
        top = "YOU ARE A"
        rest = words[3:]
    elif len(words) >= 4 and words[:2] == ["YOU", "ARE"]:
        top = "YOU ARE"
        rest = words[2:]
    else:
        top = " ".join(words[:2]) if len(words) > 2 else title
        rest = words[2:] if len(words) > 2 else []

    if len(rest) >= 3:
        middle = " ".join(rest[:-2])
        lower = " ".join(rest[-2:])
    elif len(rest) == 2:
        middle, lower = rest[0], rest[1]
    elif len(rest) == 1:
        middle, lower = rest[0], ""
    else:
        middle, lower = "", ""

    return top, middle, lower


def _draw_scripture_panel(draw, scripture_reference):
    """Draw a yellow scripture panel on the right side of the image."""
    refs = [
        part.strip()
        for part in (scripture_reference or "").replace(";", "|").split("|")
        if part.strip()
    ]
    if not refs:
        return

    # Keep the panel to the right so it does not cover the worshipper.
    panel = [(555, 1050), (1015, 1035), (1040, 1250),
             (585, 1275), (535, 1195)]
    _brush_banner(draw, panel, "#FFD21C")

    if len(refs) == 1:
        lines = [refs[0]]
    else:
        lines = refs[:2]

    if len(lines) == 1:
        font = _fit_font(draw, lines[0], FONT_BOLD, 420, 58, 32)
        _center_text(draw, lines[0], 1120, font, "#101010",
                     stroke_fill="#FFD21C", stroke_width=1, x_center=790)
    else:
        font1 = _fit_font(draw, lines[0], FONT_BOLD, 420, 52, 30)
        font2 = _fit_font(draw, lines[1], FONT_BOLD, 420, 52, 30)
        _center_text(draw, lines[0], 1080, font1, "#101010",
                     stroke_fill="#FFD21C", stroke_width=1, x_center=790)
        draw.line((650, 1160, 930, 1152), fill="#B51E18", width=5)
        _center_text(draw, lines[1], 1180, font2, "#101010",
                     stroke_fill="#FFD21C", stroke_width=1, x_center=790)


def create_faith_shorts_thumbnail(
    video_title,
    scripture_reference,
    subtitle="Faith Declaration",
    background_path=THUMBNAIL_BACKGROUND,
    output_path=THUMBNAIL_OUTPUT
):
    """
    Create a 1080 x 1920 portrait thumbnail.

    Example:
        create_faith_shorts_thumbnail(
            video_title="YOU ARE THE RIGHTEOUSNESS OF GOD",
            scripture_reference="2 Corinthians 5:21; Romans 5:17"
        )
    """
    background_path = Path(background_path)
    output_path = Path(output_path)

    if not background_path.exists():
        raise FileNotFoundError(
            f"Thumbnail background not found: {background_path}. "
            "Add a clean 9:16 background image without text or banners."
        )

    image = Image.open(background_path).convert("RGB")
    image = image.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.Resampling.LANCZOS)
    image = image.convert("RGBA")


    # Semi-transparent dark wash behind the headline improves readability
    # while allowing the sunrise photograph to remain visible.
    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shade)
    shade_draw.rectangle((0, 120, THUMB_WIDTH, 950), fill=(0, 0, 0, 48))
    image = Image.alpha_composite(image, shade)

    draw = ImageDraw.Draw(image)
    top_line, middle_line, lower_line = _split_thumbnail_title(video_title)

    # Top white line
    top_font = _fit_font(draw, top_line, FONT_HEADLINE, 900, 112, 42)
    _center_text(
        draw, top_line, 165, top_font, "#FFFFFF",
        stroke_fill="#101010", stroke_width=5
    )

    # Red brush-stroke banner and highlighted yellow phrase
    red_banner = [
        (38, 330), (160, 300), (895, 292), (1040, 320),
        (1010, 520), (865, 545), (115, 555), (25, 510)
    ]
    _brush_banner(
        draw, red_banner, "#D71920",
        extra_strokes=[
            ([(55, 345), (1020, 315)], "#F33A32", 8),
            ([(40, 510), (1005, 530)], "#A90E18", 7),
        ]
    )
    if middle_line:
        middle_font = _fit_font(draw, middle_line, FONT_HEADLINE, 900, 170, 48)
        _center_text(
            draw, middle_line, 355, middle_font, "#FFE500",
            stroke_fill="#5B0808", stroke_width=6
        )

    # Dark brush-stroke banner for the final title line
    dark_banner = [
        (75, 585), (225, 565), (930, 575), (1010, 610),
        (990, 800), (850, 825), (150, 825), (55, 780)
    ]
    _brush_banner(
        draw, dark_banner, "#171313",
        extra_strokes=[
            ([(95, 610), (990, 600)], "#332323", 7),
            ([(70, 785), (975, 800)], "#090909", 8),
        ]
    )
    if lower_line:
        lower_font = _fit_font(draw, lower_line, FONT_HEADLINE, 900, 190, 48)
        _center_text(
            draw, lower_line, 610, lower_font, "#FFFFFF",
            stroke_fill="#8D1515", stroke_width=7
        )

    # Gold subtitle brush stroke
    subtitle_banner = [
        (190, 845), (330, 825), (745, 830), (890, 860),
        (860, 965), (300, 980), (180, 935)
    ]
    _brush_banner(
        draw, subtitle_banner, "#F4C542",
        extra_strokes=[
            ([(215, 855), (865, 870)], "#FFE18A", 5),
            ([(205, 950), (850, 950)], "#C58B20", 5),
        ]
    )
    subtitle_font = _fit_font(draw, subtitle, FONT_SUBTITLE, 650, 72, 34)
    _center_text(
        draw, subtitle, 870, subtitle_font, "#111111",
        stroke_fill="#F4C542", stroke_width=1
    )

    # Scripture reference panel
    _draw_scripture_panel(draw, scripture_reference)

    # Fine border to finish the composition
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (22, 22, THUMB_WIDTH - 22, THUMB_HEIGHT - 22),
        radius=24,
        outline=(255, 215, 110, 180),
        width=3
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, "JPEG", quality=94, optimize=True)
    return str(output_path)


# Example integration in renderer.py:
#
# thumbnail_path = create_faith_shorts_thumbnail(
#     video_title=payload.get("video_title", "YOU ARE THE RIGHTEOUSNESS OF GOD"),
#     scripture_reference=payload.get("scripture_reference", "2 Corinthians 5:21; Romans 5:17"),
