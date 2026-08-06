# DECISIONS.md — Module 4: TLS via Socket Wrapping (HTTPS)

Source file: `https_client.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Why TLS itself is not implemented from scratch

**(a) Forced by platform reality, treated the same as DNS/TCP.** TLS is
built on real cryptographic primitives — asymmetric key exchange, block
ciphers, message authentication codes, and X.509 certificate chain
validation involving actual signature verification. Reimplementing any of
these correctly is a cryptography course, and reimplementing them
*incorrectly* (which is the realistic outcome of a teaching exercise) is
actively dangerous — a broken hand-rolled TLS stack is worse than no TLS
at all, because it looks secure without being secure. This is the single
clearest example in the whole course of "treated as hardware": we import
`ssl`, which wraps the system's OpenSSL (or equivalent) installation, the
same way `socket` wraps the OS's TCP/IP stack.

### `ssl.create_default_context()` instead of a bare `ssl.wrap_socket()`

**(c) Our convention — and a safety-motivated one.** Older Python code
(and older tutorials) call `ssl.wrap_socket()` directly, which historically
defaulted to `CERT_NONE` — no certificate verification at all. That
default was so consistently a source of real security bugs that Python's
own documentation now recommends `create_default_context()`, which loads
the OS's trusted CA store and enables both chain and hostname verification
by default. We use it specifically so this module, even as a teaching
example, does not model an anti-pattern that would be a real
vulnerability in production code.

### `server_hostname=host` passed to `wrap_socket()`

**(b) External contract.** TLS's Server Name Indication (SNI) extension
requires the client to state which hostname it's connecting to *during
the handshake itself* — before any HTTP request is even sent — because a
single IP address (like the Cloudflare-fronted `example.com` we've been
hitting since Module 1) may serve TLS certificates for many different
domains. Omitting `server_hostname` either breaks the handshake against
such servers or silently disables hostname verification, depending on the
Python version — neither acceptable, so it's always passed explicitly.

### Reusing `format_request` and `parse_response` from Module 3 completely unmodified

**(c) Our convention — and the entire pedagogical point of this module.**
Nothing about an HTTP request's bytes, or how a response is framed and
parsed, changes when the underlying transport is encrypted. TLS operates
below HTTP, wrapping the raw byte stream transparently — from
`format_request()`'s perspective, `sock.sendall()` behaves identically
whether `sock` is a plain `socket.socket` or an `ssl.SSLSocket`. We could
have copy-pasted Module 3's functions into this file with the serial
numbers filed off; deliberately importing them unchanged instead is the
proof, not just the claim, that the two layers are actually separate.

### Testing against `expired.badssl.com` and `wrong.host.badssl.com`

**(c) Our convention, chosen specifically to make verification falsifiable.**
It would be easy for this module to claim "certificate verification
happens" without ever showing a case where it matters — a `context =
create_default_context()` line that never gets exercised against a bad
certificate is unverified marketing copy, not a proven module. `badssl.com`
exists specifically as a public test suite of deliberately misconfigured
TLS endpoints; connecting to its expired-certificate and wrong-hostname
subdomains and observing a real `SSLCertVerificationError` is a genuine,
reproducible demonstration that both checks (chain validity, hostname
match) are actually active — not merely configured and silently ignored.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | TLS cryptography itself is imported (`ssl`), never reimplemented | (a) treated as hardware |
| 2 | `create_default_context()` used, not a no-verification bare wrap | (c) convention, safety-motivated |
| 3 | `server_hostname` always passed to `wrap_socket()` | (b) required by SNI |
| 4 | Module 3's request/response functions imported unmodified | (c) convention — the module's whole point |
| 5 | Verification tested against real misconfigured endpoints (badssl.com) | (c) convention, makes the claim falsifiable |

## What We Proved

Three real, verified outcomes from one run: a real HTTPS request to
`example.com` succeeded over TLS 1.3, returning the identical 559-byte
body Module 3 got over plain HTTP — using Module 3's `format_request`
and `parse_response` with not one line changed. A request to a site with
a deliberately expired certificate failed with a real
`SSLCertVerificationError: certificate has expired`. A request to a site
whose certificate doesn't cover the hostname requested failed with a real
`SSLCertVerificationError: Hostname mismatch`. See `tutorial.html` section
06 for the full, unedited output. Module 5 leaves networking behind
entirely and starts turning the HTML bytes these first four modules can
now reliably fetch into a structured document.
