# GLOSSARY.md — Build a Browser From Scratch

Alphabetical. Every entry is appended the module it's first substantively
introduced in — never rewritten, only added to or corrected in place.
"First seen" points to the module whose tutorial explains the term in
depth; earlier passing mentions (e.g. in Module 0's map) don't count.

---

**Allowlist** — a security filtering strategy that permits only explicitly-recognized items and rejects everything else by default, so an unanticipated dangerous item is excluded automatically rather than requiring a prior update. Contrast with a denylist, which must be updated for every newly-discovered danger. *First seen: Module 30.*

**AST (Abstract Syntax Tree)** — the tree structure a parser produces from tokens, representing a program's grammatical structure; a tree-walking interpreter evaluates it recursively. *First seen: Module 18.*

**Adoption Agency Algorithm** — the real HTML spec's algorithm for reopening a formatting element (like `<i>`) after it's implicitly closed by a misnested end tag, so later content keeps the intended formatting. Named but not implemented in this course. *First seen: Module 6.*

**AF_INET** — the socket address family selecting IPv4 (32-bit) addresses, as opposed to `AF_INET6` for IPv6. Chosen for `socket.socket()`'s first argument. *First seen: Module 1.*

**At-Rule** — a CSS construct starting with `@` (e.g. `@media`, `@font-face`) that doesn't follow the plain `selector { declarations }` shape; this course's parser detects and skips these blocks whole rather than parsing them. *First seen: Module 7.*

**Attribute Breakout** — an XSS technique where an unescaped quote character inside an attribute's value closes it early, letting the rest of the payload be parsed as new, real HTML attributes. *First seen: Module 28.*

**Authority** — the `host[:port]` portion of a URL, between `scheme://` and the path; splits further into host and an optional port. *First seen: Module 2.*

**Block Formatting Context** — a region where block-level boxes stack vertically, each one's position and auto-size resolved relative to the same containing block. *First seen: Module 11.*

**Box Model** — the layered structure of every rendered element: a content box, wrapped by padding, wrapped by a border, wrapped by margin — each layer's size defined in terms of the one inside it. *First seen: Module 10.*

**Box-Sizing** — the CSS property deciding whether `width`/`height` describe the content box (`content-box`, the default) or the border box (`border-box`), changing which formula computes content size from the declared width. *First seen: Module 10.*

**Broker Process** — the trusted side of a sandboxing architecture; holds real system access and mediates every privileged request from an untrusted renderer process against a policy. *First seen: Module 25.*

**Browser Application (Track 2)** — everything built on top of the rendering engine to make it a usable app: chrome UI, tabs, history, cookies, security policy, process isolation. Has no equivalent without the rendering engine underneath it. *First seen: Module 0.*

**Byte Stream** — the abstraction TCP provides: an ordered, reliable sequence of bytes with no built-in concept of "messages" — framing (like HTTP's headers/body split) has to be layered on top by the application. *First seen: Module 1.*

**Cascade** — the CSS conflict-resolution algorithm that picks exactly one winning value per property when multiple parsed rules match the same element, using specificity, source order, and `!important`. Distinct from *parsing* CSS. *First seen: Module 0 (map); built in Module 9.*

**Certificate Authority (CA)** — a trusted entity that digitally signs certificates, vouching that a public key belongs to a specific hostname; a client's OS/browser ships a list of CAs it trusts, and verification checks a certificate chains back to one. *First seen: Module 4.*

**Chrome UI** — the parts of a browser that exist outside any single web page: address bar, tabs, back/forward buttons, bookmarks. *First seen: Module 0.*

**Chunked Encoding** (`Transfer-Encoding: chunked`) — an HTTP body framing where data is sent as labeled, size-prefixed chunks, ending in a zero-size chunk, letting the reader know the body is complete without needing `Content-Length` or a closed connection. *First seen: Module 3.*

**Client** — in the client-server model, the side that always initiates a request and waits for a response; a browser is always the client. *First seen: prereqs/client_server_model.html.*

**Compositing** — combining separately-painted layers into the final on-screen image in the correct visual (stacking) order, independent of DOM order. *First seen: Module 0 (map); built in Module 16.*

**Closure** — a function value bundled with the lexical scope it was defined in, so it can still access that scope's variables long after the code that created it has returned. *First seen: Module 18.*

**Compound Selector** — one unit of a CSS selector with no combinator inside it, combining a type name with any number of class/id qualifiers (e.g. `div.card#main`), all ANDed together. *First seen: Module 7, matched in Module 8.*

**Computed Style** — the final, one-value-per-property result of the cascade for a given node: every conflict resolved, inheritance applied, initial values filled in. *First seen: Module 9.*

**Containing Block** — the rectangle (position + width) a box's percentage/auto sizes and position are resolved against — normally its parent's content box. *First seen: Module 11.*

**Content-Length** — an HTTP response header stating the exact byte length of the body, letting a client know precisely when to stop reading without waiting for the connection to close. *First seen: Module 3.*

**Cookie** — a small piece of state a server asks the client to store via `Set-Cookie` and resend on later matching requests, scoped by host and path. *First seen: Module 22.*

**Cookie Jar** — the client-side store of all cookies, responsible for matching which stored cookies apply to a given outgoing request (host, path, and connection security). *First seen: Module 22.*

**CRLF Injection** — smuggling a raw `\r\n` into a value reflected into an HTTP header, forging what looks like a new, legitimate header line to any real parser. Also called HTTP response/request splitting. *First seen: Module 29.*

**CSSOM** — the CSS Object Model: the structured, in-memory representation of parsed stylesheet rules, analogous to what the DOM is for HTML. *First seen: Module 0.*

**Declaration** — one `property: value` pair inside a CSS rule's block, optionally flagged `!important`. *First seen: Module 7.*

**Descendant Combinator** — whitespace between two compound selectors (e.g. `nav a`), meaning "an element matching the right side, anywhere inside an ancestor matching the left side." The only combinator this course's CSS parser supports. *First seen: Module 7.*

**DNS Resolution** — translating a hostname (`example.com`) into an IP address, performed by the OS resolver via `socket.connect()`. Treated as "hardware" in this course — never hand-implemented. *First seen: Module 1.*

**DOM (Document Object Model)** — the tree data structure a browser builds from parsed HTML, where every element, text run, and comment is a node with parent/child relationships. *First seen: Module 0 (map); built in Module 6.*

**DOM–JS Bindings** — the explicit glue code exposing specific DOM operations (like `getElementById`) to the JS engine; the DOM is not part of the JS language itself. *First seen: Module 0 (map); built in Module 19.*

**Display List** — a flat, ordered list of primitive draw commands (draw this rectangle, draw this text) produced from a laid-out tree, consumed by the rasterizer. *First seen: Module 0 (map); built in Module 14.*

**Draw Command** — one primitive instruction in a display list (`DrawRect`, `DrawBorder`, `DrawText`) — a self-contained "paint this one thing here" step with no knowledge of the tree it came from. *First seen: Module 14.*

**Encoding (text)** — the agreed-upon table mapping raw byte values to characters (e.g. UTF-8, ASCII); bytes have no inherent meaning as text without one. *First seen: prereqs/bytes_and_encoding.html.*

**Entity Encoding** — substituting HTML's special characters (`& < > " '`) with named/numeric references so untrusted text can never be tokenized as markup. *First seen: Module 27.*

**Ephemeral Port** — a temporary port number the OS assigns to the client side of a connection, used as a return address for responses; the client doesn't choose it. *First seen: Module 1.*

**Event Loop** — the loop that waits for events (input, timers, script completion) and dispatches each to its handler one at a time, guaranteeing one handler finishes before the next starts. *First seen: Module 0 (map); built in Module 17.*

**Flex-Grow** — a CSS property giving a flex item a ratio share of a flex container's leftover space; default 0 means an item never grows past its basis width. *First seen: Module 13.*

**Fragment** — the part of a URL after the first `#`; identifies a location within an already-fetched resource and is never sent to the server. *First seen: Module 2.*

**Greedy (First-Fit) Line Breaking** — the text-wrapping strategy real browsers use: pack words onto the current line until one doesn't fit, then start a new line, never revisiting earlier breaks. Cheaper than globally-optimal algorithms like Knuth-Plass, and what CSS normal flow actually specifies. *First seen: Module 12.*

**Handler** — a function registered to run in response to a specific event type (e.g. `click`); the unit of code an event loop dispatches to. *First seen: prereqs/event_driven_programming.html.*

**Header Block** — the portion of an HTTP message before the blank-line terminator (`\r\n\r\n`): the status/request line plus all header fields, parsed as text before any body-length decision is made. *First seen: Module 3.*

**HTTP Request / Response** — the two-message shape of an HTTP exchange: a request line + headers (+ optional body) sent by the client, answered by a status line + headers + body sent by the server. *First seen: Module 3.*

**Host Function** — a function implemented in the surrounding environment (Python, here) and exposed to script as a callable value — the mechanism `print` and every DOM binding use to cross from JS into the real system. *First seen: Module 18, used to build DOM bindings in Module 19.*

**Inheritance** — certain CSS properties (like `color`), when not explicitly set on a node, take their value from the parent's already-computed style rather than an initial default. *First seen: Module 9.*

**Initial Value** — the fallback value a CSS property takes when nothing in the cascade sets it and (for non-inherited properties) no parent value applies. *First seen: Module 9.*

**Invalidation (pipeline)** — the mechanism that, after a DOM mutation, triggers only the affected style/layout/paint recomputation rather than rebuilding the whole page. *First seen: Module 0 (map); built in Module 20.*

**JS Engine** — the component that tokenizes, parses, and executes JavaScript, specified (ECMAScript) with zero built-in knowledge of the DOM. *First seen: Module 0 (map); built in Module 18.*

**Key Selector** — the rightmost compound selector in a chain, checked first against a candidate node because it's the cheapest way to reject a non-matching rule before any ancestor walking happens. *First seen: Module 8.*

**Layer** — a real browser's unit of GPU-backed compositing (e.g. a promoted video or animated element), composited separately from the main 2D drawing surface. Named but not implemented in this course — see Module 16. *First seen: Module 16.*

**Layout** — the phase that assigns real x/y/width/height coordinates to every styled box, recursively, parent before child. *First seen: Module 0 (map); built in Modules 10–13.*

**Lexical Scoping** — the rule that a function's variable lookups resolve against the scope it was DEFINED in, not the scope it's CALLED from; the mechanism that makes closures work. *First seen: Module 18.*

**Line Box** — one wrapped line of inline content, with its own position, width, and height, stacked with other line boxes to fill a block's content area. *First seen: Module 12.*

**Navigation History** — the back/forward list of visited pages plus a pointer to the current one; visiting a new page while not at the end of the list truncates everything past the current position. *First seen: Module 21.*

**Open-Elements Stack** — the tree builder's record of which elements are currently "open" (started but not yet closed), top-to-bottom matching the current nesting depth; closing an element pops it and everything above it. *First seen: Module 6.*

**Origin** — the exact (scheme, host, port) triple that defines the web's unit of trust; two URLs are same-origin only if all three match exactly. *First seen: prereqs/origins_and_security_boundary.html.*

**Paint** — the phase that turns a laid-out tree into a display list of draw commands, prior to rasterization. *First seen: Module 0 (map); built in Module 14.*

**Paint Order** — the sequence in which overlapping elements are drawn, determined by z-index first and document order only as a tie-break — later-painted elements appear on top. *First seen: Module 13.*

**Percent-Encoding** — RFC 3986's scheme for representing an unsafe byte in a URL as `%XX` (its hex value); prevents untrusted data from being reinterpreted as URL structure (`&`, `=`, `/`, `?`, `#`). *First seen: Module 26.*

**Process** — an OS-isolated running program with its own private memory space, unreadable by other processes without an explicit, OS-mediated channel. *First seen: prereqs/processes_and_threads.html.*

**Process Model** — the architectural decision of which browser responsibilities (a tab, the chrome, the GPU) run in which OS process, for crash isolation and security. *First seen: Module 0 (map); built in Module 24.*

**Query String** — the part of a URL after `?` and before any `#`, conventionally `key=value` pairs joined by `&`, sent to the server as part of the request. *First seen: Module 2.*

**Rasterization** — converting draw commands (shapes, text) into actual pixels on a real drawing surface; this course delegates it entirely to Tkinter's `Canvas`. *First seen: Module 15.*

**RAWTEXT (tokenizer state)** — the HTML tokenizer mode used inside `<script>`/`<style>`, where content is captured as literal text and never re-interpreted as markup, until the matching end tag is found. *First seen: Module 5.*

**Recursive Descent Parsing** — a parsing technique with one function per grammar rule (or precedence level), each calling into others for its sub-parts; naturally encodes operator precedence without a separate table. *First seen: Module 18.*

**Reflow** — real browsers' term for re-running layout after a change; this course's Module 20 implements a bounded version of it via relayout boundaries. *First seen: Module 20.*

**Relative Reference** — a URL-like string with no scheme (e.g. `/about.html`), meaningful only when resolved against a base URL — typically the page it was found on. *First seen: Module 2.*

**Relayout Boundary** — the nearest ancestor with an explicit (non-auto) size, whose own box is guaranteed unaffected by changes inside it — the safe stopping point for a partial re-layout after a mutation. *First seen: Module 20.*

**Renderer Process** — the untrusted side of a sandboxing architecture; runs page content/script and must request privileged actions through a broker rather than performing them directly. *First seen: Module 25.*

**Rendering Engine (Track 1)** — the pure bytes-in, pixels-out transformation pipeline of a browser: networking through compositing, with no concept of tabs or chrome. *First seen: Module 0.*

**Run-to-Completion** — the guarantee that a running task/handler finishes entirely before the event loop starts the next one; the mechanism that keeps the DOM consistent for anything observing it. *First seen: Module 17.*

**Same-Origin Policy** — the browser-enforced rule that script from one origin cannot read DOM, cookies, or storage belonging to a different origin. *First seen: Module 0 (map); built in Module 23.*

**Sandboxing Broker** — a separate, trusted process that mediates and policy-checks privileged actions requested by an untrusted renderer process, which cannot perform those actions directly. *First seen: Module 0 (map); built in Module 25.*

**Scheme** — the part of a URL before `://` (e.g. `https`), identifying which protocol to use; determines the default port when none is given. *First seen: Module 2.*

**Selector** — the part of a CSS rule stating which elements it applies to; a comma-separated group of one or more compound selectors chained by combinators. *First seen: Module 7.*

**Seccomp-bpf** — a Linux kernel mechanism that enforces a syscall allow/deny filter on a process from OUTSIDE it, so even fully-compromised code inside that process cannot make a disallowed system call. The real mechanism this course's Module 25 broker/target protocol names but does not implement. *First seen: Module 25.*

**Server** — in the client-server model, the side that only ever responds to a received request; never initiates. *First seen: prereqs/client_server_model.html.*

**SNI (Server Name Indication)** — a TLS extension where the client states which hostname it's connecting to during the handshake itself, before any HTTP request is sent, letting one IP address serve certificates for many different domains. *First seen: Module 4.*

**Sink** — an API that receives untrusted data and does something with it; whether that "something" is safe (textContent, a text-only sink) or dangerous (innerHTML, an HTML-parsing sink) depends entirely on the sink, not the data. *First seen: Module 31.*

**Socket** — an OS-provided handle representing one endpoint of a network connection, through which bytes are sent and received. *First seen: Module 1.*

**SOCK_STREAM** — the socket type selecting TCP: a reliable, ordered byte stream, as opposed to `SOCK_DGRAM` (UDP), which offers no ordering or delivery guarantees. *First seen: Module 1.*

**Status Line** — the first line of an HTTP response (e.g. `HTTP/1.1 200 OK`): protocol version, numeric status code, and reason phrase. *First seen: Module 3.*

**Specificity** — a 3-part (id count, class count, type count) score comparing two matching selectors; compared positionally, so any id outweighs any number of classes, which outweighs any number of type selectors. *First seen: Module 9.*

**Stacking Context** — a self-contained scope for z-index ordering; z-index values only compare meaningfully against siblings in the same stacking context, not globally. Not modeled in this course beyond one flat context — see Module 13. *First seen: Module 13.*

**State Machine** — a system always in exactly one named state from a fixed set, with explicit rules for the next state given the current state and next input; the standard shape of a tokenizer. *First seen: prereqs/state_machines.html.*

**Task Queue** — the FIFO queue an event loop pops from, one task at a time; new work posted mid-task always joins the back, never jumping ahead of already-queued work. *First seen: Module 17.*

**TCP Handshake** — the three-packet exchange (SYN, SYN-ACK, ACK) that establishes a TCP connection before any application data is sent, performed by the OS kernel. *First seen: Module 1.*

**Thread** — a separate execution path within a single process, sharing that process's memory completely with every other thread in it. *First seen: prereqs/processes_and_threads.html.*

**TLS (Transport Layer Security)** — the protocol that encrypts a TCP byte stream and verifies the server's identity via certificates, sitting entirely below HTTP; HTTPS is HTTP run over a TLS-wrapped socket. *First seen: Module 4.*

**Token** — one classified unit produced by a tokenizer (e.g. `StartTag`, `Text`, `Comment` for HTML) — the output of tokenizing and the input to tree-building. *First seen: Module 5.*

**Tree** — a data structure where each node has zero or more children and exactly one parent (except the root, which has none); the natural shape of HTML/DOM, CSS rule nesting, and a JS AST. *First seen: prereqs/trees_and_recursion.html.*

**URL (Uniform Resource Locator)** — a string identifying a resource and how to fetch it: scheme, authority (host/port), path, query, and fragment, always in that order. *First seen: Module 2.*

**Void Element** — an HTML element (like `<br>`, `<img>`, `<input>`) defined to never have children or a closing tag; the tree builder must never push these onto the open-elements stack. *First seen: Module 6.*

**XSS (Cross-Site Scripting)** — an injection vulnerability where untrusted data is interpreted as executable markup/script instead of inert text, because it crossed into an HTML/JS context without being correctly encoded first. *First seen: Module 27.*

**Z-Index** — a CSS property setting an element's paint priority within its stacking context; higher values paint later (on top), lower/negative values paint earlier (further back). *First seen: Module 13.*
