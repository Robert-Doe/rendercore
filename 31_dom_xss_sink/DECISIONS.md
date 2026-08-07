# DECISIONS.md — Module 31: The DOM XSS Sink: innerHTML vs. textContent

Source file: `dom_xss_sink.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### `set_inner_html` reuses Module 5's tokenizer and Module 6's
    `build_tree` COMPLETELY UNMODIFIED — the exact same functions that
    parse a real page's own HTML

**(a) Forced by what makes this module's claim TRUE, not just
illustrative.** The entire point is that `innerHTML`-style insertion is
dangerous specifically BECAUSE it runs untrusted text through the SAME
parser a page's own trusted markup goes through — there is no separate,
"more careful" parsing path for content assigned this way, in this
course's engine OR in a real browser. Calling `build_tree(tokenize(html))`
directly, with zero special-casing, is what makes `set_inner_html`'s
behavior genuinely equivalent to real `element.innerHTML = ...`, not an
exaggerated stand-in for it.

### `set_text` builds exactly ONE `TextNode`, regardless of what the
    input string contains

**(a) Forced by what real `textContent` actually guarantees.** Real
`element.textContent = value` is specified to never invoke the HTML
parser at all — the assigned string becomes literal text content, full
stop, no matter what characters it contains. `set_text`'s single-line
implementation (`el.children = [TextNode(text, parent=el)]`) has no
parsing step to exploit, by construction — there's no code path inside
it that could ever produce an `Element`.

### The SAME `payload` variable is passed to all three functions,
    unmodified

**(c) Our convention — the entire demonstration's methodological
core.** It would be easy, and less convincing, to use three different
example strings tailored to each function. Using ONE identical payload
across `set_text`, `set_inner_html`, and `set_inner_html_sanitized`
proves the difference in outcome is caused ENTIRELY by which function
received it — not by any difference in the data itself. This is the
concrete, code-level version of the module's central claim: DOM-based
XSS is a SINK problem (which API received the data), not a data problem.

### `set_inner_html_sanitized` calls Module 30's `sanitize_children` on
    the freshly-parsed fragment, BEFORE attaching it to the live tree

**(a) Forced by ordering — sanitizing after attachment would be too
late.** If the parsed (dangerous) fragment were attached to `el` first
and sanitized afterward, there would be a real window — however brief in
this synchronous code — where the live tree actually contained the
dangerous `onerror` attribute. Sanitizing the detached fragment BEFORE
it ever becomes part of `el`'s children means the dangerous state never
exists in the tree a renderer/script could observe at all, not even
momentarily.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | `set_inner_html` reuses Modules 5/6 completely unmodified | (a) forced — this IS the real mechanism, not an analogy for it |
| 2 | `set_text` never invokes the parser, by construction | (a) forced by what real `textContent` guarantees |
| 3 | One identical payload used across all three functions | (c) core methodological point |
| 4 | Sanitization happens on the detached fragment, before attachment | (a) forced — sanitizing after attachment leaves a real unsafe window |

## What We Proved

The identical string, `'<img src=x onerror="alert(document.cookie)">'`,
produced three genuinely different, independently verified results
depending only on which function received it: through `set_text`, it
became exactly one `TextNode` holding the literal characters, never
parsed, never dangerous. Through `set_inner_html`, it became a REAL
`Element` with tag `img` and a REAL, structural `onerror` attribute — the
exact live DOM state a real browser would use to run the attacker's
script the moment the image failed to load. Through
`set_inner_html_sanitized`, the same string produced a real `<img>`
element (still on Module 30's allowlist) with its `onerror` attribute
completely absent — the dangerous structure never made it into the live
tree at all. See `tutorial.html` section 06 for the full, unedited
output. This is the last module in Phase 5 — the encoders and sanitizers
built across Modules 26-31 now cover every boundary named at the start
of this phase: the URL, the HTML body, the HTML attribute, the HTTP
header, untrusted markup as a whole, and finally the specific DOM API
that decides whether cleaned or uncleaned data ever becomes dangerous
structure.
