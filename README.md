<!-- ascii-profile-card:template-readme (the GitHub Action swaps this file for your card in a profile repo) -->
<h1 align="center">ascii-profile-card</h1>

<p align="center">
  A neofetch-style card for your GitHub profile, with <b>an ASCII portrait made from your photo</b><br>
  and ideas floating up out of your head. One config file. <b>No setup, nothing to install.</b> Free.
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="dark_mode.svg">
    <source media="(prefers-color-scheme: light)" srcset="light_mode.svg">
    <img alt="Example profile card" src="dark_mode.svg">
  </picture>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#customise-everything">Customise</a> ·
  <a href="#configuration-reference">Config reference</a> ·
  <a href="#run-it-locally">Run locally</a> ·
  <a href="#faq">FAQ</a> ·
  <a href="#credits">Credits</a>
</p>

---

## Quick start

> **No setup needed.** You don't need Python, a terminal or anything installed. Do it all in your browser on github.com.

1. **Use this template**: click **Use this template → Create a new repository**, and name it **exactly your GitHub username** (e.g. `octocat/octocat`). That's the repo GitHub shows on your profile.
2. **Make it yours**: upload your photo as `photo.jpg` (any photo works, since the background is removed for you), and edit `config.yml` (title, details, theme, animations; every option is [below](#configuration-reference)).
3. **Commit.** That's it. In a minute or two the included GitHub Action turns your photo into ASCII, builds the dark and light cards, and swaps this README for your card. Visit your profile.

Change anything later: edit `config.yml`, commit, and the card rebuilds.

<details>
<summary>Adding the card to a README you already have</summary>

If your profile README already has other content, the Action leaves it alone. Paste this where you want the card (replace `USERNAME` twice):

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/USERNAME/USERNAME/main/dark_mode.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/USERNAME/USERNAME/main/light_mode.svg">
  <img alt="My profile card" src="https://raw.githubusercontent.com/USERNAME/USERNAME/main/dark_mode.svg">
</picture>
```

Full `raw.githubusercontent.com` links load in about 0.1 s; relative paths go through a slow redirect.
</details>

---

## Customise everything

Every option lives under `style:` in `config.yml`, and they all combine freely. Each image below is a real card made by this repo (`python -m card.gallery` renders them all).

### Themes

`style.theme`: 10 presets, each with a dark and a light palette. You can also use `custom` with your own colours.

<table>
<tr>
<td align="center"><img src="examples/theme-github.svg" width="270"><br><code>github</code></td>
<td align="center"><img src="examples/theme-dracula.svg" width="270"><br><code>dracula</code></td>
<td align="center"><img src="examples/theme-nord.svg" width="270"><br><code>nord</code></td>
</tr>
<tr>
<td align="center"><img src="examples/theme-gruvbox.svg" width="270"><br><code>gruvbox</code></td>
<td align="center"><img src="examples/theme-tokyo-night.svg" width="270"><br><code>tokyo-night</code></td>
<td align="center"><img src="examples/theme-catppuccin.svg" width="270"><br><code>catppuccin</code></td>
</tr>
<tr>
<td align="center"><img src="examples/theme-solarized.svg" width="270"><br><code>solarized</code></td>
<td align="center"><img src="examples/theme-monokai.svg" width="270"><br><code>monokai</code></td>
<td align="center"><img src="examples/theme-one-dark.svg" width="270"><br><code>one-dark</code></td>
</tr>
<tr>
<td align="center"><img src="examples/theme-rose-pine.svg" width="270"><br><code>rose-pine</code></td>
</tr>
</table>

<details>
<summary><b>Custom colours</b></summary>

```yaml
style:
  theme: custom
themes:
  dark:  {bg: "#0b0f14", text: "#e6edf3", key: "#ff7b72", value: "#79c0ff", dots: "#484f58"}
  light: {bg: "#ffffff", text: "#1f2328", key: "#cf222e", value: "#0550ae", dots: "#afb8c1"}
```

`bg` is the card background, `text` the portrait and plain text, `key` the row labels, `value` the row values, and `dots` the leaders, dividers and faint accents. Every palette you list becomes its own `<name>_mode.svg`.
</details>

### Layouts

`style.layout`

<table>
<tr>
<td align="center" rowspan="2"><img src="examples/layout-stacked.svg" width="270"><br><code>stacked</code>: portrait on top, details below.<br>Narrower, so it reads better on phones.</td>
<td align="center"><img src="examples/layout-side.svg" width="270"><br><code>side</code>: portrait left (default)</td>
</tr>
<tr>
<td align="center"><img src="examples/layout-portrait-right.svg" width="270"><br><code>portrait-right</code></td>
</tr>
</table>

### Info styles

`style.info_style`

<table>
<tr>
<td align="center"><img src="examples/info-dots.svg" width="270"><br><code>dots</code>: <code>Key ...... value</code></td>
<td align="center"><img src="examples/info-aligned.svg" width="270"><br><code>aligned</code>: clean columns</td>
<td align="center"><img src="examples/info-arrows.svg" width="270"><br><code>arrows</code>: <code>› key → value</code></td>
</tr>
</table>

### Portrait character sets

`style.charset` redraws your portrait with different characters. Set `style.invert: true` to flip light and dark for a glowing look.

<table>
<tr>
<td align="center"><img src="examples/charset-classic.svg" width="270"><br><code>classic</code> <code>.,:;-=+*#%@</code></td>
<td align="center"><img src="examples/charset-blocks.svg" width="270"><br><code>blocks</code> <code>░▒▓█</code></td>
<td align="center"><img src="examples/charset-binary.svg" width="270"><br><code>binary</code> <code>01</code></td>
</tr>
<tr>
<td align="center"><img src="examples/charset-dots.svg" width="270"><br><code>dots</code> <code>.·•●</code></td>
<td align="center"><img src="examples/charset-dense.svg" width="270"><br><code>dense</code> (70 shades)</td>
<td align="center"><img src="examples/charset-hex.svg" width="270"><br><code>hex</code> <code>0-F</code></td>
</tr>
<tr>
<td align="center" colspan="3"><img src="examples/invert.svg" width="270"><br><code>invert: true</code></td>
</tr>
</table>

### Frame

`style.frame`

<table>
<tr>
<td align="center"><img src="examples/layout-side.svg" width="270"><br><code>plain</code> (default)</td>
<td align="center"><img src="examples/frame-window.svg" width="270"><br><code>window</code>: terminal title bar</td>
</tr>
</table>

### Animations

`style.animations` takes any mix of these, or `[]` for a still card. All motion is plain SVG/CSS (GitHub runs no scripts), and it switches off for visitors who prefer reduced motion. Open an image on its own to see it move.

<table>
<tr>
<td align="center"><img src="examples/animation-thoughts.svg" width="270"><br><code>thoughts</code>: symbols float up out of your head</td>
<td align="center"><img src="examples/animation-rain.svg" width="270"><br><code>rain</code>: faint falling characters</td>
<td align="center"><img src="examples/animation-cursor.svg" width="270"><br><code>cursor</code>: prompt with a blinking cursor</td>
</tr>
<tr>
<td align="center"><img src="examples/animation-none.svg" width="270"><br><code>[]</code>: still</td>
</tr>
</table>

The floating symbols are yours to pick: maths, your stack, your jokes.

```yaml
thoughts:
  rise_seconds: [6, 9]   # each symbol takes 6–9 s to float up and fade
  symbols: ["∑", "π", "<?php", "useState()", "npm i", "def", "LLM", "∇loss"]
```

### Header: anything above the details

`header:` adds your own lines just above the details: a greeting, a tagline, a quote, an ASCII banner, anything. Each line can set its `color` (`text`, `key`, `value` or `dots`), `size` in px, `bold` and `align` (`left`, `center` or `right`).

<table>
<tr>
<td align="center"><img src="examples/header-greeting.svg" width="270"><br><b>greeting</b></td>
<td align="center"><img src="examples/header-banner.svg" width="270"><br><b>ASCII banner</b></td>
<td align="center"><img src="examples/header-quote.svg" width="270"><br><b>quote</b></td>
</tr>
</table>

```yaml
header:
  - text: "Hi, I'm Samir 👋"        # greeting
    color: key
    size: 22
    bold: true
  - "Building plugins, agents & dev tools"   # a plain string works too

  - art: |                           # ASCII art, kept exactly as written
      ┌─┐┌─┐┌┬┐┬┬─┐
      └─┐├─┤││││├┬┘
      └─┘┴ ┴┴ ┴┴┴└─
    color: value

  - text: "“Talk is cheap. Show me the code.”"   # quote
    align: center
  - text: "— Linus Torvalds"
    color: dots
    size: 13
    align: center
```

Generate banner text with any figlet tool (e.g. [patorjk.com/software/taag](https://patorjk.com/software/taag)) and paste it under `art: |`. If a line is too wide for the details column, the build prints a warning telling you by how much.

### Mix and match

<table>
<tr>
<td align="center"><img src="examples/combo-hacker.svg" width="270"><br><b>hacker</b><br><sub>monokai · binary · window · rain + cursor</sub></td>
<td align="center"><img src="examples/combo-minimal.svg" width="270"><br><b>minimal</b><br><sub>nord · aligned · dots · still</sub></td>
<td align="center"><img src="examples/combo-retro.svg" width="270"><br><b>retro</b><br><sub>gruvbox · blocks · arrows · window</sub></td>
</tr>
</table>

```yaml
# the "hacker" card
style:
  theme: monokai
  charset: binary
  frame: window
  animations: [rain, cursor]
```

---

## Configuration reference

```yaml
title: you@yourname            # first line of the details

header:                        # optional lines just above the details
  - "plain text"
  - text: "styled"             # color: text|key|value|dots  size: px  bold: true  align: left|center|right
    color: key
  - art: |                     # ASCII art, spacing kept
      /\_/\

info:                          # one entry per row
  - OS: Me                     # "Key ......... value"
  - ""                         # empty spacer row
  - section: Contact           # "- Contact ---------" divider
  - Email: you@example.com

portrait:
  photo: photo.jpg             # jpg or png; background removed automatically
  ascii: ascii.txt             # generated portrait; you can also hand-edit it
  columns: 80                  # portrait width in characters
  rows: 45                     # portrait height in characters
  framing: shoulders           # shoulders (head and shoulders) | head (hair to chin, bigger face)
  # crop: [left, top, right, bottom]   # pixels; overrides framing
  gamma: 1.4                   # higher = lighter skin, lower = darker
  edges: 2.5                   # outline strength (glasses, jawline, hair)
  ramp: " .,:;-=+*#%@"         # characters from lightest to darkest
  model: u2net_human_seg       # background-removal model, downloaded once (167 MB)

thoughts:
  rise_seconds: [6, 9]
  symbols: ["∑", "π", "λ"]

layout:
  info_width: 64               # characters per info row
  info_offset: 30              # px lower than centred beside the portrait

style:
  theme: github                # github dracula nord gruvbox tokyo-night catppuccin solarized monokai one-dark rose-pine custom
  layout: side                 # side | portrait-right | stacked
  info_style: dots             # dots | aligned | arrows
  charset: classic             # classic | blocks | binary | dots | dense | hex
  invert: false
  frame: plain                 # plain | window
  animations: [thoughts]       # thoughts, rain, cursor in any mix, or []
```

A typo gets a clear message instead of a broken card, for example `config.yml: style.layout: 'diagonal' is not one of side, portrait-right, stacked`.

### Tips for a great portrait

- **Glasses invisible?** Thin frames vanish at 80 columns. Raise `edges` (e.g. `4`), or trace your frames darker in the photo before uploading.
- **Face too dark or too light?** Nudge `gamma` (`1.1`–`2.0`).
- **Head too small or too big?** Set `crop` by hand, or change `columns`/`rows`.
- **Want your exact look?** `ascii.txt` is plain text. Edit it by hand and the Action keeps your edits until you upload a new photo.

---

## Run it locally

*Optional.* Only needed if you'd rather build on your own machine, or want to work on the code.

With `make` (macOS and Linux), it's one command:

```sh
make
```

The first run sets everything up. After that it only redoes what changed (a new photo or new portrait settings redraw the portrait; anything else just rebuilds the cards) and opens both cards in your browser. `make help` lists the extras (`make test`, `make gallery`, `make reset`).

The first photo conversion downloads the background-removal model once (~170 MB), and later runs reuse it.

Or run the Python commands directly:

```sh
pip install -r requirements.txt          # pillow, pyyaml
pip install -r requirements-photo.txt    # rembg, only for turning a photo into ASCII

python -m card.portrait    # photo.jpg  -> ascii.txt
python -m card.build       # config.yml -> dark_mode.svg, light_mode.svg
python -m card.gallery     # every style option -> examples/
python -m unittest discover -s tests
```

Already have a transparent PNG (background removed)? Then `card.portrait` doesn't need rembg at all.

## How it works

1. **`card/portrait.py`** removes the background with [rembg](https://github.com/danielgatis/rembg). It finds your head by following the outline down from the top of your hair, ignoring anything else in the photo (laptops, signs, people behind you). It then measures the head across the temples, so a bowed head or a raised shoulder doesn't throw it off. Then it crops to head and shoulders and converts to "ink-style" ASCII: dark areas (hair, glasses, beard) get the dense characters, and edges are boosted so features survive at 80 columns.
2. **`card/build.py`** lays out the portrait and info rows as SVG `<text>`, picks colours from the theme, and adds the animations as CSS keyframes inside the SVG. GitHub only allows motion that's built into the image file itself.
3. **`.github/workflows/build.yml`** reruns both on every change and commits the result. The portrait step only runs when the photo changed, so hand edits to `ascii.txt` survive.

## FAQ

**My card didn't update.** `raw.githubusercontent.com` caches files for about 5 minutes. Wait, then hard-refresh.

**The card is blank for a moment when my profile loads.** That's GitHub fetching the image. Use the full `raw.githubusercontent.com` links from [Quick start](#quick-start), not relative paths.

**Can I see the animation before pushing?** Open any `.svg` in your browser.

**Does it need my GitHub token or any secrets?** No. The Action only uses the repo's built-in token to commit the rebuilt cards.

## Credits

Huge shout-out to **[Andrew Grant (@Andrew6rant)](https://github.com/Andrew6rant)**. His [profile README](https://github.com/Andrew6rant/Andrew6rant), with its neofetch-style card, ASCII portrait and theme-aware `dark_mode.svg` / `light_mode.svg`, is what inspired this project. If you like the look, go give his repo a ⭐.

This project is a separate, from-scratch implementation; it doesn't include any of his code.

The layout itself goes back to [neofetch](https://github.com/dylanaraps/neofetch) by Dylan Araps, the terminal tool that made "ASCII art + system info" iconic.

Thanks as well to [rembg](https://github.com/danielgatis/rembg) for the background removal that turns any photo into a clean portrait.

## License

[MIT](LICENSE) © 2026 Samir Shrestha
