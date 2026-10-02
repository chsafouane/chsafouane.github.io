"""Figures and charts for "Things I learnt asking Jev 3,000 questions". Build: uv run figkit build jev-lessons

All numbers come from my runs against jev-1.13.0 (September 28 and 30, October 1, 2026), except the decomposition
figure (the phishing study's numbers).
"""

from figkit import Axis, Figure, Format, LineChart, Series, Table

# One state, isolated questions --------------------------------------------------------------------------------------

request = Figure(
    "jev-request",
    640,
    330,
    alt=(
        "A Jev request: one state, a support ticket about a failing Stripe integration, is read once and shared by "
        "three questions, a Choice, a Score and a Noul. Each question sees the state and its own text only, never "
        "the other questions, and returns its own typed answer: technical at 0.79, a frustration score of 1.01, and "
        "1.00 for urgency."
    ),
)
request.title("Read once", 40, 20)
request.title("Isolated questions", 236, 20)
request.title("Typed answers", 470, 20)
state = request.card(
    "State",
    "Stripe connection\nfailing for 3 days.\nHelp ASAP.",
    40,
    165,
    w=150,
    hue="amber",
    anchor="start",
)
QUESTIONS = [
    ("Choice: which team?", "technical 0.79", 70),
    ("Score: how frustrated?", "score 1.01", 165),
    ("Noul: is it urgent?", "yes 1.00", 260),
]
for label, answer, y in QUESTIONS:
    q = request.node(label, 236, y, hue="blue", w=190, h=44, anchor="start", size=13)
    a = request.node(answer, 470, y, hue="green", family="mono", w=130, h=40, anchor="start", size=13)
    request.arrow(state, q, via=[(212, y)])
    request.arrow(q, a)
request.text("Each question sees the state and its own text, never another question.", 320, 312, size=12,
             color="muted", anchor="middle")

# Banking77 automation curve, label names vs descriptions -----------------------------------------------------------

THRESHOLDS = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
# (share automated %, accuracy on the automated share %) on the 308 test messages, October 1, 2026
NAMES_ONLY = [(100.0, 82.1), (93.8, 84.1), (87.3, 85.9), (83.1, 87.1), (77.6, 88.7), (67.5, 92.3), (58.1, 95.5), (45.8, 96.5)]
DESCRIBED = [(100.0, 88.3), (95.8, 90.8), (94.2, 91.7), (91.2, 92.2), (86.4, 92.5), (76.9, 94.1), (71.8, 94.6), (61.7, 96.8)]

automation = LineChart(
    "banking77-automation",
    title="Option descriptions let Jev automate more at the same accuracy",
    sub="Each dot is one confidence threshold, from 0 (decide everything) to 0.99. "
    "Banking77, 308 held-out messages, 77 intents.",
    alt=(
        "Line chart of accuracy against the share of messages automated, one dot per confidence threshold. With "
        "label names only, accuracy goes from 82.1% when automating everything to 96.5% when automating 45.8%. "
        "With a one-line description per option and not_for boundaries, it goes from 88.3% to 96.8% when "
        "automating 61.7%. To be right at least 92% of the time, names only automate 67.5% of messages "
        "(threshold 0.90) and descriptions 91.2% (threshold 0.70)."
    ),
    x=Axis((40, 100), ticks=[40, 50, 60, 70, 80, 90, 100], title="Messages automated", format=Format(decimals=1, suffix="%"),
           tick_format=Format(suffix="%")),
    y=Axis((80, 100), ticks=[80, 85, 90, 95, 100], title="Accuracy on automated messages",
           format=Format(decimals=1, suffix="%"), tick_format=Format(suffix="%")),
    series=[
        Series("Label names only", NAMES_ONLY[::-1], color="person", dots=True, label="Names only"),
        Series("With descriptions", DESCRIBED[::-1], color=1, dots=True, label="Descriptions"),
    ],
    hover="nearest",
    table=Table(
        ["Confidence threshold", "Names only: automated", "Names only: accuracy", "Descriptions: automated",
         "Descriptions: accuracy"],
        [[f"{t:.2f}", f"{a[0]:.1f}%", f"{a[1]:.1f}%", f"{b[0]:.1f}%", f"{b[1]:.1f}%"]
         for t, a, b in zip(THRESHOLDS, NAMES_ONLY, DESCRIBED)],
    ),
)

# One broad question or five small ones (numbers from the phishing study, not my runs) ---------------------------------

