# DECISIONS.md — Module 7: CSS Tokenizer & Parser

Source file: `css_parser.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Rule splitting via brace-finding, not a full low-level token stream

**(c) Our convention — a real, named simplification.** The actual CSS
Syntax Module spec defines parsing in two layers: a low-level tokenizer
(~30 distinct token types — idents, hashes, strings, numbers, delimiters,
and more) and a separate layer that groups those tokens into rules and
declarations. Module 5 modeled HTML's tokenizer at something close to
that level of granularity because HTML's grammar (RAWTEXT, attribute
quoting) genuinely needs it. CSS's rule-level structure — a selector,
then a brace-delimited declaration block — is regular enough that
`str.find("{")` / `str.find("}")` produces identical results to a full
low-level tokenizer for every stylesheet this course actually writes,
while being far more readable. Named explicitly so it isn't mistaken for
"how a real CSS engine works internally."

### At-rules (`@media`, `@font-face`, ...) are detected and skipped whole,
    never parsed

**(c) Our convention — explicit scope-out.** `@media` blocks contain
nested rules inside their own braces, which would require this parser to
recursively parse rules-within-rules and *also* evaluate a media-query
condition against a viewport — a second parser and a small conditional
language, neither of which any later module in this course depends on.
`_skip_block()` counts nested braces so an `@media { body { ... } }`
block is skipped as one atomic unit rather than corrupting the parser
that finds it. This is verified directly: the sample stylesheet's
`@media` block is confirmed absent from the parsed rule count.

### Only the descendant combinator (whitespace) is supported — no `>`, `+`, `~`

**(c) Our convention — explicit scope-out.** Real CSS selectors combine
compound selectors four different ways (descendant, child, adjacent
sibling, general sibling), each with different matching semantics. Module
8's matching logic only needs to walk "is there an ancestor, at any
depth, matching the previous compound selector" — which is what
descendant combinators require — so this module only parses that one.
`nav a.active` parses correctly; `nav > a.active` would currently parse
`>` as a garbage token inside `_parse_compound` rather than being
recognized as a different kind of combinator. Named here so it's an
understood gap, not a silent wrong answer.

### `!important` detected via `value.lower().endswith("!important")`

**(c) Our convention, deliberately narrow.** Real CSS allows whitespace
between the value and `!important` (`color: red ! important`) and mixed
case (`!IMPORTANT`). This module only recognizes the exact, no-internal-
whitespace form `!important` (case-insensitively) at the end of a
value — the overwhelmingly common way it's actually written — rather than
building a small grammar for the handful of legal variations.

### Specificity is NOT computed anywhere in this module

**(b) External contract, deliberately deferred.** As established in
Module 0's DECISIONS.md §4, parsing and cascading are separately defined
concerns in the CSS spec itself — a `Rule` here has no notion of "how
strongly" its selector matches, only "what its selector says." Computing
specificity here would blur that boundary. Module 9 computes it, using
exactly the `SimpleSelector`/`Selector` structure this module produces
and nothing more.

### Universal selector (`*`) and "no type given" (`.foo`) both parse to
    `type_name=None`

**(a) Forced by the actual semantics being identical.** `*.foo` and
`.foo` are defined by the CSS spec to mean exactly the same thing — "any
element with class foo." Representing "no type constraint" as `None` in
both cases isn't a shortcut that loses information; there is no
information to lose, because the spec doesn't distinguish these two
inputs either.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Rule splitting via brace-finding, not a full low-level tokenizer | (c) named simplification |
| 2 | At-rules detected by leading `@` and skipped whole | (c) explicit scope-out |
| 3 | Only descendant (whitespace) combinator supported | (c) explicit scope-out |
| 4 | `!important` matched only in its exact common form | (c) narrow convention |
| 5 | Specificity computation deferred entirely to Module 9 | (b) external contract (spec separates parsing/cascade) |
| 6 | `*` and no-type-given both parse to `type_name=None` | (a) forced by identical real semantics |

## What We Proved

A real stylesheet with a universal selector, a type selector, a
comma-separated class selector group, a descendant combinator, an id
selector, an `@media` block, and `!important` all parsed into 6 correctly
structured `Rule` objects — with the `@media` block correctly excluded
from that count rather than corrupting the parse. Six explicit checks
confirmed: the comma-group selector count, the `!important` flag and
cleaned value, the two-part descendant selector's structure, the id
selector's lack of a type constraint, and the universal selector's
`None` type. See `tutorial.html` section 06 for the full, unedited
output. Module 8 takes these exact `Rule` objects and, given a DOM node
from Module 6, determines which of them actually match it.
