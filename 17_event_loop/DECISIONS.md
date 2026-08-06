# DECISIONS.md — Module 17: The Event Loop

Source file: `event_loop.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### `deque` (not a `list`) backs the queue, with `append`/`popleft`

**(a) Forced by algorithmic necessity, not a style pick.** A FIFO queue
needs O(1) removal from the front. Python's `list.pop(0)` is O(n) — it
has to shift every remaining element down by one. `collections.deque` is
specifically designed for O(1) operations at both ends. Using a plain
list would still be FUNCTIONALLY correct at the small scale of this
module's demo, but would misrepresent the real, meaningful reason real
event loop implementations use a proper queue structure.

### A task is popped and fully run — via a plain, blocking function call
    — before the loop even looks at the next item

**(a) Forced by the guarantee this module exists to prove.** `task(*args)`
is an ordinary, synchronous Python call: the loop cannot proceed to its
next iteration until that call returns. This one line is the entire
mechanism behind all three of this module's guarantees (FIFO order, no
queue-jumping, run-to-completion) — nothing more elaborate is needed,
because Python's own function-call semantics already provide exactly the
one-thing-at-a-time execution a browser's main thread needs. This is
worth sitting with: the guarantee isn't implemented by some clever
locking or scheduling trick — it falls directly out of NOT using threads
or async execution here at all.

### `post()` always appends to the back, even when called from inside a
    currently-running task

**(a) Forced by the queue's own FIFO contract.** There's no special-cased
"insert at front" or "run immediately" path — `handler_b` in Case 2
calling `loop2.post("D", ...)` while it's executing has no way to make
`D` run any sooner than strict FIFO order allows, because `post()` has
exactly one behavior regardless of when it's called. This is precisely
what real `setTimeout(fn, 0)` / `queueMicrotask`-adjacent behavior in
real browsers relies on: code cannot use "post a new task" to sneak in
front of already-queued work.

### `max_iterations` is a hard cap purely for THIS module's own automated
    demo — real event loops have no such limit

**(c) Our convention — explicitly named as a testing artifact, not a
feature.** A real browser's event loop runs until the tab closes; there
is no "stop after N tasks" concept. `max_iterations` exists only so this
module's own `__main__` block terminates predictably during automated
verification, instead of relying on well-behaved test tasks to naturally
empty the queue (which they do here, but a buggy task that reposts itself
forever — exactly the scenario in prereqs/event_driven_programming.html's
Q&A — would hang a REAL event loop, and this course's own Module 21
chrome UI will not have this safety net, because a real browser doesn't
either).

### `run_log` records labels as strings, not the task objects themselves

**(c) Our convention.** Comparing a list of plain strings
(`['A', 'B', 'C']`) against an expected list is simpler and more directly
readable in test output than comparing function objects or closures would
be — a small ergonomic choice with no bearing on the loop's actual
behavior.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | `deque` used for O(1) FIFO operations | (a) forced by algorithmic necessity |
| 2 | Tasks run via a plain, blocking, synchronous call | (a) forced — this call IS the guarantee |
| 3 | `post()` always appends to the back, unconditionally | (a) forced by FIFO contract |
| 4 | `max_iterations` cap exists only for this module's own test harness | (c) explicit testing artifact, not a real feature |
| 5 | Run log uses string labels for readable test assertions | (c) convention |

## What We Proved

Four real, independently verified guarantees: three tasks ran in exactly
the order they were posted; a task posted from INSIDE a currently-running
handler correctly went to the back of the queue rather than jumping
ahead, running only after every already-queued task; a handler that made
three sequential mutations to shared state was always seen by a later
task as either fully applied or not yet started — never partially applied,
because nothing can interrupt a running task; and a simulated "render"
task interleaved between two DOM-mutating tasks only ever observed
clean, fully-settled values, never a mix of the two. See `tutorial.html`
section 06 for the full, unedited output. Module 18 builds something to
actually put IN this queue — a real interpreter for a real subset of
JavaScript.
