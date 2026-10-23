"""Run with: python -m unittest discover -s tests"""
import copy
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

from PIL import Image, ImageDraw

from card import build, config, portrait
from card.themes import PRESETS

ROOT = Path(__file__).resolve().parent.parent


def load():
    return config.load(ROOT / "config.yml")


class ConfigTest(unittest.TestCase):
    def test_rows(self):
        self.assertEqual(config.parse_row("", 0), ("blank",))
        self.assertEqual(config.parse_row({"section": "Contact"}, 0), ("section", "Contact"))
        self.assertEqual(config.parse_row({"OS": "Me"}, 0), ("kv", "OS", "Me"))
        with self.assertRaises(config.ConfigError):
            config.parse_row({"a": 1, "b": 2}, 0)

    def test_bad_style_names_explain_the_choices(self):
        with self.assertRaisesRegex(config.ConfigError, "side"):
            config.style_settings({"layout": "diagonal"})
        with self.assertRaisesRegex(config.ConfigError, "rain"):
            config.style_settings({"animations": ["fireworks"]})
        with self.assertRaisesRegex(config.ConfigError, "dracula"):
            config.theme_settings("neon", {})

    def test_custom_theme_needs_every_colour(self):
        with self.assertRaisesRegex(config.ConfigError, "value"):
            config.theme_settings("custom", {"dark": {"bg": "#000", "text": "#fff", "key": "#f00", "dots": "#888"}})

    def test_every_preset_is_complete(self):
        for name in PRESETS:
            self.assertEqual(set(config.theme_settings(name, {})), {"dark", "light"}, name)


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load()
        self.portrait = build.read_portrait(self.cfg["portrait"]["ascii"])

    def render(self, **style):
        cfg = copy.deepcopy(self.cfg)
        cfg["style"].update(style)
        art = build.restyle(self.portrait, cfg["portrait"]["ramp"], cfg["style"]["charset"], cfg["style"]["invert"])
        svg = build.render(cfg, cfg["themes"]["dark"], art)
        return svg, xml.dom.minidom.parseString(svg.encode())

    def test_every_option_renders_valid_svg(self):
        for layout in config.LAYOUTS:
            for info_style in config.INFO_STYLES:
                for charset in config.CHARSETS:
                    self.render(layout=layout, info_style=info_style, charset=charset)
        self.render(frame="window", animations=["thoughts", "rain", "cursor"], invert=True)

    def test_all_info_rows_present(self):
        svg, _ = self.render()
        for row in self.cfg["info"]:
            if row[0] == "kv":
                self.assertIn(row[1], svg)
                self.assertIn(row[2].replace("&", "&amp;"), svg)

    def test_animations_only_when_asked(self):
        still, _ = self.render(animations=[])
        self.assertNotIn('class="thought"', still)
        self.assertNotIn('class="rain"', still)
        self.assertNotIn('class="cursor"', still)
        busy, _ = self.render(animations=["thoughts", "rain", "cursor"])
        self.assertEqual(busy.count('class="thought"'), len(self.cfg["thoughts"]["symbols"]))
        self.assertIn('class="rain"', busy)
        self.assertIn('class="cursor"', busy)

    def test_thoughts_stay_inside_the_portrait_column(self):
        cols = max(map(len, self.portrait))
        art_right = build.PAD + cols * build.ART_FONT * build.CHAR
        _, dom = self.render(animations=["thoughts"])
        for node in dom.getElementsByTagName("text"):
            if node.getAttribute("class") == "thought":
                self.assertLess(float(node.getAttribute("x")), art_right)

    def test_restyle_keeps_the_outline(self):
        for charset in config.CHARSETS:
            out = build.restyle(self.portrait, self.cfg["portrait"]["ramp"], charset, invert=True)
            for before, after in zip(self.portrait, out):
                self.assertEqual([c == " " for c in before], [c == " " for c in after], charset)

    def test_build_writes_one_svg_per_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = build.build(load(), Path(tmp))
            self.assertEqual(sorted(p.name for p in written), ["dark_mode.svg", "light_mode.svg"])


