"""
Module 26 — URL Encoding & Decoding
======================================
Proves: percent-encoding an untrusted value before splicing it into a
URL prevents it from being reinterpreted as URL STRUCTURE (an extra
query parameter, a path segment boundary, a fragment) — verified by
actually parsing the resulting URL with Module 2's real parser and
confirming the attack that works WITHOUT encoding no longer works WITH
it.

This is XSS's quieter sibling: "parameter injection" / query-string
injection. Not markup running in a browser — a value smuggling in
structure it was never supposed to have, at the URL layer, before HTML
is even involved.
"""

import os
import string
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "02_url_parser"))
from url_parser import parse_url   # noqa: E402  -- REUSED, unmodified

UNRESERVED = set(string.ascii_letters + string.digits + "-._~")


def percent_encode(s: str, safe: str = "") -> str:
    """RFC 3986 percent-encoding: every byte that isn't 'unreserved' (or
    explicitly marked safe for this context) becomes %XX, using its
    UTF-8 byte value. Operating on UTF-8 BYTES, not characters, is what
    makes this correct for non-ASCII input — see DECISIONS.md."""
    out = []
    for byte in s.encode("utf-8"):
        ch = chr(byte)
        if ch in UNRESERVED or ch in safe:
            out.append(ch)
        else:
            out.append(f"%{byte:02X}")
    return "".join(out)


def percent_decode(s: str) -> str:
    """The inverse: accumulate raw BYTES (decoding %XX and literal
    characters alike into their UTF-8 byte form) before doing ONE final
    UTF-8 decode at the end — necessary because a single UTF-8 character
    can span multiple %XX escapes."""
    out = bytearray()
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "%" and i + 2 < n and all(ch in string.hexdigits for ch in s[i + 1:i + 3]):
            out.append(int(s[i + 1:i + 3], 16))
            i += 3
        else:
            out.extend(c.encode("utf-8"))
            i += 1
    return out.decode("utf-8", errors="replace")


def encode_uri_component(s: str) -> str:
    """For a single VALUE going into a URL (a query param's value, a
    path segment) — encode everything that isn't unreserved, including
    URL-structural characters like & = / ? #, so the value can never be
    mistaken for URL syntax."""
    return percent_encode(s, safe="")


def encode_uri(s: str) -> str:
    """For encoding a WHOLE, already-structured URI — leave the
    characters that make up URI syntax itself alone (: / ? # [ ] @ and
    the sub-delims), only encode genuinely unsafe characters (spaces,
    quotes, control characters, non-ASCII). See DECISIONS.md for why
    this needs a DIFFERENT safe set than encode_uri_component."""
    return percent_encode(s, safe=";/?:@&=+$,#")


if __name__ == "__main__":
    print("=" * 70)
    print("CASE 1 — round-trip correctness, including non-ASCII input")
    print("=" * 70)
    original = "héllo world! ¥100 & 50% off?"
    encoded = encode_uri_component(original)
    decoded = percent_decode(encoded)
    print(f"  original: {original!r}")
    print(f"  encoded:  {encoded!r}")
    print(f"  decoded:  {decoded!r}")
    print(f"  round-trip is lossless: {decoded == original}")

    print()
    print("=" * 70)
    print("CASE 2 — the actual vulnerability: query-string injection")
    print("=" * 70)
    user_input = "cats&admin=true"

    print("  --- WITHOUT encoding (vulnerable) ---")
    unsafe_url = f"https://site.example/search?q={user_input}"
    print(f"  constructed URL: {unsafe_url}")
    parsed_unsafe = parse_url(unsafe_url)
    print(f"  Module 2 parses its query as: {parsed_unsafe.query!r}")
    print(f"  the attacker's 'admin=true' is now a SEPARATE, real-looking "
          f"parameter, not part of the search text: "
          f"{'admin=true' in parsed_unsafe.query.split('&')}")

    print()
    print("  --- WITH encode_uri_component (safe) ---")
    safe_url = f"https://site.example/search?q={encode_uri_component(user_input)}"
    print(f"  constructed URL: {safe_url}")
    parsed_safe = parse_url(safe_url)
    print(f"  Module 2 parses its query as: {parsed_safe.query!r}")
    recovered_value = percent_decode(parsed_safe.query.split("=", 1)[1])
    print(f"  decoding the single 'q' value recovers the ORIGINAL string "
          f"whole, as ONE value: {recovered_value!r}")
    print(f"  no second 'admin' parameter exists anywhere in the query: "
          f"{'admin' not in [p.split('=')[0] for p in parsed_safe.query.split('&')]}")

    print()
    print("=" * 70)
    print("CASE 3 — encode_uri vs encode_uri_component on the SAME input")
    print("=" * 70)
    full_uri = "https://site.example/path with spaces?q=a&b=c"
    print(f"  encode_uri(...):           {encode_uri(full_uri)!r}")
    print(f"  encode_uri_component(...): {encode_uri_component(full_uri)!r}")
    print(f"  encode_uri preserves URL structure (: / ? &) but escapes the "
          f"space; encode_uri_component escapes EVERYTHING, destroying the "
          f"structure — correct when used on a whole URI vs. a single value, "
          f"wrong the other way around.")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"round-trip encode/decode is lossless for non-ASCII input: "
          f"{decoded == original}")
    print(f"UNENCODED input successfully injects a second query parameter "
          f"(the real vulnerability, reproduced): "
          f"{'admin=true' in parsed_unsafe.query}")
    print(f"ENCODED input does NOT inject a second parameter — query has "
          f"exactly one '=' at the top level: "
          f"{parsed_safe.query.count('=') == 1}")
    print(f"the encoded value, once decoded back out, exactly equals the "
          f"original malicious-looking string (proving no data was lost, "
          f"only its INTERPRETATION as structure was prevented): "
          f"{recovered_value == user_input}")
