# DECISIONS.md — Module 27: HTML Entity Encoding

Source file: `entity_encoding.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Encoding looks up each character INDEPENDENTLY (a dict per-character
    scan), not a chain of sequential `str.replace()` calls

**(c) Our convention — chosen specifically to make an entire bug class
structurally impossible, not just avoided by careful ordering.** A
sequential-replace implementation has to get its ORDER right (`&` must
be replaced before `<`/`>`, or the `&` those introduce gets re-encoded —
see Case 4). Iterating the input once and looking up each character's
replacement independently in `ENTITY_MAP` has no ordering to get wrong
at all — every character is judged once, against the original input,
never against text a previous replacement step already produced.

### `naive_wrong_order_encode` is included and its bug is real, reproduced,
    not hypothetical

**(c) Noted because it's a genuine, common real-world bug pattern, not
an invented cautionary tale.** Chaining `.replace()` calls in the wrong
order is exactly the kind of code that looks correct, passes a casual
glance, and produces subtly wrong output only for inputs containing the
specific character (`&`) whose replacement happens to be involved in
another replacement's output. Case 4 reproduces the exact double-encoding
this causes.

### Verification runs BOTH the raw and the encoded payload through
    Module 5's REAL tokenizer, checking for an actual `StartTag` token

**(a) Forced by what "prevents markup" actually has to mean, and the
core methodological choice of this module.** Claiming an encoder
"prevents XSS" without ever checking what a real HTML tokenizer does
with its output is an assertion, not a proof. `has_real_tag()` calls
Module 5's unmodified `tokenize()` and looks for a genuine `StartTag`
token — the exact same check a real browser's parser would effectively
be performing. Case 1 proves the vulnerability is real (a raw payload
DOES produce a real `StartTag('script')`); Case 2 proves the fix is real
(the encoded version produces exactly one `Text` token, nothing else).

### Case 3 specifically tests forgetting to encode `<` versus forgetting
    to encode `>`, and reports a DIFFERENT result for each

**(a) Forced by HTML's own tokenization rules (Module 5), not a
coincidence.** A tag cannot begin without an actual `<` character —
Module 5's tokenizer only ever transitions out of `DATA` state into tag
parsing upon seeing one. A stray, un-encoded `>` in body text has no
special meaning to the tokenizer at all; it's just another character.
This means encoding `<` is the single most load-bearing character for
THIS specific context (preventing tag injection into body text) — a
real, non-obvious fact about HTML's actual grammar, verified directly
against the real tokenizer rather than asserted from general
"escape everything" advice.

### All five characters (`& < > " '`) are still encoded by
    `encode_html_entities`, even though Case 3 shows `>` alone isn't
    load-bearing for THIS context

**(b) External contract — forward-looking correctness, not redundancy.**
Body-text context is only ONE of several contexts untrusted data can end
up in. `"` and `'` matter enormously the moment the same value is placed
inside an HTML attribute instead (Module 28's subject) — encoding all
five here, rather than only the two that matter for body text
specifically, is what makes `encode_html_entities` safe to reuse as a
general-purpose HTML-text encoder rather than a context-specific
shortcut that would need to be re-derived per use site.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Per-character lookup, not sequential `.replace()` chaining | (c) eliminates an entire bug class structurally |
| 2 | The classic wrong-order double-encoding bug is reproduced, not just described | (c) real, common bug pattern |
| 3 | Verification checks Module 5's real tokenizer output, not just string content | (a) forced — this is what "prevents markup" means |
| 4 | Case 3 isolates `<` vs. `>` and gets a different, HTML-grammar-driven answer for each | (a) forced by Module 5's real tokenization rules |
| 5 | All five characters encoded, even though only `<` matters for THIS context | (b) forward-looking correctness for other contexts (Module 28) |

## What We Proved

A real `<script>alert(document.cookie)</script>` payload, run through
Module 5's real, unmodified tokenizer, produced a genuine
`StartTag('script')` token — the exact mechanism that would make a real
browser execute it. The same payload, run through `encode_html_entities`
first, produced exactly one `Text` token and nothing resembling a tag at
all. A follow-up test isolating `<` and `>` independently confirmed a
real, HTML-grammar-driven asymmetry: forgetting to encode `<` still lets
a real tag form, while forgetting `>` alone does not — because HTML
tokenization itself requires a literal `<` to begin parsing a tag. And a
classic sequential-replace ordering bug was reproduced and shown to
double-encode `&`, distinct from (but related to) the security question.
See `tutorial.html` section 06 for the full, unedited output. Module 28
takes this same principle into HTML ATTRIBUTE context, where the rules —
and the load-bearing characters — are different again.
