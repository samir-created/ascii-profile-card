"""Render the profile card SVGs from config.yml and the ASCII portrait.

Run from the repo root: python -m card.build
"""
import html
import random
import sys

from . import config

FONT = 16  # info text
LINE = 20
ART_FONT = 9  # portrait text
ART_LINE = 10.5
CHAR = 0.6  # monospace character width, as a share of the font size
PAD = 24
GAP = 32
THINK_H = 80  # room above the head for thoughts to float into
BAR_H = 34  # terminal title bar for frame: window

CHARSETS = {
    "classic": " .,:;-=+*#%@",
    "blocks": " ░▒▓█",
    "binary": " 01",
    "dots": " .·•●",
    "dense": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "hex": " 0123456789ABCDEF",
}


def line_height(header_line):
    """ASCII art rows sit tight so box-drawing strokes join up; text gets normal spacing."""
    return 1.12 if header_line["art"] else 1.3


def span(text, cls):
    return f'<tspan class="{cls}">{html.escape(text)}</tspan>'


# ---- portrait ---------------------------------------------------------------

def read_portrait(path):
    if not path.exists():
        sys.exit(f"No portrait at {path}. Add a photo and run: python -m card.portrait")
    lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")
    return [line.rstrip() for line in lines]


def restyle(lines, ramp, charset, invert):
    """Redraw the portrait with another character set, optionally swapping light and dark."""
    target = CHARSETS[charset]
    if charset == "classic" and not invert and ramp == target:
        return lines
    out = []
    for line in lines:
        row = []
        for ch in line:
            if ch == " ":
                row.append(" ")
                continue
            idx = ramp.index(ch) if ch in ramp else len(ramp) // 2
            density = idx / (len(ramp) - 1)
            if invert:
                density = 1 - density
            # never map ink to a space, or the outline of the portrait would break up
            row.append(target[1 + round(density * (len(target) - 2))])
        out.append("".join(row))
    return out


def head_top(lines, col):
    """First row with ink in a column, i.e. where the hair starts."""
    return next((i for i, line in enumerate(lines) if col < len(line) and line[col] != " "), None)


# ---- info -------------------------------------------------------------------

def info_lines(cfg):
    """The title plus every info row, as styled SVG text runs."""
    style, width = cfg["style"]["info_style"], cfg["info_width"]
    title, rows = cfg["title"], cfg["info"]
    key_w = max((len(r[1]) for r in rows if r[0] == "kv"), default=0)
    out = []
    if style == "dots":
        out.append(html.escape(title) + " " + span("-" * max(1, width - len(title) - 1), "dots"))
    elif style == "aligned":
        out.append(html.escape(title) + " " + span("─" * max(1, width - len(title) - 1), "dots"))
    else:
        out.append(span("❯ ", "key") + html.escape(title))
    for row in rows:
        kind = row[0]
        if kind == "blank":
            out.append(span(".", "dots") if style == "dots" else "")
        elif kind == "section":
            name = row[1]
            if style == "dots":
                out.append(span("- ", "dots") + html.escape(name) + " " + span("-" * max(1, width - len(name) - 3), "dots"))
            elif style == "aligned":
                out.append(span("── ", "dots") + html.escape(name) + " " + span("─" * max(1, width - len(name) - 4), "dots"))
            else:
                out.append(span("# ", "dots") + html.escape(name))
        else:
            key, value = row[1], row[2]
            if style == "dots":
                dots = "." * max(1, width - len(key) - len(value) - 5)
                out.append(span(". ", "dots") + span(key, "key") + ":" + span(f" {dots} ", "dots") + span(value, "value"))
            elif style == "aligned":
                out.append("  " + span(key.ljust(key_w), "key") + "  " + span(value, "value"))
            else:
                out.append(span("› ", "dots") + span(key, "key") + span(" → ", "dots") + span(value, "value"))
    return out


# ---- animations -------------------------------------------------------------

