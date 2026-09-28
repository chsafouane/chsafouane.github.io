"""Charts for "Why does SwiGLU work ?". Build: uv run figkit build why-swiglu-works

The curves are computed from their formulas, so the charts are exact:
ReLU(x) = max(0, x), Swish(x) = x·σ(x), and SwiGLU with the identity
projections xW = xV = x used in the post.
"""

import numpy as np
from figkit import (
    Axis,
    Band,
    BarChart,
    Bars,
    Format,
    LineChart,
    Note,
    Panels,
    Ref,
    Series,
    Table,
)

X = np.round(np.linspace(-4, 4, 161), 2)  # steps of 0.05
TABLE_X = [-4, -3, -2, -1.3, -1, -0.5, 0, 0.5, 1, 2, 3, 4]


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def swish(x):
    return x * sigmoid(x)


def points(x, y):
    return list(zip(x.tolist(), y.tolist()))


x_axis = Axis((-4, 4), ticks=[-4, -3, -2, -1, 0, 1, 2, 3, 4], title="Input x", name="x", format=Format(decimals=2),
              tick_format=Format(decimals=0))

swish_min_x = X[np.argmin(swish(X))]

relu_vs_swish = LineChart(
    "relu-vs-swish",
    title="ReLU and Swish give almost the same output",
    sub="They differ only for negative inputs (shaded): ReLU returns exactly 0, Swish dips a little below 0 "
        "and comes back. Hover over or tap the chart to read both values.",
    alt=(
        "Line chart of ReLU and Swish for x from -4 to 4. ReLU is zero for every negative input, while Swish "
        "dips slightly below zero, to about -0.28 near x = -1.3, and then follows ReLU closely for positive inputs."
    ),
    x=x_axis,
    y=Axis((-1, 4), ticks=[-1, 0, 1, 2, 3, 4], title="Output f(x)", format=Format(decimals=2), tick_format=Format()),
    series=[
        Series("ReLU", points(X, np.maximum(0, X)), color="person", label="ReLU"),
        Series("Swish", points(X, swish(X)), color=1, label="Swish"),
    ],
    bands=[Band((-4, 0), "negative inputs")],
    refs=[Ref(y=0), Ref(x=0)],
    notes=[Note(f"Swish dips to {Format(decimals=2)(swish(swish_min_x))}", swish_min_x, swish(swish_min_x), anchor="middle", dy=18)],
    table_x=TABLE_X,
)

relu_grad = [(x, 0.0) for x in X if x < 0] + [None] + [(x, 1.0) for x in X if x > 0]
swish_grad = swish(X) + sigmoid(X) * (1 - swish(X))

relu_vs_swish_gradient = LineChart(
    "relu-swish-gradient",
    title="ReLU's gradient jumps, Swish's changes smoothly",
    sub="The gradient of ReLU is exactly 0 for every negative input and jumps to 1 at x = 0. "
        "The gradient of Swish only approaches 0 for very negative inputs.",
    alt=(
        "Line chart of the gradients of ReLU and Swish. The ReLU gradient jumps from 0 to 1 at x = 0, while the "
        "Swish gradient changes smoothly, dips slightly below 0 around x = -2.4 and only approaches 0 for very "
        "negative inputs."
    ),
    x=x_axis,
    y=Axis((-0.25, 1.25), ticks=[0, 0.5, 1], title="Gradient f′(x)", format=Format(decimals=2),
           tick_format=Format(decimals=1)),
    series=[
        Series("ReLU′", relu_grad, color="person", label="ReLU′"),
        Series("Swish′", points(X, swish_grad), color=1, label="Swish′"),
    ],
    bands=[Band((-4, 0), "negative inputs")],
    refs=[Ref(y=0)],
    table_x=[-4, -3, -2, -1, -0.5, 0.5, 1, 2, 3, 4],
)

features = ["A", "B", "C", "D"]
content = np.array([2.0, -1.5, 3.0, 0.5])
gate = np.array([0.9, 0.1, 0.95, 0.05])
output = content * gate

glu_valve = Panels(
    "glu-valve",
    title="The gate decides how much of each feature passes",
    sub="The content path xW carries the information, the gate σ(xV) is between 0 (closed) and 1 (open), "
        "and GLU multiplies them feature by feature: B and D are nearly blocked.",
    alt=(
        "Three bar charts over four features A to D. Content xW: 2.0, -1.5, 3.0 and 0.5. Gate σ(xV): 0.9, 0.1, "
        "0.95 and 0.05. Output, their product: 1.8, -0.15, 2.85 and 0.025, so the features with a closed gate "
        "are blocked."
    ),
    panels=[
        BarChart("content", title="Content: xW", categories=features, series=[Bars("xW", content.tolist(), color=1)],
                 y=Axis((-2, 3.5), ticks=[-2, -1, 0, 1, 2, 3], format=Format(decimals=1), tick_format=Format()),
                 alt="Content", height=220),
        BarChart("gate", title="Gate: σ(xV)", categories=features, series=[Bars("σ(xV)", gate.tolist(), color=3)],
                 y=Axis((0, 1.2), ticks=[0, 0.5, 1], format=Format(decimals=2), tick_format=Format(decimals=1)),
                 alt="Gate", height=220),
        BarChart("output", title="Output: content × gate", categories=features,
                 series=[Bars("Output", output.tolist(), color=1)],
                 y=Axis((-2, 3.5), ticks=[-2, -1, 0, 1, 2, 3], format=Format(decimals=3, trim=True), tick_format=Format()),
                 alt="Output", height=220),
    ],
    table=Table(
        ["Feature", "Content xW", "Gate σ(xV)", "Output"],
        [[f, Format(decimals=1)(c), Format(decimals=2)(g), Format(decimals=3, trim=True)(o)]
         for f, c, g, o in zip(features, content, gate, output)],
    ),
)

swiglu_components = LineChart(
    "swiglu-components",
    title="SwiGLU multiplies the Swish gate by the content",
    sub="With the identity projections xW = xV = x, the output is Swish(x) × x: close to 0 for negative inputs, "
        "and growing like x² for positive ones.",
    alt=(
        "Line chart of SwiGLU and its two inputs for x from -4 to 4: the Swish gate, the linear content xV, and "
        "the SwiGLU output, which is their product and grows to about 15.7 at x = 4."
    ),
    x=x_axis,
    y=Axis((-4, 16), ticks=[-4, 0, 4, 8, 12, 16], title="Value", format=Format(decimals=2), tick_format=Format()),
    series=[
        Series("xV, the content", points(X, X), color="person", dash=True, label="xV"),
        Series("Swish(xW), the gate", points(X, swish(X)), color=1, label="Swish(xW)"),
        Series("SwiGLU output", points(X, swish(X) * X), color=2, width=2.5, label="SwiGLU"),
    ],
    refs=[Ref(y=0), Ref(x=0)],
    table_x=TABLE_X,
)

FIGURES = [relu_vs_swish, relu_vs_swish_gradient, glu_valve, swiglu_components]
