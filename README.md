# rendercore

A browser engine built from raw sockets to painted pixels, entirely from scratch, in Python.

## What this is

This is a from-first-principles rebuild of a web browser's rendering and application stack: no `requests`, no HTML/CSS parsing libraries, no embedded JS engine, no GPU compositor. A raw TCP socket is opened by hand, HTTP is formatted and parsed by hand, HTML and CSS are tokenized and parsed by hand into a DOM and a style tree, layout and painting are computed by hand down to a Tkinter canvas, and a toy JS interpreter is written by hand to script the resulting page.

It exists because most claims about browser security — "the same-origin policy prevents X," "sanitization stops Y," "process isolation contains Z" — get taken on faith from documentation or from reading someone else's engine. This project is part of a personal research program for a PhD security researcher who wants every one of those claims grounded in something built and broken with their own hands first: you cannot really evaluate a bypass of the same-origin policy until you've implemented the same-origin policy, decided where its edges are, and tried to walk through them yourself.

The stdlib is treated as "hardware" in the same sense an OS course treats the CPU as given: `socket` stands in for the network stack, `ssl` for a TLS/crypto library, `tkinter` for the OS's native windowing and rasterizer, `multiprocessing` for OS process creation. Everything above that line — HTTP, HTML, CSS, layout, painting, scripting, cookies, the same-origin policy, sandboxing — is built here.

## Two tracks, plus a security extension

- **Track 1 — The Rendering Engine** (Modules 1–16): a pure pipeline, bytes off the wire to pixels on a canvas. No interactivity, no chrome, no scripting.
- **Track 2 — The Browser Application** (Modules 17–25): everything layered on top of the engine to make it behave like a real browser — an event loop, a JS interpreter, DOM bindings, invalidation and re-render, address bar/tabs/history, cookies, same-origin enforcement, multi-process tab isolation, and a sandboxing broker.
- **Phase 5 — XSS Defense** (Modules 26–31): an extension that revisits five earlier modules through a security lens — encoding and sanitization at every boundary where untrusted data crosses into a new interpretation context (URL, HTML body, HTML attribute, HTTP header, DOM sink).

Module 0 is a zero-code map of every subsystem a browser is made of, read before anything gets built.

## Module map

| # | Module | What it proves | Directory |
|---|--------|-----------------|-----------|
| 0 | The Big Picture | Names every subsystem of a real browser, in data-flow order, before any of them exist as code | [`00_big_picture/`](00_big_picture/) |
| 1 | Raw TCP Socket Connection | A hand-opened socket exchanges bytes with a real web server, no `requests`/`urllib` | [`01_raw_socket/`](01_raw_socket/) |
| 2 | URL Parser | A URL string decomposes into scheme/host/port/path/query with no parsing library | [`02_url_parser/`](02_url_parser/) |
| 3 | Hand-Rolled HTTP/1.1 | A hand-formatted request over the raw socket gets a real response back, split without a library | [`03_http_from_scratch/`](03_http_from_scratch/) |
| 4 | TLS via Socket Wrapping | The same request/response logic runs unmodified over `ssl`-wrapped sockets | [`04_https_tls/`](04_https_tls/) |
| 5 | HTML Tokenizer | A state machine turns raw HTML into typed tokens | [`05_html_tokenizer/`](05_html_tokenizer/) |
| 6 | HTML Tree Builder | Tokens assemble into a DOM tree, recovering from malformed/unclosed tags | [`06_dom_tree_builder/`](06_dom_tree_builder/) |
| 7 | CSS Tokenizer & Parser | A stylesheet becomes structured (selector, declaration-block) rules | [`07_css_parser/`](07_css_parser/) |
| 8 | Selector Matching Engine | Lists exactly which parsed CSS rules match a given DOM node | [`08_selector_matching/`](08_selector_matching/) |
| 9 | The Cascade | Picks one winning value per property via specificity, source order, `!important` | [`09_cascade/`](09_cascade/) |
| 10 | The Box Model | Every styled node gets a computed content/padding/border/margin box | [`10_box_model/`](10_box_model/) |
| 11 | Block & Inline Layout | Boxes get real x/y/width/height coordinates, recursively | [`11_block_inline_layout/`](11_block_inline_layout/) |
| 12 | Text Layout & Line Breaking | Long text wraps into lines at a given container width | [`12_text_line_breaking/`](12_text_line_breaking/) |
| 13 | Stacking & a Flexbox Subset | Flex main-axis distribution plus z-index stacking independent of DOM order | [`13_flexbox_stacking/`](13_flexbox_stacking/) |
| 14 | Paint / Display List | A laid-out tree flattens into an ordered list of draw commands | [`14_display_list/`](14_display_list/) |
| 15 | Rasterization to Canvas | The display list replays against a real Tkinter canvas as visible pixels | [`15_rasterizer/`](15_rasterizer/) |
| 16 | Compositing & Layers | Overlapping elements paint in correct order via stacking contexts — **Track 1 complete** | [`16_compositing/`](16_compositing/) |
| 17 | The Event Loop | Input events queue and process without blocking the render pipeline | [`17_event_loop/`](17_event_loop/) |
| 18 | A Toy JS Interpreter | Tokenizer → parser → tree-walking evaluator for a real JS subset, no embedded engine | [`18_toy_js_interpreter/`](18_toy_js_interpreter/) |
| 19 | DOM–JS Bindings | Script calls `getElementById`/`innerHTML`-equivalents and mutates the real DOM | [`19_dom_js_bindings/`](19_dom_js_bindings/) |
| 20 | Invalidation & Re-render Pipeline | A DOM mutation triggers correct partial re-layout/re-paint, not a full rebuild | [`20_invalidation_pipeline/`](20_invalidation_pipeline/) |
| 21 | Chrome UI | Address bar, tabs, and back/forward history across loaded pages | [`21_chrome_ui/`](21_chrome_ui/) |
| 22 | Cookies & Storage | Response/script-set state is sent back correctly and survives across sessions | [`22_cookies_storage/`](22_cookies_storage/) |
| 23 | Same-Origin Policy | A script from origin A is provably blocked from reading origin B's DOM/storage | [`23_same_origin_policy/`](23_same_origin_policy/) |
| 24 | Multi-Process Tab Isolation | Each tab is a real OS process; one crashing leaves the others alive | [`24_process_isolation/`](24_process_isolation/) |
| 25 | Sandboxing Deep Dive | A renderer, stripped of direct access, can only act through a policy-checked broker — **all 26 core modules complete** | [`25_sandboxing/`](25_sandboxing/) |
| 26 | URL Encoding & Decoding | Percent-encoding prevents URL structure reinterpretation, verified against Module 2's parser | [`26_url_encoding/`](26_url_encoding/) |
| 27 | HTML Entity Encoding | Encoded text survives Module 5's real tokenizer without becoming markup | [`27_entity_encoding/`](27_entity_encoding/) |
| 28 | Attribute & URL-Scheme Encoding | Attribute-context escaping plus blocking `javascript:`-scheme URLs | [`28_attribute_encoding/`](28_attribute_encoding/) |
| 29 | HTTP Header Injection Prevention | CRLF in a value can't forge headers or split the response | [`29_header_injection/`](29_header_injection/) |
| 30 | HTML Sanitization (Allowlist-Based) | Disallowed tags/attributes/schemes stripped while preserving safe structure | [`30_html_sanitization/`](30_html_sanitization/) |
| 31 | The DOM XSS Sink | `innerHTML`-equivalent executes injected markup; `textContent`-equivalent never does — **all 32 modules complete** | [`31_dom_xss_sink/`](31_dom_xss_sink/) |

