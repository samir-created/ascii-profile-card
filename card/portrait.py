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
    if image.mode in ("P", "PA") and ("transparency" in image.info or image.mode == "PA"):
        image = image.convert("RGBA")  # a palette PNG keeps its see-through background this way
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


def mask_rows(image):
    data = list(image.point(lambda v: 1 if v > 128 else 0).tobytes())
    return [data[y * image.width:(y + 1) * image.width] for y in range(image.height)]


def peaks(rows, limit=8):
    """Where each separate shape along the top of the mask begins: a head, but also a raised
    hand, a lamp the background removal kept, a shoulder. (row, stretch), highest first."""
    out, above = [], []
    for y, row in enumerate(rows):
        here = runs(row)
        for r in here:
            if not any(a[0] <= r[1] and a[1] >= r[0] for a in above):
                out.append((y, r))
                if len(out) == limit:
                    return out
        above = here
    return out


def follow(rows, top, span):
    """Walk down one shape from its top for about a head's length and measure it like a head:
    {top, width, centre}, whether it's really a body (it never narrows the way a head does at
    the jaw, it only gets wider), whether it ran on out of the bottom of the photo, and where
    the shape carries on below what was measured, as (row, stretch), if it does."""
    tracked, widest, narrowed, rest, closed, ran_out = [], 0, False, None, False, False
    for y in range(top, len(rows)):
        centre = (span[0] + span[1]) / 2
        touching = [r for r in runs(rows[y]) if r[0] <= span[1] and r[1] >= span[0]]
        if not touching:
            closed = True  # the shape ended: a head with no neck showing, or a stray object
            break
        # stay with the stretch nearest the head's centre so far
        span = min(touching, key=lambda r: abs((r[0] + r[1]) / 2 - centre))
        width = span[1] - span[0] + 1
        down = y - top
        below_dome = down >= widest * 0.6  # curly hair wobbles in width; only trust shape below it
        if narrowed and width > widest:
            rest = (y, span)
            break  # narrowed at the jaw or neck, now widening again: shoulders or arms
        if below_dome and width < widest * 0.97:
            narrowed = True
        if down < widest * 0.8 or not widest:
            widest = max(widest, width)  # the hair dome sets the head's width; later rows can't
        tracked.append(span)
        if down >= widest * 1.1:  # about a head's length down from the top of the hair
            rest = (y + 1, span) if y + 1 < len(rows) else None
            break
    else:
        ran_out = True
    # the middle of the head (temples to ears) is head, never shoulders or arms
    band = tracked[len(tracked) * 4 // 10: len(tracked) * 7 // 10] or tracked
    widths = sorted(r[1] - r[0] + 1 for r in band)
    return {
        "top": top,
        "width": widths[len(widths) // 2],
        "centre": sum((r[0] + r[1]) / 2 for r in band) / len(band),
        "body": not (narrowed or closed),
        "ran_out": ran_out,
        "rest": rest,
    }


def follow_head(rows, top, span):
    """follow(), but a bun, topknot or hat on top of the head looks just like a head on
    shoulders, so look at what's below: a head is at most about twice as wide and ends
    inside the photo (at its neck or chin), while shoulders are wider still or run on out
    of the photo."""
    shape = follow(rows, top, span)
    while shape["rest"] and not shape["body"]:
        below = follow(rows, *shape["rest"])
        if below["body"] or below["ran_out"] or not 1.3 <= below["width"] / shape["width"] <= 2.2:
            break
        shape = below | {"top": shape["top"]}  # measure the head, but crop from the top of the bun
    return shape


# below this share of the photo, what the background removal kept is specks, not a person
MIN_PERSON = 0.005


def head_span(mask, work_width=400):
    """Top of the hair, plus the head's width and centre.

    Doesn't rely on seeing a neck (a bowed head or a raised shoulder often hides it) and
    ignores other things in the mask (a laptop, a sign, a raised hand, a lamp the background
    removal kept): every shape along the top is measured like a head, and the head is the
    highest one about as wide as the widest of them. Each is measured across its middle,
    at temple and ear level, about one head-length down from its top."""
    scale = mask.width / work_width
    small = mask.resize((work_width, max(1, round(mask.height / scale))), Image.Resampling.BOX)
    # shave off anything thinner than ~3% of the photo, e.g. a tuft of hair sticking up,
    # or it would pass for the top of the head and shrink the head to its own width
    shave = work_width // 30 | 1
    raw = mask_rows(small)
    rows = mask_rows(small.filter(ImageFilter.MinFilter(shave)).filter(ImageFilter.MaxFilter(shave)))
    if sum(map(sum, rows)) < MIN_PERSON * small.width * small.height:
        sys.exit("Couldn't find a person in the photo. Try a clearer photo or set portrait.crop.")

    shapes = [follow_head(rows, y, span) for y, span in peaks(rows)]
    # nothing but body: a close-up with the face running off the photo, or hair to the shoulders
    heads = [s for s in shapes if not s["body"]] or shapes
    widest = max(s["width"] for s in heads)
    head = min((s for s in heads if s["width"] >= widest * 0.75), key=lambda s: s["top"])

    # bring hair that was shaved off back into the picture, up to half a head above it
    left = max(0, round(head["centre"] - head["width"] / 2))
    right = round(head["centre"] + head["width"] / 2) + 1
    hair = next(y for y, row in enumerate(raw) if y >= head["top"] or any(row[left:right]))
    top = max(hair, head["top"] - head["width"] / 2)
    return top * scale, head["width"] * scale, head["centre"] * scale


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
    # phone photos are often stored sideways, with a note saying which way is up
    lines = to_ascii(ImageOps.exif_transpose(Image.open(photo)), settings)
    settings["ascii"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {settings['ascii'].name} ({len(lines)} rows) from {photo.name}")


if __name__ == "__main__":
    main()
