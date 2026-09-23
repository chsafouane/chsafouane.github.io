# figkit

figkit draws the blog's figures in the style of Jay Alammar's illustrated guides.
Figures are written in Python, rendered as a light and a dark SVG that match the site, and exported as PNG (and GIF for step-by-step figures) for cross-posting to Medium or Substack.

## Quick start

```bash
uv sync                                  # once: installs figkit (add --extra plots for matplotlib)
uv run figkit build                      # render every posts/<slug>/figures.py
uv run figkit build uv-lessons           # or only one post
```

In a post, show a figure or a step-by-step figure with the shortcodes from `_extensions/figkit`:

```markdown
{{< fig uv-chain >}}
{{< fig uv-chain "An optional caption in *Markdown*." >}}
{{< stepper pre-filtering >}}
```

Each post keeps its figure code in `posts/<slug>/figures.py`, which defines `FIGURES = [...]`.
`figkit build` writes the results to `posts/<slug>/assets/figures/`:

| File | Used by |
|---|---|
| `NAME-light.svg`, `NAME-dark.svg` | the site; the shortcode shows the one matching the color scheme |
| `NAME.png` | Medium and Substack (light version, 2x, white background) |
| `NAME.gif` | Medium and Substack, for steppers (all steps, looping) |
| `NAME.json` | the manifest the shortcode reads (size, alt text, step captions) |

Commit the generated files.
CI rebuilds the SVG files and manifests and fails if they differ from what is committed.

## Style rules

The goal is Jay Alammar's clarity: few shapes, generous space, one color per concept.

- **One hue per concept, everywhere.**
  Pick the hue for a concept once and reuse it in every figure of the post (in the vector search post: Apple is green, Google blue, Sony indigo).
  Suggested defaults across posts: inputs and queries `blue`, models and LLMs `indigo`, outputs and results `green`, data and files `amber`, tokens `teal`, problems `red`, everything else `neutral`.
- **Pastel fill, darker stroke of the same hue, dark text.**
  `style="solid"` does this; `strong` doubles the stroke for emphasis, `muted` (dashed, gray) marks removed or ignored things, `ghost` is a neutral container for code or values, `filled` is a saturated chip with page-colored text, `outline` keeps only the stroke.
- **Shapes:** rounded boxes (radius 10) for components, pills for items in a list, circles for graph nodes, cells for vectors, chips for tokens.
- **Lines:** arrows (`arrow`) show flow; edges (`link`) show relations, thick for "same group", thin for "similar", dashed for "removed".
- **Text:** Inter for labels, JetBrains Mono for code, tokens and file names.
  Group titles are small, uppercase and gray (`frame(title=...)`, `title(...)`).
- **Size:** design at the column width, 640 px wide (up to about 720 px).
  Keep labels at 12 px or more; figures scale down on phones, where readers can open them full size.

The colors come from `_brand.yml` (the hue base colors and the page colors).
`figkit palette` prints the derived colors; loading the palette fails if a derived color does not meet WCAG contrast (3:1 for shapes and lines, 4.5:1 for text), in either mode.

## Writing a figure

```python
from figkit import Figure

fig = Figure("uv-chain", 640, 330, alt="What the figure shows, in one or two sentences.")
lock = fig.node("uv.lock", 40, 168, hue="amber", family="mono", anchor="start")
venv = fig.node(".venv", 40, 278, hue="green", family="mono", anchor="start")
fig.arrow(lock, venv, label="install")

FIGURES = [fig]
```

Coordinates are CSS pixels at the figure's natural size, with (0, 0) at the top left.
Every figure needs alt text; it is used for the site and the exports.

### Drawing methods

