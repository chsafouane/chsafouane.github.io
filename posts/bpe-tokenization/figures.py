"""Figures for "Byte Pair Encoding Tokenization". Build: uv run figkit build bpe-tokenization"""

from figkit import Figure

pipeline = Figure(
    "nlp-pipeline",
    700,
    150,
    alt=(
        "How text reaches an NLP model: the text 'Hello there' goes into the tokenizer, which outputs "
        "the numerical ids (tokens) 15496 and 612; the NLP model turns them into a prediction."
    ),
)
Y = 64
GAP = 34  # horizontal space taken by each arrow

text = pipeline.node("Hello there", 16, Y, style="ghost", family="mono", size=13.5, weight=400, h=40, anchor="start")
tokenizer = pipeline.node("Tokenizer", text.right + GAP, Y, hue="orange", h=44, anchor="start")
ids_left = tokenizer.right + GAP
ids = pipeline.chips(["15496", "612"], ids_left, Y, hue="teal", anchor="start", h=34)
model = pipeline.node("NLP model", ids[-1].right + GAP, Y, hue="indigo", h=44, anchor="start")
prediction = pipeline.node("Prediction", model.right + GAP, Y, hue="green", style="outline", h=44, anchor="start")

pipeline.arrow(text, tokenizer, gap=4)
pipeline.arrow(tokenizer, ids[0], gap=4)
pipeline.arrow(ids[-1], model, gap=4)
pipeline.arrow(model, prediction, gap=4)

for label, x in [
    ("text", text.x),
    ("numerical ids\n(tokens)", (ids[0].left + ids[-1].right) / 2),
]:
    pipeline.text(label, x, Y + 36, size=12, color="muted", weight=500, valign="top")

if prediction.right > pipeline.width - 16:
    raise ValueError(f"nlp-pipeline overflows: {prediction.right:.0f}px > {pipeline.width - 16}px")

FIGURES = [pipeline]
