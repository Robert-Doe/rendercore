"""
Module 29 — HTTP Header Injection Prevention
================================================
Proves: a value containing a raw CRLF (\\r\\n), if spliced unsanitized
into an HTTP header, lets an attacker inject entirely new, fake headers
— verified end to end over a REAL socket connection, parsed by
Module 3's real, unmodified `parse_response()`. The attacker doesn't
need any HTML or script — CRLF alone is enough, because CRLF is what
header-parsing code (real or ours) uses to know "this header line just
ended."

This is the classic "HTTP response splitting" vulnerability class: a
server reflects untrusted input (a cookie, a query param, an
Accept-Language header) into a RESPONSE header without checking it for
line breaks.
"""

import os
import socket
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "01_raw_socket"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "03_http_from_scratch"))
from raw_socket import open_connection            # noqa: E402
from http_client import parse_response              # noqa: E402  -- REUSED, unmodified


def sanitize_header_value(value: str) -> str:
    """A header value must never contain CR or LF — RFC 9110 defines a
    header field value as excluding them entirely. Stripping both is
    the fix; see DECISIONS.md for why stripping (not just rejecting) is
    the choice made here."""
    return value.replace("\r", "").replace("\n", "")


def build_response(lang_value: str, body: str) -> bytes:
    headers = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: text/plain\r\n"
        f"Content-Language: {lang_value}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"\r\n"
        f"{body}"
    )
    return headers.encode("utf-8")


def _serve_once(port_holder: dict, response_bytes: bytes) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    port_holder["port"] = srv.getsockname()[1]
    srv.listen(1)
    port_holder["ready"].set()
    conn, _ = srv.accept()
    conn.recv(4096)
    conn.sendall(response_bytes)
    conn.close()
    srv.close()


def fetch_from_local_server(response_bytes: bytes):
    """Starts a one-shot local server sending EXACTLY `response_bytes`,
    connects a real client socket to it, and parses the reply with
    Module 3's real, unmodified parse_response()."""
    holder = {"ready": threading.Event()}
    t = threading.Thread(target=_serve_once, args=(holder, response_bytes), daemon=True)
    t.start()
    holder["ready"].wait(timeout=5)
    sock = open_connection("127.0.0.1", holder["port"])
    sock.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
    response = parse_response(sock)
    sock.close()
    t.join(timeout=5)
    return response


if __name__ == "__main__":
    malicious_lang = "en\r\nX-Injected: true\r\nSet-Cookie: admin=true"

    print("=" * 70)
    print("CASE 1 — UNSANITIZED: a CRLF-containing value reflected into a header")
    print("=" * 70)
    unsafe_bytes = build_response(malicious_lang, "hello")
    print("  raw bytes sent by the (malicious) server:")
    print(f"  {unsafe_bytes!r}")
    unsafe_response = fetch_from_local_server(unsafe_bytes)
    print(f"\n  Module 3's REAL parse_response() extracted these headers:")
    for k, v in unsafe_response.headers.items():
        print(f"    {k}: {v}")

    print()
    print("=" * 70)
    print("CASE 2 — SANITIZED: the same value, CR/LF stripped first")
    print("=" * 70)
    safe_bytes = build_response(sanitize_header_value(malicious_lang), "hello")
    print("  raw bytes sent by the (fixed) server:")
    print(f"  {safe_bytes!r}")
    safe_response = fetch_from_local_server(safe_bytes)
    print(f"\n  Module 3's REAL parse_response() extracted these headers:")
    for k, v in safe_response.headers.items():
        print(f"    {k}: {v}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"UNSANITIZED response has a REAL, fake 'x-injected' header, "
          f"parsed as genuine by Module 3's real client: "
          f"{'x-injected' in unsafe_response.headers}")
    print(f"UNSANITIZED response ALSO has a forged 'set-cookie' header — "
          f"a real cookie-injection vector, not just a curiosity: "
          f"{'set-cookie' in unsafe_response.headers and unsafe_response.headers['set-cookie'] == 'admin=true'}")
    print(f"SANITIZED response has NO injected headers at all: "
          f"{'x-injected' not in safe_response.headers and 'set-cookie' not in safe_response.headers}")
    print(f"SANITIZED response's content-language contains the ENTIRE "
          f"payload, squashed onto one line (data kept, structure removed): "
          f"{'X-Injected' in safe_response.headers['content-language']}")
