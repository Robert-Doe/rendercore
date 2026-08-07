# ROADMAP.md — Build a Browser From Scratch

**Status: APPROVED — under active construction.** Stack: Python 3.11+,
stdlib-only, Tkinter for pixels. See build log at the bottom of this file
for live per-module status (this table is hand-updated as modules complete;
it is the source of truth over anything a tutorial page implies).

## A note on scope

Your subject line asked "how would you create a browser... don't write the
code, it'll be very heavy." Your course template requires the opposite:
every module ships real, runnable, verified source. That's the version
that's actually being built — "head first" only works if you can run
something and watch it do the thing being explained. The "very heavy"
concern is handled by scope, not by skipping code: small modules,
stdlib-only, a toy JS interpreter instead of a spec-complete one, Tkinter
instead of a GPU compositor. See **Tools / Architecture Target** below for
exactly where the line is drawn and why.

---

## Why two tracks

A browser is two systems stacked on each other, the same way an OS is a
kernel plus the userland built on it:

- **Track 1 — The Rendering Engine**: the "kernel." Pure transformation
  pipeline — bytes off the wire in, pixels on a canvas out. No interactivity,
  no chrome, no multi-page state. It doesn't know a "browser" exists around
  it.
- **Track 2 — The Browser Application**: the "userland." Everything built
  *on top of* the engine to make it feel like the app you actually use —
  scripting, navigation, tabs, storage, security boundaries, process
  isolation.

Track 1 must be fully working before Track 2 module 17 begins — you cannot
build an event loop over a rendering pipeline that doesn't render yet.

Ahead of both tracks sits **Module 0**, a zero-code orientation module: every
component a real browser is made of, bits to pixels, and the role each one
plays, before any of them get built individually. Track 2 ends with a
**bonus Module 25** on sandboxing — the security architecture question of
"who's allowed to do what, and who stops them" that cuts across almost every
module before it.

---

## Module 0 — The Big Picture

| # | Module | What it proves | Directory | Status |
|---|--------|-----------------|-----------|--------|
| 0 | The Big Picture: Every Component, Bits to Pixels | You can name every major subsystem of a real browser, in the order data actually flows through them, and state in one sentence what each one is responsible for — before any of them exist as code | `00_big_picture/` | ✅ Done |

*(Zero-code by design — this module is a map, not a build. Everything it
names gets built for real starting Module 1.)*

---

## Track 1 — The Rendering Engine

### Phase 1: Bare Metal Foundation (getting bytes off the wire)

| # | Module | What it proves | Directory | Status |
|---|--------|-----------------|-----------|--------|
| 1 | Raw TCP Socket Connection | A socket opened by hand, with no `requests`/`urllib`, can exchange bytes with a real web server | `01_raw_socket/` | ✅ Done — verified live against example.com |
| 2 | URL Parser | A URL string can be decomposed into scheme/host/port/path/query without a parsing library | `02_url_parser/` | ✅ Done — verified against urllib.parse oracle |
| 3 | Hand-Rolled HTTP/1.1 Request & Response | A correctly-formatted request line + headers, sent over the raw socket, gets a real server to respond, and the response bytes can be split back into status/headers/body without a library | `03_http_from_scratch/` | ✅ Done — verified live (chunked) + local deterministic test |
| 4 | TLS via Socket Wrapping | The same request/response logic works unmodified over an encrypted channel (`ssl.wrap_socket`), proving HTTP and transport security are separate layers | `04_https_tls/` | ✅ Done — verified live + 2 negative security tests (expired cert, hostname mismatch) |

### Phase 2: From Bytes to a Document Tree

