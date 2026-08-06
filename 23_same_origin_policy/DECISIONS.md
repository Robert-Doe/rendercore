# DECISIONS.md — Module 23: Same-Origin Policy

Source file: `same_origin.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Enforcement lives in `BrowserRegistry`, a component OUTSIDE any tab's
    own script — not as a check individual bindings perform on their own

**(a) Forced by a real architectural necessity, not a style choice.** A
script running inside a tab cannot be trusted to enforce a security
boundary against ITSELF — if the check lived inside, say, the DOM itself,
nothing would stop a modified or buggy binding from skipping it. The
registry is the one component with visibility into every tab's origin at
once, external to any single tab's script — which mirrors why real
browsers enforce same-origin policy in the browser/renderer-process
boundary, not inside the JS engine's own object model.

### `own_origin` is captured as a closure variable when a tab's
    interpreter is CREATED, not read from a mutable "current origin" variable

**(a) Forced by what the guarantee actually requires.** If a script
could somehow influence what origin it's currently "reporting as," the
entire check would be meaningless — it would be asking the attacker to
self-report honestly. `make_interpreter_for(registry, own_origin)`
closes over the tab's real, registry-assigned origin at binding-creation
time, with no code path that lets a running script change it afterward.

### The comparison is exact string equality on the FULL origin
    (`scheme://host:port`), not a hostname-only comparison

**(a) Forced by spec, and directly, concretely tested.** Test 4
specifically constructs `http://bank.example.com` (same host as the real
bank tab, different scheme) and confirms it's STILL denied — proving the
check isn't accidentally comparing only hostnames, which would be a real
and dangerous same-origin policy bug (an attacker serving lookalike
content over plain HTTP on a shared or spoofed hostname could otherwise
gain access to HTTPS-origin data).

### `SecurityError` propagates as an ordinary Python exception, uncaught
    by the JS interpreter itself

**(c) Our convention — a direct, honest consequence of Module 18's own
scope.** Module 18's interpreter has no `try`/`catch` construct (named
explicitly in its own DECISIONS.md). A denied access in this module
doesn't get "handled" by the script at all — it terminates the script's
execution entirely, the same way any other unhandled exception would.
This is arguably MORE realistic than it might first appear: an
unhandled `SecurityError`-equivalent in a real browser also stops that
specific script's execution (though real JS's `try`/`catch` COULD catch
it there, which this simplified interpreter cannot).

### Same-origin tabs (Test 2) are explicitly proven to succeed, not just
    assumed to work because "no denial happened"

**(c) Our convention — a deliberate test-design choice.** A same-origin
access that silently did nothing (returning `None`, or an empty stub)
could pass a naive "it didn't raise an error" check while not actually
granting real access. Test 2 checks the script's own captured output
contains genuine content from the target document (`'real access
granted'` embedded in what the script itself printed) — proving the
ALLOW path is a real, working code path, not just the absence of the
DENY path.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Enforcement lives in an external registry, not inside individual bindings | (a) forced by real architecture |
| 2 | `own_origin` fixed via closure at interpreter creation, not mutable | (a) forced — otherwise the check is meaningless |
| 3 | Comparison is exact full-origin string equality | (a) forced by spec, tested directly via a scheme-mismatch case |
| 4 | Denials propagate as uncaught exceptions (Module 18 has no try/catch) | (c) honest consequence of Module 18's scope |
| 5 | Same-origin ALLOW path proven with real content, not just "no error" | (c) deliberate test design |

## What We Proved

Four tabs were registered across three distinct real origins
(`https://bank.example.com`, `https://evil.example.com`, and — critically
— `http://bank.example.com`, same host as the bank tab but a different
scheme). A script running as `evil.example.com` was blocked from reading
both the bank tab's document AND its cookies, with a real
`SecurityError` raised each time. A script running in a SECOND
`bank.example.com` tab successfully read the FIRST bank tab's real
document content — proving the policy correctly allows same-origin
access, not just denies everything. And a script running as
`http://bank.example.com` — same hostname as the real bank tab, wrong
scheme — was ALSO correctly denied, proving the enforcement compares the
full origin triple, not hostname alone. See `tutorial.html` section 06
for the full, unedited output. Module 24 adds the OS-level counterpart to
this logical boundary: running each tab in a genuinely separate process.