| Method | Draws |
|---|---|
| `node(label, x, y, hue, style, shape, w, h, size, weight, family, anchor)` | a box, pill or circle sized to its label; returns it for arrows and links |
| `card(title, body, x, y, w, hue, style, badge)` | a box with a bold title, body text and an optional numbered badge |
| `chips(tokens, x, y, hue)` | a row of token chips; returns the chips |
| `cells(x, y, count, hue, labels=None, shades=None)` | a vector as a row of square cells, optionally with values or intensities |
| `frame(x, y, w, h, title, hue, dashed)` / `frame_around(nodes, title=...)` | a group frame with a small uppercase title |
| `arrow(a, b, label, color, via, bend)` | an arrow between nodes or points, through `via` points or bent |
| `link(a, b, weight, color, dashed, bend)` | an undirected edge (thin or thick) |
| `text(content, x, y, size, weight, color, anchor, valign)` / `title(...)` | free text; newlines split lines |
| `icon("warning", x, y)` | a warning sign |

Colors are given as roles: a hue name (`indigo`, `green`, `blue`, `orange`, `pink`, `teal`, `amber`, `red`, `neutral`) or `text`, `muted`, `edge`, `soft`.
Text that a font cannot draw raises an error instead of silently drawing boxes; the latin subsets of the site fonts cover English text and common symbols.

### Steppers

A stepper shows a figure in stages, the way Jay Alammar's animations build up a diagram.
Readers move through the steps with buttons or the arrow keys, or press play.

```python
from figkit import Stepper

def draw(fig, step):          # called once per step on a fresh canvas
    ...

FIGURES = [Stepper("pre-filtering", 640, 232, alt="Why pre-filtering fails.",
                   captions=["First step.", "Second step.", "Third step."], draw=draw)]
```

Keep every element that does not change at the same position in every step, so only the change moves.

### Plots

`Plot` renders a matplotlib figure in the site style (Inter, palette colors, transparent background) for both modes:

```python
from figkit import Plot

def draw(fig, p):
    ax = fig.add_subplot()
    ax.plot(x, y, label="Swish")        # the color cycle follows the figure hues
    ax.legend()

FIGURES = [Plot("swish", 640, 360, alt="...", draw=draw)]
```

It needs `uv sync --extra plots`.
`p` is the palette of the mode being drawn, for colors that must stay fixed (`p.hue("orange").stroke`).

## Keynote

Some figures are faster to draw by hand, which is how Jay Alammar works.
The Keynote kit keeps them consistent with code-drawn figures.

1. Install the fonts once: `brew install --cask font-inter font-jetbrains-mono`.
2. Install the palette once: `uv run figkit keynote --install`, then restart Keynote.
   The colors appear in the color picker, under Color Palettes, as `figkit`: `text`, `edge`, and a `fill`, `stroke` and `label` color for every hue.
3. Start from the component sheets in `tools/figkit/keynote/components/` (`nodes.svg`, `tokens.svg`, `lines.svg`, `frames.svg`).
   Drag a sheet onto a slide, then choose Format > Shapes and Lines > Break Apart to get native, editable Keynote shapes with the right colors, strokes and fonts.
4. Set the slide size to twice the figure size (for example 1280 × 660 for a 640 × 330 figure) and export with File > Export To > Images (PNG).
   For a step-by-step figure, draw one slide per step.
5. Bring the export into the post:

   ```bash
   uv run figkit import ~/Desktop/export/ --post uv-lessons --name my-figure --alt "..."
   uv run figkit import ~/Desktop/steps/ --post uv-lessons --name my-steps --alt "..." \
     --caption "First step." --caption "Second step."
   ```

   One PNG gives a figure, several give a stepper (in file-name order, one caption each).
   Use the same shortcodes in the post.

Keynote figures exist in light mode only, so the site shows them on a white card in dark mode.

## Commands

| Command | Does |
|---|---|
| `uv run figkit build [SLUG ...]` | render figures (`--no-raster` skips PNG and GIF, as CI does) |
| `uv run figkit palette` | print the figure palette and its contrast ratios |
| `uv run figkit keynote [--install]` | write the Keynote palette and component sheets |
| `uv run figkit import PNG... --post SLUG --name NAME --alt TEXT [--caption TEXT ...]` | bring PNG exports into a post |

PNG export needs `rsvg-convert` (`brew install librsvg`).
