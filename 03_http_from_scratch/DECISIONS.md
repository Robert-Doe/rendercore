# DECISIONS.md — Module 3: Hand-Rolled HTTP/1.1 Request & Response

Source file: `http_client.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Importing Module 1 and Module 2 via `sys.path.insert`, not a package

**(c) Our convention.** This course deliberately keeps every module a
standalone, runnable folder rather than one installable Python package,
so a learner can `cd` into any module and run it with no setup. The cost
is that reusing Module 1/2's code from Module 3 needs an explicit
`sys.path.insert(...)` pointing at their folders, done at the top of the
file before importing. A real project would use a proper package
(`pip install -e .` or similar); we accept the extra two lines here in
exchange for "every folder just runs" staying true through Module 25.

### `Host` header is required, not optional

**(b) External contract.** HTTP/1.0 made `Host` optional; HTTP/1.1 (RFC
9110 §7.2) makes it mandatory, precisely because a single server (or a
reverse proxy like the `cloudflare` one this module actually talked to)
may host many different sites on the same IP address, and needs `Host` to
know which one you're asking for. Omitting it is a real bug, not a style
issue — some servers will reject the request outright.

### Sending `Connection: close` even though we don't rely on it to know when the body ends

**(c) Our convention, explained precisely so it isn't confused with the
module's main point.** We still ask the server to close the connection
after responding — it keeps the demo's socket lifecycle simple (one
request, one response, one `sock.close()`). But `parse_response()` never
uses the connection closing as its signal that the body is done — it uses
`Content-Length` or chunked framing. This is deliberate: the real run
against `example.com` below actually shows the server ignoring our
"please close" preference and using `Transfer-Encoding: chunked` instead
— proof, not just a claim, that a client relying on connection-close would
have gotten this wrong if the server had also kept the connection open
past the response.

### `Content-Length` checked before `Transfer-Encoding: chunked`

**(a) Forced by the spec's own precedence rule.** RFC 9112 §6.3 defines
exactly this priority order when determining a response's length, and
further says a response must not send both in a way that conflicts. We
mirror that precedence directly in `parse_response()`'s `if/elif` chain
rather than inventing our own order.

### `_read_chunked()`'s structure: size line, then exactly that many bytes, then a CRLF, repeat, until a zero-size chunk

**(a) Forced by spec.** This is RFC 9112 §7.1's chunked transfer coding
grammar verbatim — chunk-size (in hex) + CRLF + chunk-data + CRLF,
repeated, terminated by a `0`-size chunk. There's no alternative framing
to choose between here; every byte of `_read_chunked()`'s control flow
exists because the wire format demands it.

### The final `else` branch — reading until the connection closes

**(a) Forced by necessity, but flagged as a fallback, not the default
path.** A response with neither `Content-Length` nor
`Transfer-Encoding: chunked` genuinely has no other way to signal where
the body ends, per spec, than the connection closing (this was HTTP/1.0's
only mechanism). We implement it because it's spec-legal and does occur,
but the code comment above it exists specifically so nobody mistakes it
for the primary strategy — see the real run in `tutorial.html` section 06,
where the live request actually took the chunked path, not this one.

### The local hand-rolled test server (`_serve_once`)

**(c) Our convention, and a deliberate testing choice.** Verifying the
chunked decoder against a real website is one honest data point, but it's
also nondeterministic — a live server could change its framing at any
time (as seen: two different real runs against `example.com` both used
chunked, but that isn't guaranteed to stay true). `_serve_once` sends a
byte-for-byte known response over a real socket on `127.0.0.1`, so the
chunked decoder's correctness can be checked against an exact expected
string (`b"Hello, World!"`), independent of any external site's behavior.
It uses only the same `socket` module already permitted for this course —
no test framework, no mocking library.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Sibling-module import via `sys.path.insert`, not a package | (c) convention |
| 2 | `Host` header sent on every request | (b) mandatory in HTTP/1.1 |
| 3 | `Connection: close` sent, but never relied on for framing | (c) convention |
| 4 | `Content-Length` checked before `chunked` | (a) forced by spec precedence |
| 5 | Chunked decoder follows RFC 9112 §7.1 grammar exactly | (a) forced by spec |
| 6 | Read-until-closed kept only as a last-resort fallback | (a) forced by necessity, flagged as fallback |
| 7 | Local hand-rolled server used for deterministic chunked testing | (c) convention |

## What We Proved

Two real, verified runs: first, a genuine HTTP/1.1 request to
`example.com` returned a 200 response whose body arrived
`Transfer-Encoding: chunked` — and `parse_response()` correctly decoded
559 bytes of real HTML starting with `<!doctype html>`, using the chunked
path, not connection-close. Second, a hand-rolled local server (built with
nothing but `socket`) sent a byte-for-byte known chunked response, and the
same decoder reproduced the exact expected string `b"Hello, World!"`. See
`tutorial.html` section 06 for the full, unedited output of both runs.
Module 4 wraps this exact request/response logic in TLS with zero changes
to `format_request` or `parse_response` — proof that HTTP and transport
security are genuinely separate layers.
