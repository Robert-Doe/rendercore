# DECISIONS.md — Module 26: URL Encoding & Decoding

Source file: `url_encoding.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Encoding operates on UTF-8 BYTES, not characters

**(a) Forced by spec.** RFC 3986 defines percent-encoding as operating on
octets (bytes), not on abstract characters — a non-ASCII character like
`é` is not "one thing to encode," it's TWO UTF-8 bytes, each becoming
its own `%XX` escape (`%C3%A9`). `percent_encode` iterating
`s.encode("utf-8")` rather than iterating `s` directly is what makes
Case 1's round-trip correct for non-ASCII input — iterating characters
and trying to encode each one as if it were a single byte would corrupt
anything outside plain ASCII.

### `percent_decode` accumulates raw bytes and does ONE final UTF-8 decode
    at the end, rather than decoding each `%XX` independently

**(a) Forced by the same byte-vs-character reality, in reverse.** A
single UTF-8 character can be represented by two, three, or four
consecutive `%XX` escapes. Decoding each one independently and trying to
interpret it as its own character would produce garbage for anything
non-ASCII; accumulating the full byte sequence first and decoding once
at the end is the only correct approach.

### `encode_uri_component` and `encode_uri` use DIFFERENT "safe" character
    sets

**(b) External contract, and the actual point of Case 3.** These mirror
real JavaScript's `encodeURIComponent`/`encodeURI` distinction (simplified
— see below) for a real reason: encoding a single VALUE that's going
INTO a URL needs to escape structural characters like `&` and `=`
(otherwise the value could inject fake structure — exactly Case 2's
vulnerability). Encoding an ALREADY-COMPLETE URI needs to leave those
same characters alone, because in that context they're not attacker
data — they're the URI's own actual, intended structure. Using the wrong
one of these two functions for a given job is a real, common source of
either broken URLs (over-encoding a whole URI) or injection
vulnerabilities (under-encoding a single value) in real code.

### `encode_uri_component`'s safe set is simplified from real JavaScript's

**(c) Our convention — an explicit, named simplification.** Real
`encodeURIComponent` additionally leaves `! * ' ( )` unescaped (a
historical quirk from an older URI spec, RFC 2396, that RFC 3986 later
reserved as "sub-delims"). This module's `encode_uri_component` encodes
those too, sticking strictly to RFC 3986's `unreserved` set only. This
produces MORE escaping than real JavaScript in a few characters' cases —
strictly safer, never less safe, but worth naming as a real, deliberate
difference from what `encodeURIComponent` actually does in a browser.

### Verification uses Module 2's REAL parser to confirm the exploit and
    the fix, not a hand-written string check

**(c) Our convention — the module's central methodological point,
consistent with this course's established discipline (Modules 16, 20,
23, 24).** It would be easy to claim "encoding prevents injection"
without ever proving a real parser actually behaves differently before
and after. Constructing both the vulnerable and the fixed URL strings
and running BOTH through Module 2's unmodified `parse_url()` — checking
what it ACTUALLY extracts as the query string in each case — proves the
vulnerability is real and the fix genuinely closes it, against the exact
parser this course already built and trusts.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Encoding operates on UTF-8 bytes, not characters | (a) forced by spec |
| 2 | Decoding accumulates bytes, decodes UTF-8 once at the end | (a) forced by the same byte reality |
| 3 | Two functions with different safe sets, matching real encodeURI/encodeURIComponent | (b) external contract |
| 4 | `encode_uri_component`'s safe set is RFC-3986-strict, more conservative than real JS | (c) named simplification, strictly safer |
| 5 | Verification runs the exploit and the fix through Module 2's real parser | (c) core methodological point |

## What We Proved

A round-trip encode/decode of text containing spaces, punctuation, and
non-ASCII characters was confirmed lossless. A simulated query-string
injection attack — a search box value containing `&admin=true` — was
proven to genuinely work when spliced into a URL unencoded (Module 2's
own parser extracted a real second `admin` parameter that was never
supposed to exist) and proven to be fully prevented when the same value
was run through `encode_uri_component` first (the parser found exactly
one parameter, and decoding it recovered the attacker's original string
completely intact — encoding didn't destroy the data, it only stopped
it from being reinterpreted as structure). See `tutorial.html` section
06 for the full, unedited output. Module 27 moves this same idea — encode
untrusted data before it crosses into a new interpretation context —
from the URL layer to the HTML body layer, where the stakes become
actual script execution.
