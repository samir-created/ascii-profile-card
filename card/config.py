"""Load config.yml and turn it into plain values the builders use."""
from pathlib import Path

import yaml

from .themes import PRESETS

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_RAMP = " .,:;-=+*#%@"

LAYOUTS = ("side", "portrait-right", "stacked")
INFO_STYLES = ("dots", "aligned", "arrows")
CHARSETS = ("classic", "blocks", "binary", "dots", "dense", "hex")
FRAMES = ("plain", "window")
ANIMATIONS = ("thoughts", "rain", "cursor")
FRAMINGS = ("shoulders", "head")
HEADER_COLORS = ("text", "key", "value", "dots")
ALIGNS = ("left", "center", "right")


class ConfigError(ValueError):
    pass


def load(path=None):
    path = Path(path) if path else ROOT / "config.yml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    base = path.parent
    return {
        "title": str(raw.get("title", "you@yourname")),
        "header": parse_header(raw.get("header") or []),
        "info": [parse_row(row, i) for i, row in enumerate(raw.get("info") or [])],
        "portrait": portrait_settings(raw.get("portrait") or {}, base),
        "thoughts": thought_settings(raw.get("thoughts") or {}),
        "info_width": int((raw.get("layout") or {}).get("info_width", 64)),
        "info_offset": float((raw.get("layout") or {}).get("info_offset", 30)),
        "style": style_settings(raw.get("style") or {}),
        "themes": theme_settings((raw.get("style") or {}).get("theme", "github"), raw.get("themes") or {}),
        "root": base,
    }


def parse_row(row, index):
    """One info entry becomes ("blank",), ("section", name) or ("kv", key, value)."""
    if row in ("", None):
        return ("blank",)
    if isinstance(row, dict) and len(row) == 1:
        key, value = next(iter(row.items()))
        if key == "section":
            return ("section", str(value))
        return ("kv", str(key), "" if value is None else str(value))
    raise ConfigError(f"info row {index + 1}: expected '- Key: value', '- section: Name' or '- \"\"', got {row!r}")


def parse_header(raw):
    """Free lines above the details. Each entry is a string, {text: ...} or {art: ...};
    multi-line text becomes several lines. Returns one dict per line."""
    lines = []
    for i, entry in enumerate(raw):
        if isinstance(entry, str):
            entry = {"text": entry}
        if not isinstance(entry, dict) or ("text" in entry) == ("art" in entry):
            raise ConfigError(f"header line {i + 1}: use a string, '- text: ...' or '- art: |' (one of text or art)")
        art = "art" in entry
        body = str(entry["art" if art else "text"])
        color = str(entry.get("color", "dots" if art else "text"))
        if color not in HEADER_COLORS:
            raise ConfigError(f"header line {i + 1}: color '{color}' is not one of {', '.join(HEADER_COLORS)}")
        align = str(entry.get("align", "left"))
        if align not in ALIGNS:
            raise ConfigError(f"header line {i + 1}: align '{align}' is not one of {', '.join(ALIGNS)}")
        size = float(entry.get("size", 12 if art else 16))
        if not 6 <= size <= 64:
            raise ConfigError(f"header line {i + 1}: size must be between 6 and 64")
        text = body.rstrip("\n").split("\n") if art else body.strip("\n").split("\n")
        for line in text:
            lines.append({"text": line.rstrip(), "color": color, "size": size,
                          "bold": bool(entry.get("bold", False)), "align": align, "art": art})
    return lines


def portrait_settings(raw, base):
    crop = raw.get("crop")
    if crop is not None and (len(crop) != 4 or not all(isinstance(v, (int, float)) for v in crop)):
        raise ConfigError("portrait.crop must be [left, top, right, bottom] in pixels")
    ramp = str(raw.get("ramp", DEFAULT_RAMP))
    if len(ramp) < 2:
        raise ConfigError("portrait.ramp needs at least two characters, lightest first")
    return {
        "photo": base / raw["photo"] if raw.get("photo") else None,
        "ascii": base / raw.get("ascii", "ascii.txt"),
        "columns": int(raw.get("columns", 80)),
        "rows": int(raw.get("rows", 45)),
        "crop": crop,
        "gamma": float(raw.get("gamma", 1.4)),
        "edges": float(raw.get("edges", 2.5)),
        "ramp": ramp,
        "model": str(raw.get("model", "u2net_human_seg")),
        "framing": framing(raw),
    }


def framing(raw):
    value = str(raw.get("framing", "shoulders"))
    if value not in FRAMINGS:
        raise ConfigError(f"portrait.framing: '{value}' is not one of {', '.join(FRAMINGS)}")
    return value


def thought_settings(raw):
    rise = raw.get("rise_seconds", [6, 9])
    if len(rise) != 2 or rise[0] <= 0 or rise[1] < rise[0]:
        raise ConfigError("thoughts.rise_seconds must be [shortest, longest], e.g. [6, 9]")
    return {
        "rise": (float(rise[0]), float(rise[1])),
        "symbols": [str(s) for s in raw.get("symbols") or []],
    }


def choice(raw, name, allowed, default):
    value = str(raw.get(name, default))
    if value not in allowed:
        raise ConfigError(f"style.{name}: '{value}' is not one of {', '.join(allowed)}")
    return value


def style_settings(raw):
    animations = raw.get("animations", ["thoughts"]) or []
    unknown = [a for a in animations if a not in ANIMATIONS]
    if unknown:
        raise ConfigError(f"style.animations: unknown {', '.join(map(str, unknown))}; pick from {', '.join(ANIMATIONS)}")
    return {
        "layout": choice(raw, "layout", LAYOUTS, "side"),
        "info_style": choice(raw, "info_style", INFO_STYLES, "dots"),
        "charset": choice(raw, "charset", CHARSETS, "classic"),
        "invert": bool(raw.get("invert", False)),
        "frame": choice(raw, "frame", FRAMES, "plain"),
        "animations": list(dict.fromkeys(animations)),
    }


def theme_settings(name, custom):
    """A preset by name, or "custom" to use the palettes written under themes:."""
    if name == "custom":
        palettes = custom
    elif name in PRESETS:
        palettes = PRESETS[name]
    else:
        raise ConfigError(f"style.theme: '{name}' is not one of {', '.join(PRESETS)} or custom")
    if not palettes:
        raise ConfigError("themes: define at least one palette, e.g. dark and light")
    themes = {}
    for mode, colors in palettes.items():
        missing = {"bg", "text", "key", "value", "dots"} - set(colors or {})
        if missing:
            raise ConfigError(f"themes.{mode} is missing: {', '.join(sorted(missing))}")
        themes[str(mode)] = {k: str(v) for k, v in colors.items()}
    return themes