Supporting material: [`ROADMAP.md`](ROADMAP.md) (full build log and architecture rationale), [`GLOSSARY.md`](GLOSSARY.md) (every term, tied to the module that introduces it), [`prerequisites.html`](prerequisites.html) and [`prereqs/`](prereqs/) (background reading: byte encoding, client/server model, state machines, trees/recursion, event-driven programming, coordinate systems, processes/threads, origins/the security boundary).

## Tech stack

- **Language:** Python 3.11+, standard library only.
- **Rendering surface:** Tkinter `Canvas` — an immediate-mode 2D drawing surface standing in for a GPU compositor, the way a textbook OS course uses QEMU instead of real silicon.
- **Treated as "hardware" (imported, not rebuilt):** `socket`, `ssl`, `tkinter`, `multiprocessing`, `subprocess` + OS pipes.
- **Built from scratch in this repo:** HTTP formatting/parsing, the HTML tokenizer/tree builder, the CSS tokenizer/parser/selector matcher/cascade, the box model and block/inline/flex layout, text line breaking, display-list generation and rasterization, the JS tokenizer/parser/interpreter, DOM–JS bindings, the cookie jar, same-origin enforcement, and the sandboxing policy broker.

Explicitly out of scope: full ECMAScript spec compliance, JIT/bytecode VMs, GC internals, real GPU compositing, full Unicode shaping/bidi, real X.509 chain validation UI, real extension APIs, an accessibility tree, DevTools.

## Status

All 32 modules complete (1 orientation + 16-module rendering engine + 9-module browser application + 6-module XSS defense extension). Each module was verified against a concrete, stated check (a live request against a real host, a known-malformed-HTML case, a pixel-level canvas query, a reproduced-then-blocked injection) rather than left as an unverified exercise — see each module's `DECISIONS.md` for what was checked and why.

## How to explore / run the code

Each module directory is self-contained:

- `tutorial.html` — the write-up: what the module builds, why, and the concepts behind it.
- `DECISIONS.md` — the design decisions made in that module and the trade-offs behind them.
- a `.py` file (from Module 1 onward) — the actual runnable implementation.

To run a given module's code directly:

```bash
cd 05_html_tokenizer
python html_tokenizer.py
```

Most modules are written to run standalone and print or assert their own verification checks (e.g. Module 6 will run its five malformed-HTML recovery cases; Module 25 will run the real sandbox-denial and bypass demonstration). Later modules import from earlier ones (e.g. Module 19 imports Module 6's DOM, Module 20 imports Modules 9/11/14/15/19), so run them from within this repo rather than in isolation. No external dependencies are required beyond the Python 3.11+ standard library; Tkinter must be present (it ships with standard CPython installers on Windows/macOS, and via the `python3-tk` package on most Linux distributions).
