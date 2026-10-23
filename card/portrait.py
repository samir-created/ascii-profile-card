"""Turn a photo of you into the ASCII portrait the card uses.

Run from the repo root: python -m card.portrait

The background is removed with rembg. A PNG that already has a transparent background
is used as it is, so rembg is only needed for ordinary photos.
"""
import sys

from PIL import Image, ImageChops, ImageFilter, ImageOps

from . import config

# monospace characters are about half as wide as a line is tall
CELL_ASPECT = 0.5


def cut_out(image, model):
    """Return the photo as RGBA with the background made transparent."""
    if image.mode in ("RGBA", "LA") and image.getchannel("A").getextrema()[0] < 128:
        return image.convert("RGBA")
    try:
        from rembg import new_session, remove
    except ImportError:
        sys.exit(
            "Removing the photo background needs rembg: pip install -r requirements-photo.txt\n"
            "Or use a PNG whose background is already transparent."
        )
    # name the model: rembg's own default changes between versions (2.0.86 defaults to a ~1 GB one)
    return remove(image.convert("RGB"), session=new_session(model)).convert("RGBA")


# how much of the portrait's width the head fills, per framing
HEAD_SHARE = {"shoulders": 0.42, "head": 0.78}


def runs(row):
    """(start, end) of each stretch of mask in one row of 0/1 values."""
    out, start = [], None
    for x, on in enumerate(row + [0]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            out.append((start, x - 1))
            start = None
    return out


def head_span(mask, work_width=400):
    """Top of the hair, plus the head's width and centre.

    Follows only the outline connected to the top of the head, so other objects in the mask
    (a laptop, a sign, someone behind you) are ignored, and doesn't rely on seeing a neck:
    a bowed head or a raised shoulder often hides it. Walk down about one head-length from
    the top of the hair, then measure the head across its middle, at temple and ear level."""
    scale = mask.width / work_width
    small = mask.resize((work_width, max(1, round(mask.height / scale))), Image.Resampling.BOX)
    w, h = small.size
    data = list(small.point(lambda v: 1 if v > 128 else 0).tobytes())
    rows = [data[y * w:(y + 1) * w] for y in range(h)]
    top = next((y for y, row in enumerate(rows) if any(row)), None)
    if top is None:
        sys.exit("Couldn't find a person in the photo. Try a clearer photo or set portrait.crop.")

    # the top of the hair: the widest stretch in the first row with any mask
    span = max(runs(rows[top]), key=lambda r: r[1] - r[0])
    tracked, widest, narrowed = [], 0, False
    for y in range(top, h):
        centre = (span[0] + span[1]) / 2
        touching = [r for r in runs(rows[y]) if r[0] <= span[1] and r[1] >= span[0]]
        if not touching:
            break
        # stay with the stretch nearest the head's centre so far
        span = min(touching, key=lambda r: abs((r[0] + r[1]) / 2 - centre))
        width = span[1] - span[0] + 1
        down = y - top
        below_dome = down >= widest * 0.6  # curly hair wobbles in width; only trust shape below it
        if narrowed and width > widest:
            break  # narrowed at the jaw or neck, now widening again: shoulders or arms
        if below_dome and width < widest * 0.97:
            narrowed = True
        if down < widest * 0.8 or not widest:
            widest = max(widest, width)  # the hair dome sets the head's width; later rows can't
        tracked.append(span)
        if down >= widest * 1.1:  # about a head's length down from the top of the hair
            break

    # the middle of the head (temples to ears) is head, never shoulders or arms
    band = tracked[len(tracked) * 4 // 10: len(tracked) * 7 // 10] or tracked
    widths = sorted(r[1] - r[0] + 1 for r in band)
    head_w = widths[len(widths) // 2]
    centre = sum((r[0] + r[1]) / 2 for r in band) / len(band)
    return top * scale, head_w * scale, centre * scale


def auto_crop(mask, columns, rows, framing="shoulders"):
    """From just above the hair, in the proportions the ASCII grid needs: head and shoulders,
    or just the head (hair to chin)."""
    top, head_w, centre = head_span(mask)
    width = head_w / HEAD_SHARE[framing]
    height = width * rows / (columns * CELL_ASPECT)
    top -= height * 0.03
    return (centre - width / 2, top, centre + width / 2, top + height)


def to_ascii(image, settings):
    """Ink-style conversion: dark parts of the photo (hair, glasses, beard) get the dense characters."""
    columns, rows, ramp = settings["columns"], settings["rows"], settings["ramp"]
    rgba = cut_out(image, settings["model"])
    mask = rgba.getchannel("A")
    box = settings["crop"] or auto_crop(mask, columns, rows, settings["framing"])
    box = tuple(round(v) for v in box)
    # crop on a padded canvas so a box reaching past the photo edge is fine
    gray = Image.new("L", rgba.size, 0)
    gray.paste(rgba.convert("L"), (0, 0))
    gray, mask = gray.crop(box), mask.crop(box)

    big = (columns * 4, rows * 4)  # work at 4x, then average down for smoother tones
    gray = gray.resize(big, Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(4, 160, 2))
    mask = mask.resize(big, Image.Resampling.LANCZOS)
    solid = mask.point(lambda v: 255 if v > 128 else 0)
    gray = ImageOps.autocontrast(gray, cutoff=2, mask=solid)

    ink = ImageOps.invert(gray).point(lambda v: int(255 * (v / 255) ** settings["gamma"]))
    edges = gray.filter(ImageFilter.GaussianBlur(1.5)).filter(ImageFilter.FIND_EDGES)
    edges = edges.point(lambda v: min(255, int(v * settings["edges"])))
    ink = ImageChops.lighter(ink, edges).resize((columns, rows), Image.Resampling.BOX)
    mask = mask.resize((columns, rows), Image.Resampling.BOX)

    lines = []
    for y in range(rows):
        row = []
        for x in range(columns):
            if mask.getpixel((x, y)) < 100:
                row.append(" ")
            else:
                level = ink.getpixel((x, y)) / 256
                row.append(ramp[max(1, min(len(ramp) - 1, int(level * len(ramp))))])
        lines.append("".join(row).rstrip())
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return lines


def main():
    try:
        cfg = config.load(sys.argv[1] if len(sys.argv) > 1 else None)
    except config.ConfigError as e:
        sys.exit(f"config.yml: {e}")
    settings = cfg["portrait"]
    photo = settings["photo"]
    if not photo or not photo.exists():
        print(f"No photo at {photo}; keeping {settings['ascii'].name} as it is.")
        return
    lines = to_ascii(Image.open(photo), settings)
    settings["ascii"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {settings['ascii'].name} ({len(lines)} rows) from {photo.name}")


if __name__ == "__main__":
    main()
