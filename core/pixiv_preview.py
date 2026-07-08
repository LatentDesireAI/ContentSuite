"""Pixiv cover collage — up to 3 images on white background."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

BACKGROUND = (255, 255, 255)

LAYOUT_KEYS = {
    "auto": "layout.auto",
    "single": "layout.single",
    "row_2": "layout.row_2",
    "col_2": "layout.col_2",
    "row_3": "layout.row_3",
    "hero_left": "layout.hero_left",
}

LAYOUT_IMAGE_COUNT = {
    "single": 1,
    "row_2": 2,
    "col_2": 2,
    "row_3": 3,
    "hero_left": 3,
}


@dataclass(frozen=True)
class Cell:
    x: int
    y: int
    w: int
    h: int


def load_rgb(path: Path) -> Image.Image:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    with Image.open(path) as img:
        img.load()
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, BACKGROUND)
            background.paste(img, mask=img.split()[-1])
            return background
        if img.mode == "P":
            converted = img.convert("RGBA")
            background = Image.new("RGB", converted.size, BACKGROUND)
            background.paste(converted, mask=converted.split()[-1])
            return background
        if img.mode in ("CMYK", "I", "I;16", "F"):
            return img.convert("RGB")
        if img.mode != "RGB":
            return img.convert("RGB")
        return img.copy()


def layout_for_count(count: int, preferred: str = "auto") -> str:
    if count <= 1:
        return "single"
    if count == 2:
        if preferred == "col_2":
            return "col_2"
        return "row_2"
    if preferred == "hero_left":
        return "hero_left"
    if preferred == "col_2":
        return "col_2"
    return "row_3"


def resolve_layout(layout: str, image_count: int) -> str:
    if layout == "auto":
        return layout_for_count(image_count)
    required = LAYOUT_IMAGE_COUNT.get(layout)
    if required != image_count:
        return layout_for_count(image_count)
    return layout


def layout_label(layout: str) -> str:
    from core.i18n import tr

    key = LAYOUT_KEYS.get(layout)
    return tr(key) if key else layout


def parse_color(value: str, default: tuple[int, int, int] = (45, 45, 45)) -> tuple[int, int, int]:
    text = (value or "").strip().lstrip("#")
    if len(text) == 6:
        try:
            return (
                int(text[0:2], 16),
                int(text[2:4], 16),
                int(text[4:6], 16),
            )
        except ValueError:
            pass
    return default


def color_to_hex(color: tuple[int, int, int]) -> str:
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def _inner_size(canvas: int, padding: int) -> int:
    return canvas - padding * 2


def _cells_for_layout(layout: str, inner: int, gap: int) -> list[Cell]:
    if layout == "single":
        return [Cell(0, 0, inner, inner)]

    if layout == "row_2":
        w = (inner - gap) // 2
        return [Cell(0, 0, w, inner), Cell(w + gap, 0, w, inner)]

    if layout == "col_2":
        h = (inner - gap) // 2
        return [Cell(0, 0, inner, h), Cell(0, h + gap, inner, h)]

    if layout == "row_3":
        w = (inner - gap * 2) // 3
        return [
            Cell(0, 0, w, inner),
            Cell(w + gap, 0, w, inner),
            Cell((w + gap) * 2, 0, w, inner),
        ]

    if layout == "hero_left":
        left_w = int(inner * 0.58)
        right_w = inner - left_w - gap
        top_h = (inner - gap) // 2
        bottom_h = inner - top_h - gap
        return [
            Cell(0, 0, left_w, inner),
            Cell(left_w + gap, 0, right_w, top_h),
            Cell(left_w + gap, top_h + gap, right_w, bottom_h),
        ]

    raise ValueError(f"Unknown layout: {layout}")


def _prepare_tile(
    img: Image.Image,
    box_w: int,
    box_h: int,
    crop_fill: bool,
) -> tuple[Image.Image, int, int]:
    if img.width <= 0 or img.height <= 0:
        raise ValueError("Image has zero dimensions.")

    if crop_fill:
        scale = max(box_w / img.width, box_h / img.height)
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - box_w) // 2)
        top = max(0, (new_h - box_h) // 2)
        cropped = resized.crop((left, top, left + box_w, top + box_h))
        return cropped, 0, 0

    scale = min(box_w / img.width, box_h / img.height)
    new_w = max(1, int(img.width * scale))
    new_h = max(1, int(img.height * scale))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return resized, (box_w - new_w) // 2, (box_h - new_h) // 2


def _paste_in_cell(
    canvas: Image.Image,
    img: Image.Image,
    cell: Cell,
    origin_x: int,
    origin_y: int,
    crop_fill: bool,
    frame_width: int,
    frame_color: tuple[int, int, int],
) -> None:
    tile, offset_x, offset_y = _prepare_tile(img, cell.w, cell.h, crop_fill)
    base_x = origin_x + cell.x + offset_x
    base_y = origin_y + cell.y + offset_y
    canvas.paste(tile, (base_x, base_y))

    if frame_width <= 0:
        return

    draw = ImageDraw.Draw(canvas)
    x0 = base_x
    y0 = base_y
    x1 = base_x + tile.width - 1
    y1 = base_y + tile.height - 1
    draw.rectangle(
        [x0, y0, x1, y1],
        outline=frame_color,
        width=frame_width,
    )


def compose_cover(
    image_paths: list[Path | str],
    layout: str = "auto",
    canvas_size: int = 1200,
    padding: int = 24,
    gap: int = 16,
    crop_fill: bool = True,
    frame_width: int = 4,
    frame_color: str | tuple[int, int, int] = "#2d2d2d",
) -> tuple[Image.Image, str]:
    if not image_paths:
        raise ValueError("Add at least one image.")
    if len(image_paths) > 3:
        raise ValueError("Maximum 3 images for Pixiv preview.")

    images = [load_rgb(Path(p)) for p in image_paths]
    resolved = resolve_layout(layout, len(images))
    inner = _inner_size(canvas_size, padding)
    cells = _cells_for_layout(resolved, inner, gap)

    border = parse_color(frame_color) if isinstance(frame_color, str) else frame_color
    frame_px = max(0, int(frame_width))

    canvas = Image.new("RGB", (canvas_size, canvas_size), BACKGROUND)
    for img, cell in zip(images, cells, strict=True):
        _paste_in_cell(
            canvas,
            img,
            cell,
            padding,
            padding,
            crop_fill=crop_fill,
            frame_width=frame_px,
            frame_color=border,
        )

    return canvas, resolved


def layout_options_for_count(count: int) -> list[tuple[str, str]]:
    from core.i18n import tr

    options: list[tuple[str, str]] = [("auto", tr(LAYOUT_KEYS["auto"]))]
    if count == 1:
        options.append(("single", tr(LAYOUT_KEYS["single"])))
    elif count == 2:
        options.extend([
            ("row_2", tr(LAYOUT_KEYS["row_2"])),
            ("col_2", tr(LAYOUT_KEYS["col_2"])),
        ])
    elif count == 3:
        options.extend([
            ("row_3", tr(LAYOUT_KEYS["row_3"])),
            ("hero_left", tr(LAYOUT_KEYS["hero_left"])),
        ])
    return options