| # | Module | What it proves | Directory | Status |
|---|--------|-----------------|-----------|--------|
| 5 | HTML Tokenizer | A state machine can turn a raw HTML string into a stream of typed tokens (tag-open, tag-close, text, comment) | `05_html_tokenizer/` | ✅ Done — verified, 1 real bug caught &amp; fixed |
| 6 | HTML Tree Builder | Tokens can be assembled into a DOM tree, including recovering from real-world malformed/unclosed tags | `06_dom_tree_builder/` | ✅ Done — 5 malformed-HTML cases verified |
| 7 | CSS Tokenizer & Parser | A stylesheet string becomes a structured list of (selector, declaration-block) rules | `07_css_parser/` | ✅ Done — verified, 6 checks pass |
| 8 | Selector Matching Engine | For any DOM node, the engine can list exactly which parsed CSS rules match it | `08_selector_matching/` | ✅ Done — 4 matching scenarios verified |
| 9 | The Cascade | Given multiple matching, conflicting rules, the engine picks one winning value per property using specificity, source order, and `!important` — deterministically | `09_cascade/` | ✅ Done — 6 checks verified (specificity, order, !important, inheritance, initial values) |

### Phase 3: From Tree to Geometry

| # | Module | What it proves | Directory | Status |
|---|--------|-----------------|-----------|--------|
| 10 | The Box Model | Every styled node gets a computed content/padding/border/margin box, in the correct order of operations | `10_box_model/` | ✅ Done — 6 checks verified (content-box vs border-box, auto) |
| 11 | Block & Inline Layout | A tree of boxes can be assigned real x/y/width/height coordinates on a page, recursively | `11_block_inline_layout/` | ✅ Done — 6 checks verified, 2 real bugs found &amp; fixed |
| 12 | Text Layout & Line Breaking | A long run of text correctly wraps into multiple lines at a given container width, word by word | `12_text_line_breaking/` | ✅ Done — 3 cases verified, hand-math matched exactly |
| 13 | Stacking & a Flexbox Subset | A `flex` container distributes space among children on the main axis, and z-index ordering is resolved independent of DOM order | `13_flexbox_stacking/` | ✅ Done — flex + stacking checks verified |

### Phase 4: From Geometry to Pixels

| # | Module | What it proves | Directory | Status |
|---|--------|-----------------|-----------|--------|
| 14 | Paint / Display List | A laid-out tree becomes an ordered, flat list of primitive draw commands (rect, text, border) | `14_display_list/` | ✅ Done — verified, reuses Module 13's paint_order directly |
| 15 | Rasterization to Canvas | The display list, replayed against a Tkinter canvas, produces actual visible pixels matching the page | `15_rasterizer/` | ✅ Done — verified against real Tk canvas state |
| 16 | Compositing & Layers | Overlapping elements paint in the correct visual order via stacking contexts, not raw DOM order | `16_compositing/` | ✅ Done — verified via real pixel-level canvas query. **TRACK 1 COMPLETE** |

---

## Track 2 — The Browser Application

