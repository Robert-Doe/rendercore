# DECISIONS.md — Module 28: Attribute & URL-Scheme Encoding

Source file: `attribute_encoding.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

## Part A — Attribute breakout

### `render_attr_safe` reuses Module 27's `encode_html_entities` WHOLESALE,
    rather than a narrower, attribute-only encoder

**(c) Our convention — and the direct payoff of a decision flagged back
in Module 27's own DECISIONS.md.** A minimal attribute encoder only
strictly needs to escape the delimiter quote character in use (and `&`,
to stop double-decoding). Module 27 deliberately encoded all five
characters — including both quote types — even though only `<` mattered
for body-text context specifically. That forward-looking choice is what
makes reusing it here, unmodified, already correct: no new
attribute-specific logic had to be written at all.

### Verification checks the parsed `StartTag.attrs` DICT, not the raw
    HTML string

**(a) Forced by what "breakout" actually means, and this course's
established discipline (Modules 16, 20, 23, 24, 26, 27) of checking the
real downstream state, not a proxy for it.** A string-level check
(`"onmouseover" in unsafe_html`) would be true even in a WORLD where the
tokenizer somehow failed to treat it as a real attribute. Checking
`'onmouseover' in unsafe_tag.attrs` — the REAL parsed result from
Module 5's unmodified tokenizer — proves the injection is a genuine,
structural attribute, indistinguishable from one the page's own
developer wrote on purpose.

## Part B — URL scheme checking

### The "fixed" scheme check strips tab/CR/newline characters from
    ANYWHERE in the string, not just the ends

**(b) External contract — this matches real, documented browser
behavior, not a hypothetical hardening.** Per the WHATWG URL Standard,
browsers strip ASCII tab and newline characters from a URL string
UNCONDITIONALLY, from any position, before further processing it —
originally to tolerate URLs that got accidentally line-wrapped in HTML
source. This has a real, well-known security consequence: a scheme
check that only trims leading/trailing whitespace can be defeated by
hiding a tab in the MIDDLE of the word "javascript," because the browser
will still remove that tab before deciding the scheme is
`javascript:`. `is_dangerous_url_scheme`'s `re.sub(r"[\t\r\n]", "", url)`
mirrors this real browser behavior specifically so the check can't be
fooled by the exact same trick a real browser would still fall for if a
naive check were relied upon.

### `is_dangerous_url_scheme_NAIVE` is included and its bypass is
    demonstrated, not just asserted

**(c) Noted because it's a genuine class of real-world filter-bypass bug,
not an invented example.** `.strip()` only removes whitespace from the
very start and end of a string — it does nothing about a tab sitting in
the middle. Shipping the naive version alongside a live demonstration of
its bypass (Case 3) is more convincing, and more honestly instructive,
than describing the risk in prose without ever exploiting the flawed
version against itself.

### The dangerous-scheme list (`javascript:`, `vbscript:`, `data:`) is an
    explicit denylist, not derived from Module 2's URL parser

**(c) Our convention — explicit scope-out, and a deliberate choice not to
lean on the wrong tool.** Module 2's parser only recognizes `http`/`https`
and would reject `javascript:` for lacking `://` before ever reaching a
scheme check — it was built to parse URLs this course's browser actually
fetches, not to serve as a security filter for URLs a page merely
DISPLAYS as a link target. Building a small, purpose-specific denylist
here, rather than repurposing Module 2, keeps each piece doing the one
job it was actually designed for.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Attribute encoding reuses Module 27's encoder unmodified | (c) payoff of a forward-looking Module 27 decision |
| 2 | Verification checks the real parsed `attrs` dict, not raw strings | (a) forced — this is what "breakout" means |
| 3 | Scheme check strips tab/CR/newline from anywhere, not just the ends | (b) matches real, documented browser URL-parsing behavior |
| 4 | The naive check's bypass is demonstrated live, not just described | (c) real bug class, shown working |
| 5 | Dangerous-scheme list is a purpose-built denylist, not derived from Module 2 | (c) each tool used for what it was actually built for |

## What We Proved

An unencoded value containing `" onmouseover="alert(...)`, spliced into
a double-quoted HTML attribute, was proven — via Module 5's real
tokenizer, inspecting the actual parsed `attrs` dictionary — to create a
genuine, structurally real `onmouseover` attribute that was never
supposed to exist. The identical value, run through Module 27's reused
encoder first, produced a tag with no such attribute at all, the entire
malicious-looking string preserved intact as inert text inside the
original, single `value` attribute. Separately, a naive `javascript:`
URL-scheme check was shown to correctly catch an obvious payload, but be
completely bypassed by hiding a single tab character in the middle of
the word "javascript" — and a fixed check, stripping tab/CR/newline
characters from anywhere in the string first (matching real browsers'
own documented URL-parsing behavior), correctly caught the exact same
bypass attempt. See `tutorial.html` section 06 for the full, unedited
output. Module 29 moves from HTML contexts to the HTTP layer itself:
preventing untrusted data from injecting fake response headers.
