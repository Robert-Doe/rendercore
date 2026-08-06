"""
Module 1 — Raw TCP Socket Connection
=====================================
Proves: a socket opened by hand, with no `requests`/`urllib`, can exchange
real bytes with a real web server.

This module deliberately does NOT build a correct HTTP request. That's
Module 3's job. Here we send the smallest possible byte string that will
make a real server respond and hang up, purely to prove the *connection*
itself — open, send, receive, close — works with nothing but the `socket`
module (which we treat as "hardware": see ../prerequisites.html and
DECISIONS.md).
"""

import socket


def open_connection(host: str, port: int, timeout: float = 5.0) -> socket.socket:
    """Open a raw TCP connection to (host, port). Returns a connected socket.

    AF_INET   = use IPv4 addresses (a 4-byte number, not IPv6's 16-byte one)
    SOCK_STREAM = use TCP, not UDP: a reliable, ordered byte stream, which
                  is what HTTP is defined to run on top of.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((host, port))  # this line does DNS resolution + the TCP handshake
    return sock


def send_all(sock: socket.socket, data: bytes) -> None:
    """Send every byte of `data`, even if the OS needs several calls to do it.

    A single sock.send(data) call is allowed by the OS to send fewer bytes
    than you asked for — it returns how many it actually sent. sendall()
    is the standard-library helper that loops until everything is sent,
    but we spell out why it's necessary rather than treating it as magic.
    """
    sock.sendall(data)


def recv_all(sock: socket.socket, chunk_size: int = 4096) -> bytes:
    """Read from the socket until the other end closes the connection.

    recv() returns b"" (empty bytes) specifically to signal "the other side
    closed the connection" — not "there's nothing to read right now."
    Distinguishing those two cases is the whole reason this loop exists.
    """
    chunks = []
    while True:
        chunk = sock.recv(chunk_size)
        if not chunk:          # empty bytes = the peer closed the connection
            break
        chunks.append(chunk)
    return b"".join(chunks)


def demo(host: str = "example.com", port: int = 80) -> bytes:
    """Connect, send a minimal (deliberately not-yet-correct) request, and
    return the raw bytes that come back."""
    sock = open_connection(host, port)
    local_ip, local_port = sock.getsockname()
    print(f"[1] Connected. Local endpoint: {local_ip}:{local_port} "
          f"-> Remote endpoint: {host}:{port}")

    # NOT the real HTTP formatter (that's Module 3) — just enough bytes to
    # get a real server to respond and close the connection.
    minimal_request = (
        f"GET / HTTP/1.0\r\n"
        f"Host: {host}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode("ascii")

    print(f"[2] Sending {len(minimal_request)} bytes...")
    send_all(sock, minimal_request)

    print("[3] Waiting for the server to respond and close the connection...")
    raw_response = recv_all(sock)
    sock.close()
    print(f"[4] Connection closed. Received {len(raw_response)} raw bytes total.")

    return raw_response


if __name__ == "__main__":
    response = demo()

    print()
    print("=" * 60)
    print("First 120 raw bytes (this is genuinely just numbers —")
    print("see prereqs/bytes_and_encoding.html):")
    print("=" * 60)
    print(response[:120])

    print()
    print("=" * 60)
    print("The same bytes, decoded as text (first 300 characters):")
    print("=" * 60)
    print(response.decode("utf-8", errors="replace")[:300])