| # | Module | What it proves | Directory | Depends on (Track 1) | Status |
|---|--------|-----------------|-----------|----------------------|--------|
| 17 | The Event Loop | Input events (click, key) can be queued and processed in a loop without blocking the render pipeline | `17_event_loop/` | 15, 16 | ✅ Done — 4 guarantees verified |
| 18 | A Toy JS Interpreter | A tokenizer→parser→tree-walking evaluator can run a small real subset of JS (vars, functions, if/for, arithmetic) with no embedded engine (no V8/Duktape/QuickJS) | `18_toy_js_interpreter/` | — | ✅ Done — recursion + independent closures verified |
| 19 | DOM–JS Bindings | Script code (via module 18) can call `getElementById`/`innerHTML`-equivalents and observably mutate the real DOM from module 6 | `19_dom_js_bindings/` | 6 | ✅ Done — verified via pre-held object reference |
| 20 | Invalidation & Re-render Pipeline | A DOM mutation from script automatically triggers correct partial re-layout and re-paint, not a full rebuild | `20_invalidation_pipeline/` | 9, 11, 14, 15, 19 | ✅ Done — verified via object identity, 1 real bug found &amp; fixed |
| 21 | Chrome UI: Address Bar, Tabs, History | A user can type a URL, navigate, and go back/forward across multiple loaded pages with correct history state | `21_chrome_ui/` | 1–16 | ✅ Done — verified live against 2 real sites incl. truncation |
| 22 | Cookies & Storage | State set by one response (or by script) is correctly sent back on a later request to the same origin, and survives across "sessions" | `22_cookies_storage/` | 3, 19 | ✅ Done — verified via real socket round-trip + persistence |
| 23 | Same-Origin Policy | A script from origin A is provably blocked from reading DOM/storage belonging to origin B loaded in another tab | `23_same_origin_policy/` | 19, 22 | ✅ Done — 5 checks verified incl. same-host/different-scheme case |
| 24 | Multi-Process Tab Isolation | Each tab runs as a separate OS process (via `multiprocessing`, standing in for Chromium's process model); crashing one tab's process leaves the others and the chrome process alive | `24_process_isolation/` | 21 | ✅ Done — verified via real OS processes, real crash, post-crash re-ping |
| 25 | **Bonus:** Sandboxing Deep Dive | A renderer process, stripped of direct filesystem/network access, can *only* act through a policy-checked broker process — and a request outside the allow-list is provably denied, not just "trusted not to happen" | `25_sandboxing/` | 24, 23, 4 | ✅ Done — verified: real denial + honest malicious-bypass demonstration. **ALL 26 MODULES COMPLETE** |

**Total: 26 modules (1 orientation + 16 in Track 1 + 9 in Track 2, incl. the sandboxing bonus).**

---

## Track 2 (extension) — Phase 5: XSS Defense — Encoders & Sanitizers

Added after the original 26-module course, at the user's request, to cover
the encoding/sanitization boundaries a real browser (and the servers it
talks to) rely on to prevent Cross-Site Scripting. Every module here
extends an EXISTING module rather than starting fresh — XSS defense is
fundamentally about correctly encoding untrusted data at each boundary
where it crosses into a new interpretation context (URL, HTML body, HTML
attribute, HTTP header, or the DOM itself), so each module below attaches
to the specific earlier module that owns that boundary.

| # | Module | What it proves | Directory | Depends on | Status |
|---|--------|-----------------|-----------|------------|--------|
| 26 | URL Encoding & Decoding | Percent-encoding a value before inserting it into a URL prevents it from being reinterpreted as extra path/query/fragment structure — verified against Module 2's own parser | `26_url_encoding/` | 2 | ✅ Done — real injection reproduced &amp; prevented |
| 27 | HTML Entity Encoding | Encoding untrusted text before inserting it into an HTML body prevents it from being tokenized as markup — verified by feeding encoded output back through Module 5's real tokenizer | `27_entity_encoding/` | 5 | ✅ Done — real `&lt;script&gt;` payload neutralized, verified via real tokenizer |
| 28 | Attribute & URL-Scheme Encoding | HTML-attribute context needs different escaping rules than body text, and `javascript:`-scheme URLs in `href`/`src` need to be blocked outright — both proven against real parsing/matching, not just described | `28_attribute_encoding/` | 5, 6 | ✅ Done — breakout + scheme-check bypass both reproduced &amp; fixed |
| 29 | HTTP Header Injection Prevention | A value containing a raw CRLF cannot be used to inject extra HTTP headers or split the response, verified against Module 3's real request formatter | `29_header_injection/` | 3 | ✅ Done — real socket round-trip, forged Set-Cookie reproduced &amp; blocked |
| 30 | HTML Sanitization (Allowlist-Based) | Untrusted HTML can have disallowed tags, attributes, and dangerous URL schemes stripped while preserving safe structure — verified by parsing real malicious payloads with Module 6 and checking the sanitized tree | `30_html_sanitization/` | 5, 6 | ✅ Done — 10 checks verified against real sanitized tree |
| 31 | The DOM XSS Sink: innerHTML vs. textContent | Routing untrusted text through an HTML-parsing sink (`innerHTML`-equivalent) executes injected markup, while routing the exact same text through a text-only sink (Module 19's `setText`) never does — the actual, reproducible mechanism behind real DOM-based XSS | `31_dom_xss_sink/` | 6, 19 | ✅ Done — one identical payload, 3 verified outcomes. **ALL 32 MODULES COMPLETE** |

**Total (with this extension): 32 modules — ALL COMPLETE.**

---

## Recommended Stopping Points

| Goal | Stop at |
|------|---------|
| "I just want to understand how HTTP actually works under the hood" | Module 4 |
| "I want to understand how a page of text becomes a DOM + computed styles" | Module 9 |
| "I want the full static-page pipeline: request → pixels on screen, no scripting" | Module 16 *(a complete, if inert, rendering engine)* |
| "I want pages that respond to clicks and run scripts" | Module 20 |
| "I want the full experience: tabs, history, cookies, security boundaries" | Module 24 |
| "I want to understand *why* browsers are considered relatively safe to point at untrusted websites" | Module 25 *(the whole course)* |

Module 0 is not a stopping point — read it first regardless of where you stop, it's the map for everything below it.

---

## Tools / Architecture Target

**Language:** Python 3.11+. Chosen because its stdlib already contains the
"hardware" layer we're allowed to assume (see below) without hiding any of
the logic we're actually here to learn behind unfamiliar syntax.

**Rendering surface:** Tkinter `Canvas` (stdlib, ships with Python). It gives
us an immediate-mode 2D drawing surface — `draw_rect`, `draw_text` — and
nothing else. It stands in for a GPU compositor the way a textbook OS course
uses QEMU instead of real silicon.

**What we build ourselves (no library import allowed for these — this *is*
the course):**
HTTP request/response formatting and parsing · HTML tokenizer/parser/DOM ·
CSS tokenizer/parser/selector matching/cascade · box model · block/inline/
flex layout · text line breaking · display-list generation · the JS
tokenizer/parser/interpreter · DOM–JS bindings · cookie jar · same-origin
enforcement.

**What we treat as "hardware" (imported, not rebuilt, exactly like an OS
course doesn't ask you to fabricate a CPU):**
- `socket` — the OS TCP/IP stack. Reimplementing TCP is a networking course,
  not a browser course.
- `ssl` — wraps OpenSSL for TLS. Reimplementing RSA/AES/certificate math is
  a cryptography course.
- `tkinter` — wraps the OS's native windowing system and Tk's renderer for
  the final pixel-push and for keyboard/mouse event delivery.
- `multiprocessing` — OS process creation, standing in for Chromium's
  process model in Module 24.
- `subprocess` + OS pipes — used in Module 25 to build a real broker/target
  process pair. The *policy engine* (what's allowed) is ours; the *process
  boundary itself* (one process literally cannot touch another's memory) is
  the OS's, the same way a real browser leans on the OS process boundary
  and then layers seccomp-bpf (Linux) / restricted tokens & AppContainer
  (Windows) / the Sandbox.kext (macOS) on top of it. We approximate that
  extra OS-level layer with our own policy broker and say so explicitly in
  Module 25's docs — see its DECISIONS.md for exactly which real primitive
  each piece of our sandbox stands in for.

**Explicitly out of scope** (named so nobody expects it later): full
ECMAScript spec compliance, JIT compilation / bytecode VMs, garbage
collection internals, real GPU-accelerated compositing, full Unicode
shaping/bidi text, real X.509 chain validation UI, real browser extension
APIs, an accessibility tree, DevTools.

**Platform:** cross-platform (Windows/macOS/Linux) — Tkinter ships with
standard Python on all three.

---

## Awaiting your approval

Confirm before I start Phase 1:
1. Is the **24-module / 2-track** breakdown the right size, or should I cut
   it down (e.g. stop the designed course at Module 16 or 20 as a smaller
   target) or split it further?
2. Does the **Python + Tkinter, stdlib-only** architecture work for you, or
   would you rather a different language/rendering surface?
3. Any module you want removed, merged, or added before I lock this in?
