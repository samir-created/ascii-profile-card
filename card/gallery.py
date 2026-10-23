"""Render one example card per style option into examples/, for browsing the variations.

Run from the repo root: python -m card.gallery
"""
import copy
import sys

from . import build, config
from .themes import PRESETS

GREETING = [
    {"text": "Hi, I'm Samir 👋", "color": "key", "size": 22, "bold": True},
    "Building plugins, agents & dev tools",
]
BANNER = [{"art": "┌─┐┌─┐┌┬┐┬┬─┐\n└─┐├─┤││││├┬┘\n└─┘┴ ┴┴ ┴┴┴└─", "color": "value", "size": 14}]
QUOTE = [
    {"text": "“Talk is cheap. Show me the code.”", "color": "value", "align": "center"},
    {"text": "— Linus Torvalds", "color": "dots", "size": 13, "align": "center"},
]

# (file name, overrides). Every example starts from config.yml; "header" swaps the header lines,
# everything else is a style option.
VARIANTS = (
    [(f"theme-{name}", {"theme": name}) for name in PRESETS]
    + [(f"layout-{name}", {"layout": name}) for name in config.LAYOUTS]
    + [(f"info-{name}", {"info_style": name}) for name in config.INFO_STYLES]
    + [(f"charset-{name}", {"charset": name}) for name in config.CHARSETS]
    + [
        ("invert", {"invert": True}),
        ("frame-window", {"frame": "window"}),
        ("animation-thoughts", {"animations": ["thoughts"]}),
        ("animation-rain", {"animations": ["rain"]}),
        ("animation-cursor", {"animations": ["cursor"]}),
        ("animation-none", {"animations": []}),
        ("combo-hacker", {"theme": "monokai", "charset": "binary", "frame": "window", "animations": ["rain", "cursor"]}),
        ("combo-minimal", {"theme": "nord", "info_style": "aligned", "charset": "dots", "animations": []}),
        ("combo-retro", {"theme": "gruvbox", "charset": "blocks", "info_style": "arrows", "frame": "window"}),
        ("header-greeting", {"header": GREETING}),
        ("header-banner", {"header": BANNER}),
        ("header-quote", {"header": QUOTE}),
    ]
)


def main():
    try:
        base = config.load(sys.argv[1] if len(sys.argv) > 1 else None)
    except config.ConfigError as e:
        sys.exit(f"config.yml: {e}")
    out = base["root"] / "examples"
    for mode in ("dark", "light"):
        (out / mode).mkdir(parents=True, exist_ok=True)
    raw_portrait = build.read_portrait(base["portrait"]["ascii"])
    for name, overrides in VARIANTS:
        cfg = copy.deepcopy(base)
        cfg["style"].update({k: v for k, v in overrides.items() if k not in ("theme", "header")})
        if "header" in overrides:
            cfg["header"] = config.parse_header(overrides["header"])
        if "theme" in overrides:
            cfg["themes"] = config.theme_settings(overrides["theme"], {})
        style = cfg["style"]
        portrait = build.restyle(raw_portrait, cfg["portrait"]["ramp"], style["charset"], style["invert"])
        # examples/dark/<name>.svg and examples/light/<name>.svg, so the README can switch
        # with the reader's GitHub theme
        for mode in ("dark", "light"):
            theme = cfg["themes"].get(mode) or next(iter(cfg["themes"].values()))
            (out / mode / f"{name}.svg").write_text(build.render(cfg, theme, portrait), encoding="utf-8")
    print(f"wrote {len(VARIANTS)} examples to examples/dark/ and examples/light/")


if __name__ == "__main__":
    main()
