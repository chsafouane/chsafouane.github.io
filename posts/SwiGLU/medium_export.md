# Why does SwiGLU work?

**Author:** Safouane Chergui
**Date:** 2026-01-14
**Categories:** Python, NLP, Deep Learning

---

The goal of this blog post is to explain why modern LLM architectures use `SwiGLU` as the activation function for the feed-forward part and have moved away from `ReLU`.

**Table of contents**
- Q1: Why do we need activation functions at all?
- Q2: What's wrong with ReLU?
- Q3: What is the Swish activation function?
- Q4: What are Gated Linear Units (GLU)?
- Q5: What is SwiGLU then?
- Final note

---

# Q1: Why do we need activation functions at all?

Consider this: a neural network is essentially a series of matrix multiplications. If we stack linear layers without any activation function:

![formula](https://latex.codecogs.com/png.latex?y%20%3D%20W_3%28W_2%28W_1%20x%29%29)

This simplifies to:

![formula](https://latex.codecogs.com/png.latex?y%20%3D%20%28W_3%20W_2%20W_1%29%20x%20%3D%20W_%7Bcombined%7D%20x)

No matter how many layers you stack, it's still just a linear transformation. The network can only learn linear relationships.

Activation functions introduce **non-linearity**, allowing the network to approximate complex, non-linear functions. This is the foundation of deep learning's expressive power.

Now, if you have a hard time mentally visualizing the impact of applying activation functions, I highly advise you to watch [the section 3 of this video](https://youtu.be/5_qrxVq1kvc?list=PL80I41oVxglKcAHllsU0txr3OuTTaWX2v&t=1693) from Alfredo Canziani's Deep Learning course. It will help you build a great intuition!

---

# Q2: What's wrong with ReLU?

`ReLU` literally revolutionized deep learning:

![formula](https://latex.codecogs.com/png.latex?%5Ctext%7BReLU%7D%28x%29%20%3D%20%5Cmax%280%2C%20x%29)

It's simple, fast, and solves the vanishing gradient problem that is a problem with functions like `sigmoid` or `tanh`.

While people usually list problems that might be encountered when `ReLU` is used like the *dying neuron problem*, these problems are either theoretical or can be well managed most of the time with techniques used in neural networks nowadays (batch normalization, adaptive learning weights, etc)

---

# Q3: What is the Swish activation function?

Now, before moving to SwiGLU, we'll look at an activation function **Swish** that is part of **SwiGLU**

![formula](https://latex.codecogs.com/png.latex?%5Ctext%7BSwish%7D%28x%29%20%3D%20x%20%5Ccdot%20%5Csigma%28x%29%20%3D%20%5Cfrac%7Bx%7D%7B1%20%2B%20e%5E%7B-x%7D%7D)

Swish is a 'self-gated' activation function: the input `x` is multiplied by its own sigmoid `σ(x)`, which acts as a **gate** that controls how much of the input passes through.

Looking at how the gate behaves:
- When `x` is very negative: `σ(x) ≈ 0`, so the gate is **closed** (suppresses the output)
- When `x` is very positive: `σ(x) ≈ 1`, so the gate is **fully open** (passes the input through almost unchanged)

Despite the bit more complicated formula, `Swish` has a very similar behavior to `ReLU`.

![Activation Functions: Output Comparison of ReLU & Swish](https://chsafouane.github.io/posts/SwiGLU/All%20you%20need%20to%20know%20about%20SwiGLU_files/figure-html/cell-2-output-1.png)

### Is Swish better than ReLU?

Empirically, `Swish` is found to work better than `ReLU` but like many things in deep learning, we don't know for sure why `Swish` works better, but here are the key differences:

**1. No hard gradient cutoff**

Looking at the plot above, the key difference is how they handle negative inputs:

- **ReLU**: Hard cutoff at zero
  - When `x < 0`: output = 0 & gradient = 0 (exactly)
  - This is the dying neuron problem (though as mentioned in Q2, it's often manageable with modern techniques like BatchNorm)

- **Swish**: Smooth, gradual approach to zero
  - For negative `x`: gradient approaches zero asymptotically but never exactly hits zero for finite values
  - Neurons can theoretically always receive updates (though updates may be negligible for very negative inputs)

**2. Smoothness**

`ReLU` has a discontinuity at `x = 0` (derivative jumps from 0 to 1). `Swish` is infinitely differentiable everywhere, which means that the gradient landscape is smooth. Whether this smoothness contributes to the performance of `Swish` is not 100% clear but it's plausible that this helps with optimization

![Gradient Comparison: Hard Cutoff vs Smooth Decay](https://chsafouane.github.io/posts/SwiGLU/All%20you%20need%20to%20know%20about%20SwiGLU_files/figure-html/cell-3-output-1.png)

---

# Q4: What are Gated Linear Units (GLU)?

Now, this is our last component before getting to `SwiGLU`. Let's talk about **GLU**.

![formula](https://latex.codecogs.com/png.latex?%5Ctext%7BGLU%7D%28x%2C%20W%2C%20V%2C%20b%2C%20c%29%20%3D%20%28xW%20%2B%20b%29%20%5Codot%20%5Csigma%28xV%20%2B%20c%29)

Where:
- `x` is the input
- `W, V` are weight matrices
- `b, c` are bias vectors
- `⊙` is element-wise multiplication
- `σ` is the sigmoid function

The first thing that you should note is that `GLU` uses a gating mechanism and is somehow similar to `Swish` in that manner. The difference is that instead of applying the same transformation (identity) to all features and then gating with a fixed function (sigmoid), GLU uses two separate linear projections:

1. `xW + b`: this just takes the input & transforms it. It is usually called the *content path*
2. `σ(xV + c)`: this second part says how much of the content of each feature should pass through and for that, it's called the *gate path*

So, `GLU` can really be thought of as a generalization of `Swish`

### Why is multiplicative gating powerful?

The element-wise multiplication `⊙` allows *the gate* to select which element of *the content* to let pass through. The gate can completely suppress certain features (when `σ(xV + c) ≈ 0`) while fully passing through others (when `σ(xV + c) ≈ 1`).

### Concrete example of gating

Let suppose we have a 4-dim vector `x`

![formula](https://latex.codecogs.com/png.latex?x%20%3D%20%5B1.0%2C%20-0.5%2C%202.0%2C%200.3%5D)

GLU applies 2 transformations to this same input:

1. A transformation to the content through the content path: `xW + b`. Let us say that it produces `[2.0, -1.5, 3.0, 0.5]`
2. A 2nd transformation that's supposed to play the role of the gate: `σ(xV + c)`. Let us say that it produces `[0.9, 0.1, 0.95, 0.05]`

The GLU output is their element-wise product:

![formula](https://latex.codecogs.com/png.latex?%5Ctext%7BGLU%20output%7D%20%3D%20%5B2.0%20%5Ctimes%200.9%2C%20%5C%3B%5C%3B%20-1.5%20%5Ctimes%200.1%2C%20%5C%3B%5C%3B%203.0%20%5Ctimes%200.95%2C%20%5C%3B%5C%3B%200.5%20%5Ctimes%200.05%5D)

![formula](https://latex.codecogs.com/png.latex?%3D%20%5B1.8%2C%20%5C%3B%5C%3B%20-0.15%2C%20%5C%3B%5C%3B%202.85%2C%20%5C%3B%5C%3B%200.025%5D)

This means that:
- **Feature 1**: Content is positive (2.0), gate is high (0.9) → passes through strongly (1.8)
- **Feature 2**: Content is negative (-1.5), gate is low (0.1) → blocked (-0.15)
- **Feature 3**: Content is positive (3.0), gate is very high (0.95) → fully passes (2.85)
- **Feature 4**: Content is small (0.5), gate is very low (0.05) → suppressed (0.025)

This allows the network to learn complex decision rules: "for inputs like `x`, amplify feature 1 and 3, but suppress features 2 and 4."

![GLU Visualization: Content, Gate, and Output](https://chsafouane.github.io/posts/SwiGLU/All%20you%20need%20to%20know%20about%20SwiGLU_files/figure-html/cell-4-output-1.png)

---

# Q5: What is SwiGLU then?

Now we have all the pieces. `SwiGLU` (Swish-Gated Linear Unit) simply combines Swish and GLU:

![formula](https://latex.codecogs.com/png.latex?%5Ctext%7BSwiGLU%7D%28x%2C%20W%2C%20V%29%20%3D%20%5Ctext%7BSwish%7D%28xW%29%20%5Codot%20xV)

That's it. Instead of using sigmoid for the gate (like in GLU), it uses Swish. That's why it's called **Swi**sh + **GLU**.

So what does each part of the formula do? Well, it's exactly the same logic as GLU as what changes is just the gating function.

- `Swish(xW)`: The **gate** - decides how much of each feature passes through
- `xV`: The **content** - the actual information being transmitted
- `⊙`: Element-wise multiplication - applies the gate to the content

![SwiGLU Visualization](https://chsafouane.github.io/posts/SwiGLU/All%20you%20need%20to%20know%20about%20SwiGLU_files/figure-html/cell-5-output-1.png)

### Why does SwiGLU work so well?

Empirically, SwiGLU outperforms other activation functions in LLMs (even though not sure about VLMs for now). But why? Here's the intuition:

**1. Multiplicative interactions create feature combinations**

This is the key insight. Consider what each architecture computes:

**Standard FFN** (ReLU/GELU): `output = activation(xW₁) @ W₂`

Each output dimension is a weighted sum of activated features. The activation is applied *element-wise*—features don't interact with each other inside the activation.

**SwiGLU FFN**: `output = (Swish(xW) ⊙ xV) @ W₂`

The element-wise multiplication `⊙` creates **products between the two paths**. If we denote `g = Swish(xW)` and `c = xV`, then output dimension `i` before the final projection is `gᵢ × cᵢ`.

Here's why this matters: both `gᵢ` and `cᵢ` are linear combinations of input features (before the Swish). Their product contains **cross-terms** like `xⱼ × xₖ`. The network can learn `W` and `V` such that certain input feature combinations are amplified or suppressed.

**Analogy**: This is similar to why attention is powerful. Attention computes `softmax(QKᵀ)V`, where the `QKᵀ` product captures interactions between query and key features. SwiGLU brings a similar multiplicative expressiveness to the FFN.

**2. Why not use sigmoid in the gate instead of Swish?**

GLU uses sigmoid: `σ(xW) ⊙ xV`. The problem with the `sigmoid` is that it saturates. For large positive or negative inputs, `σ(x) ≈ 1` or `σ(x) ≈ 0`, and the gradient `∂σ/∂x ≈ 0`. The gate becomes "frozen."

Swish doesn't saturate for positive inputs—it grows approximately linearly (just like `ReLU`). This implies that:
- Gradients flow better through the gate path
- The gate can modulate rather than just switch on/off

**3. Smoothness**

Another thing is that SwiGLU is infinitely differentiable & this smoothness likely helps optimization stability.

---

# Final note

SwiGLU's power comes from its **gating mechanism** & **multiplicative interactions**. By splitting the input into two paths and multiplying them, the network can learn which feature combinations matter—similar to how attention captures interactions through `QKᵀ`.

Combined with Swish's non-saturating gradients, this makes SwiGLU particularly effective for large models.
