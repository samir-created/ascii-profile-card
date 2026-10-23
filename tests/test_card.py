"""Run with: python -m unittest discover -s tests"""
import contextlib
import copy
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

from PIL import Image, ImageDraw

import io
from unittest import mock

import yaml

from card import build, config, portrait, preview
from card.themes import PRESETS

ROOT = Path(__file__).resolve().parent.parent


def load():
    return config.load(ROOT / "config.yml")


def bust():
    """A head-and-shoulders shape on a transparent background, so no background removal is needed."""
    img = Image.new("RGBA", (400, 500), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((130, 40, 270, 200), fill=(60, 40, 30, 255))
    d.rectangle((175, 190, 225, 260), fill=(200, 150, 120, 255))
    d.polygon([(60, 500), (100, 270), (300, 270), (340, 500)], fill=(40, 40, 60, 255))
    return img


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
        settings = load()["portrait"] | {"crop": None, "columns": 40, "rows": 24}
        lines = portrait.to_ascii(bust(), settings)
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

    def test_a_tuft_of_hair_is_not_the_head(self):
        mask = Image.new("L", (800, 600), 0)
        d = ImageDraw.Draw(mask)
        d.ellipse((300, 100, 500, 340), fill=255)                         # head, 200 wide
        d.polygon([(420, 110), (440, 20), (452, 22), (440, 112)], fill=255)  # thin tuft, ~15 wide
        d.polygon([(120, 600), (220, 360), (580, 360), (680, 600)], fill=255)
        top, width, centre = portrait.head_span(mask)
        self.assertAlmostEqual(width, 200, delta=20)
        self.assertAlmostEqual(centre, 400, delta=16)

    # Each of these draws the mask background removal would give for an awkward photo:
    # a head 200 wide, centred at x=400, on shoulders, plus whatever makes the photo awkward.
    def awkward(self, extra, head=(300, 150, 500, 390)):
        mask = Image.new("L", (800, 700), 0)
        d = ImageDraw.Draw(mask)
        d.ellipse(head, fill=255)
        d.polygon([(120, 700), (220, 400), (580, 400), (680, 700)], fill=255)
        extra(d)
        return portrait.head_span(mask)

    def assertHead(self, found, top=None):
        self.assertAlmostEqual(found[1], 200, delta=20)
        self.assertAlmostEqual(found[2], 400, delta=16)
        if top is not None:
            self.assertAlmostEqual(found[0], top, delta=8)

    def test_a_raised_hand_is_not_the_head(self):
        def hand(d):
            d.rectangle((600, 70, 640, 450), fill=255)  # arm, up from the shoulder
            d.ellipse((580, 20, 660, 100), fill=255)    # hand, above the head
        self.assertHead(self.awkward(hand), top=150)

    def test_something_left_above_the_head_is_ignored(self):
        self.assertHead(self.awkward(lambda d: d.ellipse((60, 10, 180, 110), fill=255)), top=150)  # a lamp

    def test_a_bun_stays_in_the_picture(self):
        found = self.awkward(lambda d: d.ellipse((350, 70, 450, 170), fill=255))
        self.assertHead(found, top=70)  # measured as the head, cropped from the top of the bun

    def test_a_shoulder_rising_on_its_own_is_not_the_head(self):
        # head tilted away, so the far shoulder shows up as its own wide, sloping shape
        found = self.awkward(lambda d: d.polygon([(530, 260), (560, 260), (800, 700), (520, 700)], fill=255),
                             head=(300, 150, 500, 390))
        self.assertHead(found, top=150)

    def test_head_cut_off_by_the_top_of_the_photo(self):
        self.assertHead(self.awkward(lambda d: None, head=(300, -100, 500, 220)), top=0)

    def test_no_person_explains(self):
        mask = Image.new("L", (800, 600), 0)
        ImageDraw.Draw(mask).ellipse((10, 10, 40, 40), fill=255)  # a speck
        with self.assertRaisesRegex(SystemExit, "Couldn't find a person"):
            portrait.head_span(mask)

    def test_palette_png_keeps_its_transparent_background(self):
        img = bust().convert("RGBA").quantize(16)
        img.info["transparency"] = img.getpixel((0, 0))
        out = portrait.cut_out(img, "no-such-model")  # would fail if it went to background removal
        self.assertEqual(out.getpixel((0, 0))[3], 0)
        self.assertEqual(out.getpixel((200, 120))[3], 255)

    def test_sideways_phone_photos_are_turned_upright(self):
        with tempfile.TemporaryDirectory() as tmp:
            exif = Image.Exif()
            exif[0x0112] = 6  # "rotate 90° to view"
            bust().rotate(90, expand=True).save(Path(tmp) / "photo.png", exif=exif)
            (Path(tmp) / "config.yml").write_text("portrait:\n  photo: photo.png\n", encoding="utf-8")
            seen = []
            with mock.patch.object(portrait, "to_ascii", lambda image, s: seen.append(image.size) or ["x"]), \
                    mock.patch("sys.argv", ["portrait", str(Path(tmp) / "config.yml")]), \
                    contextlib.redirect_stdout(io.StringIO()):
                portrait.main()
            self.assertEqual(seen, [(400, 500)])

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


FORM = """### Your photo

<img width="800" alt="me" src="https://github.com/user-attachments/assets/1234-abcd" />

### Title

ada@lovelace

### Details

OS: Analytical Engine
# Contact
Email: ada@example.com: yes

### Theme

nord

### Layout

stacked (portrait on top, reads better on phones)

### Info style

arrows (› key → value)

### Portrait characters

blocks ( ░▒▓█ )

### Framing

shoulders (head and shoulders)

### Frame

window (terminal title bar)

### Animations

- [X] rain
- [ ] thoughts
- [x] cursor

### Invert

- [ ] invert
"""




class PreviewTest(unittest.TestCase):
    def test_form_answers_become_a_config(self):
        base = (ROOT / "config.yml").read_text(encoding="utf-8")
        base = base.replace("  # crop: [120, 40, 900, 1000]", "  crop: [120, 40, 900, 1000]")
        base = base.replace("\ninfo:", '\nheader:\n  - "Hi, I\'m the repo owner"\n\ninfo:')
        text = preview.to_config(preview.parse_form(FORM), base)
        raw = yaml.safe_load(text)
        self.assertEqual(raw["title"], "ada@lovelace")
        self.assertEqual(raw["info"], [{"OS": "Analytical Engine"}, {"section": "Contact"}, {"Email": "ada@example.com: yes"}])
        self.assertEqual(raw["style"], {"theme": "nord", "layout": "stacked", "info_style": "arrows", "charset": "blocks",
                                        "invert": False, "frame": "window", "animations": ["rain", "cursor"]})
        self.assertNotIn("crop", raw["portrait"])
        self.assertNotIn("header", raw)
        self.assertEqual(raw["portrait"]["framing"], "shoulders")
        # everything the form doesn't ask about is left exactly as written, comments and all
        self.assertIn('  symbols: [\n    "∑", "π",', text)
        self.assertIn("  theme: nord           # github, dracula", text)
        self.assertIn("# Each entry is one row of the card:", text)
        self.assertEqual(raw["thoughts"], yaml.safe_load(base)["thoughts"])

    def test_missing_keys_are_added(self):
        text = preview.to_config(preview.parse_form(FORM), "title: x\n")
        raw = yaml.safe_load(text)
        self.assertEqual((raw["style"]["theme"], raw["portrait"]["framing"]), ("nord", "shoulders"))

    def test_only_uploaded_photos_are_fetched(self):
        self.assertEqual(preview.photo_url("![me](https://github.com/user-attachments/assets/42)"),
                         "https://github.com/user-attachments/assets/42")
        for bad in ("![x](https://evil.example/a.png)", "![x](http://github.com/user-attachments/assets/1)",
                    "![x](https://github.com/someone/repo/raw/main/a.png)", "no photo"):
            with self.assertRaises(preview.PreviewError, msg=bad):
                preview.photo_url(bad)

    def test_too_many_rows_explain(self):
        with self.assertRaisesRegex(preview.PreviewError, "40"):
            preview.info_rows("\n".join(f"k{i}: v" for i in range(41)))

    def test_form_choices_match_the_builder(self):
        form = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/preview.yml").read_text(encoding="utf-8"))
        fields = {f["attributes"]["label"]: f["attributes"] for f in form["body"] if f["type"] != "markdown"}

        def names(label):  # the option names, without their descriptions
            return [preview.choice({label: o}, label, None) for o in fields[label]["options"]]

        self.assertEqual(names("Theme"), list(PRESETS))
        self.assertEqual(names("Layout"), list(config.LAYOUTS))
        self.assertEqual(names("Info style"), list(config.INFO_STYLES))
        self.assertEqual(names("Portrait characters"), list(config.CHARSETS))
        self.assertEqual(sorted(names("Framing")), sorted(config.FRAMINGS))
        self.assertEqual(names("Frame"), list(config.FRAMES))
        self.assertEqual([o["label"] for o in fields["Animations"]["options"]], list(config.ANIMATIONS))
        self.assertIn("Your photo", fields)

    def test_issue_to_cards(self):
        png = io.BytesIO()
        bust().save(png, "PNG")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(preview, "download", return_value=png.getvalue()):
            out = Path(tmp)
            cards = preview.make(FORM, out)
            self.assertEqual(sorted(cards), ["dark_mode.svg", "light_mode.svg"])
            self.assertFalse((out / "photo.jpg").exists())
            svg = (out / "dark_mode.svg").read_text(encoding="utf-8")
            self.assertIn("ada@lovelace", svg)
            self.assertIn('class="rain"', svg)
            self.assertIn("__BASE__/dark_mode.svg", preview.comment(out, cards, "https://github.com/o/r/generate"))

    def test_replies_cant_ping_or_escape(self):
        self.assertNotIn("@someone", preview.failed("style.theme: '@someone' is not one of github"))
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.yml").write_text("title: a```b\n", encoding="utf-8")
            text = preview.comment(Path(tmp), [], "u")
            self.assertIn("````yaml\ntitle: a```b\n````", text)


if __name__ == "__main__":
    unittest.main()
