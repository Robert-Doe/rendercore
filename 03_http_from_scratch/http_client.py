"""
Module 3 — Hand-Rolled HTTP/1.1 Request & Response
=====================================================
Proves: a correctly-formatted HTTP/1.1 request, sent over Module 1's raw
socket to a real server, gets a real response back — and that response
can be split into status/headers/body WITHOUT waiting for the connection
to close. That last part is the actual point of this module: Module 1's
recv_all() only worked because we cheated with "Connection: close" and a
server that honored it. A real client can't assume that — it has to read
the `Content-Length` header, or decode `Transfer-Encoding: chunked`
framing, to know exactly when a response ends.

No `http.client`, no `requests` — only Module 1's socket helpers and
Module 2's URL parser.
"""

import os
import socket
import sys
import threading
from dataclasses import dataclass, field

# Reuse Module 1 and Module 2 as sibling modules — see DECISIONS.md for
# why plain sys.path insertion (not a package) is the chosen convention.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "01_raw_socket"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "02_url_parser"))
from raw_socket import open_connection, send_all           # noqa: E402
from url_parser import parse_url, URL                       # noqa: E402


@dataclass
class HTTPResponse:
    status_code: int
    reason: str
    headers: dict = field(default_factory=dict)   # lowercase keys
    body: bytes = b""


def format_request(url: URL, method: str = "GET") -> bytes:
    """Build a spec-correct HTTP/1.1 request as raw bytes.

    Every header here exists because the spec or the server needs it —
    see DECISIONS.md for which is which.
    """
    target = url.path + (f"?{url.query}" if url.query else "")
    headers = {
        "Host": url.host,                      # required by HTTP/1.1, unlike 1.0
        "Connection": "close",                  # ask nicely; we don't rely on it
        "User-Agent": "FromScratchBrowser/0.1 (educational)",
        "Accept": "*/*",
    }
    lines = [f"{method} {target} HTTP/1.1"]
    lines += [f"{k}: {v}" for k, v in headers.items()]
    lines += ["", ""]   # blank line terminator: header block ends with \r\n\r\n
    return "\r\n".join(lines).encode("ascii")


# ---------------------------------------------------------------- reading


def _recv_until(sock: socket.socket, marker: bytes, buf: bytes = b"") -> tuple[bytes, bytes]:
    """Read from sock until `marker` is seen. Returns (before, after)."""
    while marker not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError(f"connection closed before {marker!r} was found")
        buf += chunk
    idx = buf.index(marker)
    return buf[:idx], buf[idx + len(marker):]


def _recv_exact(sock: socket.socket, n: int, buf: bytes = b"") -> tuple[bytes, bytes]:
    """Read until at least n bytes are buffered. Returns (first n bytes, leftover)."""
    while len(buf) < n:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("connection closed before body was fully received")
        buf += chunk
    return buf[:n], buf[n:]


def _read_chunked(sock: socket.socket, buf: bytes) -> bytes:
    """Decode 'Transfer-Encoding: chunked' framing (RFC 9112 §7.1).

    Format: <hex size>\\r\\n<that many bytes>\\r\\n ... repeated, terminated
    by a chunk of size 0 followed by a final \\r\\n. No dependency on the
    connection closing — the 0-size chunk IS the end-of-body signal.
    """
    body = bytearray()
    while True:
        size_line, buf = _recv_until(sock, b"\r\n", buf)
        chunk_size = int(size_line.split(b";")[0], 16)   # ';' introduces chunk extensions, ignored
        if chunk_size == 0:
            _, buf = _recv_until(sock, b"\r\n", buf)      # consume the final trailer/blank line
            break
        chunk_data, buf = _recv_exact(sock, chunk_size, buf)
        body += chunk_data
        _, buf = _recv_until(sock, b"\r\n", buf)          # consume the CRLF after each chunk's data
    return bytes(body)


def parse_response(sock: socket.socket) -> HTTPResponse:
    """Read one full HTTP response from an open socket.

    The load-bearing decision: body length comes from the response's own
    framing (Content-Length or chunked), never from "read until closed."
    """
    head, leftover = _recv_until(sock, b"\r\n\r\n")
    header_text = head.decode("iso-8859-1")   # header bytes are defined to be Latin-1/ASCII-safe
    status_line, *header_lines = header_text.split("\r\n")

    _, code_str, reason = status_line.split(" ", 2)
    headers = {}
    for line in header_lines:
        key, _, value = line.partition(":")
        headers[key.strip().lower()] = value.strip()

    if "content-length" in headers:
        length = int(headers["content-length"])
        body, _ = _recv_exact(sock, length, leftover)
    elif headers.get("transfer-encoding", "").lower() == "chunked":
        body = _read_chunked(sock, leftover)
    else:
        # Neither framing present — the only spec-legal fallback IS to
        # read until closed. Named explicitly so it's clear this is a
        # last resort, not the primary strategy.
        chunks = [leftover]
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        body = b"".join(chunks)

    return HTTPResponse(status_code=int(code_str), reason=reason,
                         headers=headers, body=body)


def fetch(url_string: str, base: URL | None = None) -> HTTPResponse:
    """Parse a URL (Module 2), open a connection (Module 1), send a
    request, and return the parsed response — the full round trip."""
    url = parse_url(url_string, base=base)
    sock = open_connection(url.host, url.port)
    try:
        send_all(sock, format_request(url))
        return parse_response(sock)
    finally:
        sock.close()


# ---------------------------------------------------------- local test rig


def _serve_once(port_holder: dict, response_bytes: bytes) -> None:
    """A minimal hand-rolled server: accept exactly one connection, send
    canned bytes, close. Used only to deterministically test our chunked
    decoder against a known-correct byte stream, independent of any real
    website's behavior on the day this runs."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    port_holder["port"] = srv.getsockname()[1]
    srv.listen(1)
    port_holder["ready"].set()
    conn, _ = srv.accept()
    conn.recv(4096)             # drain the request, we don't need to parse it here
    conn.sendall(response_bytes)
    conn.close()
    srv.close()


if __name__ == "__main__":
    print("=" * 70)
    print("PART 1 — real request against a real server")
    print("=" * 70)
    resp = fetch("http://example.com/")
    print(f"status: {resp.status_code} {resp.reason}")
    print(f"headers: {resp.headers}")
    print(f"body length: {len(resp.body)} bytes")
    print(f"body starts with: {resp.body[:60]!r}")

    print()
    print("=" * 70)
    print("PART 2 — hand-rolled local server sending chunked encoding")
    print("=" * 70)
    canned = (
        b"HTTP/1.1 200 OK\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"Connection: close\r\n"
        b"\r\n"
        b"7\r\nHello, \r\n"
        b"6\r\nWorld!\r\n"
        b"0\r\n\r\n"
    )
    holder = {"ready": threading.Event()}
    t = threading.Thread(target=_serve_once, args=(holder, canned), daemon=True)
    t.start()
    holder["ready"].wait(timeout=5)
    port = holder["port"]

    test_url = parse_url(f"http://127.0.0.1:{port}/")
    sock = open_connection(test_url.host, test_url.port)
    send_all(sock, format_request(test_url))
    chunked_resp = parse_response(sock)
    sock.close()
    t.join(timeout=5)

    print(f"status: {chunked_resp.status_code} {chunked_resp.reason}")
    print(f"headers: {chunked_resp.headers}")
    print(f"decoded body: {chunked_resp.body!r}")
    expected = b"Hello, World!"
    print(f"matches expected {expected!r}: {chunked_resp.body == expected}")
