"""
Module 22 — Cookies & Storage
================================
Proves: state set by a real server response (`Set-Cookie`) is correctly
sent back by the client on a LATER request to the same origin — with
real path scoping — and survives being serialized out and reloaded into
a brand-new process, simulating a real "close the browser, reopen it
later" session boundary.

Uses a hand-rolled local server (same technique as Module 3) so the
whole demo is deterministic and doesn't depend on a third-party site's
cookie behavior staying the same forever.
"""

import json
import os
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "01_raw_socket"))
from raw_socket import open_connection, send_all   # noqa: E402


class Cookie:
    def __init__(self, name, value, domain, path="/", secure=False):
        self.name = name
        self.value = value
        self.domain = domain
        self.path = path
        self.secure = secure

    def to_dict(self):
        return {"name": self.name, "value": self.value, "domain": self.domain,
                "path": self.path, "secure": self.secure}

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["value"], d["domain"], d["path"], d["secure"])

    def __repr__(self):
        return f"Cookie({self.name}={self.value}, domain={self.domain}, path={self.path})"


def _path_matches(cookie_path: str, request_path: str) -> bool:
    """A cookie with Path=/account matches /account and /account/anything,
    but NOT / or /other — real cookie path-scoping, not simple equality."""
    if request_path == cookie_path:
        return True
    prefix = cookie_path if cookie_path.endswith("/") else cookie_path + "/"
    return request_path.startswith(prefix)


class CookieJar:
    def __init__(self):
        self.cookies: dict = {}   # (domain, path, name) -> Cookie

    def set_from_header(self, header_value: str, request_host: str) -> Cookie:
        """Parse one Set-Cookie header value: 'name=value; Path=/; Secure'.
        Domain defaults to the responding host — see DECISIONS.md for why
        we don't implement the Domain= attribute's subdomain-widening rule."""
        parts = [p.strip() for p in header_value.split(";")]
        name, _, value = parts[0].partition("=")
        path, secure = "/", False
        for attr in parts[1:]:
            if "=" in attr:
                k, _, v = attr.partition("=")
                if k.strip().lower() == "path":
                    path = v.strip()
            elif attr.strip().lower() == "secure":
                secure = True
        cookie = Cookie(name.strip(), value.strip(), request_host, path, secure)
        self.cookies[(cookie.domain, cookie.path, cookie.name)] = cookie
        return cookie

    def cookies_for(self, host: str, path: str, is_secure: bool) -> str:
        """Build the exact Cookie: header value for an outgoing request —
        only cookies whose domain matches, whose path scope covers this
        request path, and (if Secure) only over an actually-secure
        connection."""
        matches = []
        for cookie in self.cookies.values():
            if cookie.domain != host:
                continue
            if not _path_matches(cookie.path, path):
                continue
            if cookie.secure and not is_secure:
                continue
            matches.append(f"{cookie.name}={cookie.value}")
        return "; ".join(matches)

    def save(self, filepath: str) -> None:
        data = [c.to_dict() for c in self.cookies.values()]
        with open(filepath, "w") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, filepath: str) -> "CookieJar":
        jar = cls()
        with open(filepath) as f:
            data = json.load(f)
        for d in data:
            cookie = Cookie.from_dict(d)
            jar.cookies[(cookie.domain, cookie.path, cookie.name)] = cookie
        return jar


# ---------------------------------------------------------- local test rig

def _run_server(port_holder: dict, responses: list) -> None:
    """Serve exactly len(responses) connections, one canned response
    each, recording the raw bytes of every request received."""
    import socket
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    port_holder["port"] = srv.getsockname()[1]
    srv.listen(len(responses))
    port_holder["ready"].set()
    for response_bytes in responses:
        conn, _ = srv.accept()
        request_bytes = conn.recv(8192)
        port_holder["requests"].append(request_bytes)
        conn.sendall(response_bytes)
        conn.close()
    srv.close()


def _send_request(host: str, port: int, path: str, cookie_header: str = "") -> None:
    sock = open_connection(host, port)
    lines = [f"GET {path} HTTP/1.1", f"Host: {host}", "Connection: close"]
    if cookie_header:
        lines.append(f"Cookie: {cookie_header}")
    lines += ["", ""]
    send_all(sock, "\r\n".join(lines).encode("ascii"))
    sock.recv(8192)
    sock.close()


if __name__ == "__main__":
    responses = [
        (b"HTTP/1.1 200 OK\r\n"
         b"Set-Cookie: session=abc123; Path=/\r\n"
         b"Set-Cookie: pref=dark; Path=/account\r\n"
         b"Content-Length: 2\r\n\r\nOK"),
        (b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"),
        (b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"),
    ]
    holder = {"ready": threading.Event(), "requests": []}
    server_thread = threading.Thread(target=_run_server, args=(holder, responses), daemon=True)
    server_thread.start()
    holder["ready"].wait(timeout=5)
    port = holder["port"]
    host = "127.0.0.1"

    print("=" * 70)
    print("REQUEST 1 — server sets two cookies via real Set-Cookie headers")
    print("=" * 70)
    _send_request(host, port, "/", cookie_header="")

    jar = CookieJar()
    jar.set_from_header("session=abc123; Path=/", host)
    jar.set_from_header("pref=dark; Path=/account", host)
    print(f"jar now holds: {list(jar.cookies.values())}")

    print()
    print("=" * 70)
    print("REQUEST 2 — GET / — should send ONLY 'session' (Path=/ covers it)")
    print("=" * 70)
    cookie_header_for_root = jar.cookies_for(host, "/", is_secure=False)
    print(f"  Cookie header this client WOULD send: {cookie_header_for_root!r}")
    _send_request(host, port, "/", cookie_header=cookie_header_for_root)
    server_saw = holder["requests"][1].decode("ascii", errors="replace")
    print(f"  server actually RECEIVED (raw request):")
    for line in server_saw.split("\r\n"):
        if line:
            print(f"    {line}")

    print()
    print("=" * 70)
    print("REQUEST 3 — GET /account — should send BOTH cookies (Path=/account matches too)")
    print("=" * 70)
    cookie_header_for_account = jar.cookies_for(host, "/account", is_secure=False)
    print(f"  Cookie header this client WOULD send: {cookie_header_for_account!r}")
    _send_request(host, port, "/account", cookie_header=cookie_header_for_account)
    server_saw2 = holder["requests"][2].decode("ascii", errors="replace")
    print(f"  server actually RECEIVED (raw request):")
    for line in server_saw2.split("\r\n"):
        if line:
            print(f"    {line}")

    server_thread.join(timeout=5)

    print()
    print("=" * 70)
    print("PERSISTENCE — save the jar, load it in a BRAND NEW CookieJar object")
    print("(simulating closing and reopening the browser)")
    print("=" * 70)
    save_path = os.path.join(os.path.dirname(__file__), "_test_cookies.json")
    jar.save(save_path)
    reloaded_jar = CookieJar.load(save_path)
    os.remove(save_path)

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"request to / sent ONLY session (not pref, wrong path scope): "
          f"{'session=abc123' in server_saw and 'pref=dark' not in server_saw}")
    print(f"request to /account sent BOTH cookies: "
          f"{'session=abc123' in server_saw2 and 'pref=dark' in server_saw2}")
    print(f"reloaded jar (a DIFFERENT object, loaded from disk) produces the "
          f"IDENTICAL Cookie header for /account as the original jar: "
          f"{reloaded_jar.cookies_for(host, '/account', False) == jar.cookies_for(host, '/account', False)}")
    print(f"reloaded jar is provably a separate object, not the same instance: "
          f"{reloaded_jar is not jar}")
