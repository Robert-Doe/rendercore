# DECISIONS.md — Module 24: Multi-Process Tab Isolation

Source file: `process_isolation.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### `multiprocessing.Process`, not `threading.Thread`

**(a) Forced by what isolation actually requires.** As established in
prereqs/processes_and_threads.html, a thread shares its process's memory
completely — a crash or memory corruption in one thread can take down
every thread in that process. A `multiprocessing.Process` is a real,
separate OS process with its own private memory space, enforced by the
kernel. Using `threading` here would make this module's entire premise
false: a crash in a "tab" thread genuinely CAN corrupt or kill the whole
program in a way a crash in a separate process provably cannot.

### Each worker reports its OWN `os.getpid()`, not a value the parent
    assigns or assumes

**(c) Our convention, chosen specifically to make cross-process
verification real rather than assumed.** It would be easy for this
module to just assert "these are 3 separate processes" without proof.
Having each worker report the pid IT SEES from inside its own execution
context (`os.getpid()` called inside `tab_worker`, running in the child)
means the parent's check — `len(set(all_pids)) == 4` — verifies real,
independently-observed values, not a number the parent process invented.

### The crash is a genuinely unhandled `RuntimeError`, not a controlled
    `sys.exit()` or a caught-and-reported error

**(c) Our convention, chosen for realism.** A real renderer crash isn't a
polite, caught error — it's the kind of unexpected failure (a null
pointer, a stack overflow, a genuine bug) that no one predicted or
wrapped in a handler. Letting `tab_worker` raise a real, unhandled
exception and observing `multiprocessing` report a real non-zero exit
code is a more honest test of isolation than a scripted, cooperative
shutdown would be.

### Isolation is verified by RE-PINGING the surviving tabs AFTER the
    crash, not just checking `.is_alive()`

**(c) Our convention — the module's central methodological point,
consistent with Modules 16, 20, and 23's shared discipline of checking
the actual claim, not a proxy for it.** `.is_alive()` only proves a
process object hasn't been reaped yet — it says nothing about whether
that process can still do useful work. Sending a second `"ping"` command
to `tab_a` and `tab_c` AFTER `tab_b`'s crash, and confirming a real
`"pong"` comes back with the SAME pid as before, proves genuine,
continued responsiveness — not just that the process technically still
exists.

### Worker processes are started with `daemon=True`

**(c) Our convention, a safety/cleanup choice for this module's own
demo.** A daemon process is automatically terminated if the main process
exits unexpectedly (e.g., during development, if a test script itself
crashed before reaching its own cleanup code) — preventing orphaned tab
processes from lingering after a failed run. Real browser tab processes
are managed with more deliberate, explicit lifecycle control by the
browser process; `daemon=True` here is a pragmatic testing convenience,
not a claim about how a real browser manages its child processes.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | `multiprocessing.Process`, not `threading.Thread` | (a) forced — this IS the isolation guarantee |
| 2 | Each worker reports its own real, self-observed pid | (c) makes verification real, not assumed |
| 3 | Crash is a genuine unhandled exception | (c) realism — matches how real crashes actually happen |
| 4 | Isolation verified by re-pinging survivors, not just `.is_alive()` | (c) checks the real claim, not a proxy |
| 5 | Workers run as daemon processes | (c) testing-convenience cleanup safety net |

## What We Proved

Four real OS processes — one "chrome" (the main process) and three
"tabs" — were confirmed to have four genuinely distinct process IDs,
each self-reported from inside its own execution context. One tab was
deliberately made to raise a real, unhandled exception; `multiprocessing`
correctly reported its exit code as `1` (a real crash), with a real
Python traceback printed to stderr from that process. The other two
tabs were then proven — not just assumed — to have survived: they were
pinged a SECOND time, after the crash, and both responded with a real
`"pong"` from the exact same pid they started with, and the main chrome
process's own pid never changed, having continued executing the entire
time. See `tutorial.html` section 06 for the full, unedited output,
including the real crash traceback. Module 25, this course's bonus
module, builds the security layer that goes one step further than
isolation: constraining what a tab's process is even ALLOWED to attempt,
regardless of whether it crashes.
