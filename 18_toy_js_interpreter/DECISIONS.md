# DECISIONS.md — Module 18: A Toy JS Interpreter

Source file: `js_interpreter.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Recursive descent with one method per precedence level

**(b) External contract — this is how expression grammars with
precedence are conventionally implemented, not a stylistic pick.** Each
level (`parse_or` → `parse_and` → `parse_equality` → `parse_relational` →
`parse_additive` → `parse_multiplicative` → `parse_unary` → `parse_call`
→ `parse_primary`) only ever calls the level above it for its operands.
This structure is exactly what makes `2 + 3 * 4` parse as `2 + (3 * 4)`
without a separate precedence table: multiplication is parsed by a level
CLOSER to the leaves, so it's naturally grouped tighter, with no special
logic beyond "call the next function down."

### `call_env`'s parent is the function's `closure_env` (where it was
    DEFINED), never the caller's environment (where it's being CALLED from)

**(a) Forced by what "lexical scoping" actually means — get this backwards
and closures simply don't work.** This one line —
`call_env = Environment(callee.closure_env)` — is the entire closure
mechanism. `makeCounter`'s `increment` function captures the `n` that
existed in `makeCounter`'s OWN call environment at the moment `increment`
was defined, regardless of where `increment` is later called from. Using
the CALLER's environment instead (a mistake called "dynamic scoping")
would make `counter1()` and `counter2()` share state through whatever
variables happen to be in scope at each call site — not the two
genuinely independent counters this module's test proves exist.

### `ReturnSignal` is raised as a Python exception to implement `return`

**(c) Our convention — a standard, deliberate technique, not a
workaround.** A `return` statement needs to immediately unwind out of
however many nested blocks/loops/if-statements it's inside, back to the
function call that's waiting for a result. Python's own exception
mechanism already does exactly this kind of non-local unwinding — reusing
it (rather than threading a "did we return yet?" flag through every
`exec_*` method's return value) keeps every statement-execution method's
signature simple, at the cost of using exceptions for non-error control
flow, a real and known tradeoff.

### `==`/`!=` use Python's own `==`/`!=` directly — no JS-style type coercion

**(c) Our convention — explicit scope-out, and arguably a real
improvement.** Real JavaScript's `==` performs surprising implicit type
conversions (`"5" == 5` is `true`; `null == undefined` is `true`; a long,
genuinely confusing table of rules). This interpreter's `==` behaves like
real JS's `===` (strict equality, no coercion) for every `==` in a
program run through it. This is a real semantic difference from actual
JavaScript, named here rather than silently present — and it happens to
match the "always use `===`" advice given to real JS developers.

### No `++`/`--` operators; `for` loops must write `i = i + 1`

**(c) Our convention — explicit scope-out.** Prefix/postfix increment
have subtly different semantics (return the old vs. new value) and would
add another operator-precedence special case for comparatively little
teaching value once assignment and arithmetic already work. This
module's own `for` loop test spells out `i = i + 1` for exactly this
reason.

### No objects, arrays, or property access (`.` / `[]`)

**(c) Our convention — the single largest scope-out in this module,
named explicitly.** Supporting object/array literals, indexing, and
method calls would roughly double this module's size for a genuinely
different (though related) parsing and evaluation problem — and Module
19's DOM bindings, the very next module, need functions and variables far
more than they need JS objects, since the DOM itself will be exposed
through Python objects and Python function calls, not JS object literals.

### `print` is the only built-in, injected as a Python closure

**(c) Our convention.** A JS program run through this interpreter has
exactly one way to produce observable output: calling `print(...)`,
which this module wires directly to `self.output.append(...)` — giving
every test in this module (and Module 19's DOM-mutation tests) a simple,
reliable way to assert on what a script actually did, without needing a
`console` object or any other machinery.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | One parser method per precedence level | (b) conventional technique for precedence |
| 2 | `call_env`'s parent is `closure_env`, not the caller's env | (a) forced — this IS lexical scoping |
| 3 | `return` implemented via a Python exception | (c) standard technique, real tradeoff acknowledged |
| 4 | `==`/`!=` are strict, no JS-style coercion | (c) explicit scope-out, arguably safer |
| 5 | No `++`/`--` operators | (c) explicit scope-out |
| 6 | No objects, arrays, or property access | (c) largest named scope-out |
| 7 | `print` as the sole built-in | (c) convention, testing-motivated |

## What We Proved

A real tokenizer, recursive-descent parser, and tree-walking evaluator —
with zero embedded JS engine — correctly ran a program combining
recursion (`factorial(6) == 720`), a C-style `for` loop (summing 1
through 10 to 55), a `while` loop, string concatenation, and — the
result that actually proves lexical scoping works, not just that
functions can be called — two independently-created counters via a
closure-returning factory function, where calling one three times had
zero effect on the other, which correctly still started fresh at 1. See
`tutorial.html` section 06 for the full, unedited output. Module 19
builds the bridge between this interpreter and the real DOM from Module
6 — script that can finally read and mutate an actual web page.
