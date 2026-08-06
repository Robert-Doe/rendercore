# DECISIONS.md — Module 21: Chrome UI — Address Bar, Tabs, History

Source file: `chrome_ui.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### `push()` truncates `entries[index+1:]` BEFORE appending, every time

**(a) Forced by what "history" has to mean, not a style choice.** If a
user goes back once, then visits a brand-new URL, the page they
"forward"-ed away from is no longer reachable by forward navigation in
any real browser — it's been replaced by a new branch of history. Not
truncating would leave a dangling, unreachable-by-forward,
never-cleaned-up entry sitting in the list forever, and — worse — would
make `can_go_forward()` lie about what's actually reachable. This isn't
an edge case this module chose to handle carefully; it's the ORDINARY
case any time a user goes back and then clicks a different link, which
is extremely common browsing behavior.

### `index` always points at the CURRENT entry, not "the last entry"

**(b) External contract, matching how every real browser's history
actually works.** `entries[-1]` (the last item in the list) and "the
current page" are NOT the same thing once a user has gone back — the
current page is somewhere in the MIDDLE of the list. Tracking `index`
explicitly, rather than assuming "current == most recently added," is
required precisely because `back()`/`forward()` move through history
without adding or removing anything from the list itself.

### `extract_title()` reuses Module 5's real tokenizer, not a regex or
    string search

**(c) Our convention — reuse over reimplementation, the same discipline
as Modules 4, 14, 19, and 20.** A regex like `<title>(.*?)</title>`
would work for simple cases but is exactly the kind of "looks fine until
real-world HTML breaks it" shortcut this course has avoided since Module
5 — a title containing an escaped `&lt;` or unusual whitespace could
trip up a naive regex in ways Module 5's real tokenizer, built to handle
real HTML, already doesn't have a problem with.

### The scheme decides `fetch_http` vs. `fetch_https` at the point of
    navigation, not inside a shared "smart" fetch function

**(c) Our convention.** `go()`'s one `if url.scheme == "https"` line
keeps the choice visible at the call site rather than hidden inside a
combined fetcher — consistent with Module 4's own decision to keep HTTP
and TLS-wrapped HTTP as two distinct, composable pieces rather than one
merged "just fetch it" function.

### `back()`/`forward()` at a history boundary return `None` rather than
    raising an exception

**(c) Our convention — matching real UI expectations.** A user clicking
a disabled back/forward button (or a script calling `history.back()`
with nothing to go back to) doesn't crash a real browser — the button is
simply inert. Returning `None` (checked by the caller, as this module's
own test does) models that same "safe no-op," rather than forcing every
caller to wrap navigation in a `try/except`.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | `push()` truncates forward history before appending | (a) forced by what history must mean |
| 2 | `index` tracks the current position explicitly | (b) matches real browser history semantics |
| 3 | Title extraction reuses Module 5's tokenizer | (c) reuse over reimplementation |
| 4 | Scheme decides http vs. https fetch at the call site | (c) convention, mirrors Module 4's own separation |
| 5 | Boundary navigation returns `None`, doesn't raise | (c) convention, matches real UI behavior |

## What We Proved

A real tab visited two genuinely different real websites over real
network connections (`example.com` and `info.cern.ch` — the actual first
website ever published), with titles pulled out using Module 5's real
tokenizer, not a shortcut. Going back correctly returned to the first
page while leaving the second reachable via forward. Visiting a THIRD
real page (the HTTPS version of `example.com`, exercising Module 4's TLS
path) after that back navigation correctly discarded the abandoned
`info.cern.ch` entry — history settled at exactly 2 entries, not 3 —
and `forward()` correctly confirmed nothing remained to go forward to.
See `tutorial.html` section 06 for the full, unedited output. Module 22
adds the piece a real multi-page browsing session also needs: state
that survives BETWEEN page loads, not just within one navigation
sequence.