decomposition = Figure(
    "decomposition",
    640,
    330,
    alt=(
        "Diagram of the phishing study's two setups. One email goes either to one broad question, \"Is this email "
        "phishing?\", which got 62.6% of 2,000 emails right, or to five small yes/no questions: does it ask for a "
        "password or payment, does the sender not match, does it promise a reward, does it push you to act now, does "
        "it push a link or attachment. A logistic regression trained on 1,000 labeled emails combines the five answers, "
        "and that setup got 95.0% right."
    ),
)
decomposition.title("One email", 30, 20)
decomposition.title("Questions", 210, 20)
decomposition.title("Combined", 452, 20)
decomposition.title("Accuracy", 565, 20)
email = decomposition.card(
    "Email",
    "Confirm your\npassword within\n24 hours or your\naccount closes.",
    30,
    175,
    w=130,
    hue="amber",
    anchor="start",
)
# One broad question: an elbow from the card's right edge up to the top row.
broad = decomposition.node("Is this email phishing?", 210, 62, hue="blue", w=200, h=40, anchor="start", size=13)
decomposition.arrow((160, 140), broad, via=[(185, 140), (185, 62)])
decomposition.arrow(broad, decomposition.node("62.6%", 565, 62, hue="red", family="mono", w=70, h=40, anchor="start", size=13))
# Five small questions, framed as one group: one arrow in, one arrow out.
SMALL_QUESTIONS = [
    "Asks for a password or payment?",
    "Sender doesn't match?",
    "Promises a reward?",
    "Pushes you to act now?",
    "Pushes a link or attachment?",
]
small = [decomposition.node(label, 210, 125 + 35 * i, hue="blue", w=200, h=28, anchor="start", size=12)
         for i, label in enumerate(SMALL_QUESTIONS)]
decomposition.frame_around(small, pad=10)
decomposition.arrow((160, 195), (195, 195))
model = decomposition.node("Logistic\nregression", 452, 195, hue="neutral", w=92, h=56, anchor="start", size=12)
decomposition.arrow((420, 195), model)
decomposition.arrow(model, decomposition.node("95.0%", 565, 195, hue="green", family="mono", w=70, h=40, anchor="start", size=13))
decomposition.text("Accuracy on 2,000 emails in the phishing study. The model was trained on 1,000 labeled emails.", 320, 312,
                   size=12, color="muted", anchor="middle")

# Same state, one extra option (09_added_option.py, first run, averages over 35 states) --------------------------------

added_option = Figure(
    "added-option",
    640,
    300,
    alt=(
        "Diagram: the same states, such as \"The refund bounced. The customer isn't sure which account they gave us.\", "
        "are sent to three versions of the payout question. Bars show the average probability of each option over all "
        "the states, and provider gets 0.00 in all three. With the 4 "
        "options: customer 0.56, unknown 0.39, bank 0.04. With weather added: customer 0.53, unknown 0.41, bank 0.05, "
        "weather 0.00. With details added: customer 0.31, details 0.23, unknown 0.44, bank 0.01."
    ),
)
added_option.title("Example state", 20, 18)
added_option.title("Question", 205, 18)
added_option.title("Average over all the states", 345, 18)
state_card = added_option.card(
    "State",
    "The refund bounced.\nThe customer isn't\nsure which account\nthey gave us.",
    20,
    150,
    w=150,
    hue="amber",
    anchor="start",
)
BAR_X, BAR_W = 345, 280
SEGMENT_HUES = {"customer": "indigo", "details": "pink", "unknown": "neutral", "bank": "teal"}
ROWS = [  # (question, y, segments left to right; customer first so its shrinking lines up)
    ("4 options", 70, [("customer", 0.56), ("unknown", 0.39), ("bank", 0.04)]),
    ("4 + weather", 150, [("customer", 0.53), ("unknown", 0.41), ("bank", 0.05)]),
    ("4 + details", 230, [("customer", 0.31), ("details", 0.23), ("unknown", 0.44), ("bank", 0.01)]),
]
for label, y, segments in ROWS:
    question_node = added_option.node(label, 205, y, hue="blue", w=110, h=44, anchor="start", size=13)
    if y == 150:
        added_option.arrow((170, 150), question_node)
    else:
        added_option.arrow((170, 150), question_node, via=[(186, 150), (186, y)])
    added_option.arrow(question_node, (BAR_X - 6, y))
    x = BAR_X
    for name, p in segments:
        w = max(p * BAR_W, 4)  # at least 4 px, so bank's 0.01 still shows
        text = f"{name}\n{p:.2f}" if w >= 60 else ""
        added_option.node(text, x, y, hue=SEGMENT_HUES[name], w=w, h=44, anchor="start", size=11, radius=3)
        x += w
added_option.text("weather: 0.00", BAR_X + BAR_W, 150 + 32, size=11, color="muted", anchor="end")
added_option.text("The thin piece at the end of each bar is bank (0.04, 0.05, 0.01). provider got 0.00 in all three.", 320, 285, size=12,
                  color="muted", anchor="middle")

FIGURES = [request, decomposition, added_option, automation]
