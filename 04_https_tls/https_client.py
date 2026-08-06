"""
Module 4 — TLS via Socket Wrapping (HTTPS)
=============================================
Proves: Module 3's exact request/response logic works over an encrypted
connection with ZERO changes — because HTTP and transport security are
genuinely separate layers. This module only adds one new thing: wrapping
the raw socket in TLS before handing it to code that already exists.

We do not implement TLS itself (no hand-rolled RSA, no hand-rolled AES,
no certificate chain math) — see DECISIONS.md for why that's treated as
"hardware," the same way DNS and TCP already are.
"""

import os
import ssl
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "01_raw_socket"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "02_url_parser"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "03_http_from_scratch"))
from raw_socket import open_connection, send_all              # noqa: E402
from url_parser import parse_url, URL                          # noqa: E402
from http_client import format_request, parse_response, HTTPResponse  # noqa: E402  -- UNCHANGED imports


def open_tls_connection(host: str, port: int, timeout: float = 5.0) -> ssl.SSLSocket:
    """Open a plain TCP connection (Module 1), then wrap it in TLS.

    ssl.create_default_context() loads the OS's trusted certificate
    authority list and turns on the two checks that actually make HTTPS
    meaningful: the server's certificate must chain to a trusted CA, AND
    the certificate's hostname must match the host we asked for.
    """
    raw_sock = open_connection(host, port, timeout=timeout)
    context = ssl.create_default_context()
    tls_sock = context.wrap_socket(raw_sock, server_hostname=host)
    return tls_sock


def fetch_https(url_string: str, base: URL | None = None) -> HTTPResponse:
    """Identical shape to Module 3's fetch() — only the connection function
    changed, from open_connection() to open_tls_connection()."""
    url = parse_url(url_string, base=base)
    if url.scheme != "https":
        raise ValueError(f"fetch_https() only handles https:// URLs, got {url.scheme!r}")

    sock = open_tls_connection(url.host, url.port)
    try:
        print(f"  TLS established: {sock.version()}, cipher: {sock.cipher()[0]}")
        send_all(sock, format_request(url))          # <- Module 3's function, unmodified
        return parse_response(sock)                    # <- Module 3's function, unmodified
    finally:
        sock.close()


if __name__ == "__main__":
    print("=" * 70)
    print("PART 1 — a real HTTPS request, using Module 3's request/response")
    print("logic completely unmodified, just wrapped in TLS")
    print("=" * 70)
    resp = fetch_https("https://example.com/")
    print(f"status: {resp.status_code} {resp.reason}")
    print(f"body length: {len(resp.body)} bytes")
    print(f"body starts with: {resp.body[:60]!r}")

    print()
    print("=" * 70)
    print("PART 2 — proving verification is real: connecting to a site with")
    print("a deliberately EXPIRED certificate should fail, not succeed")
    print("=" * 70)
    try:
        fetch_https("https://expired.badssl.com/")
        print("UNEXPECTED: connection succeeded — verification did not run!")
    except ssl.SSLCertVerificationError as e:
        print(f"EXPECTED FAILURE (verification correctly rejected the cert):")
        print(f"  {type(e).__name__}: {e}")

    print()
    print("=" * 70)
    print("PART 3 — proving hostname checking is real: connecting to a host")
    print("whose certificate is valid for a DIFFERENT name should also fail")
    print("=" * 70)
    try:
        fetch_https("https://wrong.host.badssl.com/")
        print("UNEXPECTED: connection succeeded — hostname check did not run!")
    except ssl.SSLCertVerificationError as e:
        print(f"EXPECTED FAILURE (hostname mismatch correctly rejected):")
        print(f"  {type(e).__name__}: {e}")
