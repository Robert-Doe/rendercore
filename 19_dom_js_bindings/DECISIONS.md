# DECISIONS.md — Module 19: DOM–JS Bindings

Source file: `dom_bindings.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Bindings are flat function calls (`setText(el, "...")`), not property
    assignment (`el.textContent = "..."`)

**(c) Our convention — a direct, honest consequence of Module 18's own
scope-out.** Module 18's interpreter has no `.`/`[]` property-access
syntax at all (named explicitly in its DECISIONS.md). Real DOM bindings
use property assignment; this course's bindings use plain function calls
because that's the only calling convention the underlying interpreter
actually supports. This is a real difference from the real DOM API's
shape, not a smaller version of the same capability — named here so it's
never confused with how real `element.textContent = "..."` works.

### `bind_dom()` requires ZERO changes to `js_interpreter.py`

**(a) Forced by how `eval_Call` was already written in Module 18.**
`eval_Call`'s fallback branch — `if callable(callee): return callee(*args)`
— already accepts any Python callable as a valid thing to call from JS,
with no special-casing for "built-in" vs. "user-defined" functions. This
was true in Module 18's DECISIONS.md even before Module 19 existed
(`print` used exactly this path). DOM bindings are simply MORE Python
callables declared into the global environment before running a script —
proof that Module 18's design was already general enough for this, not
a coincidence discovered here.

### `getElementById` returns the REAL Python `Element` object, not a
    copy, a wrapper, or an id/handle

**(a) Forced by what "mutating the DOM" has to mean.** If
`getElementById` returned a copy, `setText`/`setAttribute` calls on it
would be invisible to the rest of the program — the DOM the render
pipeline (Modules 10-16) would eventually see would be unchanged. Passing
the exact same object reference JS holds onto is what makes a script's
mutation OBSERVABLE outside the script — proven directly in this
module's own test by holding a Python reference to `target` from before
the script runs, and reading its (mutated) state after, with no
re-fetching in between.

### `setText()` replaces ALL of an element's children with one new text node

**(c) Our convention, matching a real simplification real DOM APIs also
make.** This mirrors what real `element.textContent = "..."` actually
does — it isn't a "set the first text node" operation, it wholesale
replaces everything inside the element. Modeling it the same way here
means this binding's behavior isn't a novel invention; it's a smaller,
single-purpose version of a real, well-known DOM operation.

### `getText()` concatenates only DIRECT `TextNode` children, not text
    nested inside child elements

**(c) Our convention — explicit scope-out, a real simplification of
`textContent`.** Real `textContent` recursively collects text from every
descendant, however deeply nested. This binding only looks at immediate
children, which is enough for this module's own test cases (and simpler
to reason about) but is a real, named gap from full `textContent`
semantics.

### No `removeChild`, `querySelector`, or event-registration bindings
    (`addEventListener`) in this module

**(c) Our convention — explicit scope-out, deferred to later modules.**
`addEventListener`-equivalent bindings specifically need Module 17's
event loop wired in alongside the DOM (a click needs to eventually
call back into a JS function) — that integration is Module 20's job, not
this one. This module's scope is deliberately just: can script read and
mutate DOM state at all, proven with the smallest sufficient set of
bindings.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Function-call bindings, not property assignment | (c) forced consequence of Module 18's scope |
| 2 | Zero changes needed to `js_interpreter.py` | (a) already supported by Module 18's design |
| 3 | `getElementById` returns the real object, not a copy | (a) forced — this is what "mutation" requires |
| 4 | `setText` replaces all children, matching real `textContent` | (c) convention, mirrors a real API |
| 5 | `getText` only reads direct text-node children | (c) explicit scope-out |
| 6 | No `removeChild`/`querySelector`/event bindings yet | (c) explicit scope-out, deferred to Module 20 |

## What We Proved

A script running through Module 18's unmodified interpreter looked up a
real element by id, read its original text, replaced it, set a new
attribute, created a brand-new element, and appended it as a real child —
and every one of those mutations was independently confirmed by reading
the SAME Python `Element` object a test held a reference to from BEFORE
the script ever ran, not by trusting the script's own `print()` output.
The object's `.attrs` dictionary and `.children` list were both directly,
observably changed. See `tutorial.html` section 06 for the full, unedited
output. Module 20 closes the loop: making a DOM mutation like this one
automatically trigger the correct partial re-layout and re-paint, instead
of requiring a full pipeline rebuild.