class HeaderTest(unittest.TestCase):
    def test_entry_forms(self):
        lines = config.parse_header([
            "plain",
            {"text": "Hi 👋", "color": "key", "size": 22, "bold": True, "align": "center"},
            {"art": "  /\\\n /  \\\n"},
        ])
        self.assertEqual([l["text"] for l in lines], ["plain", "Hi 👋", "  /\\", " /  \\"])
        self.assertEqual((lines[1]["color"], lines[1]["size"], lines[1]["bold"], lines[1]["align"]), ("key", 22, True, "center"))
        self.assertTrue(lines[2]["art"])
        self.assertEqual(lines[2]["color"], "dots")  # art defaults to the faint colour

    def test_bad_entries_explain(self):
        for bad, hint in [({"text": "a", "art": "b"}, "one of text or art"), ({"text": "a", "color": "pink"}, "key"),
                          ({"text": "a", "align": "middle"}, "center"), ({"text": "a", "size": 200}, "between")]:
            with self.assertRaisesRegex(config.ConfigError, hint):
                config.parse_header([bad])

    def test_header_sits_above_the_details(self):
        cfg = load()
        art = build.read_portrait(cfg["portrait"]["ascii"])
        cfg["header"] = config.parse_header([{"text": "Hi, I'm Samir", "size": 22}, "tagline"])
        dom = xml.dom.minidom.parseString(build.render(cfg, cfg["themes"]["dark"], art).encode())
        texts = dom.getElementsByTagName("text")
        hi = next(float(t.getAttribute("y")) for t in texts if t.firstChild and t.firstChild.data == "Hi, I'm Samir")
        title_y = min(float(ts.getAttribute("y")) for ts in dom.getElementsByTagName("tspan")
                      if cfg["title"] in "".join(n.data for n in ts.childNodes if n.nodeType == n.TEXT_NODE))
        self.assertLess(hi, title_y)

    def test_too_wide_lines_warn(self):
        cfg = load()
        cfg["header"] = config.parse_header([{"text": "x" * 80, "size": 20}, "short"])
        warnings = build.header_warnings(cfg)
        self.assertEqual(len(warnings), 1)
        self.assertIn("xxxx", warnings[0])


class PortraitTest(unittest.TestCase):
    def test_transparent_png_needs_no_background_removal(self):
        # a simple bust: round head, narrow neck, wide shoulders, on a transparent background
        img = Image.new("RGBA", (400, 500), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((130, 40, 270, 200), fill=(60, 40, 30, 255))
        d.rectangle((175, 190, 225, 260), fill=(200, 150, 120, 255))
        d.polygon([(60, 500), (100, 270), (300, 270), (340, 500)], fill=(40, 40, 60, 255))
        settings = load()["portrait"] | {"crop": None, "columns": 40, "rows": 24}
        lines = portrait.to_ascii(img, settings)
        self.assertTrue(lines)
        self.assertLessEqual(max(map(len, lines)), 40)
        self.assertTrue(all(set(line) <= set(settings["ramp"]) for line in lines))

    def test_head_is_found_above_the_shoulders(self):
        mask = Image.new("L", (400, 500), 0)
        d = ImageDraw.Draw(mask)
        d.ellipse((130, 40, 270, 200), fill=255)
        d.rectangle((175, 190, 225, 260), fill=255)
        d.polygon([(60, 500), (100, 270), (300, 270), (340, 500)], fill=255)
        top, width, centre = portrait.head_span(mask)
        self.assertAlmostEqual(top, 40, delta=2)
        self.assertAlmostEqual(width, 140, delta=6)
        self.assertAlmostEqual(centre, 200, delta=6)

    def test_head_framing_zooms_in(self):
        mask = Image.new("L", (800, 900), 0)
        d = ImageDraw.Draw(mask)
        d.ellipse((330, 60, 470, 240), fill=255)
        d.polygon([(150, 900), (250, 300), (550, 300), (650, 900)], fill=255)
        shoulders = portrait.auto_crop(mask, 80, 45, "shoulders")
        head = portrait.auto_crop(mask, 80, 45, "head")
        self.assertLess(head[2] - head[0], (shoulders[2] - shoulders[0]) * 0.6)
        self.assertLess(head[3], 300)  # hair to chin: stops above the shoulders
        with self.assertRaisesRegex(config.ConfigError, "shoulders"):
            config.framing({"framing": "torso"})

    def test_head_found_without_a_visible_neck_or_with_clutter(self):
        # bowed head: the shoulder rises into the head with no neck gap, plus a stray
        # object (a laptop corner, a sign) off to the left at head height
        mask = Image.new("L", (800, 600), 0)
        d = ImageDraw.Draw(mask)
        d.ellipse((380, 60, 540, 240), fill=255)                          # head, 160 wide
        d.polygon([(460, 200), (700, 260), (760, 600), (300, 600)], fill=255)  # shoulder/back
        d.rectangle((40, 120, 120, 300), fill=255)                        # clutter
        top, width, centre = portrait.head_span(mask)
        self.assertAlmostEqual(top, 60, delta=3)
        self.assertAlmostEqual(width, 160, delta=16)
        self.assertAlmostEqual(centre, 460, delta=16)


if __name__ == "__main__":
    unittest.main()
