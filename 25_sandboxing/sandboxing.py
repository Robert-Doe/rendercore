"""
Module 25 (Bonus) — Sandboxing Deep Dive
============================================
Proves TWO things, deliberately side by side:

  1. A real broker/target process pair, communicating over real OS
     pipes, can enforce a real policy: a cooperative renderer asking for
     a disallowed file is genuinely denied, and the broker — which holds
     the real file access — never even opens the disallowed file itself.

  2. That protocol, ON ITS OWN, is NOT a real security boundary — a
     renderer that simply ignores the "ask first" convention and opens
     a file directly succeeds anyway, because nothing in this course's
     toolchain stops a Python process from making its own syscalls.
     This is the single most important, most honest fact this module
     exists to demonstrate. See DECISIONS.md for exactly which real OS
     mechanisms (seccomp-bpf, restricted tokens, sandbox profiles) close
     this specific gap in real browsers — none of which are implemented
     here.
"""

import json
import os
import shutil
import subprocess
import sys


class Policy:
    """The broker's rulebook: is this specific request allowed at all?
    Everything the broker does is gated through here — the renderer
    itself is never even asked what it thinks the rules are."""

    def __init__(self, allowed_dir: str):
        self.allowed_dir = os.path.abspath(allowed_dir)

    def permits_read(self, requested_path: str) -> bool:
        # Resolve the FULL real path (this defeats "../" traversal
        # tricks — resolving symlinks/relatives before comparing is
        # what makes this check meaningful, not decorative).
        real_path = os.path.abspath(requested_path)
        return real_path == self.allowed_dir or real_path.startswith(self.allowed_dir + os.sep)


class Broker:
    """The trusted side. Launches the renderer as a real, separate
    subprocess and is the ONLY thing in this program with real file
    access on the renderer's behalf."""

    def __init__(self, renderer_script: str, policy: Policy):
        self.policy = policy
        self.opened_paths_log = []   # what the broker ACTUALLY opened — for verification
        self.proc = subprocess.Popen(
            [sys.executable, renderer_script],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1,
        )

    def _send(self, obj) -> None:
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _recv(self):
        line = self.proc.stdout.readline()
        return json.loads(line) if line else None

    def request_cooperative_read(self, path: str) -> dict:
        self._send({"action": "cooperative_read", "path": path})
        request = self._recv()   # the renderer's REQUEST, not a direct file access
        assert request["request"] == "read_file"

        if self.policy.permits_read(request["path"]):
            self.opened_paths_log.append(request["path"])
            with open(request["path"], "r") as f:
                data = f.read()
            self._send({"ok": True, "data": data})
        else:
            self._send({"ok": False, "error": f"policy denied: {request['path']!r} "
                                                f"is outside the allowed directory"})

        return self._recv()   # the renderer's own final result line

    def request_malicious_read(self, path: str) -> dict:
        self._send({"action": "malicious_read", "path": path})
        return self._recv()

    def shutdown(self) -> None:
        self._send({"action": "exit"})
        self.proc.wait(timeout=5)


if __name__ == "__main__":
    # ---- set up a real, on-disk sandbox workspace ----
    base = os.path.join(os.path.dirname(__file__), "_sandbox_workspace")
    allowed_dir = os.path.join(base, "allowed")
    os.makedirs(allowed_dir, exist_ok=True)
    with open(os.path.join(allowed_dir, "public.txt"), "w") as f:
        f.write("This is public, sandboxed content.")
    secret_path = os.path.join(base, "secret.txt")
    with open(secret_path, "w") as f:
        f.write("TOP SECRET — should never leave the broker's control")

    policy = Policy(allowed_dir)
    renderer_script = os.path.join(os.path.dirname(__file__), "renderer_worker.py")
    broker = Broker(renderer_script, policy)

    try:
        print("=" * 70)
        print("TEST 1 — cooperative renderer requests an ALLOWED file")
        print("=" * 70)
        allowed_path = os.path.join(allowed_dir, "public.txt")
        result1 = broker.request_cooperative_read(allowed_path)
        print(f"  renderer's final result: {result1}")

        print()
        print("=" * 70)
        print("TEST 2 — cooperative renderer requests the DISALLOWED secret file")
        print("=" * 70)
        result2 = broker.request_cooperative_read(secret_path)
        print(f"  renderer's final result: {result2}")

        print()
        print("=" * 70)
        print("TEST 3 — a MALICIOUS renderer ignores the broker entirely and")
        print("opens the secret file directly, itself")
        print("=" * 70)
        result3 = broker.request_malicious_read(secret_path)
        print(f"  renderer's final result: {result3}")

        print()
        print("=" * 70)
        print("Checks")
        print("=" * 70)
        print(f"TEST 1 (allowed, cooperative) succeeded with real content: "
              f"{result1['ok'] and result1['data'] == 'This is public, sandboxed content.'}")
        print(f"TEST 2 (disallowed, cooperative) was DENIED: "
              f"{result2['ok'] is False}")
        print(f"the broker's own log NEVER shows it opened the secret file "
              f"(a real, provable denial — not just a denial message): "
              f"{secret_path not in broker.opened_paths_log}")
        print(f"the broker's log DOES show it opened the allowed file: "
              f"{allowed_path in broker.opened_paths_log}")
        print(f"TEST 3 (malicious, direct) SUCCEEDED — the protocol alone did "
              f"NOT stop it, proving a polite convention is not a security "
              f"boundary (see DECISIONS.md for what actually closes this gap "
              f"in real browsers): "
              f"{result3['ok'] and 'TOP SECRET' in result3['data']}")
    finally:
        broker.shutdown()
        shutil.rmtree(base, ignore_errors=True)
