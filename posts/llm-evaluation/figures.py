"""Figures for "Stop Vibe-Checking". Build: uv run figkit build llm-evaluation"""

from figkit import Figure

# ---------------------------------------------------------------------------
# The three-step error analysis loop
# ---------------------------------------------------------------------------

loop = Figure(
    "error-analysis-loop",
    640,
    330,
    alt=(
        "The error analysis loop: collect real or synthetic queries, then 1. generate traces by running "
        "each query through the system, 2. open coding: note the first failure in each trace, 3. axial "
        "coding: cluster the failures into failure mode families, then iterate from the start."
    ),
)
W = 250
LEFT, RIGHT = 160, 480
TOP, BOTTOM = 85, 245
start = loop.card("Collect queries", "real or synthetic", LEFT, TOP, W, hue="blue")
traces = loop.card("Generate traces", "run each query through the system\nand capture every step", RIGHT, TOP, W, hue="amber", badge="1")
open_coding = loop.card("Open coding", "note the first failure\nin each trace", RIGHT, BOTTOM, W, hue="green", badge="2")
axial = loop.card("Axial coding", "cluster the failures into\nfailure mode families", LEFT, BOTTOM, W, hue="pink", badge="3")
loop.arrow(start, traces)
loop.arrow(traces, open_coding)
loop.arrow(open_coding, axial)
loop.arrow(axial, start, label="Iterate", color="blue", width=2.4, label_side=-1, label_color="blue", label_size=13)

# ---------------------------------------------------------------------------
# Why clustering production queries did not work
# ---------------------------------------------------------------------------

attempts = Figure(
    "query-classification",
    640,
    430,
    alt=(
        "Two ways to classify production queries. Tried: define query classes plus an 'Other' bucket and "
        "classify with GPT-4, but most queries land in 'Other', which defeats the purpose. Considered: "
        "fine-tune a BERT classifier, but every new class found in 'Other' means retraining it, a "
        "maintenance nightmare."
    ),
)
COL_W = 296
L_X, R_X = 16, 328
L_C, R_C = L_X + COL_W / 2, R_X + COL_W / 2
CARD_W = 248
attempts.frame(L_X, 12, COL_W, 406, title="Tried: LLM classifier")
attempts.frame(R_X, 12, COL_W, 406, title="Considered: fine-tuned BERT", dashed=True)

define = attempts.card("Define query classes", "plus an 'Other' bucket", L_C, 88, CARD_W, hue="blue")
classify = attempts.card("Classify with GPT-4", "one label per query", L_C, 188, CARD_W, hue="amber")
attempts.arrow(define, classify)

# Where the queries ended up: a bar split between the classes and 'Other'.
BAR_Y, BAR_H = 268, 26
bar_left, bar_w = L_C - CARD_W / 2, CARD_W
split = bar_left + bar_w * 0.18
classes_seg = attempts.node("", (bar_left + split) / 2, BAR_Y, hue="neutral", w=split - bar_left, h=BAR_H, radius=6)
other_seg = attempts.node("'Other'", (split + bar_left + bar_w) / 2, BAR_Y, hue="red", w=bar_left + bar_w - split, h=BAR_H, radius=6, size=12.5)
attempts.text("classes", bar_left + (split - bar_left) / 2, BAR_Y + 26, size=11.5, color="muted", weight=500)
attempts.text("most queries", (split + bar_left + bar_w) / 2, BAR_Y + 26, size=11.5, color="red", weight=500)
attempts.arrow(classify, (L_C, BAR_Y - BAR_H / 2))
problem = attempts.card("Most queries land in 'Other'", "which defeats the purpose", L_C, 364, CARD_W, hue="red", style="strong", badge="!")
attempts.arrow((L_C, BAR_Y + 38), problem, gap=3)

bert = attempts.card("Fine-tune a BERT classifier", "on the defined classes", R_C, 88, CARD_W, hue="teal")
new_class = attempts.card("A new class shows up", "for example in the 'Other' queries", R_C, 188, CARD_W, hue="neutral")
attempts.arrow(bert, new_class)
problem2 = attempts.card("Retrain for every new class", "a maintenance nightmare", R_C, 364, CARD_W, hue="red", style="strong", badge="!")
attempts.arrow(new_class, problem2)

FIGURES = [loop, attempts]
