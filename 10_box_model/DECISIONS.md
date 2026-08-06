# DECISIONS.md — Module 10: The Box Model

Source file: `box_model.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### `box-sizing` is read and branched on BEFORE content width/height are computed

**(a) Forced by spec — this is the module's entire reason to exist.**
`box-sizing: content-box` (the default) defines the `width` property as
the size of the content area alone — padding and border are added on top.
`box-sizing: border-box` redefines the SAME property to mean the size of
content+padding+border combined — so content width has to be back-solved
by subtracting padding and border from it. These aren't two ways of
computing the same number; they're two different definitions of what the
`width` number *refers to*. There is no valid order that computes content
width first and applies box-sizing after — the box-sizing decision has to
gate which formula even runs. `resolve()`'s `if box_sizing ==
"border-box"` branch exists precisely because of this.

### `border-width` is treated as one uniform value on all four sides

**(c) Our convention — explicit scope-out.** Real CSS lets each border
edge have an independent width (`border-top-width`, etc.). This module's
`_edges()` helper has a `uniform_key` parameter specifically to model
border as "one number, all four sides" for now, while padding and margin
already support independent per-side values (`padding-top` etc.) — a
deliberate asymmetry, named here so it isn't mistaken for an oversight.
A later module could extend `border` to four independent values using the
exact same `_edges()` shape padding and margin already use.

### `width: auto` resolves to `content_width = 0.0`, not a "real" auto-fit size

**(b) External contract, explicitly deferred — not solved incorrectly.**
An element's actual auto-computed width depends on its *containing
block's* available width (e.g. "fill the rest of the parent's width") —
information this module doesn't have, because it operates on one style
dict in isolation with no knowledge of the layout tree around it. Rather
than guess or approximate, `resolve()` returns exactly `0.0` for `auto`
and the code comment says so explicitly. Module 11, which walks the tree
and therefore knows each box's containing block, is where `auto` gets
correctly resolved. Test case 5's assertion exists specifically to keep
this boundary honest rather than silently wrong.

### Only bare numbers and `px` units are parsed; anything else becomes 0.0
    silently

**(c) Our convention — explicit scope-out.** Real CSS lengths can be
`%`, `em`, `rem`, `vw`, `vh`, and more, several of which (like `%`) also
depend on the containing block, same as `auto` does. Supporting only
`px` keeps this module's arithmetic self-contained and independently
testable; any other unit falling back to `0.0` rather than raising is a
deliberate "don't crash on real-world CSS this course doesn't model,"
the same philosophy Module 6 applied to malformed HTML and Module 7
applied to unrecognized at-rules.

### `EdgeSizes.horizontal`/`.vertical` and `Box`'s box-width properties are
    each defined purely in terms of the previous layer

**(c) Our convention, chosen so the "expand outward one layer at a time"
mental model is literally visible in the code, not just the diagram.**
`border_box_width` is written as `padding_box_width + border.horizontal`,
not recomputed from `content_width` directly — so the code's own
structure mirrors the box model's actual nested-layers definition
(content, wrapped by padding, wrapped by border, wrapped by margin) one
property at a time.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | `box-sizing` branch gates content-size computation | (a) forced by spec — the module's core point |
| 2 | Border width uniform on all 4 sides, unlike padding/margin | (c) explicit scope-out, deliberately asymmetric |
| 3 | `auto` resolves to exactly `0.0`, not approximated | (b) correctly deferred to Module 11 |
| 4 | Only `px` and bare numbers parsed; other units silently become 0 | (c) explicit scope-out |
| 5 | Each box layer defined in terms of the layer inside it | (c) convention mirroring the spec's own model |

## What We Proved

Given IDENTICAL declared width, padding, border, and margin values, the
box model correctly produced two DIFFERENT content widths purely based
on `box-sizing` (300px vs. 250px) — and, critically, `border-box`'s
result satisfied its defining property exactly: the computed border-box
width equalled the declared `300px` precisely, byte-for-byte the same
number that was typed in the stylesheet. `content-box`'s margin box
correctly expanded to 370px (300 content + 40 padding + 10 border + 20
margin), confirming each layer's arithmetic composes correctly. And
`width: auto` was confirmed to stop at exactly `0.0` rather than silently
guessing a wrong "real" value. See `tutorial.html` section 06 for the
full, unedited output. Module 11 takes this box's dimensions and finally
gives it a position on the page — including correctly resolving the
`auto` case this module deliberately left alone.
