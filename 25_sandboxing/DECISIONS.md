# DECISIONS.md — Module 25 (Bonus): Sandboxing Deep Dive

Source files: `sandboxing.py` (the broker), `renderer_worker.py` (the
renderer). This module's decisions carry unusual weight — get the
framing wrong here and a learner walks away with a FALSE sense of
security about what was actually built. Every entry below is written
with that risk specifically in mind.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### The renderer is a real, separate `subprocess.Popen` process, communicating over real OS pipes (stdin/stdout)

**(a) Forced by what a broker architecture requires to mean anything.**
As established in prereqs/processes_and_threads.html and Module 24's
DECISIONS.md, a policy check living inside the SAME process as the code
it's supposed to constrain provides no real protection — code with
access to that process's own memory could simply skip the check. Using
`subprocess.Popen` with `stdin=PIPE, stdout=PIPE` creates a real OS
process boundary: the renderer cannot read or write the broker's memory
directly, only exchange bytes through the two pipes explicitly
connected. This is the SAME reason Module 24 used `multiprocessing`
instead of `threading` — a different API here (`subprocess` instead of
`multiprocessing`), but the same underlying OS guarantee.

### The broker holds the ONLY real file-reading code for `cooperative_read` — the renderer never calls `open()` in that path

**(a) Forced by the definition of "broker."** `Broker.request_cooperative_read`
is the only place in the entire cooperative flow that calls Python's
`open()`. The renderer's `cooperative_read` branch only ever sends a
JSON `request` and waits for a JSON `reply` — it has no file-reading
code in that path at all. This is what makes TEST 2's denial REAL rather
than cosmetic: `secret_path not in broker.opened_paths_log` is checking
that the broker's own, sole point of file access was never invoked for
that path — not just that an error message was returned.

### `Policy.permits_read` compares `os.path.abspath()` results, not raw
    string prefixes

**(a) Forced by how path traversal attacks actually work.** A naive
check like `requested_path.startswith(allowed_dir)` could be defeated by
a request like `allowed/../secret.txt`, which starts with the string
`"allowed"` but resolves to a completely different real location.
Resolving both sides to their real, absolute, `..`-collapsed form BEFORE
comparing is the only way to make a path-based policy check actually
mean what it appears to mean.

---

## THE central decision — and the one this whole module exists to make honest

### Test 3's "malicious" renderer SUCCEEDS at reading the secret file
    directly, bypassing the broker entirely — and this module ships that
    result on purpose, as its own headline finding

**(c) Our convention — but the single most consequential framing choice
in this entire course.** Nothing about the broker/target ARCHITECTURE
built in this module stops a renderer process from simply calling
`open()` itself. `subprocess.Popen` gives real MEMORY isolation (the
renderer can't read the broker's Python variables) — it does NOT give
real SYSCALL restriction (the renderer, as an ordinary OS process, can
still ask the operating system to open any file its own OS-level user
permissions allow, with nothing in this course's code stopping it).

This is not a bug in this module — it's the actual, honest state of
what a "broker asks nicely, renderer promises to cooperate" architecture
provides ON ITS OWN, with no additional OS enforcement layered under it.
A real attacker who has already compromised a renderer process (found a
memory-corruption bug, achieved arbitrary code execution inside it) is
in EXACTLY the position `renderer_worker.py`'s `malicious_read` branch
simulates — and Test 3 proves that against THIS module's own code, not
against a hypothetical.

**What actually closes this gap in real browsers** (named here
precisely, none of it implemented in this course):

| Platform | Real mechanism | What it does |
|---|---|---|
| Linux | **seccomp-bpf** | A kernel-enforced filter installed on the renderer process that allows or denies individual SYSCALLS by number/arguments — even if the renderer's code is fully compromised, a call like `open()` can be made to fail at the kernel level before it ever executes, because the kernel itself refuses it. |
| Windows | **Restricted tokens / Job Objects / AppContainer** | The renderer process is launched with a Windows access token stripped of most privileges, and/or placed in a Job Object or AppContainer that the OS uses to deny access to most of the filesystem/registry/network regardless of what the process's code tries to do. |
| macOS | **Sandbox.kext / the Seatbelt sandbox profile system** | A kernel extension enforces a declarative profile (a list of allowed operations) against every relevant syscall the process makes, the same category of enforcement as seccomp-bpf, implemented differently. |

In every real case, the enforcement point is the OPERATING SYSTEM KERNEL,
acting on the process from OUTSIDE it — not a check the process's own
code chooses to run. This module's broker/target split is architecturally
real and is a genuine, necessary PART of how real sandboxing is
structured (real Chromium literally has a broker process and calls the
untrusted side "the sandboxed process") — but the actual enforcement
teeth, the part that would stop `malicious_read` from succeeding, live in
kernel-level primitives this course explicitly does not implement,
consistent with the roadmap's Tools/Architecture Target treating
low-level OS syscall filtering the same way it treats TLS cryptography:
real, necessary, and out of scope for a from-scratch teaching build.

### Where this fits in the whole picture (Module 0 callback)

Module 0's DECISIONS.md §10 explained why sandboxing was deferred to a
bonus module instead of woven through every earlier one: you can't
meaningfully constrain a component you don't understand yet. Now that
every other component has been built (networking, parsing, layout,
scripting, process isolation), this module's honest answer is: the
broker/target PATTERN is real and matches real browsers structurally,
but the ENFORCEMENT requires OS primitives this course treats as
hardware, the same way it treats TCP and TLS. A learner who takes only
one fact from this module should take this one: **process separation
(Module 24) stops accidental crashes from spreading; only OS-level
syscall restriction stops a DELIBERATE, successful attacker inside a
compromised renderer — and this course built the former, honestly
simulated the protocol shape of the latter, and did not build the
latter's actual enforcement.**

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Renderer is a real separate `subprocess`, communicating over real pipes | (a) forced — this IS the broker architecture |
| 2 | Broker holds the only real file-access code for cooperative requests | (a) forced by the definition of "broker" |
| 3 | Policy check compares resolved absolute paths, not raw prefixes | (a) forced — defeats `..` traversal |
| 4 | Test 3's malicious bypass is shipped as a headline result, not hidden | (c) the module's central, deliberate honesty |
| 5 | Real OS enforcement (seccomp-bpf, restricted tokens, Sandbox.kext) named but not implemented | (c) explicit scope-out, matching the roadmap |

## What We Proved

A real broker process and a real renderer process, communicating over
real OS pipes, correctly enforced a path-based policy: a cooperative
request for an allowed file succeeded with real file content, verified
against the broker's own access log; a cooperative request for a
disallowed file was denied, and the broker's log proves it never even
opened that file — real, provable denial, not a cosmetic error message.
And — the result this module is actually built to surface — a renderer
that simply ignored the broker protocol and opened the same disallowed
file directly succeeded completely, proving that the broker/target
PATTERN alone, without OS-level syscall enforcement underneath it, is
not a real security boundary. See `tutorial.html` for the full, unedited
output and a detailed walkthrough of exactly which real OS mechanisms
would close this gap in an actual browser. This is the last module in
the numbered course — see `lessons/` for cross-cutting material that
spans multiple modules at once.
