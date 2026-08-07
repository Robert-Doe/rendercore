# DECISIONS.md — Module 30: HTML Sanitization (Allowlist-Based)

Source file: `html_sanitization.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Tags, and attributes-per-tag, are both ALLOWLISTS, not denylists

**(c) Our convention — the single most important architectural decision
in this module.** A denylist ("block `<script>`, block `onclick`, block
...") has to be updated every time a new dangerous tag or attribute is
discovered — and HTML has genuinely surprising ones (`<svg><script>`
nested oddly, obscure event-handler-like attributes on rarely-used
elements). An allowlist inverts the failure mode: anything NOT
explicitly recognized as safe is removed by default, so a tag or
attribute this module's author never even thought of is still excluded,
not accidentally permitted. This is why real production sanitizers
(DOMPurify, Bleach, etc.) are allowlist-based, and why `ALLOWED_TAGS`/
`ALLOWED_ATTRS` are the only two data structures that decide what
survives.

### Dangerous tags (`script`, `style`, `iframe`, ...) have their ENTIRE
    subtree removed — not just the tag, their content too

**(a) Forced by what these tags actually mean.** A `<script>` element's
TEXT CONTENT is code, not display text — leaving it behind as plain text
after stripping just the `<script>`/`</script>` wrapper would still be
wrong (it would visibly print the attacker's JavaScript source on the
page, at best confusing, and depending on how the surrounding page
handles it, potentially still dangerous). Dropping the whole subtree,
content included, is the only choice that matches what these tags are
actually for.

### Tags that are neither dangerous NOR explicitly allowed are UNWRAPPED
    (tag discarded, children kept), not dropped entirely

**(c) Our convention — a real, deliberate design choice with a genuine
tradeoff.** An unrecognized tag like `<fancybox>` is far more likely to
be harmless-but-unsupported markup than a deliberate attack — dropping
its TEXT content along with the tag would be needlessly destructive to
a legitimate user's content. Unwrapping preserves what's very likely
real, intended text while still refusing to trust the tag itself. A
stricter sanitizer could instead drop unknown tags' content entirely;
this module's choice favors content preservation for the "merely
unrecognized" case, while still treating explicitly `DANGEROUS_TAGS`
as content-destroying — two different tiers of risk, two different
responses.

### `href`/`src` values are checked for dangerous URL SCHEMES even when
    the ATTRIBUTE NAME itself is on the allowlist

**(a) Forced by the fact that an allowed attribute name doesn't imply a
safe value.** `href` is a perfectly legitimate, allowed attribute — but
`href="javascript:alert(1)"` is dangerous regardless of the attribute
name being fine. `_sanitize_attrs` reuses Module 28's
`is_dangerous_url_scheme` check specifically ON THE VALUE, layered on
top of (not instead of) the name-based allowlist — two independent
checks, because they're checking two independent things.

### Comments are dropped entirely, not preserved

**(c) Our convention — explicit scope-out, chosen conservatively.**
HTML comments have historically been involved in real parser-differential
attacks (old Internet Explorer "conditional comments" being one
notorious example) — content inside a comment that one parser treats as
inert and another treats as live markup. Dropping comments unconditionally
sidesteps that entire class of parser-disagreement risk, at the small
cost of losing genuinely harmless comments a user might have intended
(rare in untrusted user content in the first place).

### Sanitization is BOTTOM-UP: a node's children are sanitized before the
    node's own fate (keep / unwrap / drop) is decided

**(a) Forced by dependency order.** Whether to unwrap `<div>` depends on
nothing about its children, but the CONTENT that ends up surviving in
its place (if unwrapped) or inside it (if kept) has to already be
sanitized before that decision is made — otherwise a dangerous child
could slip through attached to a parent that was processed first. This
mirrors the same "children before parent" dependency Modules 11 and 20
already established for auto-height layout, applied here to a
correctness question instead of a sizing one.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Tags and attributes are allowlists, not denylists | (c) the module's central architectural choice |
| 2 | Dangerous tags lose their entire subtree, content included | (a) forced by what those tags mean |
| 3 | Unrecognized-but-not-dangerous tags are unwrapped, not dropped | (c) deliberate content-preservation tradeoff |
| 4 | URL-bearing attribute VALUES checked for scheme danger independently of the attribute NAME | (a) forced — an allowed name doesn't imply a safe value |
| 5 | Comments dropped entirely | (c) explicit scope-out, conservative |
| 6 | Sanitization is bottom-up (children before parent's own fate) | (a) forced by dependency order |

## What We Proved

A single deliberately mixed payload — safe formatted text, a `<script>`
tag with real exploit code as its content, a `javascript:` link, an
`onerror` handler on an otherwise-safe `<img>`, an unrecognized custom
tag, and an allowed `<div>` carrying an `onclick` handler — was run
through the sanitizer, and the RESULTING TREE (not the output string)
was walked and checked structurally: no dangerous tag survived anywhere;
no `on*` attribute survived anywhere; no surviving URL attribute used a
dangerous scheme; the `javascript:` link's `href` was dropped entirely
rather than left dangling; and — the harder half of the claim — real,
safe content was genuinely preserved: `<b>world</b>` remained a real
Element, the unknown tag's text content survived after unwrapping, and
the `<div>`'s safe text content survived with only its dangerous
attribute removed. The `<script>` tag's actual exploit code was
confirmed absent from the sanitized tree's text entirely, not just
hidden inside a stripped tag. See `tutorial.html` section 06 for the
full, unedited output. Module 31, the final module in this phase, looks
at the last mile: even with server-side sanitization done perfectly,
the specific JavaScript API a page's OWN script uses to insert content
still decides whether the exact same string is safe or dangerous.
