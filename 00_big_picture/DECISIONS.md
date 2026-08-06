# DECISIONS.md — Module 0: The Big Picture

Module 0 has no source code — it's a map. But the map itself embodies real
decisions about how to carve up "a browser" into named boxes, and those
decisions deserve the same scrutiny as a line of code would. This document
explains why the boxes are drawn where they're drawn.

Every decision below is tagged:
- **(a) Forced by platform/spec** — not a choice; the underlying technology
  requires it.
- **(b) Forced by an external contract** — a spec, file format, or protocol
  that the rest of the world already agreed on, which we must respect if we
  want to talk to real servers and render real HTML/CSS/JS.
- **(c) Our own convention** — chosen for teaching clarity; a different
  browser/course could split this differently and still be correct.

---

## 1. Why "networking" is one box, not four

DNS resolution, TCP handshake, TLS handshake, and HTTP request/response are
four genuinely different protocols. We draw them as one box in the Module 0
diagram, then *do* split three of them into their own modules later
(TCP → Module 1, HTTP → Module 3, TLS → Module 4).

- **(c) Convention.** At the "big picture" altitude, a learner doesn't yet
  need the internal seams of networking — they need to know "getting bytes
  off the internet" is one phase that happens before any parsing starts.
  We zoom in once we're actually inside that phase (Modules 1–4).

## 2. Why DNS never gets its own module

DNS (turning `example.com` into an IP address) is a real, separate protocol
— arguably as deep a rabbit hole as HTTP.

- **(b) External contract, deliberately left to the OS.** Python's
  `socket.connect((host, port))` performs DNS resolution internally via the
  OS resolver. We never call a DNS library or hand-parse a DNS packet
  anywhere in this course. This is the same category of decision as an OS
  course not asking you to fabricate a CPU: DNS is infrastructure we're
  allowed to stand on, not infrastructure we're here to build. Named
  explicitly here so it isn't mistaken for an oversight later.

## 3. Why HTML parsing and CSS parsing are drawn as two parallel boxes, not one

- **(a) Forced by spec.** HTML and CSS are two independent, differently
  shaped grammars, standardized separately (WHATWG HTML spec vs. CSS
  Syntax Module). A browser genuinely runs two different tokenizer/parser
  pairs, not one shared one. Drawing them as parallel, separate boxes that
  both feed into the next stage reflects a real architectural fact, not a
  teaching simplification.

## 4. Why "Style / Cascade" is its own box, separate from CSS parsing

- **(b) External contract.** The CSS Cascade (deciding which of several
  matching, conflicting rules wins) is defined by its own spec (the CSS
  Cascade and Inheritance Module) and is conceptually a different job than
  parsing: parsing turns text into structured rules; the cascade turns
  "many candidate rules for this one node" into "one final value per
  property." Real engines implement these as separate passes too. Modules
  7 (parse) and 9 (cascade) are kept separate for the same reason, with
  Module 8 (selector matching) as the connective step between them.

## 5. Why Layout is downstream of Style, and Paint is downstream of Layout

- **(a) Forced by data dependency, not spec text, but still not a choice.**
  You cannot compute where a box sits on the page (layout) until you know
  its `display`, `width`, `margin`, etc. (style). You cannot decide what
  color to paint a pixel until you know where its box is (layout). Every
  real browser's pipeline has this same dependency order because the math
  requires it — there's no valid ordering that computes layout before style
  is resolved.

## 6. Why "Paint" and "Composite" are two boxes, not one

- **(c) Convention, but modeling a real distinction.** Real browsers
  separate "what to draw" (a display list of draw commands) from "turning
  that list into actual pixels, correctly layered" (compositing). We keep
  them separate (Modules 14 and 15/16) because it's the difference between
  *deciding* the picture and *producing* the picture — and because
  stacking-context bugs (Module 16) are a different kind of bug than
  display-list bugs (Module 14), worth understanding independently.

## 7. Why the JS Engine is drawn as a box beside the pipeline, not inside it

- **(b) External contract.** JavaScript (ECMAScript) is specified entirely
  independently of HTML/CSS/DOM — you could run a JS engine with no DOM at
  all (Node.js does exactly this). The DOM is not part of the JS language;
  it's a set of objects a *host environment* (the browser) chooses to
  expose to JS. That's why Module 18 (the JS interpreter) is built with
  zero DOM knowledge, and Module 19 (DOM–JS bindings) is a separate,
  later module whose entire job is wiring the two independent things
  together.

## 8. Why the Event Loop sits between JS and the rendering pipeline

- **(a) Forced by a real constraint.** A browser is single-threaded for
  script execution and rendering on the main thread. If JS could freeze
  mid-execution and let rendering "cut in," DOM mutations could be observed
  half-applied. The event loop is the mechanism that guarantees script runs
  to completion before rendering resumes. This isn't a stylistic choice —
  it's the only way to keep the DOM consistent for any code observing it.

## 9. Why Chrome UI, Storage, Security, and Process Model are drawn as an
    outer boundary around the pipeline, not as pipeline stages

- **(c) Convention.** Nothing about tabs, cookies, same-origin policy, or
  process isolation transforms bytes into pixels — they *govern* the
  pipeline (what's allowed to talk to what, what persists, what's isolated
  from what) rather than being a step in it. Drawing them as an outer frame
  rather than inline stages is a modeling choice meant to make that
  governance-vs-transformation distinction visible at a glance.

## 10. Why Sandboxing is a bonus module at the very end, not woven into
     every earlier module

- **(c) Convention, chosen deliberately.** We build the unprotected version
  of every subsystem first (Modules 1–24), so the *mechanism* is
  understood before the *threat model* is layered on. Module 25 then goes
  back over the same subsystems and asks "what could go wrong if this
  component were handed hostile input, and what stops it from reaching the
  rest of the system." This ordering mirrors how real browser security
  work actually proceeds — you can't sandbox a component you don't
  understand yet.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Networking shown as one box at this altitude, split into 3 modules later | (c) convention |
| 2 | DNS resolution left entirely to the OS resolver, no module | (b) external contract |
| 3 | HTML parsing and CSS parsing drawn as separate parallel boxes | (a) forced by spec |
| 4 | Cascade is its own box, separate from CSS parsing | (b) external contract |
| 5 | Layout after Style, Paint after Layout | (a) forced by data dependency |
| 6 | Paint and Composite kept as two boxes | (c) convention modeling a real distinction |
| 7 | JS Engine drawn independent of the DOM | (b) external contract (ECMAScript spec) |
| 8 | Event loop sits between JS and rendering | (a) forced by single-thread consistency requirement |
| 9 | Chrome/Storage/Security/Process drawn as an outer frame | (c) convention |
| 10 | Sandboxing deferred to a final bonus module | (c) convention |

## What This Map Established

Before any code exists, every subsystem a real browser needs has a name, a
position in the data-flow order, and a one-sentence job description (see
`tutorial.html` section 04). Every module built from here forward (1
through 25) fills in exactly one box on this map — nothing gets built later
that wasn't named here, and nothing named here goes unbuilt by the end of
Module 25.
