from lib.hardware_config import DISPLAY_REGIONS

# Low Level Helpers


def get_region(key):
    """Safe lookup for regions."""
    return DISPLAY_REGIONS.get(key, (0, 0, 0, 0))


class TextOptions:
    def __init__(
        self,
        font_size=1,
        align="center",
        send_payload=False,
        clear=True,
        x_offset=0,
        y_offset=0,
    ):
        self.font_size = font_size
        self.align = align
        self.send_payload = send_payload
        self.clear = clear
        self.x_offset = x_offset
        self.y_offset = y_offset


DEFAULT_OPTIONS = TextOptions()


def draw_text_in_region(oled, region_key, text, options=DEFAULT_OPTIONS):
    """
    Draws text aligned within a specific region.
    Uses TextOptions for styling and behavior configuration.
    """
    x, y, w, h = get_region(region_key)
    x += options.x_offset
    y += options.y_offset

    if options.clear:
        oled.rect(x, y, w, h, oled.black, True)

    # Calculate text dimensions (approximate based on font size)
    char_w = 8 * options.font_size
    text_w = len(str(text)) * char_w

    # Calculate X position
    if options.align == "center":
        draw_x = x + (w - text_w) // 2
    elif options.align == "right":
        draw_x = x + w - text_w
    else:  # left
        draw_x = x

    # Calculate Y position (vertically centered)
    char_h = 8 * options.font_size
    draw_y = y + (h - char_h) // 2

    oled.text_scaled(str(text), int(draw_x), int(draw_y), options.font_size)

    if options.send_payload:
        oled.show()


def draw_rect_in_region(
    oled, region_key, fill=True, send_payload=False, clear=True, x_offset=0
):
    """Draws a rectangle in the specified region."""
    x, y, w, h = get_region(region_key)
    x += x_offset

    if clear:
        oled.rect(x, y, w, h, oled.black, True)

    if fill:
        oled.rect(x, y, w, h, oled.white, True)
    else:
        # Draw outline manually because framebuf.rect with fill=False
        # isn't always reliable or to match existing style of explicit lines
        oled.line(x, y, x + w - 1, y, oled.white)
        oled.line(x, y, x, y + h - 1, oled.white)
        oled.line(x + w - 1, y, x + w - 1, y + h - 1, oled.white)
        oled.line(x, y + h - 1, x + w - 1, y + h - 1, oled.white)

    if send_payload:
        oled.show()


def display_clear(oled, *regions, send_payload=True):
    """Clears specified sections of the OLED display."""
    for region in regions:
        if region in DISPLAY_REGIONS:
            x, y, width, height = DISPLAY_REGIONS[region]
            oled.rect(x, y, width, height, oled.black, True)

    if send_payload:
        oled.show()


def process_timer_duration(duration):
    """Formats duration as a string with leading zeros."""
    return f"{duration:02d}"


def format_match_timer(seconds):
    """Formats seconds into MM:SS."""
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def format_stopwatch(ms):
    """Formats milliseconds into SS.CC (Seconds.Centiseconds)."""
    # Total seconds and remainder ms
    total_seconds, rem_ms = divmod(ms, 1000)
    # Centiseconds
    cs = rem_ms // 10
    return f"{total_seconds:02d}.{cs:02d}"
