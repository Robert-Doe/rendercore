"""
Module 2 — URL Parser
=======================
Proves: a URL string can be decomposed into scheme/host/port/path/query/
fragment without importing a parsing library (no `urllib.parse`).

Scope, stated explicitly: this parser handles the URL shapes this course
actually needs — http/https, optional port, optional path/query/fragment,
relative URLs resolved against a base. It does NOT handle IPv6 literal
hosts (`http://[::1]/`), userinfo (`http://user:pass@host/`), or every
percent-encoding edge case in RFC 3986. Real browsers handle all of that;
we scope it out on purpose (see DECISIONS.md) to keep the parsing logic
readable.
"""

from dataclasses import dataclass


@dataclass
class URL:
    scheme: str
    host: str
    port: int
    path: str
    query: str          # "" if absent
    fragment: str        # "" if absent

    def origin(self) -> str:
        """scheme://host:port — see prereqs/origins_and_security_boundary.html"""
        return f"{self.scheme}://{self.host}:{self.port}"


DEFAULT_PORTS = {"http": 80, "https": 443}


def parse_url(url: str, base: "URL | None" = None) -> URL:
    """Hand-parse a URL string into its component pieces.

    Splits left to right, in the order the pieces actually appear in a
    URL, consuming what it just matched before looking for the next piece.
    That ordering is not a style choice — it mirrors the URL grammar
    itself (scheme, then authority, then path, then query, then fragment
    always appear in that fixed order; see DECISIONS.md).
    """
    rest = url

    # ---- fragment: everything after the FIRST "#", strip it off first
    # since nothing after it is part of scheme/host/path/query. ----
    if "#" in rest:
        rest, fragment = rest.split("#", 1)
    else:
        fragment = ""

    # ---- scheme: letters before "://" ----
    if "://" in rest:
        scheme, rest = rest.split("://", 1)
        scheme = scheme.lower()
    else:
        # relative URL (e.g. "/about", "styles.css") — needs a base
        if base is None:
            raise ValueError(f"relative URL {url!r} given with no base URL")
        return _resolve_relative(rest, fragment, base)

    if scheme not in DEFAULT_PORTS:
        raise ValueError(f"unsupported scheme {scheme!r} (only http/https)")

    # ---- authority (host[:port]): up to the next "/", "?", or end ----
    authority_end = len(rest)
    for ch in ("/", "?"):
        idx = rest.find(ch)
        if idx != -1:
            authority_end = min(authority_end, idx)
    authority = rest[:authority_end]
    rest = rest[authority_end:]

    if ":" in authority:
        host, port_str = authority.rsplit(":", 1)
        if not port_str.isdigit():
            raise ValueError(f"invalid port {port_str!r} in {url!r}")
        port = int(port_str)
    else:
        host = authority
        port = DEFAULT_PORTS[scheme]

    if not host:
        raise ValueError(f"missing host in {url!r}")

    # ---- query: everything after "?" (fragment already stripped) ----
    if "?" in rest:
        path, query = rest.split("?", 1)
    else:
        path, query = rest, ""

    # ---- path: whatever's left; "" becomes "/" (an empty path always
    # means "the root", per HTTP convention) ----
    if path == "":
        path = "/"

    return URL(scheme=scheme, host=host, port=port, path=path,
               query=query, fragment=fragment)


def _resolve_relative(rest: str, fragment: str, base: URL) -> URL:
    """Resolve a path-only or query-only relative reference against a base URL.

    Handles the two shapes this course's later modules actually produce:
    an absolute path ("/other.html") and a query-only reference
    ("?x=1"). Does not implement full RFC 3986 relative resolution
    (".." segments, scheme-relative "//host/path", etc.) — see
    DECISIONS.md for why that's out of scope.
    """
    if "?" in rest:
        path, query = rest.split("?", 1)
    else:
        path, query = rest, ""

    if path == "":
        path = base.path            # query-only reference: keep base's path
    elif not path.startswith("/"):
        raise ValueError(f"relative path {rest!r} must start with '/' "
                          f"(only absolute-path references are supported)")

    return URL(scheme=base.scheme, host=base.host, port=base.port,
               path=path, query=query, fragment=fragment)


if __name__ == "__main__":
    samples = [
        "https://example.com/index.html",
        "http://example.com:8080/search?q=browsers&page=2",
        "https://example.com",
        "https://example.com/a/b/c#section-2",
        "https://example.com:443/",
    ]

    print("=" * 70)
    print("Parsing absolute URLs")
    print("=" * 70)
    for s in samples:
        u = parse_url(s)
        print(f"\n{s!r}")
        print(f"  scheme={u.scheme!r} host={u.host!r} port={u.port} "
              f"path={u.path!r} query={u.query!r} fragment={u.fragment!r}")
        print(f"  origin() = {u.origin()!r}")

    print()
    print("=" * 70)
    print("Resolving a relative URL against a base")
    print("=" * 70)
    base = parse_url("https://example.com/docs/index.html")
    rel = parse_url("/docs/other.html", base=base)
    print(f"base={base.path!r}, relative '/docs/other.html' -> {rel.path!r}")

    # ---- Self-check against Python's own urllib.parse, used ONLY as an
    # oracle to verify our from-scratch logic — never imported by the
    # parser itself above this line. ----
    print()
    print("=" * 70)
    print("Cross-checking against urllib.parse.urlsplit (verification only)")
    print("=" * 70)
    from urllib.parse import urlsplit
    all_ok = True
    for s in samples:
        ours = parse_url(s)
        theirs = urlsplit(s)
        their_host = theirs.hostname
        their_port = theirs.port or DEFAULT_PORTS[theirs.scheme]
        their_path = theirs.path or "/"
        ok = (ours.scheme == theirs.scheme and ours.host == their_host and
              ours.port == their_port and ours.path == their_path and
              ours.query == theirs.query and ours.fragment == theirs.fragment)
        all_ok &= ok
        print(f"  {s!r}: {'MATCH' if ok else 'MISMATCH'}")
    print(f"\nAll samples matched urllib.parse: {all_ok}")
