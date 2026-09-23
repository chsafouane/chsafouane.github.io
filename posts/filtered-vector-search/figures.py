"""Figures for "Why filtering breaks your vector search". Build: uv run figkit build filtered-vector-search"""

from figkit import Figure, Stepper

BRAND_HUE = {"Apple": "green", "Google": "blue", "Sony": "indigo"}
BRAND_OF = {"A": "Apple", "B": "Apple", "E": "Apple", "C": "Google", "D": "Google", "G": "Google", "F": "Sony", "H": "Sony", "I": "Sony"}

# Positions in "embedding space": the brands sell similar products, so their
# points are interleaved. The same layout is used by every graph figure.
POS = {
    "A": (120, 118), "F": (300, 104), "C": (520, 118),
    "B": (190, 222), "H": (362, 228), "D": (450, 222),
    "E": (110, 326), "I": (290, 338), "G": (520, 326),
}
BRAND_EDGES = [("A", "B"), ("A", "E"), ("B", "E"), ("C", "D"), ("C", "G"), ("D", "G"), ("F", "H"), ("F", "I"), ("H", "I")]
SIMILARITY_EDGES = [("A", "F"), ("F", "C"), ("B", "H"), ("H", "D"), ("E", "I"), ("I", "G"), ("B", "G")]
NODE = 40


def point(fig, name, style="solid", dy=0):
    x, y = POS[name]
    return fig.node(name, x, y + dy, hue=BRAND_HUE[BRAND_OF[name]], style=style, shape="circle", w=NODE, size=15, weight=600)


def legend(fig, y, extra=()):
    """Brand colors and edge kinds, in one row at the bottom."""
    x = 24
    for brand in ("Apple", "Google", "Sony"):
        fig.node("", x + 7, y, hue=BRAND_HUE[brand], shape="circle", w=14)
        fig.text(brand, x + 20, y, size=12.5, anchor="start", color="muted", weight=500)
        x += 80
    x += 14
    fig.link((x, y), (x + 28, y), weight="thin")
    fig.text("similarity edge", x + 36, y, size=12.5, anchor="start", color="muted", weight=500)
    x += 140
    fig.link((x, y), (x + 28, y), weight="thick", color="green")
    fig.text("brand edge", x + 36, y, size=12.5, anchor="start", color="muted", weight=500)
    for label, draw in extra:
        x += 112
        draw(x, y)
        fig.text(label, x + 22, y, size=12.5, anchor="start", color="muted", weight=500)


# ---------------------------------------------------------------------------
# One graph per brand
# ---------------------------------------------------------------------------

subgraphs = Figure(
    "brand-subgraphs",
    640,
    250,
    alt=(
        "Three small graphs, one per brand: Apple links A, B and E; Google links C, D and G; "
        "Sony links F, H and I."
    ),
)
TRIANGLE = [(58, 78), (138, 128), (62, 182)]
for index, (brand, names) in enumerate([("Apple", "ABE"), ("Google", "CDG"), ("Sony", "FHI")]):
    fx = 16 + index * 208
    subgraphs.frame(fx, 16, 192, 218, title=brand, hue=BRAND_HUE[brand])
    nodes = []
    for name, (dx, dy) in zip(names, TRIANGLE):
        nodes.append(subgraphs.node(name, fx + dx + 8, 16 + dy, hue=BRAND_HUE[brand], shape="circle", w=NODE, size=15, weight=600))
    for a, b in [(0, 1), (0, 2), (1, 2)]:
        subgraphs.link(nodes[a], nodes[b], weight="thick", color=BRAND_HUE[brand])

# ---------------------------------------------------------------------------
# The merged graph: similarity edges plus brand edges
# ---------------------------------------------------------------------------

merged = Figure(
    "merged-graph",
    640,
    430,
    alt=(
        "One merged graph. Thin similarity edges link neighbors across brands (A-F, F-C, B-H, H-D, E-I, "
        "I-G, and the direct Apple-Google edges A-C and B-G); thick brand edges link each brand's points "
        "(A, B, E for Apple; C, D, G for Google; F, H, I for Sony)."
    ),
)
merged.frame(16, 16, 608, 364, title="Merged graph: similarity + brand edges")
nodes = {name: point(merged, name) for name in POS}
for a, b in SIMILARITY_EDGES:
    merged.link(nodes[a], nodes[b])
merged.link(nodes["A"], nodes["C"], bend=-0.23)
for a, b in BRAND_EDGES:
    merged.link(nodes[a], nodes[b], weight="thick", color=BRAND_HUE[BRAND_OF[a]])
legend(merged, 404)

# ---------------------------------------------------------------------------
# The same graph after filtering brand IN ('Apple', 'Google')
# ---------------------------------------------------------------------------

filtered = Figure(
    "filtered-graph",
    640,
    430,
    alt=(
        "The merged graph after filtering on Apple and Google. The Sony points F, H and I are removed "
        "with their edges. Brand edges keep Apple (A, B, E) and Google (C, D, G) connected internally, "
        "and the direct similarity edges A-C and B-G still connect Apple to Google."
    ),
)
filtered.frame(16, 16, 608, 364, title="After filtering: brand IN ('Apple', 'Google')")
kept = {}
for name in POS:
    if BRAND_OF[name] == "Sony":
        point(filtered, name, style="muted")
    else:
        kept[name] = point(filtered, name)
