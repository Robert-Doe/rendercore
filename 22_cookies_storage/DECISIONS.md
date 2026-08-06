# DECISIONS.md — Module 22: Cookies & Storage

Source file: `cookies.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Verification inspects the RAW BYTES the server actually received,
    not just the client's own `cookies_for()` return value

**(c) Our convention — the module's central methodological point,
matching Module 19's "check the real object, not the script's own
claim" discipline.** It would be easy for this module to only check that
`jar.cookies_for(...)` RETURNS the expected string, without ever proving
that string actually got sent over the wire and arrived intact. Because
the local test server records every request's raw bytes (`_run_server`'s
`port_holder["requests"]`), this module's checks inspect what the
SERVER received — an independent, end-to-end confirmation that the
`Cookie:` header wasn't just computed correctly, but transmitted
correctly.

### Path matching uses `request_path.startswith(cookie_path + "/")`,
    not substring or prefix-without-boundary matching

**(a) Forced by spec, and a real, meaningful distinction.** A cookie
scoped to `Path=/account` must match `/account` and `/account/settings`,
but must NOT match `/accounting` — a plain `request_path.startswith(cookie_path)`
would incorrectly match that last case, since `"/accounting".startswith("/account")`
is `True` in Python. Appending a trailing `/` before the prefix check
(`_path_matches`) closes exactly that gap, matching RFC 6265's actual
path-matching algorithm.

### `Secure` cookies are withheld unless the OUTGOING request is
    explicitly marked secure — checked at `cookies_for()` time, not baked
    into storage

**(b) External contract.** A cookie marked `Secure` when set must never
be sent over a plain HTTP connection, even to the exact same host —
this is a real security property (protecting against a
network-eavesdropper on an unencrypted connection subsequently
impersonating an authenticated session). Checking `is_secure` as a
parameter to `cookies_for()`, rather than only fetching secure cookies
into a "secure jar," keeps the enforcement point exactly where the
actual outgoing connection's security is known.

### `Domain=` cookie attribute's real subdomain-widening behavior is NOT
    implemented — a cookie's domain is always exactly the responding host

**(c) Our convention — explicit scope-out.** Real cookies can specify
`Domain=example.com` to opt into being sent to `sub.example.com` as well
as `example.com` itself — genuine, spec-defined behavior with its own
matching algorithm. This module's `set_from_header` ignores any
`Domain=` attribute entirely and always scopes a cookie to the exact
host that set it, which is simpler and correct for same-host scenarios
(everything this module's own tests exercise) but not spec-complete for
cross-subdomain cookies.

### Persistence uses plain JSON to a file, not a database or the
    platform's real cookie-storage format

**(c) Our convention.** The actual point being proven — that cookie
state can outlive the process that created it — doesn't require a real
database engine to demonstrate. `save()`/`load()` round-tripping through
JSON is the simplest mechanism that genuinely crosses a process boundary
(a fresh `CookieJar.load()` call, proven via `is not` identity checking
against the original object, has no shared memory with the jar that
saved it).

### `Expires`/`Max-Age` (cookie lifetime) attributes are NOT parsed or enforced

**(c) Our convention — explicit scope-out.** Every cookie this module
creates is effectively a "session cookie" with no expiration tracked.
Real expiration requires wall-clock comparison logic that adds real
complexity without changing the core mechanism (parse Set-Cookie, scope
by domain/path, resend on matching requests) this module exists to
prove.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Verification checks the server's actually-received raw bytes | (c) core methodological point |
| 2 | Path matching uses a trailing-slash-guarded prefix check | (a) forced by spec — closes a real false-match gap |
| 3 | `Secure` enforcement checked per-request, not per-storage | (b) external contract, real security property |
| 4 | No `Domain=` subdomain-widening; always exact-host scoped | (c) explicit scope-out |
| 5 | Persistence via plain JSON file | (c) convention, sufficient to prove the point |
| 6 | No `Expires`/`Max-Age` parsing or enforcement | (c) explicit scope-out |

## What We Proved

A hand-rolled local server (following Module 3's own local-server
pattern for determinism) sent two real `Set-Cookie` headers with
different path scopes. A client correctly computed different `Cookie:`
header values for two different request paths — sending only the
root-scoped cookie to `/`, and both cookies to `/account` — and the
SERVER'S own recorded raw request bytes confirmed exactly those headers
actually arrived, not just that the client claimed to send them.
Finally, the cookie jar was saved to disk and reloaded into a
provably different Python object, which reproduced identical
`Cookie:` header output — real evidence of state surviving a process
boundary. See `tutorial.html` section 06 for the full, unedited output.
Module 23 builds the security boundary around this exact storage: proving
a script from one origin cannot read another origin's cookies or DOM.
