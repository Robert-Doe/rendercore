# DECISIONS.md — Module 2: URL Parser

Source file: `url_parser.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract (a spec/protocol/format) · **(c)** our own convention.

---

### Splitting off the fragment (`#...`) first, before anything else

**(a) Forced by the URL grammar.** RFC 3986 defines a URL's grammar as
`scheme://authority/path?query#fragment`, strictly in that order, with the
fragment explicitly defined as "whatever comes after the first `#`, to the
end of the string — including any `#`, `?`, or `/` characters that appear
inside it." If we split on `?` or `/` before removing the fragment, a
fragment containing those characters (e.g. `#section?2` or `#a/b`) would
be incorrectly sliced into query or path. Stripping the fragment first is
not a style preference — it's the only order that matches the spec's own
definition of what a fragment contains.

### Requiring `"://"` to detect an absolute URL

**(b) External contract, simplified.** The real grammar allows schemes
without `//` (like `mailto:`) — we don't support those, so requiring
`"://"` is a safe, explicit narrowing for this course's http/https-only
scope, not a general URL-parsing technique. Named here so it isn't mistaken
for "how URLs work in general."

### Only supporting `http` and `https` as schemes

**(c) Our convention.** A general-purpose URL parser handles dozens of
schemes (`ftp:`, `mailto:`, `data:`, `file:`, ...). This course's browser
only ever fetches over HTTP/HTTPS (Modules 1, 3, 4), so `DEFAULT_PORTS`
intentionally only knows those two — anything else raises immediately
rather than silently mishandling it.

### Defaulting an empty path to `"/"`

**(b) External contract.** `http://example.com` and
`http://example.com/` are defined by the HTTP spec to be requests for the
same resource — the root. Treating a missing path as `/` isn't a
convenience; it's matching what a real server expects to receive in the
request line (Module 3 sends exactly this value as the request path).

### Deriving the port from the scheme when none is given

**(b) External contract.** Port 80 for `http` and 443 for `https` are the
IANA-registered default ports for those schemes — not something we
invented. A URL with no explicit port is defined to mean "use the
scheme's default," so `DEFAULT_PORTS` encodes a fact, not a preference.

### Not supporting IPv6 literal hosts, userinfo, or `..`-segment resolution

**(c) Our convention — explicit scope-out.** Real URL parsing has to
handle `http://[::1]:8080/`, `http://user:pass@host/`, and relative
resolution involving `..` path segments (RFC 3986 §5). None of these
shapes appear in this course's own test pages or in the sites Modules 1–4
fetch from in their demos, so supporting them would add real parsing
complexity with no module ever exercising it. `_resolve_relative()`'s
docstring names this limitation explicitly rather than silently mishandling
an unsupported input.

### Verifying against `urllib.parse.urlsplit` in `__main__`, but never
    importing it into the parser itself

**(c) Our convention, deliberately drawn as a hard line.** The import of
`urllib.parse` appears only below the `if __name__ == "__main__":` guard,
used purely as an independent oracle to check our hand-written logic
against Python's own battle-tested implementation. `parse_url()` and
`_resolve_relative()` — the actual deliverable — never see that import.
This mirrors a real technique (differential testing against a trusted
reference implementation) without compromising the "from scratch" premise
of the module it's testing.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Strip the fragment (`#...`) before any other splitting | (a) forced by URL grammar |
| 2 | Require `"://"` to treat a string as an absolute URL | (b) contract, narrowed |
| 3 | Only `http`/`https` schemes supported | (c) convention |
| 4 | Empty path defaults to `/` | (b) external contract |
| 5 | Missing port defaults from scheme (80/443) | (b) external contract (IANA) |
| 6 | No IPv6 literals, userinfo, or `..` resolution | (c) convention, explicit scope-out |
| 7 | `urllib.parse` used only as a test oracle, never in the parser | (c) convention |

## What We Proved

`url_parser.py` decomposed five real, differently-shaped URLs — with a
port, without a port, with a query string, with a fragment — into
scheme/host/port/path/query/fragment using only string methods, and every
single result was cross-checked byte-for-byte against Python's own
`urllib.parse.urlsplit` and matched. See `tutorial.html` section 06 for
the full, unedited run. Module 3 will use this module's `URL` object
directly to know which host and port to connect to, and which path to
put in the request line.
