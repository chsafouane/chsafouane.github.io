"""Figures for "Things I wish I'd known about uv". Build: uv run figkit build uv-lessons"""

from figkit import Figure

FILE_X = 40        # left edge of the file column
FILE_W = 176
VALUE_X = 292      # left edge of the "what it holds" column
ROWS = [58, 168, 278]

chain = Figure(
    "uv-chain",
    640,
    330,
    alt=(
        "The two steps that link uv's files: resolve turns the ranges in pyproject.toml "
        "(pandas>=3.0.5) into exact pins in uv.lock (pandas 3.0.5 with hashes and markers), "
        "and install turns uv.lock into packages in .venv (pandas and numpy in site-packages)."
    ),
)
chain.title("File", FILE_X, 14)
chain.title("What it holds", VALUE_X, 14)
files = []
for (name, hue, value), y in zip(
    [
        ("pyproject.toml", "blue", "pandas>=3.0.5"),
        ("uv.lock", "amber", "pandas 3.0.5 + hashes + markers"),
        (".venv", "green", "pandas/ and numpy/ in site-packages"),
    ],
    ROWS,
):
    node = chain.node(name, FILE_X, y, hue=hue, family="mono", size=14, w=FILE_W, h=46, anchor="start")
    held = chain.node(value, VALUE_X, y, style="ghost", family="mono", size=13, weight=400, h=40, anchor="start")
    chain.link(node, held, color="soft", dashed=True)
    files.append(node)
chain.arrow(files[0], files[1], label="resolve", label_side=1, label_offset=12, label_size=13)
chain.arrow(files[1], files[2], label="install", label_side=1, label_offset=12, label_size=13)

FIGURES = [chain]
