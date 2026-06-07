from PIL import Image, ImageDraw

TRAY_SIZE = 32


def _create_icon(fill: tuple[int, int, int], accent: tuple[int, int, int]) -> Image.Image:
    size = TRAY_SIZE
    image = Image.new("RGB", (size, size), fill)
    draw = ImageDraw.Draw(image)

    margin = 2
    draw.ellipse(
        (margin, margin, size - margin, size - margin),
        fill=fill,
        outline=accent,
        width=2,
    )

    cx, cy = size // 2, size // 2
    draw.rectangle((cx - 7, cy - 5, cx + 7, cy + 6), fill=accent)
    draw.rectangle((cx - 5, cy - 8, cx + 5, cy - 4), fill=accent)

    return image


def create_idle_icon() -> Image.Image:
    return _create_icon((247, 245, 242), (255, 107, 107))


def create_active_icon() -> Image.Image:
    image = _create_icon((126, 200, 164), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    cx, cy = TRAY_SIZE // 2, TRAY_SIZE // 2 + 2
    draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(255, 255, 255))
    draw.line((cx, cy, cx, cy - 6), fill=(255, 255, 255), width=1)
    draw.line((cx, cy, cx + 5, cy + 2), fill=(255, 255, 255), width=1)
    return image


def create_paused_icon() -> Image.Image:
    image = _create_icon((255, 193, 120), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    cx = TRAY_SIZE // 2
    draw.rectangle((cx - 5, 10, cx - 2, 22), fill=(255, 255, 255))
    draw.rectangle((cx + 2, 10, cx + 5, 22), fill=(255, 255, 255))
    return image
