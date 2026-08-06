# DECISIONS.md — Module 1: Raw TCP Socket Connection

Source file: `raw_socket.py`. Read alongside the source — every heading
below matches a function or block in it.

Category key: **(a)** forced by platform/OS/network reality — not a
choice · **(b)** forced by an external contract (a spec/protocol/format)
· **(c)** our own convention, chosen for clarity or safety.

---

### `socket.AF_INET`

**(b) External contract.** `AF_INET` selects IPv4 addressing. The
alternative, `AF_INET6`, is equally valid for a real browser (which
tries both — "happy eyeballs" — in practice). We hardcode IPv4 here
purely to keep one code path in a teaching module; a production client
would negotiate this, not pick one arbitrarily. Named as a contract, not
"just because," since the address family is dictated by what the target
server actually listens on.

### `socket.SOCK_STREAM`

**(b) External contract.** HTTP is specified to run over a *reliable,
ordered byte stream* — RFC 9110 assumes bytes arrive in the order sent,
with none lost or duplicated. TCP (`SOCK_STREAM`) is the transport that
provides that guarantee; UDP (`SOCK_DGRAM`) does not. We don't get to
choose this once we've decided to speak HTTP — the protocol dictates the
transport underneath it.

### `sock.settimeout(timeout)`

**(c) Our convention.** Nothing forces a timeout to exist — a socket call
will happily block forever waiting for a server that never responds. We
set one (5 seconds by default) specifically so a broken network condition
fails loudly and fast during learning, instead of hanging silently. A
different, equally valid convention would omit this and let calls block
indefinitely; we chose fail-fast for a debugging-friendly course.

### `sock.connect((host, port))`

**(a) Forced by the OS/network stack.** This single call does two things
neither of which we implement ourselves: it asks the OS resolver to turn
`host` into an IP address (DNS), then performs the actual TCP three-way
handshake (SYN, SYN-ACK, ACK) with the kernel's TCP/IP implementation.
Both are treated as "hardware" per the roadmap's Tools/Architecture
Target — reimplementing either is a networking-course, not a
browser-course, topic.

### Why `send_all()` exists instead of calling `sock.send()` once

**(a) Forced by the socket API's contract.** `sock.send(data)` is
permitted by the OS to transmit *fewer* bytes than requested under normal
conditions (e.g. the OS send buffer is momentarily full) — it returns the
actual count sent, and the caller is responsible for resending the rest.
`sendall()`, which we call from our `send_all()` wrapper, is the
stdlib's own loop that handles this. We wrap it in our own function name
(rather than calling `sock.sendall` directly at the call site) purely as
**(c) convention** — so every module downstream imports one obviously-named
`send_all` instead of remembering which raw method name is "the safe one."

### Why `recv_all()` loops on `sock.recv()` until it gets `b""`

**(a) Forced by the socket API's contract.** `recv(n)` returns *up to* `n`
bytes — a full HTTP response, even a small one, routinely arrives across
several `recv()` calls. `recv()` returning `b""` (empty bytes) is the
API's specific, unambiguous signal that the peer closed the connection —
it is not the same as "no data available right now" (which would instead
raise a timeout or block). Looping until that exact empty-bytes signal is
the only correct way to read "everything the server is going to send."

### Why the demo sends `Connection: close`

**(b) External contract, but a deliberate simplification.** HTTP/1.1
defaults to *keeping the connection open* for more requests
(`Connection: keep-alive`), which means a real client can't just "read
until the socket closes" the way `recv_all()` does — it has to know from
`Content-Length` or chunked-encoding framing exactly when the response
body ends, without waiting for the connection to close. We deliberately
sidestep that harder problem in Module 1 by requesting the server close
the connection for us, so `recv_all()`'s simple loop is sufficient. Module
3 removes this crutch and parses `Content-Length` properly, because a
real client can't always rely on `Connection: close`.

### Why the request line is HTTP/1.0, not HTTP/1.1, in this module only

**(c) Our convention, temporary and explicit.** `HTTP/1.0` servers close
the connection by default after one response, which pairs naturally with
`recv_all()`'s "read until closed" loop and lets Module 1 stay focused
on the socket, not the request format. Module 3 upgrades to a properly
formatted `HTTP/1.1` request and handles keep-alive framing correctly —
this module's request string is explicitly *not* the one to copy forward.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Use `AF_INET` (IPv4) only | (b) external contract, simplified |
| 2 | Use `SOCK_STREAM` (TCP) | (b) external contract |
| 3 | 5-second timeout on all socket ops | (c) convention, fail-fast for learning |
| 4 | DNS + TCP handshake left to `sock.connect()` | (a) forced by OS |
| 5 | Wrap `sendall()` in our own `send_all()` name | (c) convention |
| 6 | Loop `recv()` until `b""` in `recv_all()` | (a) forced by socket API contract |
| 7 | Demo request uses `Connection: close` | (b) contract, chosen to simplify |
| 8 | Demo request uses HTTP/1.0, not 1.1 | (c) convention, temporary |

## What We Proved

Running `raw_socket.py` opened a real TCP connection to `example.com:80`,
sent 56 hand-built bytes with no `requests`/`urllib`/`http.client` import,
and received a real 828-byte HTTP response back — headers, blank line,
and the start of an HTML document — using nothing but Python's `socket`
module. See `tutorial.html` section 06 for the exact, unedited output of
that run. The next module (URL Parser) builds the piece that decides
*which* host and port to connect to from a typed URL string; this module
proves the connection mechanics work once you have them.
