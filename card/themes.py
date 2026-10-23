"""Colour presets. Each theme has a dark and a light palette; GitHub shows whichever matches the viewer.

Every palette needs: bg (card background), text (portrait and plain text), key (row labels),
value (row values), dots (leaders, dividers, faint accents).
"""

PRESETS = {
    "github": {
        "dark": {"bg": "#161b22", "text": "#c9d1d9", "key": "#ffa657", "value": "#a5d6ff", "dots": "#616e7f"},
        "light": {"bg": "#f6f8fa", "text": "#24292f", "key": "#953800", "value": "#0a3069", "dots": "#c2cfde"},
    },
    "dracula": {
        "dark": {"bg": "#282a36", "text": "#f8f8f2", "key": "#ff79c6", "value": "#8be9fd", "dots": "#6272a4"},
        "light": {"bg": "#f8f8f2", "text": "#1f1f1f", "key": "#a3144d", "value": "#036a96", "dots": "#9ea2b8"},
    },
    "nord": {
        "dark": {"bg": "#2e3440", "text": "#d8dee9", "key": "#88c0d0", "value": "#a3be8c", "dots": "#4c566a"},
        "light": {"bg": "#eceff4", "text": "#2e3440", "key": "#5e81ac", "value": "#4c7a3d", "dots": "#a7b1c2"},
    },
    "gruvbox": {
        "dark": {"bg": "#282828", "text": "#ebdbb2", "key": "#fe8019", "value": "#b8bb26", "dots": "#665c54"},
        "light": {"bg": "#fbf1c7", "text": "#3c3836", "key": "#af3a03", "value": "#79740e", "dots": "#bdae93"},
    },
    "tokyo-night": {
        "dark": {"bg": "#1a1b26", "text": "#c0caf5", "key": "#bb9af7", "value": "#7dcfff", "dots": "#565f89"},
        "light": {"bg": "#e1e2e7", "text": "#3760bf", "key": "#9854f1", "value": "#007197", "dots": "#a1a6c5"},
    },
    "catppuccin": {
        "dark": {"bg": "#1e1e2e", "text": "#cdd6f4", "key": "#f5c2e7", "value": "#89b4fa", "dots": "#585b70"},
        "light": {"bg": "#eff1f5", "text": "#4c4f69", "key": "#ea76cb", "value": "#1e66f5", "dots": "#acb0be"},
    },
    "solarized": {
        "dark": {"bg": "#002b36", "text": "#93a1a1", "key": "#b58900", "value": "#2aa198", "dots": "#586e75"},
        "light": {"bg": "#fdf6e3", "text": "#586e75", "key": "#b58900", "value": "#268bd2", "dots": "#93a1a1"},
    },
    "monokai": {
        "dark": {"bg": "#272822", "text": "#f8f8f2", "key": "#f92672", "value": "#a6e22e", "dots": "#75715e"},
        "light": {"bg": "#fafafa", "text": "#272822", "key": "#c4144f", "value": "#5c8a00", "dots": "#b5b19c"},
    },
    "one-dark": {
        "dark": {"bg": "#282c34", "text": "#abb2bf", "key": "#e5c07b", "value": "#61afef", "dots": "#5c6370"},
        "light": {"bg": "#fafafa", "text": "#383a42", "key": "#986801", "value": "#4078f2", "dots": "#a0a1a7"},
    },
    "rose-pine": {
        "dark": {"bg": "#191724", "text": "#e0def4", "key": "#ebbcba", "value": "#9ccfd8", "dots": "#6e6a86"},
        "light": {"bg": "#faf4ed", "text": "#575279", "key": "#d7827e", "value": "#286983", "dots": "#9893a5"},
    },
}
