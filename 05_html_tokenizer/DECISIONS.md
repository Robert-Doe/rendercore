# DECISIONS.md — Module 5: HTML Tokenizer

Source file: `html_tokenizer.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Two top-level states (`DATA`, `RAWTEXT`), not one state per tag-parsing
    detail

**(c) Our convention, a deliberate simplification of a real spec.** The
actual WHATWG HTML tokenization algorithm defines around 80 named states
(`TagOpenState`, `BeforeAttributeNameState`, `AttributeValueDoubleQuotedState`,
and so on) — genuinely one state per meaningfully different parsing
situation, each spelled out because the spec is a contract implementers
must match byte-for-byte. This module keeps only the two states that
actually change *what kind of content* is being scanned (markup vs. raw
text) as named `state` values, and handles the finer-grained situations
inside a tag (attribute name vs. value, quoted vs. unquoted) with
dedicated methods instead. The behavior for the cases we support matches
the spec; the *naming granularity* is simplified for readability. See
prereqs/state_machines.html.

### `RAWTEXT` mode for `<script>` and `<style>`

**(a) Forced by spec, and forced by reality.** Real script content is
full of `<` and `>` characters that are not markup — the WHATWG spec
defines script and style content as *not* re-entering tag tokenization
until the matching end tag is found. There's no reasonable alternative:
without this, `if (x < 10)` inside a `<script>` block would tokenize `<`
as the start of a (nonsensical) tag, corrupting every script on every
real page.

### Comments are found via `str.find("-->", ...)`, not char-by-char state transitions

**(c) Our convention.** The real spec models comment parsing as its own
multi-state sequence (to correctly handle edge cases like `--!>` and
nested-looking `<!--` inside a comment). Because a comment's content is
never re-interpreted as markup regardless of what's inside it, a single
`str.find` for the literal end marker produces identical results for the
overwhelming majority of real comments, including the deliberately tricky
`<!-- a comment with <fake> tags inside -->` this module tests against,
while being far easier to read than the spec's full state sequence.

### Entity/character-reference decoding (`&amp;`, `&lt;`, ...) is NOT implemented

**(c) Our convention — explicit scope-out.** Decoding HTML character
references is a genuinely separate, sizeable piece of the spec (a table
of over 2000 named references, plus numeric and hex forms). Every text
token this tokenizer emits keeps entities literal (`&amp;` stays as the
four characters `&amp;`, not becomes `&`). A real browser decodes these
during or after tokenization; we don't, so any test HTML this course
writes going forward avoids relying on entity decoding having happened.

### The text-flush bug this module's real development run caught

**(c) Our convention — noted here because it happened, not as an abstract
example.** The first working version of `_consume_markup()` flushed
buffered text before a *start* tag but not before an *end* tag or a
*comment*. Running the tokenizer against real sample HTML (not just
reading the code) surfaced this immediately: `<title>Test Page</title>`
tokenized with the `Text("Test Page")` token appearing *after*
`EndTag("title")` and even after the next element's end tag, instead of
between the start and end tags where it belongs. The fix — calling
`_emit_text_if_any()` before emitting an `EndTag` or `Comment` token, not
just before a `StartTag` — is now covered by an explicit regression check
in `__main__`. This is left in the module (and called out in
`tutorial.html`'s Q&A) specifically because "I read the code and it looked
right" and "I ran the code and checked the actual output" caught two
different bugs, which is the whole reason this course's process requires
running every module before writing docs about it.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Two top-level states, finer detail handled by methods | (c) simplification of the real spec's ~80 states |
| 2 | RAWTEXT mode for script/style content | (a) forced by spec and by real script content |
| 3 | Comments located via `str.find("-->")` | (c) convention, behaviorally equivalent for our cases |
| 4 | Entity decoding not implemented | (c) explicit scope-out |
| 5 | Text buffer flushed before EndTag/Comment, not just StartTag | (c) bug fix, caught by running the code, not reading it |

## What We Proved

Tokenizing a real, deliberately tricky HTML sample — with quoted and
unquoted attributes, a self-closing tag, a comment containing fake tags,
and a `<script>` block containing `<` and `>` inside real code — produced
30 tokens in the correct order, verified by four explicit checks: script
content stayed one unbroken text token (`<script>` didn't get corrupted
by its own operators), the comment's embedded `<fake>` never became a
real tag, the self-closing `<img>` was correctly flagged, and — after a
real bug was found and fixed — text ahead of a closing tag is correctly
ordered before it. See `tutorial.html` section 06 for the full, unedited
output. Module 6 takes this exact token stream and assembles it into an
actual tree.
