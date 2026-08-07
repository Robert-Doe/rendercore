# DECISIONS.md — Module 29: HTTP Header Injection Prevention

Source file: `header_injection.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Verification runs over a REAL socket connection, parsed by Module 3's
    real, unmodified `parse_response()`

**(a) Forced by what "injection" actually has to mean, and this course's
established discipline.** It would be easy to just show the raw bytes
string and point at where `X-Injected` appears — but that only proves
the STRING looks bad, not that a real HTTP client would actually be
fooled by it. Sending the bytes over an actual local server (the same
technique Modules 3 and 22 already established) and parsing the reply
with Module 3's genuine, unmodified header-parsing logic proves the
injection is REAL from a real client's perspective — `x-injected` and
`set-cookie` appear in `unsafe_response.headers` because Module 3's
parser has no way to distinguish an attacker's injected header line from
a legitimate one once both are separated by a real `\r\n`.

### `sanitize_header_value` STRIPS `\r`/`\n` characters, rather than
    rejecting the whole value if either is present

**(c) Our convention — a real, deliberate tradeoff, named explicitly.**
Rejecting the entire request/response outright (refusing to serve
anything if a header value contains a newline) is arguably the SAFER
default for a production system, since it fails loudly rather than
silently munging data. This module strips instead, to make the
BEFORE/AFTER comparison in Case 2 directly legible — the sanitized
output visibly contains the entire original payload, proving data
wasn't discarded, only its ability to be interpreted as new header
structure. A real system should seriously consider outright rejection
(a 400 Bad Request) as the stricter, arguably better choice for this
exact scenario — named here as the road not taken, not hidden.

### The attack targets a RESPONSE header (server → client), not a request
    header

**(b) External contract — matching the historically dominant, higher-impact
real-world version of this vulnerability class ("HTTP response
splitting").** A server reflecting untrusted input into its OWN response
headers is the more dangerous direction: it can inject fake headers
(including `Set-Cookie`, hijacking session state for OTHER users if a
shared cache is involved) into a response every subsequent client might
receive. Request-header injection (a client injecting into its own
outgoing request) is a real but narrower concern, usually mattering only
when a proxy blindly forwards client-controlled values into headers of
its own.

### `Content-Language` was chosen as the reflected header, arbitrarily

**(c) Our convention.** Any header whose value a server might plausibly
build from user input (a locale cookie, an `Accept-Language` header, a
custom application header) would work identically for this
demonstration — `Content-Language` was picked simply as a plausible,
concrete, real-world example of the pattern, not because it has any
special relevance to header injection specifically.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Verification uses a real socket + Module 3's real unmodified parser | (a) forced — proves real client impact, not just string shape |
| 2 | Sanitization strips CR/LF rather than rejecting the whole value | (c) deliberate tradeoff, named; rejection is the stricter alternative |
| 3 | Targets response-header injection (server → client) | (b) matches the historically dominant, higher-impact real vulnerability |
| 4 | `Content-Language` used as an arbitrary, plausible example header | (c) convention |

## What We Proved

A malicious value containing embedded `\r\n` sequences, reflected
unsanitized into a `Content-Language` response header and sent over a
REAL socket connection, was parsed by Module 3's real, completely
unmodified `parse_response()` as containing not one but THREE separate
headers — the legitimate `Content-Language`, plus a forged
`X-Injected: true`, plus a forged `Set-Cookie: admin=true` — indistinguishable,
from the real client's point of view, from headers the server had
genuinely intended to send. The identical value, run through
`sanitize_header_value()` first, produced a response where all three
pieces of the payload survived intact as ONE squashed, harmless line —
no forged headers, verified against the same real client. See
`tutorial.html` section 06 for the full, unedited output, including the
raw bytes difference between the vulnerable and fixed versions. Module
30 moves from "encode/strip everything" to a more permissive, harder
problem: safely allowing SOME real HTML through, by allowlist.