def thoughts(cfg, lines, art_x, art_top, art_w, theme):
    """Symbols that rise from the top of the head and fade out, like ideas being worked out."""
    symbols = cfg["thoughts"]["symbols"]
    cols = [c for c in range(max(map(len, lines))) if (head_top(lines, c) or 10**6) < len(lines) // 4]
    if not symbols or not cols:
        return ""
    rng = random.Random(7)
    lo, hi = min(cols), max(cols)
    shortest, longest = cfg["thoughts"]["rise"]
    colors = [theme["key"], theme["value"], theme["dots"]]
    out = []
    for i, token in enumerate(symbols):
        col = lo + (hi - lo) * (i + rng.random()) / len(symbols)
        y = art_top + head_top(lines, round(col)) * ART_LINE
        duration = rng.uniform(shortest, longest)
        delay = -rng.uniform(0, duration)  # start mid-flight so the head is never idle
        drift = rng.choice((-1, 1)) * rng.uniform(4, 14)
        size = rng.choice((12, 13, 14, 16))
        # keep the whole token, plus its drift, inside the portrait column
        x = min(art_x + col * ART_FONT * CHAR, art_x + art_w - abs(drift) - len(token) * size * CHAR)
        out.append(
            f'<text class="thought" x="{x:.0f}" y="{y:.0f}" font-size="{size}px" fill="{colors[i % 3]}" '
            f'style="--drift: {drift:.0f}px; animation-duration: {duration:.2f}s; animation-delay: {delay:.2f}s">'
            f"{html.escape(token)}</text>"
        )
    return "\n".join(out)


def rain(cfg, width, height, theme):
    """Faint columns of characters falling behind the card, Matrix style."""
    rng = random.Random(11)
    chars = CHARSETS[cfg["style"]["charset"]].strip() or "01"
    size, step = 11, 13
    out = []
    for x in range(12, int(width), 46):
        length = rng.randint(8, 16)
        column = "".join(
            f'<tspan x="{x + rng.uniform(-6, 6):.0f}" dy="{step if i else 0}">{html.escape(rng.choice(chars))}</tspan>'
            for i in range(length)
        )
        duration = rng.uniform(7, 13)
        out.append(
            f'<text class="rain" y="0" font-size="{size}px" fill="{theme["dots"]}" '
            f'style="--fall: {height + length * step:.0f}px; animation-duration: {duration:.2f}s; '
            f'animation-delay: {-rng.uniform(0, duration):.2f}s">{column}</text>'
        )
    return "\n".join(out)


def window_bar(cfg, width, theme):
    title = html.escape(f"{cfg['title']} — zsh")
    lights = "".join(
        f'<circle cx="{PAD + i * 18}" cy="{BAR_H / 2:.0f}" r="6" fill="{color}"/>'
        for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f"))
    )
    return (
        f'<path d="M15 0H{width - 15:.0f}A15 15 0 0 1 {width:.0f} 15V{BAR_H}H0V15A15 15 0 0 1 15 0Z" '
        f'fill="{theme["text"]}" fill-opacity="0.07"/>\n{lights}\n'
        f'<text x="{width / 2:.0f}" y="{BAR_H / 2 + 4:.0f}" font-size="12px" text-anchor="middle" '
        f'fill="{theme["dots"]}">{title}</text>'
    )


# ---- layout -----------------------------------------------------------------

def render(cfg, theme, portrait):
    style = cfg["style"]
    animations = style["animations"]
    rows = info_lines(cfg)
    cursor = "cursor" in animations
    think = THINK_H if "thoughts" in animations else 0
    bar = BAR_H if style["frame"] == "window" else 0

    cols = max(map(len, portrait), default=0)
    art_w, art_h = cols * ART_FONT * CHAR, len(portrait) * ART_LINE
    info_w = cfg["info_width"] * FONT * CHAR
    header = cfg["header"]
    header_h = sum(h["size"] * line_height(h) for h in header) + (12 if header else 0)
    info_h = header_h + (len(rows) + cursor) * LINE
    top = bar + PAD

    if style["layout"] == "stacked":
        width = max(art_w, info_w) + PAD * 2
        height = top + think + art_h + GAP + info_h + PAD
        art_x, info_x = (width - art_w) / 2, (width - info_w) / 2
        art_top = top + think
        info_top = art_top + art_h + GAP
    else:
        width = PAD + art_w + GAP + info_w + PAD
        content_h = max(think + art_h, info_h)
        height = top + content_h + PAD
        art_top = top + content_h - art_h - (content_h - think - art_h) / 2
        info_top = art_top + (art_h - info_h) / 2 + cfg["info_offset"]
        info_top = min(max(info_top, top), height - PAD - info_h)  # never spill off the card
        if style["layout"] == "side":
            art_x, info_x = PAD, PAD + art_w + GAP
        else:
            info_x, art_x = PAD, PAD + info_w + GAP

    art = "\n".join(
        f'<tspan x="{art_x:.1f}" y="{art_top + ART_FONT + i * ART_LINE:.1f}">{html.escape(line)}</tspan>'
        for i, line in enumerate(portrait)
    )
    head, y = [], info_top
    for line in header:
        y += line["size"] * line_height(line)
        anchor, x = {"left": ("start", info_x), "center": ("middle", info_x + info_w / 2),
                     "right": ("end", info_x + info_w)}[line["align"]]
        weight = ' font-weight="bold"' if line["bold"] else ""
        head.append(
            f'<text x="{x:.0f}" y="{y - line["size"] * 0.3:.1f}" font-size="{line["size"]:g}px" '
            f'text-anchor="{anchor}" fill="{theme[line["color"]]}"{weight}>{html.escape(line["text"])}</text>'
        )
    details_top = info_top + header_h
    info = "\n".join(
        f'<tspan x="{info_x:.0f}" y="{details_top + FONT + i * LINE:.0f}">{row}</tspan>'
        for i, row in enumerate(rows)
    )
    extras = []
    if "rain" in animations:
        extras.append(f'<g clip-path="url(#card)">\n{rain(cfg, width, height, theme)}\n</g>')
    if bar:
        extras.append(window_bar(cfg, width, theme))
    after = []
    if cursor:
        prompt = f"{cfg['title']}:~$ "
        y = details_top + FONT + len(rows) * LINE
        after.append(f'<text x="{info_x:.0f}" y="{y:.0f}" font-size="{FONT}px" fill="{theme["key"]}">{html.escape(prompt)}</text>')
        after.append(
            f'<rect class="cursor" x="{info_x + len(prompt) * FONT * CHAR:.0f}" y="{y - FONT + 3:.0f}" '
            f'width="{FONT * CHAR:.0f}" height="{FONT + 2}" fill="{theme["value"]}"/>'
        )
    if think:
        after.append(thoughts(cfg, portrait, art_x, art_top, art_w, theme))

    return f"""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,'SFMono-Regular',Menlo,monospace" width="{width:.0f}" height="{height:.0f}">
<style>
.key {{fill: {theme['key']};}}
.value {{fill: {theme['value']};}}
.dots {{fill: {theme['dots']};}}
text, tspan {{white-space: pre;}}
.thought {{opacity: 0; transform-box: fill-box; transform-origin: center; animation: think ease-out infinite;}}
@keyframes think {{
  0% {{opacity: 0; transform: translate(0, 0) scale(0.6);}}
  20% {{opacity: 0.95;}}
  70% {{opacity: 0.6;}}
  100% {{opacity: 0; transform: translate(var(--drift), -{THINK_H - 5}px) scale(1.1);}}
}}
.rain {{opacity: 0.35; animation: fall linear infinite;}}
@keyframes fall {{from {{transform: translateY(-100%);}} to {{transform: translateY(var(--fall));}}}}
.cursor {{animation: blink 1s step-end infinite;}}
@keyframes blink {{0%, 100% {{opacity: 1;}} 50% {{opacity: 0;}}}}
@media (prefers-reduced-motion: reduce) {{
  .thought, .rain {{display: none;}}
  .cursor {{animation: none;}}
}}
</style>
<defs><clipPath id="card"><rect width="{width:.0f}" height="{height:.0f}" rx="15"/></clipPath></defs>
<rect width="{width:.0f}" height="{height:.0f}" fill="{theme['bg']}" rx="15"/>
{chr(10).join(extras)}
<text fill="{theme['text']}" font-size="{ART_FONT}px">
{art}
</text>
{chr(10).join(head)}
<text fill="{theme['text']}" font-size="{FONT}px">
{info}
</text>
{chr(10).join(after)}
</svg>
"""


def header_warnings(cfg):
    """Header lines too wide for the details column would run off the card."""
    limit = cfg["info_width"] * FONT * CHAR
    return [
        f"header line '{h['text'][:30]}' is about {len(h['text']) * h['size'] * CHAR:.0f}px wide; "
        f"the details column is {limit:.0f}px. Shorten it or lower its size."
        for h in cfg["header"]
        if len(h["text"]) * h["size"] * CHAR > limit
    ]


def build(cfg, out_dir=None):
    """Write <theme>_mode.svg for every theme palette. Returns the paths written."""
    for warning in header_warnings(cfg):
        print(f"warning: {warning}", file=sys.stderr)
    p = cfg["portrait"]
    portrait = restyle(read_portrait(p["ascii"]), p["ramp"], cfg["style"]["charset"], cfg["style"]["invert"])
    out_dir = out_dir or cfg["root"]
    written = []
    for mode, theme in cfg["themes"].items():
        path = out_dir / f"{mode}_mode.svg"
        path.write_text(render(cfg, theme, portrait), encoding="utf-8")
        written.append(path)
    return written


def main():
    try:
        cfg = config.load(sys.argv[1] if len(sys.argv) > 1 else None)
    except config.ConfigError as e:
        sys.exit(f"config.yml: {e}")
    for path in build(cfg):
        print(f"wrote {path.relative_to(cfg['root']) if path.is_relative_to(cfg['root']) else path}")


if __name__ == "__main__":
    main()