filtered.link(kept["A"], kept["C"], bend=-0.23, color="text", weight="thin")
filtered.link(kept["B"], kept["G"], color="text", weight="thin")
for a, b in BRAND_EDGES:
    if a in kept and b in kept:
        filtered.link(kept[a], kept[b], weight="thick", color=BRAND_HUE[BRAND_OF[a]])
filtered.text("A–C and B–G survive", 320, 170, size=12.5, color="muted", weight=500, halo=True)


def removed_marker(x, y):
    filtered.node("", x + 7, y, style="muted", shape="circle", w=14)


legend(filtered, 404, extra=[("removed", removed_marker)])

# ---------------------------------------------------------------------------
# Pre-filtering: removing nodes cuts the only path
# ---------------------------------------------------------------------------


def pre_filtering(fig, step):
    y = 128
    fig.title("HNSW graph", 24, 18)
    apple_style = "strong" if step == 3 else "solid"
    apple = fig.node("Apple Earbuds", 110, y, hue="green", style=apple_style, shape="pill", w=150, h=44)
    google = fig.node("Google Earbuds", 530, y, hue="blue", shape="pill", w=150, h=44)
    if step == 1:
        sony = fig.node("Sony Earbuds", 320, y, hue="indigo", shape="pill", w=150, h=44)
        fig.link(apple, sony, weight="thick", color="edge")
        fig.link(sony, google, weight="thick", color="edge")
        fig.text("the only path goes through Sony", 320, y + 54, size=12.5, color="muted", weight=500)
    else:
        fig.node("Sony Earbuds", 320, y, style="muted", shape="pill", w=150, h=44)
        fig.node("brand IN ('Apple', 'Google')", 320, 44, style="ghost", family="mono", size=12.5, weight=400, h=34)
        fig.text("filter", 320, 18, size=11, color="muted", weight=600, upper=True, tracking=0.08)
        fig.text("removed", 320, y + 40, size=12.5, color="muted", weight=500)
    if step == 3:
        fig.text("search starts here", 110, y - 48, size=12.5, color="green", weight=600)
        fig.arrow((110, y - 38), apple, color="green", gap=3)
        fig.icon("warning", 530, y + 48, 17)
        fig.text("unreachable", 530, y + 74, size=13, color="red", weight=600)


pre = Stepper(
    "pre-filtering",
    640,
    232,
    alt="Why pre-filtering fails.",
    captions=[
        "In the HNSW graph, the only path from Apple Earbuds to Google Earbuds goes through Sony Earbuds.",
        "Pre-filtering keeps Apple and Google only, so Sony Earbuds and its edges disappear.",
        "The search starts from Apple Earbuds and can no longer reach Google Earbuds.",
    ],
    draw=pre_filtering,
)

# ---------------------------------------------------------------------------
# Post-filtering: the filter throws away most of the top K
# ---------------------------------------------------------------------------

RESULTS = [("#1 Sony", "indigo", False), ("#2 Samsung", "neutral", False), ("#3 Apple", "green", True), ("#4 JBL", "neutral", False), ("#5 Bose", "neutral", False)]


def post_filtering(fig, step):
    xs = [64 + i * 112 for i in range(5)]
    cx = xs[2]  # the column of the one result that matches the filter
    query = fig.node("query: wireless earbuds, K = 5", cx, 34, style="ghost", family="mono", size=12.5, weight=400, h=36)
    fig.title("HNSW top 5", 16, 84)
    chips = []
    for (label, hue, keep), x in zip(RESULTS, xs):
        style = "solid" if step == 1 or keep else "muted"
        chips.append(fig.node(label, x, 124, hue=hue if style == "solid" else "neutral", style=style, shape="pill", w=100, h=38, size=13))
    fig.arrow(query, (cx, 98), gap=4)  # into the row as a whole, not one result
    if step >= 2:
        filter_chip = fig.node("brand IN ('Apple', 'Google')", cx, 196, style="ghost", family="mono", size=12.5, weight=400, h=34)
        fig.text("filter", filter_chip.left - 14, 196, size=11, color="muted", weight=600, upper=True, tracking=0.08, anchor="end")
        fig.arrow(chips[2], filter_chip, gap=4, color="green")
    if step == 3:
        returned = fig.node("returned: #3 Apple", cx, 268, hue="green", style="strong", shape="pill", w=190, h=40, size=13.5)
        fig.arrow(filter_chip, returned, gap=4)
        fig.node("#6 Google", 514, 226, style="muted", shape="pill", w=88, h=30, size=12)
        fig.node("#9 Apple", 608 - 39, 262, style="muted", shape="pill", w=78, h=30, size=12)
        fig.text("closer matches ranked\nbeyond K: never seen", 540, 190, size=12, color="muted", weight=500)


post = Stepper(
    "post-filtering",
    640,
    300,
    alt="Why post-filtering fails.",
    captions=[
        "HNSW returns the 5 products closest to the query.",
        "The filter keeps Apple and Google only, so 4 of the 5 results are thrown away.",
        "Only 1 result is returned. Closer Apple and Google earbuds ranked beyond K were never retrieved.",
    ],
    draw=post_filtering,
)

FIGURES = [pre, post, subgraphs, merged, filtered]
